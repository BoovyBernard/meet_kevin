"""
streamlit_fundamental_scanner_integrated.py

Full integrated Streamlit app:
 - Safe fundamental scanner (robust to yfinance changes)
 - SQLite watchlist & scan history
 - Automatic daily scans (APSheduler) while app runs
 - Sector / ETF groups (Wikipedia or CSV)
 - Technical indicators (RSI, MA short/long)
 - Configurable scoring weights in UI
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import sqlite3
import json
import traceback
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import create_engine
from typing import List, Dict

## ---------------------------
## Database / persistence
## ---------------------------
DB_FILE = "mk_scanner.db"

def init_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY,
            ticker TEXT UNIQUE,
            added_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS scan_results (
            id INTEGER PRIMARY KEY,
            ticker TEXT,
            ts TEXT,
            json TEXT
        )
    """)
    conn.commit()
    return conn

DB_CONN = init_db()
DB_ENGINE = create_engine(f"sqlite:///{DB_FILE}", echo=False)

def add_to_watchlist(ticker: str):
    ts = datetime.utcnow().isoformat()
    try:
        DB_CONN.execute("INSERT OR IGNORE INTO watchlist (ticker, added_at) VALUES (?,?)", (ticker.upper(), ts))
        DB_CONN.commit()
    except Exception as e:
        st.error(f"DB error adding watchlist: {e}")

def remove_from_watchlist(ticker: str):
    try:
        DB_CONN.execute("DELETE FROM watchlist WHERE ticker = ?", (ticker.upper(),))
        DB_CONN.commit()
    except Exception as e:
        st.error(f"DB error removing watchlist: {e}")

def get_watchlist() -> List[str]:
    cur = DB_CONN.execute("SELECT ticker FROM watchlist ORDER BY id")
    return [r[0] for r in cur.fetchall()]

def save_scan_result(ticker: str, obj: dict):
    ts = datetime.utcnow().isoformat()
    try:
        DB_CONN.execute("INSERT INTO scan_results (ticker, ts, json) VALUES (?,?,?)", (ticker.upper(), ts, json.dumps(obj)))
        DB_CONN.commit()
    except Exception as e:
        st.error(f"DB error saving scan result: {e}")

## ---------------------------
## Helpers: safe getters & TA
## ---------------------------

def safe_get(info, key, default=None):
    """
    Safe getter for:
    - dict-like objects (info)
    - yfinance .fast_info (attributes)
    - python objects with attributes
    Returns default if anything fails.
    """
    try:
        if info is None:
            return default
        if isinstance(info, dict):
            return info.get(key, default)
        # some yfinance objects expose attributes
        if hasattr(info, key):
            return getattr(info, key, default)
        # fallback: try key as attribute on object
        return default
    except Exception:
        return default

def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    ma_up = up.ewm(alpha=1/period, adjust=False).mean()
    ma_down = down.ewm(alpha=1/period, adjust=False).mean()
    rs = ma_up / ma_down
    rsi = 100 - (100 / (1 + rs))
    return rsi

def moving_average(series: pd.Series, window: int):
    return series.rolling(window=window, min_periods=1).mean()

def pct_change_safe(a, b):
    try:
        if pd.isna(a) or pd.isna(b) or b == 0:
            return np.nan
        return (a - b) / abs(b) * 100.0
    except Exception:
        return np.nan

def score_metric(value, thresholds):
    """Return -1/0/1 using (good, neutral) thresholds. NaN -> 0"""
    try:
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return 0
        good, neutral = thresholds
        if value >= good:
            return 1
        if value >= neutral:
            return 0
        return -1
    except Exception:
        return 0

## ---------------------------
## Fetch fundamentals (safe)
## ---------------------------

def fetch_fundamentals_safe(ticker: str):
    t = yf.Ticker(ticker)
    # yfinance sometimes raises; encapsulate
    info = {}
    fin = pd.DataFrame()
    bal = pd.DataFrame()
    cf = pd.DataFrame()
    earnings = pd.DataFrame()
    hist = pd.DataFrame()
    fast = {}
    try:
        # try both .info and .fast_info
        try:
            info = t.info if hasattr(t, "info") else {}
        except Exception:
            info = {}
        try:
            fast = t.fast_info if hasattr(t, "fast_info") else {}
        except Exception:
            fast = {}
        try:
            fin = t.financials
        except Exception:
            fin = pd.DataFrame()
        try:
            bal = t.balance_sheet
        except Exception:
            bal = pd.DataFrame()
        try:
            cf = t.cashflow
        except Exception:
            cf = pd.DataFrame()
        try:
            earnings = t.earnings
        except Exception:
            earnings = pd.DataFrame()
        try:
            hist = t.history(period="1y", interval="1d")
        except Exception:
            hist = pd.DataFrame()
    except Exception:
        traceback.print_exc()
    return {"info": info, "fast": fast, "fin": fin, "bal": bal, "cf": cf, "earnings": earnings, "hist": hist}

