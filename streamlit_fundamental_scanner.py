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
from typing import List, Dict, Any, Optional

# ---------------------------
# Database / persistence
# ---------------------------

DB_FILE = "mk_scanner.db"

@st.cache_resource
def get_db_engine():
    return create_engine(f"sqlite:///{DB_FILE}", echo=False)

def get_db_connection():
    # Use a context manager in the calling code or just open/close here.
    # For SQLite in Streamlit, creating a new connection per request is safer than sharing one
    # unless we use thread-local storage, but simple open/close is fine for low traffic.
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    with get_db_connection() as conn:
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

# Initialize DB on first run
init_db()

def add_to_watchlist(ticker: str):
    ts = datetime.utcnow().isoformat()
    try:
        with get_db_connection() as conn:
            conn.execute("INSERT OR IGNORE INTO watchlist (ticker, added_at) VALUES (?,?)", (ticker.upper(), ts))
            conn.commit()
    except Exception as e:
        st.error(f"DB error adding watchlist: {e}")

def remove_from_watchlist(ticker: str):
    try:
        with get_db_connection() as conn:
            conn.execute("DELETE FROM watchlist WHERE ticker = ?", (ticker.upper(),))
            conn.commit()
    except Exception as e:
        st.error(f"DB error removing watchlist: {e}")

def get_watchlist() -> List[str]:
    try:
        with get_db_connection() as conn:
            cur = conn.execute("SELECT ticker FROM watchlist ORDER BY id")
            return [r[0] for r in cur.fetchall()]
    except Exception:
        return []

def save_scan_result(ticker: str, js: str):
    ts = datetime.utcnow().isoformat()
    try:
        with get_db_connection() as conn:
            conn.execute("INSERT INTO scan_results (ticker, ts, json) VALUES (?,?,?)", (ticker.upper(), ts, js))
            conn.commit()
    except Exception as e:
        print(f"Error saving scan result for {ticker}: {e}")

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
        if pd.isna(a) or pd.isna(b) or b == 0:
            return np.nan
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
    # Handle directionality: if good > neutral, higher is better.
    # If good < neutral (e.g. PE: -15 > -25), higher (less negative) is better?
    # Actually the caller passes negative values for things where lower is better (like PE).
    # So we can always assume 'value >= good' means 'good result' if we stick to that convention.
    
    if value >= good:
        return 1
    if value >= neutral:
        return 0
    return -1

def get_safe_val(df: pd.DataFrame, row_label: str, col_idx: int = 0, default=np.nan):
    """Safely extract a value from a DataFrame by index label and column position."""
    if df.empty:
        return default
    try:
        # Check if index exists
        if row_label in df.index:
            # Check if column exists
            if df.shape[1] > col_idx:
                val = df.loc[row_label].iloc[col_idx]
                return val if val is not None else default
    except Exception:
        pass
    return default

