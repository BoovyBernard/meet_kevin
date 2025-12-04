"""
streamlit_fundamental_scanner_full.py

Meet-Kevin style fundamental scanner with:
 - SQLite watchlist persistence
 - Automatic daily scans (background scheduler while app runs)
 - Sector / ETF groups (live fetch from Wikipedia OR upload your own)
 - Technical indicators: RSI, moving averages
 - Configurable scoring weights + sector-normalization

Run:
pip install streamlit yfinance pandas numpy sqlalchemy apscheduler
streamlit run streamlit_fundamental_scanner_full.py
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import sqlite3
import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import create_engine
from typing import List, Dict

# ---------------------------
# Database / persistence
# ---------------------------

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

def save_scan_result(ticker: str, js: str):
    ts = datetime.utcnow().isoformat()
    DB_CONN.execute("INSERT INTO scan_results (ticker, ts, json) VALUES (?,?,?)", (ticker.upper(), ts, js))
    DB_CONN.commit()

# ---------------------------
# Utility & technical indicators
# ---------------------------

def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    # Standard RSI calculation
    delta = series.diff().dropna()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.ewm(alpha=1/period, adjust=False).mean()
    ma_down = down.ewm(alpha=1/period, adjust=False).mean()
    rs = ma_up / ma_down
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.reindex(series.index)  # align
    return rsi

def moving_average(series: pd.Series, window: int):
    return series.rolling(window=window, min_periods=1).mean()

# ---------------------------
# Fundamental analysis logic
# ---------------------------

def safe_div(a, b):
    try:
        return a / b
    except Exception:
        return np.nan

def pct_change(a, b):
    try:
        if pd.isna(a) or pd.isna(b) or b == 0:
            return np.nan
        return (a - b) / abs(b) * 100.0
    except Exception:
        return np.nan

def score_metric(value, thresholds):
    """
    thresholds: (good_cutoff, neutral_cutoff)
    returns +1/0/-1
    """
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return 0
    good, neutral = thresholds
    if value >= good:
        return 1
    if value >= neutral:
        return 0
    return -1

def fetch_fundamentals(ticker: str):
    # Light wrapper around yfinance to get needed fields. Keep exceptions contained.
    t = yf.Ticker(ticker)
    info = {}
    try:
        info = t.info
    except Exception:
        info = {}
    # statements
    fin = pd.DataFrame()
    bal = pd.DataFrame()
    cf = pd.DataFrame()
    earnings = pd.DataFrame()
    try:
        fin = t.financials
        bal = t.balance_sheet
        cf = t.cashflow
        earnings = t.earnings
    except Exception:
        pass
    hist = pd.DataFrame()
    try:
        hist = t.history(period="1y", interval="1d")
    except Exception:
        pass
    return {"info": info, "fin": fin, "bal": bal, "cf": cf, "earnings": earnings, "hist": hist}

def analyze_ticker_full(ticker: str, weights: Dict[str, float], rsi_period:int=14, ma_short:int=20, ma_long:int=50, sector_median:Dict[str, float]=None):
    data = fetch_fundamentals(ticker)
    info = data["info"]
    fin = data["fin"]
    bal = data["bal"]
    cf = data["cf"]
    earnings = data["earnings"]
    hist = data["hist"]

    result = {"ticker": ticker.upper(), "timestamp": datetime.utcnow().isoformat()}

    # Market & basic info
    price = info.get("currentPrice") or (hist["Close"].iloc[-1] if not hist.empty else np.nan)
    market_cap = info.get("marketCap", np.nan)
    beta = info.get("beta", np.nan)
    fifty_two_week_high = info.get("fiftyTwoWeekHigh", np.nan)
    fifty_two_week_low = info.get("fiftyTwoWeekLow", np.nan)
    result.update({"price": price, "market_cap": market_cap, "beta": beta})

    # Fundamentals - safe reads
    try:
        revenue_ttm = fin.loc["Total Revenue"].iloc[0]
    except Exception:
        revenue_ttm = np.nan
    try:
        net_income_ttm = fin.loc["Net Income"].iloc[0]
    except Exception:
        net_income_ttm = np.nan
    try:
        operating_income_ttm = fin.loc["Operating Income"].iloc[0]
    except Exception:
        operating_income_ttm = np.nan
    ebitda = info.get("ebitda", np.nan)

    total_debt = bal.loc.get("Short Long Term Debt", pd.Series([np.nan])).iloc[0] if not bal.empty else np.nan
    cash_and_equiv = bal.loc.get("Cash", pd.Series([np.nan])).iloc[0] if not bal.empty else np.nan
    total_assets = bal.loc.get("Total Assets", pd.Series([np.nan])).iloc[0] if not bal.empty else np.nan
    shareholders_equity = bal.loc.get("Total Stockholder Equity", pd.Series([np.nan])).iloc[0] if not bal.empty else np.nan
    current_assets = bal.loc.get("Total Current Assets", pd.Series([np.nan])).iloc[0] if not bal.empty else np.nan
    current_liab = bal.loc.get("Total Current Liabilities", pd.Series([np.nan])).iloc[0] if not bal.empty else np.nan

    # cashflow
    try:
        cfo = cf.loc["Total Cash From Operating Activities"].iloc[0]
    except Exception:
        cfo = np.nan
    capex = cf.loc.get("Capital Expenditures", pd.Series([np.nan])).iloc[0] if not cf.empty else np.nan
    free_cash_flow = np.nan
    if not pd.isna(cfo) and not pd.isna(capex):
        free_cash_flow = cfo + capex  # yfinance reports capex as negative
    # valuations
    pe = info.get("trailingPE", np.nan)
    forward_pe = info.get("forwardPE", np.nan)
    peg = info.get("pegRatio", np.nan)
    ps = info.get("priceToSalesTrailing12Months", np.nan)
    dividend_yield = info.get("dividendYield", 0.0) or 0.0
    # margins / returns
    gross_profit = fin.loc.get("Gross Profit", pd.Series([np.nan])).iloc[0] if not fin.empty else np.nan
    gross_margin = safe_div(gross_profit, revenue_ttm)
    op_margin = safe_div(operating_income_ttm, revenue_ttm)
    net_margin = safe_div(net_income_ttm, revenue_ttm)
    roe = safe_div(net_income_ttm, shareholders_equity)
    roa = safe_div(net_income_ttm, total_assets)
    # leverage
    debt_equity = safe_div(total_debt, shareholders_equity)
    net_debt = np.nan if pd.isna(total_debt) or pd.isna(cash_and_equiv) else (total_debt - cash_and_equiv)
    net_debt_ev = np.nan
    if not pd.isna(ebitda) and not pd.isna(net_debt) and not pd.isna(market_cap):
        try:
            enterprise_value = market_cap + net_debt
            net_debt_ev = safe_div(net_debt, ebitda) if ebitda != 0 else np.nan
        except Exception:
            net_debt_ev = np.nan
    interest_expense = fin.loc.get("Interest Expense", pd.Series([np.nan])).iloc[0] if not fin.empty else np.nan
    interest_cov = safe_div(operating_income_ttm, abs(interest_expense)) if not pd.isna(interest_expense) else np.nan
    current_ratio = safe_div(current_assets, current_liab) if (not pd.isna(current_assets) and not pd.isna(current_liab)) else np.nan

    # growth
    revenue_yoy = np.nan
    netinc_yoy = np.nan
    try:
        if fin.shape[1] >= 2:
            rev_latest = fin.loc["Total Revenue"].iloc[0]
            rev_prev = fin.loc["Total Revenue"].iloc[1]
            revenue_yoy = pct_change(rev_latest, rev_prev)
    except Exception:
        pass
    try:
        if not earnings.empty and earnings.shape[0] >= 2:
            netinc_yoy = pct_change(earnings["Earnings"].iloc[-1], earnings["Earnings"].iloc[-2])
    except Exception:
        pass

    # price history indicators
    rsi_val = np.nan
    ma_short_val = np.nan
    ma_long_val = np.nan
    if not hist.empty:
        hist = hist.dropna(subset=["Close"])
        hist_close = hist["Close"]
        rsi_series = compute_rsi(hist_close, period=rsi_period)
        rsi_val = rsi_series.iloc[-1] if not rsi_series.empty else np.nan
        ma_short_val = moving_average(hist_close, ma_short).iloc[-1] if ma_short > 0 else np.nan
        ma_long_val = moving_average(hist_close, ma_long).iloc[-1] if ma_long > 0 else np.nan

    # pack snapshot
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
        "net_debt_ebitda": net_debt_ev,
        "interest_coverage": interest_cov,
        "current_ratio": current_ratio,
        "rsi": rsi_val,
        "ma_short": ma_short_val,
        "ma_long": ma_long_val,
        "beta": beta,
        "52w_high": fifty_two_week_high,
        "52w_low": fifty_two_week_low
    }

    # ---------------------------
    # Scoring (weighted)
    # ---------------------------
    # Default thresholds tuned to Meet-Kevin style (editable by user in UI)
    metric_scores = {}

    metric_scores["valuation_pe"] = score_metric(-pe if not pd.isna(pe) else np.nan, ( -15, -25))
    metric_scores["peg"] = score_metric(-peg if not pd.isna(peg) else np.nan, (-1.5, -2.5))
    metric_scores["p_s"] = score_metric(-ps if not pd.isna(ps) else np.nan, (-3, -5))
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

    # Technical signals (RSI & MA crossover)
    tech_score = 0
    if not pd.isna(snapshot["rsi"]):
        # prefer RSI between 30 and 70 (not extreme overbought). Slightly reward 30-60 range.
        if 30 <= snapshot["rsi"] <= 60:
            tech_score += 1
        elif snapshot["rsi"] < 30:
            tech_score += 0  # oversold — mixed (user can tune)
        else:
            tech_score -= 1
    # MA crossover (short vs long)
    if not pd.isna(snapshot["ma_short"]) and not pd.isna(snapshot["ma_long"]):
        if snapshot["ma_short"] > snapshot["ma_long"]:
            tech_score += 1
        else:
            tech_score -= 1
    metric_scores["tech"] = np.sign(tech_score)  # -1 / 0 / 1

    # Now apply user weights (weights param passed from UI)
    weighted_sum = 0.0
    total_weight = 0.0
    for m, w in weights.items():
        total_weight += w
        weighted_sum += metric_scores.get(m, 0) * w

    # normalize weighted_sum from -total_weight..+total_weight to 0..100
    if total_weight <= 0:
        score_pct = 50.0
    else:
        normalized = (weighted_sum + total_weight) / (2 * total_weight)  # 0..1
        score_pct = max(0.0, min(100.0, normalized * 100.0))

    # sector normalization (optional)
    sector_flag = False
    if sector_median:
        # If sector_median has 'fcf_yield_pct' etc., adjust score slightly if below sector median
        sector_flag = True
        adjustments = 0.0
        # Example: penalize if fcf_yield below median
        med_fcf = sector_median.get("fcf_yield_pct", np.nan)
        if not pd.isna(med_fcf) and not pd.isna(snapshot["fcf_yield_pct"]):
            if snapshot["fcf_yield_pct"] < med_fcf:
                adjustments -= 0.02 * total_weight  # small penalty applied to weighted sum
        # apply adjustment (convert to percent like earlier)
        if total_weight > 0:
            normalized = (weighted_sum + adjustments + total_weight) / (2 * total_weight)
            score_pct = max(0.0, min(100.0, normalized * 100.0))

    # recommendation thresholds - configurable in UI (but here default)
    if score_pct >= 65:
        rec = "BUY"
    elif score_pct >= 45:
        rec = "HOLD"
    else:
        rec = "SELL"

    # final result pack
    result.update({"snapshot": snapshot, "metric_scores": metric_scores,
                   "raw_weighted": weighted_sum, "score_pct": round(score_pct,2),
                   "recommendation": rec, "sector_adjusted": sector_flag})

    return result

# ---------------------------
# Sector / group helpers
# ---------------------------

@st.cache_data(ttl=60*60)
def load_wikipedia_constituents(list_name: str):
    """
    Accepts 'S&P 500', 'NASDAQ-100', 'Dow 30' and returns list of tickers by scraping Wikipedia.
    This runs at app runtime and is live.
    """
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
        # heuristics: for S&P500 first table contains tickers in 'Symbol' or 'Ticker symbol'
        for t in tables:
            cols = [c.lower() for c in t.columns]
            if any("symbol" in c or "ticker" in c for c in cols):
                # pick the column name that contains symbol
                symbol_col = next(c for c in t.columns if "symbol" in str(c).lower() or "ticker" in str(c).lower())
                tickers = t[symbol_col].astype(str).str.replace('.', '-', regex=False).str.strip().tolist()
                return tickers
    except Exception:
        return []
    return []

# ---------------------------
# Background scheduler for automatic daily scans
# ---------------------------

scheduler = BackgroundScheduler()
scheduler_started = False

def schedule_daily_scan(tickers: List[str], job_id="daily_scan_job"):
    global scheduler_started
    if not scheduler_started:
        scheduler.start()
        scheduler_started = True

    def do_scan():
        # iterate tickers, run analyze_ticker_full with default weights
        # Use simple weights (these will be overridden by UI when run interactively)
        default_weights = {
            "valuation_pe": 0.08, "peg": 0.06, "p_s": 0.04, "fcf_yield": 0.08,
            "revenue_growth": 0.08, "netinc_growth": 0.06, "op_margin": 0.06,
            "net_margin": 0.05, "roe": 0.06, "debt_eq": 0.05, "net_debt_ebitda": 0.05,
            "interest_cov": 0.04, "current_ratio": 0.03, "tech": 0.06
        }
        for tk in tickers:
            try:
                res = analyze_ticker_full(tk, default_weights)
                save_scan_result(tk, str(res))
            except Exception:
                pass

    # Remove existing
    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass
    # schedule at ~ 08:00 UTC daily by default — but we allow immediate run in UI
    scheduler.add_job(do_scan, 'interval', hours=24, id=job_id, next_run_time=datetime.utcnow())
    return True

# ---------------------------
# Streamlit UI
# ---------------------------

st.set_page_config(page_title="MK Fundamental Scanner (Full)", layout="wide")
st.title("📈 MK Fundamental Scanner — Full (SQLite, Scheduler, TA, Groups)")

# Sidebar: watchlist management, settings
st.sidebar.header("Watchlist & Scan Settings")

# Watchlist controls
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

# Groups section
st.sidebar.header("Sector / Groups")
group_choice = st.sidebar.selectbox("Choose a preset group (or upload your own)", ["--select--", "S&P 500", "NASDAQ-100", "Dow 30", "Small sample (AAPL,MSFT,AMZN)", "Upload CSV"])
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

# Scanning parameters
st.sidebar.header("Technical indicator params")
rsi_period = st.sidebar.number_input("RSI period", value=14, min_value=5, max_value=50)
ma_short = st.sidebar.number_input("MA short window", value=20, min_value=5, max_value=200)
ma_long = st.sidebar.number_input("MA long window", value=50, min_value=5, max_value=400)

st.sidebar.header("Scoring weights (sum will be normalized)")
# default weights (same keys expected in analyze function)
default_weights = {
    "valuation_pe": 0.08, "peg": 0.06, "p_s": 0.04, "fcf_yield": 0.08,
    "revenue_growth": 0.08, "netinc_growth": 0.06, "op_margin": 0.06,
    "net_margin": 0.05, "roe": 0.06, "debt_eq": 0.05, "net_debt_ebitda": 0.05,
    "interest_cov": 0.04, "current_ratio": 0.03, "tech": 0.06
}
weights_ui = {}
for key, val in default_weights.items():
    weights_ui[key] = st.sidebar.slider(key, min_value=0.0, max_value=0.3, value=float(val), step=0.01)

# Normalize weights to sum to 1 (but keep relative)
sum_weights = sum(weights_ui.values())
if sum_weights == 0:
    final_weights = weights_ui
else:
    final_weights = {k: (v / sum_weights) for k, v in weights_ui.items()}

st.sidebar.header("Auto scan & persistence")
auto_scan_toggle = st.sidebar.checkbox("Enable automatic daily scans (while app runs)", value=False)
if auto_scan_toggle:
    schedule_daily_scan(get_watchlist() or ["AAPL","MSFT"])
    st.sidebar.success("Scheduled daily scan (runs while app is running). Results saved to SQLite.")

# ---------------------------
# Main app area
# ---------------------------

col1, col2 = st.columns([2,1])
with col1:
    st.header("Scan runner")
    tickers_text = st.text_area("Tickers to scan (comma-separated) — blank to use watchlist or group", value="")
    # prepare tickers list
    tickers_list = [t.strip().upper() for t in tickers_text.split(",") if t.strip()]
    # if empty, use uploaded group -> preset -> watchlist
    if not tickers_list:
        if uploaded_group:
            tickers_list = uploaded_group
        elif group_choice in ["S&P 500", "NASDAQ-100", "Dow 30"]:
            with st.spinner("Fetching group tickers from Wikipedia (cached)..."):
                tickers_list = load_wikipedia_constituents(group_choice)
                if not tickers_list:
                    st.warning("Could not fetch group; try Upload CSV or use watchlist.")
        elif group_choice == "Small sample (AAPL,MSFT,AMZN)":
            tickers_list = ["AAPL","MSFT","AMZN"]
        else:
            tickers_list = get_watchlist()

    st.write(f"Tickers to scan: {len(tickers_list)} tickers")
    run_now = st.button("Run scan now")

    if run_now:
        results = []
        progress = st.progress(0)
        n = max(1, len(tickers_list))
        for i, tk in enumerate(tickers_list):
            try:
                res = analyze_ticker_full(tk, final_weights, rsi_period=rsi_period, ma_short=ma_short, ma_long=ma_long)
                results.append(res)
                save_scan_result(tk, str(res))
            except Exception as e:
                st.error(f"Error scanning {tk}: {e}")
            progress.progress((i+1)/n)
        st.success("Scan complete")
        # display summary table
        df_rows = []
        for r in results:
            s = r["snapshot"]
            df_rows.append({
                "ticker": r["ticker"],
                "price": s["price"],
                "score": r["score_pct"],
                "rec": r["recommendation"],
                "fcf_yield_pct": s.get("fcf_yield_pct"),
                "rsi": s.get("rsi"),
                "ma_short": s.get("ma_short"),
                "ma_long": s.get("ma_long")
            })
        df = pd.DataFrame(df_rows).sort_values("score", ascending=False)
        st.dataframe(df.reset_index(drop=True))

        # Expand results cards
        for r in results:
            st.markdown("---")
            st.subheader(f"{r['ticker']}  —  {r['recommendation']}  —  Score: {r['score_pct']}")
            snap = r["snapshot"]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Price", f"${snap['price']:.2f}" if not pd.isna(snap['price']) else "N/A")
            c2.metric("FCF yield", f"{snap.get('fcf_yield_pct'):.2f}%" if not pd.isna(snap.get('fcf_yield_pct')) else "N/A")
            c3.metric("RSI", f"{snap.get('rsi'):.2f}" if not pd.isna(snap.get('rsi')) else "N/A")
            c4.metric("MA short / long", f"{snap.get('ma_short'):.2f}/{snap.get('ma_long'):.2f}" if not pd.isna(snap.get('ma_short')) and not pd.isna(snap.get('ma_long')) else "N/A")

            with st.expander("Full snapshot & metric scores"):
                st.json(r)

        csv = pd.DataFrame(df_rows).to_csv(index=False)
        st.download_button("Download scan results CSV", csv, "mk_scan_results.csv", "text/csv")

with col2:
    st.header("Quick tools")
    st.write("Saved scan history (recent)")
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
    st.write("Reset DB (watchlist + scan history)")
    if st.button("Reset DB (danger!)"):
        DB_CONN.close()
        import os
        os.remove(DB_FILE)
        st.warning("Database removed. Please refresh the app.")
        st.stop()

st.markdown("---")
st.caption("Notes: Automatic daily scans only run while the Streamlit app process is running. Scheduled jobs will not scan while the app is stopped or sleeping. For always-on scanning, deploy to a server with the app kept running.")