## ---------------------------
## Core analysis function (safe + robust)
## ---------------------------

def analyze_ticker_full_safe(ticker: str,
                             weights: Dict[str, float],
                             rsi_period: int = 14,
                             ma_short: int = 20,
                             ma_long: int = 50,
                             sector_median: Dict[str, float] = None):
    """
    Returns a dict with:
     - ticker, timestamp
     - snapshot: fundamental & TA values
     - metric_scores: -1/0/1 per metric
     - score_pct, recommendation
    """
    data = fetch_fundamentals_safe(ticker)
    info = data["info"]
    fast = data["fast"]
    fin = data["fin"]
    bal = data["bal"]
    cf = data["cf"]
    earnings = data["earnings"]
    hist = data["hist"]

    now = datetime.utcnow().isoformat()
    result = {"ticker": ticker.upper(), "timestamp": now}
    # MARKET INFO
    price = safe_get(fast, "last_price", None) or safe_get(info, "currentPrice", None)
    market_cap = safe_get(fast, "market_cap", None) or safe_get(info, "marketCap", None)
    beta = safe_get(info, "beta", None)
    result.update({"price": price, "market_cap": market_cap, "beta": beta})

    # FUNDAMENTALS (safe reads)
    try:
        revenue_ttm = fin.loc["Total Revenue"].iloc[0] if (not fin.empty and "Total Revenue" in fin.index) else np.nan
    except Exception:
        revenue_ttm = np.nan
    try:
        net_income_ttm = fin.loc["Net Income"].iloc[0] if (not fin.empty and "Net Income" in fin.index) else np.nan
    except Exception:
        net_income_ttm = np.nan
    try:
        operating_income_ttm = fin.loc["Operating Income"].iloc[0] if (not fin.empty and "Operating Income" in fin.index) else np.nan
    except Exception:
        operating_income_ttm = np.nan

    ebitda = safe_get(info, "ebitda", np.nan)
    # balance
    total_debt = bal.loc.get("Short Long Term Debt").iloc[0] if (not bal.empty and "Short Long Term Debt" in bal.index) else (bal.loc["Long Term Debt"].iloc[0] if (not bal.empty and "Long Term Debt" in bal.index) else np.nan) if not bal.empty else np.nan
    cash_and_equiv = bal.loc.get("Cash").iloc[0] if (not bal.empty and "Cash" in bal.index) else np.nan
    total_assets = bal.loc.get("Total Assets").iloc[0] if (not bal.empty and "Total Assets" in bal.index) else np.nan
    shareholders_equity = bal.loc.get("Total Stockholder Equity").iloc[0] if (not bal.empty and "Total Stockholder Equity" in bal.index) else np.nan
    current_assets = bal.loc.get("Total Current Assets").iloc[0] if (not bal.empty and "Total Current Assets" in bal.index) else np.nan
    current_liab = bal.loc.get("Total Current Liabilities").iloc[0] if (not bal.empty and "Total Current Liabilities" in bal.index) else np.nan

    # cashflow
    try:
        cfo = cf.loc["Total Cash From Operating Activities"].iloc[0] if (not cf.empty and "Total Cash From Operating Activities" in cf.index) else np.nan
    except Exception:
        cfo = np.nan
    capex = cf.loc.get("Capital Expenditures").iloc[0] if (not cf.empty and "Capital Expenditures" in cf.index) else np.nan
    free_cash_flow = np.nan
    if not pd.isna(cfo) and not pd.isna(capex):
        free_cash_flow = cfo + capex  # capex reported negative on yfinance

    # valuations & ratios
    pe = safe_get(info, "trailingPE", np.nan)
    forward_pe = safe_get(info, "forwardPE", np.nan)
    peg = safe_get(info, "pegRatio", np.nan)
    ps = safe_get(info, "priceToSalesTrailing12Months", np.nan)
    dividend_yield = safe_get(info, "dividendYield", 0.0) or 0.0

    # margins & returns
    gross_profit = fin.loc.get("Gross Profit").iloc[0] if (not fin.empty and "Gross Profit" in fin.index) else np.nan
    gross_margin = (safe_div := (lambda a, b: a/b if (not pd.isna(a) and not pd.isna(b) and b != 0) else np.nan))(gross_profit, revenue_ttm)
    op_margin = safe_div(operating_income_ttm, revenue_ttm)
    net_margin = safe_div(net_income_ttm, revenue_ttm)
    roe = safe_div(net_income_ttm, shareholders_equity)
    roa = safe_div(net_income_ttm, total_assets)

    # leverage metrics
    debt_equity = safe_div(total_debt, shareholders_equity)
    net_debt = np.nan if pd.isna(total_debt) or pd.isna(cash_and_equiv) else (total_debt - cash_and_equiv)
    net_debt_ebitda = np.nan
    if not pd.isna(ebitda) and not pd.isna(net_debt):
        try:
            net_debt_ebitda = net_debt / ebitda if ebitda != 0 else np.nan
        except Exception:
            net_debt_ebitda = np.nan
    interest_expense = fin.loc.get("Interest Expense").iloc[0] if (not fin.empty and "Interest Expense" in fin.index) else np.nan
    interest_cov = safe_div(operating_income_ttm, abs(interest_expense)) if not pd.isna(interest_expense) else np.nan
    current_ratio = safe_div(current_assets, current_liab)

    # growth (yoy)
    revenue_yoy = np.nan
    netinc_yoy = np.nan
    try:
        if fin.shape[1] >= 2 and "Total Revenue" in fin.index:
            rev_latest = fin.loc["Total Revenue"].iloc[0]
            rev_prev = fin.loc["Total Revenue"].iloc[1]
            revenue_yoy = pct_change_safe(rev_latest, rev_prev)
    except Exception:
        revenue_yoy = np.nan
    try:
        if not earnings.empty and "Earnings" in earnings.columns and earnings.shape[0] >= 2:
            netinc_yoy = pct_change_safe(earnings["Earnings"].iloc[-1], earnings["Earnings"].iloc[-2])
    except Exception:
        netinc_yoy = np.nan

    # technical indicators
    rsi_val = np.nan
    ma_short_val = np.nan
    ma_long_val = np.nan
    if not hist.empty and "Close" in hist.columns and len(hist) >= max(5, ma_long):
        close = hist["Close"].dropna()
        try:
            rsi_series = compute_rsi(close, period=rsi_period)
            rsi_val = rsi_series.iloc[-1] if not rsi_series.empty else np.nan
        except Exception:
            rsi_val = np.nan
        try:
            ma_short_val = moving_average(close, ma_short).iloc[-1]
            ma_long_val = moving_average(close, ma_long).iloc[-1]
        except Exception:
            ma_short_val = np.nan
            ma_long_val = np.nan

    # snapshot pack
    snapshot = {
        "price": price,
        "market_cap": market_cap,
        "pe": pe,
        "forward_pe": forward_pe,
        "peg": peg,
        "ps": ps,
        "dividend_yield_pct": dividend_yield * 100 if not pd.isna(dividend_yield) else 0.0,
        "gross_margin_pct": gross_margin * 100 if not pd.isna(gross_margin) else np.nan,
        "op_margin_pct": op_margin * 100 if not pd.isna(op_margin) else np.nan,
        "net_margin_pct": net_margin * 100 if not pd.isna(net_margin) else np.nan,
        "revenue_yoy_pct": revenue_yoy,
        "netinc_yoy_pct": netinc_yoy,
        "fcf": free_cash_flow,
        "fcf_yield_pct": safe_div(free_cash_flow, market_cap) * 100 if (not pd.isna(free_cash_flow) and not pd.isna(market_cap) and market_cap != 0) else np.nan,
        "debt_equity": debt_equity,
        "net_debt_ebitda": net_debt_ebitda,
        "interest_coverage": interest_cov,
        "current_ratio": current_ratio,
        "rsi": rsi_val,
        "ma_short": ma_short_val,
        "ma_long": ma_long_val,
        "52w_high": safe_get(info, "fiftyTwoWeekHigh", np.nan),
        "52w_low": safe_get(info, "fiftyTwoWeekLow", np.nan)
    }

    # ---------------------------
    # Metric scoring (opinionated)
    # ---------------------------
    metric_scores = {}
    metric_scores["valuation_pe"] = score_metric(-snapshot["pe"] if not pd.isna(snapshot["pe"]) else np.nan, (-15, -25))
    metric_scores["peg"] = score_metric(-snapshot["peg"] if not pd.isna(snapshot["peg"]) else np.nan, (-1.5, -2.5))
    metric_scores["p_s"] = score_metric(-snapshot["ps"] if not pd.isna(snapshot["ps"]) else np.nan, (-3, -5))
    metric_scores["fcf_yield"] = score_metric(snapshot["fcf_yield_pct"] if not pd.isna(snapshot["fcf_yield_pct"]) else np.nan, (5.0, 2.5))
    metric_scores["revenue_growth"] = score_metric(snapshot["revenue_yoy_pct"] if not pd.isna(snapshot["revenue_yoy_pct"]) else np.nan, (10.0, 3.0))
    metric_scores["netinc_growth"] = score_metric(snapshot["netinc_yoy_pct"] if not pd.isna(snapshot["netinc_yoy_pct"]) else np.nan, (10.0, 0.0))
    metric_scores["op_margin"] = score_metric(snapshot["op_margin_pct"] if not pd.isna(snapshot["op_margin_pct"]) else np.nan, (15.0, 5.0))
    metric_scores["net_margin"] = score_metric(snapshot["net_margin_pct"] if not pd.isna(snapshot["net_margin_pct"]) else np.nan, (10.0, 3.0))
    metric_scores["roe"] = score_metric(roe*100 if not pd.isna(roe) else np.nan, (15.0, 8.0))
    metric_scores["debt_eq"] = score_metric(-snapshot["debt_equity"] if not pd.isna(snapshot["debt_equity"]) else np.nan, (-1.0, -2.0))
    metric_scores["net_debt_ebitda"] = score_metric(-snapshot["net_debt_ebitda"] if not pd.isna(snapshot["net_debt_ebitda"]) else np.nan, (-3.0, -4.0))
    metric_scores["interest_cov"] = score_metric(snapshot["interest_coverage"] if not pd.isna(snapshot["interest_coverage"]) else np.nan, (5.0, 2.0))
    metric_scores["current_ratio"] = score_metric(snapshot["current_ratio"] if not pd.isna(snapshot["current_ratio"]) else np.nan, (1.5, 1.0))

    # Technical aggregate
    tech_score = 0
    if not pd.isna(snapshot["rsi"]):
        if 30 <= snapshot["rsi"] <= 60:
            tech_score += 1
        elif snapshot["rsi"] > 70:
            tech_score -= 1
    if not pd.isna(snapshot["ma_short"]) and not pd.isna(snapshot["ma_long"]):
        if snapshot["ma_short"] > snapshot["ma_long"]:
            tech_score += 1
        else:
            tech_score -= 1
    metric_scores["tech"] = int(np.sign(tech_score))  # -1/0/1

    # ---------------------------
    # Weighted aggregation
    # ---------------------------
    weighted_sum = 0.0
    total_weight = 0.0
    for k, w in weights.items():
        total_weight += w
        weighted_sum += metric_scores.get(k, 0) * w

    # Convert to 0..100
    if total_weight <= 0:
        score_pct = 50.0
    else:
        normalized = (weighted_sum + total_weight) / (2 * total_weight)  # 0..1
        score_pct = max(0.0, min(100.0, normalized * 100.0))

    # Sector adjustment (optional, small)
    if sector_median:
        med_fcf = sector_median.get("fcf_yield_pct", np.nan)
        if not pd.isna(med_fcf) and not pd.isna(snapshot.get("fcf_yield_pct")):
            if snapshot["fcf_yield_pct"] < med_fcf:
                # small penalty proportional to weights
                score_pct = max(0.0, score_pct - 3.0)

    # recommendation
    if score_pct >= 65:
        rec = "BUY"
    elif score_pct >= 45:
        rec = "HOLD"
    else:
        rec = "SELL"

    result.update({"snapshot": snapshot, "metric_scores": metric_scores, "score_pct": round(float(score_pct), 2), "recommendation": rec})
    return result