def fetch_fundamentals(ticker: str):
    # Light wrapper around yfinance to get needed fields. Keep exceptions contained.
    t = yf.Ticker(ticker)
    info = {}
    try:
        info = t.info
    except Exception:
        info = {}
    
    # Helper to get DF safely
    def get_df(attr):
        try:
            d = getattr(t, attr)
            return d if d is not None else pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    fin = get_df("financials")
    bal = get_df("balance_sheet")
    cf = get_df("cashflow")
    earnings = get_df("earnings")
    
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
    # Fallback to history close if currentPrice is missing
    current_price = info.get("currentPrice")
    if not current_price and not hist.empty:
        current_price = hist["Close"].iloc[-1]
    
    price = current_price if current_price else np.nan
    market_cap = info.get("marketCap", np.nan)
    beta = info.get("beta", np.nan)
    fifty_two_week_high = info.get("fiftyTwoWeekHigh", np.nan)
    fifty_two_week_low = info.get("fiftyTwoWeekLow", np.nan)
    result.update({"price": price, "market_cap": market_cap, "beta": beta})

    # Fundamentals - safe reads using get_safe_val
    revenue_ttm = get_safe_val(fin, "Total Revenue")
    net_income_ttm = get_safe_val(fin, "Net Income")
    operating_income_ttm = get_safe_val(fin, "Operating Income")
    ebitda = info.get("ebitda", np.nan)

    # Balance sheet
    # Try different keys as yfinance sometimes changes them or they vary by sector
    total_debt = get_safe_val(bal, "Total Debt")
    if pd.isna(total_debt):
         total_debt = get_safe_val(bal, "Short Long Term Debt")
         
    cash_and_equiv = get_safe_val(bal, "Cash And Cash Equivalents")
    if pd.isna(cash_and_equiv):
        cash_and_equiv = get_safe_val(bal, "Cash")
        
    total_assets = get_safe_val(bal, "Total Assets")
    shareholders_equity = get_safe_val(bal, "Stockholders Equity")
    if pd.isna(shareholders_equity):
        shareholders_equity = get_safe_val(bal, "Total Stockholder Equity")
        
    current_assets = get_safe_val(bal, "Current Assets")
    if pd.isna(current_assets):
        current_assets = get_safe_val(bal, "Total Current Assets")
        
    current_liab = get_safe_val(bal, "Current Liabilities")
    if pd.isna(current_liab):
        current_liab = get_safe_val(bal, "Total Current Liabilities")

    # Cashflow
    cfo = get_safe_val(cf, "Operating Cash Flow")
    if pd.isna(cfo):
        cfo = get_safe_val(cf, "Total Cash From Operating Activities")
        
    capex = get_safe_val(cf, "Capital Expenditure")
    if pd.isna(capex):
        capex = get_safe_val(cf, "Capital Expenditures")
        
    free_cash_flow = np.nan
    if not pd.isna(cfo) and not pd.isna(capex):
        # yfinance usually reports capex as negative, so we add it. 
        # If it's positive for some reason, we might need to subtract. 
        # Standard convention in yf is negative for outflows.
        free_cash_flow = cfo + capex 

    # Valuations
    pe = info.get("trailingPE", np.nan)
    forward_pe = info.get("forwardPE", np.nan)
    peg = info.get("pegRatio", np.nan)
    ps = info.get("priceToSalesTrailing12Months", np.nan)
    dividend_yield = info.get("dividendYield", 0.0)
    if dividend_yield is None: dividend_yield = 0.0

    # Margins / Returns
    gross_profit = get_safe_val(fin, "Gross Profit")
    gross_margin = safe_div(gross_profit, revenue_ttm)
    op_margin = safe_div(operating_income_ttm, revenue_ttm)
    net_margin = safe_div(net_income_ttm, revenue_ttm)
    roe = safe_div(net_income_ttm, shareholders_equity)
    roa = safe_div(net_income_ttm, total_assets)

    # Leverage
    debt_equity = safe_div(total_debt, shareholders_equity)
    
    net_debt = np.nan
    if not pd.isna(total_debt) and not pd.isna(cash_and_equiv):
        net_debt = total_debt - cash_and_equiv
        
    net_debt_ev = np.nan
    if not pd.isna(ebitda) and not pd.isna(net_debt) and not pd.isna(market_cap):
        # EV = Market Cap + Net Debt
        enterprise_value = market_cap + net_debt
        net_debt_ev = safe_div(net_debt, ebitda) if ebitda != 0 else np.nan

    interest_expense = get_safe_val(fin, "Interest Expense")
    # Interest expense is usually negative. Coverage = Op Income / abs(Interest)
    interest_cov = safe_div(operating_income_ttm, abs(interest_expense)) if not pd.isna(interest_expense) else np.nan
    current_ratio = safe_div(current_assets, current_liab)

    # Growth
    revenue_yoy = np.nan
    netinc_yoy = np.nan
    
    # Try to calculate YoY from financials if we have at least 2 columns
    if not fin.empty and fin.shape[1] >= 2:
        rev_latest = get_safe_val(fin, "Total Revenue", 0)
        rev_prev = get_safe_val(fin, "Total Revenue", 1)
        revenue_yoy = pct_change(rev_latest, rev_prev)

    # For earnings growth, we can look at 'earnings' DF or quarterly financials
    # Let's try quarterly financials for immediate growth or just use what we have
    # The original code used 'earnings' DF which is annual usually.
    if not earnings.empty and earnings.shape[0] >= 2:
        # Earnings DF usually has rows as years.
        try:
            # Assuming last row is latest
            netinc_yoy = pct_change(earnings["Earnings"].iloc[-1], earnings["Earnings"].iloc[-2])
        except Exception:
            pass

    # Price history indicators
    rsi_val = np.nan
    ma_short_val = np.nan
    ma_long_val = np.nan
    
    if not hist.empty:
        try:
            hist_clean = hist.dropna(subset=["Close"])
            if not hist_clean.empty:
                hist_close = hist_clean["Close"]
                rsi_series = compute_rsi(hist_close, period=rsi_period)
                if not rsi_series.empty:
                    rsi_val = rsi_series.iloc[-1]
                
                ma_short_series = moving_average(hist_close, ma_short)
                if not ma_short_series.empty:
                    ma_short_val = ma_short_series.iloc[-1]
                    
                ma_long_series = moving_average(hist_close, ma_long)
                if not ma_long_series.empty:
                    ma_long_val = ma_long_series.iloc[-1]
        except Exception:
            pass

    # Pack snapshot
    snapshot = {
        "price": price,
        "market_cap": market_cap,
        "pe": pe,
        "forward_pe": forward_pe,
        "peg": peg,
        "ps": ps,
        "dividend_yield_pct": dividend_yield * 100,
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
    metric_scores = {}

    # Helper to invert score for things where lower is better (PE, Debt, etc)
    # We pass negative value to score_metric so that >= threshold works.
    # e.g. PE 20. Target < 25.  -20 >= -25 is True.
    
    metric_scores["valuation_pe"] = score_metric(-pe if not pd.isna(pe) else np.nan, ( -15, -25))
    metric_scores["peg"] = score_metric(-peg if not pd.isna(peg) else np.nan, (-1.5, -2.5))
    metric_scores["p_s"] = score_metric(-ps if not pd.isna(ps) else np.nan, (-3, -5))
    metric_scores["fcf_yield"] = score_metric(snapshot["fcf_yield_pct"], (5.0, 2.5))
    metric_scores["revenue_growth"] = score_metric(snapshot["revenue_yoy_pct"], (10.0, 3.0))
    metric_scores["netinc_growth"] = score_metric(snapshot["netinc_yoy_pct"], (10.0, 0.0))
    metric_scores["op_margin"] = score_metric(snapshot["op_margin_pct"], (15.0, 5.0))
    metric_scores["net_margin"] = score_metric(snapshot["net_margin_pct"], (10.0, 3.0))
    metric_scores["roe"] = score_metric(roe*100 if not pd.isna(roe) else np.nan, (15.0, 8.0))
    metric_scores["debt_eq"] = score_metric(-snapshot["debt_equity"] if not pd.isna(snapshot["debt_equity"]) else np.nan, (-1.0, -2.0))
    metric_scores["net_debt_ebitda"] = score_metric(-snapshot["net_debt_ebitda"] if not pd.isna(snapshot["net_debt_ebitda"]) else np.nan, (-3.0, -4.0))
    metric_scores["interest_cov"] = score_metric(snapshot["interest_coverage"], (5.0, 2.0))
    metric_scores["current_ratio"] = score_metric(snapshot["current_ratio"], (1.5, 1.0))

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
        sector_flag = True
        adjustments = 0.0
        med_fcf = sector_median.get("fcf_yield_pct", np.nan)
        if not pd.isna(med_fcf) and not pd.isna(snapshot["fcf_yield_pct"]):
            if snapshot["fcf_yield_pct"] < med_fcf:
                adjustments -= 0.02 * total_weight
        
        if total_weight > 0:
            normalized = (weighted_sum + adjustments + total_weight) / (2 * total_weight)
            score_pct = max(0.0, min(100.0, normalized * 100.0))

    # recommendation thresholds
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
        for t in tables:
            cols = [c.lower() for c in t.columns]
            if any("symbol" in c or "ticker" in c for c in cols):
                symbol_col = next(c for c in t.columns if "symbol" in str(c).lower() or "ticker" in str(c).lower())
                tickers = t[symbol_col].astype(str).str.replace('.', '-', regex=False).str.strip().tolist()
                return tickers
    except Exception:
        return []
    return []

# ---------------------------
# Background scheduler for automatic daily scans
# ---------------------------

@st.cache_resource
def get_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.start()
    return scheduler

def schedule_daily_scan(tickers: List[str], job_id="daily_scan_job"):
    scheduler = get_scheduler()
    
    def do_scan():
        # Use simple weights for auto-scan
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
            except Exception as e:
                print(f"Auto-scan error {tk}: {e}")

    # Remove existing if present
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        
    # Schedule
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
        st.rerun()

    wl = get_watchlist()
    st.write("Saved watchlist:")
    if wl:
        for t in wl:
            col1, col2 = st.columns([3,1])
            col1.write(t)
            if col2.button(f"Remove {t}", key=f"rm_{t}"):
                remove_from_watchlist(t)
                st.rerun()
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
        if df_rows:
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
        else:
            st.warning("No results found.")

with col2:
    st.header("Quick tools")
    st.write("Saved scan history (recent)")
    try:
        with get_db_connection() as conn:
            cur = conn.execute("SELECT ticker, ts FROM scan_results ORDER BY id DESC LIMIT 10")
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
        import os
        try:
            os.remove(DB_FILE)
            st.warning("Database removed. Please refresh the app.")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"Error removing DB: {e}")

st.markdown("---")
st.caption("Notes: Automatic daily scans only run while the Streamlit app process is running. Scheduled jobs will not scan while the app is stopped or sleeping. For always-on scanning, deploy to a server with the app kept running.")