## ---------------------------
## Groups loader (wikipedia)
## ---------------------------
@st.cache_data(ttl=60*60)
def load_wikipedia_constituents(list_name: str):
    mapping = {
        "S&P 500": "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
        "NASDAQ-100": "https://en.wikipedia.org/wiki/Nasdaq-100",
        "Dow 30": "https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average"
    }
    if list_name not in mapping:
        return []
    url = mapping[list_name]
    try:
        tables = pd.read_html(url)
        for t in tables:
            cols = [c.lower() for c in t.columns]
            if any("symbol" in c or "ticker" in c for c in cols):
                symbol_col = next(c for c in t.columns if "symbol" in str(c).lower() or "ticker" in str(c).lower())
                tickers = t[symbol_col].astype(str).str.replace('.', '-', regex=False).str.strip().tolist()
                return tickers
    except Exception:
        return []
    return []

## ---------------------------
## Scheduler for auto scans
## ---------------------------
scheduler = BackgroundScheduler()
scheduler_started = False

def schedule_daily_scan(tickers: List[str], weights: Dict[str,float], job_id="daily_scan_job"):
    global scheduler_started
    if not scheduler_started:
        scheduler.start()
        scheduler_started = True

    def do_scan():
        for tk in tickers:
            try:
                res = analyze_ticker_full_safe(tk, weights)
                save_scan_result(tk, res)
            except Exception:
                traceback.print_exc()

    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass
    # run immediately and then every 24 hours
    scheduler.add_job(do_scan, 'interval', hours=24, id=job_id, next_run_time=datetime.utcnow())

## ---------------------------
## Streamlit UI
## ---------------------------
st.set_page_config(page_title="MK Fundamental Scanner — Integrated", layout="wide")
st.title("📈 MK Fundamental Scanner — Integrated")

# Sidebar: watchlist management, settings
st.sidebar.header("Watchlist & Scan Settings")

with st.sidebar.expander("Watchlist"):
    ticker_input = st.text_input("Add ticker to watchlist (comma-separated)", value="")
    if st.button("Add to watchlist"):
        for t in [x.strip().upper() for x in ticker_input.split(",") if x.strip()]:
            add_to_watchlist(t)
        st.experimental_rerun()

    wl = get_watchlist()
    st.write("Saved watchlist:")
    if wl:
        for t in wl:
            col1, col2 = st.columns([3,1])
            col1.write(t)
            if col2.button(f"Remove {t}", key=f"rm_{t}"):
                remove_from_watchlist(t)
                st.experimental_rerun()
    else:
        st.write("_empty_")

st.sidebar.header("Groups")
group_choice = st.sidebar.selectbox("Choose a group", ["--select--", "S&P 500", "NASDAQ-100", "Dow 30", "Small sample (AAPL,MSFT,AMZN)", "Upload CSV"])
uploaded_group = None
if group_choice == "Upload CSV":
    uploaded = st.sidebar.file_uploader("Upload CSV of tickers (single column)", type=["csv","txt"])
    if uploaded:
        try:
            dfu = pd.read_csv(uploaded, header=None)
            uploaded_group = dfu.iloc[:,0].astype(str).str.strip().tolist()
            st.sidebar.success(f"Loaded {len(uploaded_group)} tickers")
        except Exception as e:
            st.sidebar.error(f"CSV error: {e}")

st.sidebar.header("Technical indicator params")
rsi_period = st.sidebar.number_input("RSI period", value=14, min_value=5, max_value=50)
ma_short = st.sidebar.number_input("MA short window", value=20, min_value=5, max_value=200)
ma_long = st.sidebar.number_input("MA long window", value=50, min_value=5, max_value=400)

st.sidebar.header("Scoring weights (sliders)")
default_weights = {
    "valuation_pe": 0.08, "peg": 0.06, "p_s": 0.04, "fcf_yield": 0.08,
    "revenue_growth": 0.08, "netinc_growth": 0.06, "op_margin": 0.06,
    "net_margin": 0.05, "roe": 0.06, "debt_eq": 0.05, "net_debt_ebitda": 0.05,
    "interest_cov": 0.04, "current_ratio": 0.03, "tech": 0.06
}
weights_ui = {}
for key, val in default_weights.items():
    weights_ui[key] = st.sidebar.slider(key, min_value=0.0, max_value=0.3, value=float(val), step=0.01)

# Normalize weights so they sum to 1 (if all zero, keep defaults)
sum_w = sum(weights_ui.values())
if sum_w == 0:
    final_weights = default_weights
else:
    final_weights = {k: (v / sum_w) for k, v in weights_ui.items()}

st.sidebar.header("Auto scan & persistence")
auto_scan_toggle = st.sidebar.checkbox("Enable automatic daily scans (while app runs)", value=False)
if auto_scan_toggle:
    watch = get_watchlist() or ["AAPL", "MSFT"]
    schedule_daily_scan(watch, final_weights)
    st.sidebar.success("Scheduled daily scan (runs while app is running). Results saved to SQLite.")

# ---------------------------
# Main: scan runner
# ---------------------------
col1, col2 = st.columns([2,1])
with col1:
    st.header("Run a scan")
    tickers_text = st.text_area("Tickers to scan (comma-separated) — leave blank to use watchlist or group", value="")
    tickers_list = [t.strip().upper() for t in tickers_text.split(",") if t.strip()]

    if not tickers_list:
        if uploaded_group:
            tickers_list = uploaded_group
        elif group_choice in ["S&P 500", "NASDAQ-100", "Dow 30"]:
            with st.spinner("Fetching group tickers from Wikipedia (cached)..."):
                tickers_list = load_wikipedia_constituents(group_choice)
                if not tickers_list:
                    st.warning("Could not fetch group; try uploading CSV or use watchlist.")
        elif group_choice == "Small sample (AAPL,MSFT,AMZN)":
            tickers_list = ["AAPL","MSFT","AMZN"]
        else:
            tickers_list = get_watchlist()

    st.write(f"Tickers to scan: {len(tickers_list)}")
    run_now = st.button("Run scan now")

    if run_now:
        results = []
        df_rows = []
        progress = st.progress(0)
        n = max(1, len(tickers_list))
        for i, tk in enumerate(tickers_list):
            try:
                res = analyze_ticker_full_safe(tk, final_weights, rsi_period=rsi_period, ma_short=ma_short, ma_long=ma_long)
                results.append(res)
                save_scan_result(tk, res)
                # safe row
                score_val = res.get("score_pct", 0.0)
                snap = res.get("snapshot", {})
                df_rows.append({
                    "ticker": res.get("ticker", tk),
                    "price": snap.get("price"),
                    "score": score_val,
                    "recommendation": res.get("recommendation"),
                    "fcf_yield_pct": snap.get("fcf_yield_pct"),
                    "rsi": snap.get("rsi"),
                    "ma_short": snap.get("ma_short"),
                    "ma_long": snap.get("ma_long")
                })
            except Exception as e:
                st.error(f"Error scanning {tk}: {e}")
                traceback.print_exc()
                df_rows.append({"ticker": tk, "price": None, "score": 0.0, "recommendation": "ERROR"})
            progress.progress((i+1)/n)

        # Build DataFrame safely
        df = pd.DataFrame(df_rows)
        if "score" not in df.columns:
            df["score"] = 0.0
        df = df.sort_values("score", ascending=False).reset_index(drop=True)
        st.success("Scan complete")
        st.subheader("Results")
        st.dataframe(df)

        # detailed cards
        for r in results:
            st.markdown("---")
            st.subheader(f"{r['ticker']}  —  {r['recommendation']}  —  Score: {r['score_pct']}")
            snap = r.get("snapshot", {})
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Price", f"${snap.get('price'):.2f}" if snap.get('price') is not None else "N/A")
            c2.metric("FCF yield", f"{snap.get('fcf_yield_pct'):.2f}%" if snap.get('fcf_yield_pct') is not None else "N/A")
            c3.metric("RSI", f"{snap.get('rsi'):.2f}" if snap.get('rsi') is not None else "N/A")
            c4.metric("MA short / long", f"{snap.get('ma_short'):.2f}/{snap.get('ma_long'):.2f}" if snap.get('ma_short') is not None and snap.get('ma_long') is not None else "N/A")
            with st.expander("Full snapshot & metric scores"):
                st.json(r)

        csv = df.to_csv(index=False)
        st.download_button("Download scan results CSV", csv, "mk_scan_results.csv", "text/csv")

with col2:
    st.header("Quick tools & history")
    st.write("Recent scan history")
    try:
        cur = DB_CONN.execute("SELECT ticker, ts FROM scan_results ORDER BY id DESC LIMIT 10")
        rows = cur.fetchall()
        if rows:
            for tk, ts in rows:
                st.write(f"{tk}  —  {ts}")
        else:
            st.write("_no history yet_")
    except Exception:
        st.write("_history not available_")

    st.markdown("---")
    st.write("Reset DB (watchlist + history)")
    if st.button("Reset DB (danger!)"):
        DB_CONN.close()
        import os
        try:
            os.remove(DB_FILE)
            st.warning("Database removed. Please refresh the app.")
            st.stop()
        except Exception as e:
            st.error(f"Could not remove DB: {e}")

st.markdown("---")
st.caption("Notes: Automatic daily scans run only while the app process is alive. To run 24/7 deploy on a server/VM and keep the process running.")
