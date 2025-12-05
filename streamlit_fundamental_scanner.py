import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")

# Set page config
st.set_page_config(page_title="Ultimate Market Scanner", page_icon="🚀", layout="wide")

# -----------------------------
# CONFIGURATION
# -----------------------------
HIST_DAYS = 180
EMA_FAST = 20
EMA_SLOW = 50
RSI_PERIOD = 14
OBV_LOOKBACK = 14
VOLUME_SPIKE_MULT = 1.5

# Multi-timeframe config
MTF_TIMEFRAMES = ["1d", "4h", "1h"]
MTF_CONFIRM_THRESHOLD = 2
MTF_POSITIVE_PRICE_SCORE = 60.0

# Buy-the-Dip config
BTD_LOOKBACK_DAYS = 20
BTD_MIN_PULLBACK = 0.02
BTD_MAX_PULLBACK = 0.08
BTD_REQUIRE_DAILY_UPTREND = True

# Score weights (Technical)
SCORES_CONFIG = {
    "EQUITY": {"price": 0.40, "flow": 0.35, "fund": 0.25},
    "ETF": {"price": 0.45, "flow": 0.45, "fund": 0.10},
    "INDEX": {"price": 0.70, "flow": 0.00, "fund": 0.30},
    "COMMODITY": {"price": 0.80, "flow": 0.20, "fund": 0.00},
    "CRYPTOCURRENCY": {"price": 0.75, "flow": 0.25, "fund": 0.00},
    "CURRENCY": {"price": 0.80, "flow": 0.20, "fund": 0.00},
    "UNKNOWN": {"price": 0.40, "flow": 0.35, "fund": 0.25}
}
INST_FLOW_WEIGHT = 0.10

# -----------------------------
# TECHNICAL ANALYSIS HELPERS
# -----------------------------
def ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

def rsi(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.rolling(period, min_periods=period).mean()
    ma_down = down.rolling(period, min_periods=period).mean()
    rs = ma_up / ma_down
    return 100 - (100 / (1 + rs))

def compute_obv(df):
    obv = [0]
    for i in range(1, len(df)):
        if df['Close'].iat[i] > df['Close'].iat[i-1]:
            obv.append(obv[-1] + int(df['Volume'].iat[i]) if 'Volume' in df.columns else obv[-1])
        elif df['Close'].iat[i] < df['Close'].iat[i-1]:
            obv.append(obv[-1] - int(df['Volume'].iat[i]) if 'Volume' in df.columns else obv[-1])
        else:
            obv.append(obv[-1])
    return pd.Series(obv, index=df.index)

def safe_div(a,b,default=np.nan):
    try:
        return a/b if b else default
    except Exception:
        return default

def get_history(ticker, timeframe='1d', days=HIST_DAYS):
    t = yf.Ticker(ticker)
    if timeframe == '1d':
        interval = '1d'
        period = f"{days}d"
    elif timeframe == '4h':
        interval = '60m' # yfinance 4h is flaky, use 60m and resample if needed, or just use 60m as proxy for intraday trend
        period = "60d" 
    elif timeframe == '1h':
        interval = '1h'
        period = "60d"
    else:
        interval = timeframe
        period = f"{days}d"
    
    try:
        hist = t.history(period=period, interval=interval, actions=False)
        if hist is None or hist.empty:
            return pd.DataFrame()
        return hist.dropna(subset=['Close'])
    except Exception:
        return pd.DataFrame()

def compute_technical_metrics_from_hist(hist):
    if hist.empty: return {}
    close = hist['Close']
    low = hist['Low'] if 'Low' in hist.columns else close
    vol = hist['Volume'] if 'Volume' in hist.columns else pd.Series([0]*len(hist), index=hist.index)

    tech = {}
    tech['last_close'] = float(close.iloc[-1])
    tech['ema_fast'] = float(ema(close, EMA_FAST).iloc[-1])
    tech['ema_slow'] = float(ema(close, EMA_SLOW).iloc[-1])
    tech['ema_cross'] = int(tech['ema_fast'] > tech['ema_slow'])
    tech['price_above_ema_slow'] = int(close.iloc[-1] > tech['ema_slow'])

    r = rsi(close, RSI_PERIOD)
    tech['rsi'] = float(r.iloc[-1]) if not r.isna().all() else 50.0
    tech['rsi_rising'] = int(r.iloc[-1] > r.iloc[-3]) if len(r) >= 3 else 0

    try:
        lows = low.dropna().iloc[-5:]
        tech['higher_lows_3'] = int(len(lows) >= 3 and lows.iloc[-1] > lows.iloc[-2] > lows.iloc[-3])
    except Exception:
        tech['higher_lows_3'] = 0

    obv = compute_obv(hist)
    tech['obv_latest'] = float(obv.iloc[-1])
    if len(obv) >= OBV_LOOKBACK:
        y = obv.iloc[-OBV_LOOKBACK:].values
        x = np.arange(len(y))
        if np.all(np.isfinite(y)):
            m = np.polyfit(x, y, 1)[0]
            tech['obv_slope'] = float(m)
            tech['obv_slope_pos'] = int(m > 0)
        else:
            tech['obv_slope'] = 0.0
            tech['obv_slope_pos'] = 0
    else:
        tech['obv_slope'] = 0.0
        tech['obv_slope_pos'] = 0

    avg30 = vol.rolling(30, min_periods=5).mean().iloc[-1] if len(vol) >= 5 else (vol.mean() if len(vol)>0 else 0)
    tech['avg_vol_30'] = float(avg30 if not np.isnan(avg30) else 0.0)
    tech['today_vol'] = float(vol.iloc[-1]) if len(vol)>0 else 0.0
    today_up = int(close.iloc[-1] > close.iloc[-2]) if len(close) >= 2 else 0
    tech['vol_spike_up'] = int((tech['today_vol'] > VOLUME_SPIKE_MULT * tech['avg_vol_30']) and today_up)

    return tech

def compute_options_metrics(ticker):
    t = yf.Ticker(ticker)
    res = {
        'call_put_vol_ratio': np.nan,
        'call_put_oi_ratio': np.nan
    }
    try:
        exps = t.options
        if not exps: return res
        ne = exps[0]
        chain = t.option_chain(ne)
        calls = chain.calls
        puts = chain.puts
        cv = int(calls['volume'].dropna().sum()) if not calls.empty else 0
        pv = int(puts['volume'].dropna().sum()) if not puts.empty else 0
        coi = int(calls['openInterest'].dropna().sum()) if not calls.empty else 0
        poi = int(puts['openInterest'].dropna().sum()) if not puts.empty else 0
        res.update({
            'call_put_vol_ratio': safe_div(cv,pv),
            'call_put_oi_ratio': safe_div(coi,poi)
        })
    except Exception:
        pass
    return res

def score_price_momentum(tech):
    w_ema = 0.35
    w_price = 0.25
    w_rsi = 0.20
    w_hl = 0.20
    score = 0.0
    score += w_ema * (1.0 if tech.get('ema_cross',0)==1 else 0.0)
    score += w_price * (1.0 if tech.get('price_above_ema_slow',0)==1 else 0.0)
    r = tech.get('rsi', 50.0)
    if r < 30: r_score = 0.0
    elif r > 80: r_score = 0.2
    else: r_score = max(0.0, 1.0 - abs(r-60)/30.0)
    if tech.get('rsi_rising',0): r_score = min(1.0, r_score*1.2)
    score += w_rsi * r_score
    score += w_hl * (1.0 if tech.get('higher_lows_3',0)==1 else 0.0)
    return float(score*100.0)

def score_volume_flow(tech, opt):
    w_vol_spike = 0.30
    w_obv = 0.30
    w_cp_vol = 0.20
    w_cp_oi = 0.20
    s = 0.0
    s += w_vol_spike * (1.0 if tech.get('vol_spike_up',0)==1 else 0.0)
    s += w_obv * (1.0 if tech.get('obv_slope_pos',0)==1 else 0.0)
    cpv = opt.get('call_put_vol_ratio', np.nan)
    cpoi = opt.get('call_put_oi_ratio', np.nan)
    
    if np.isfinite(cpv):
        mapped = max(0.0, min(1.0, cpv/2.0))
        s += w_cp_vol * mapped
    else:
        s += w_cp_vol * 0.5
        
    if np.isfinite(cpoi):
        mapped = max(0.0, min(1.0, cpoi/2.0))
        s += w_cp_oi * mapped
    else:
        s += w_cp_oi * 0.5
        
    total = w_vol_spike + w_obv + w_cp_vol + w_cp_oi
    return float(s/total*100.0)

def detect_buy_the_dip(ticker, tech, hist):
    if BTD_REQUIRE_DAILY_UPTREND:
        if not (tech.get('ema_cross',0) == 1 and tech.get('price_above_ema_slow',0) == 1):
            return False, 0.0
    
    last_close = tech.get('last_close', 0)
    if last_close == 0: return False, 0.0

    look = hist['Close'].iloc[-BTD_LOOKBACK_DAYS:] if len(hist) >= BTD_LOOKBACK_DAYS else hist['Close']
    recent_high = float(look.max())
    pullback = (recent_high - last_close) / recent_high if recent_high>0 else 0.0
    is_btd = (pullback >= BTD_MIN_PULLBACK) and (pullback <= BTD_MAX_PULLBACK)
    return bool(is_btd), pullback

# -----------------------------
# FUNDAMENTAL ANALYSIS HELPERS (MEET KEVIN)
# -----------------------------
def get_growth_metrics(ticker_obj):
    try:
        financials = ticker_obj.financials
        if financials.empty: return None, None, None
        
        # Revenue
        rev_key = 'Total Revenue' if 'Total Revenue' in financials.index else 'TotalRevenue'
        if rev_key not in financials.index: return None, None, None
        
        revenue = financials.loc[rev_key]
        if len(revenue) < 2: return None, None, None
        
        current_rev = revenue.iloc[0]
        prev_rev = revenue.iloc[1]
        revenue_growth = ((current_rev - prev_rev) / prev_rev) * 100

        # Opex
        opex_key = 'Total Operating Expenses' if 'Total Operating Expenses' in financials.index else 'Operating Expenses'
        opex_growth = None
        if opex_key in financials.index:
            opex = financials.loc[opex_key]
            if len(opex) >= 2:
                current_opex = opex.iloc[0]
                prev_opex = opex.iloc[1]
                opex_growth = ((current_opex - prev_opex) / prev_opex) * 100

        operating_leverage = False
        if opex_growth is not None:
            if revenue_growth > opex_growth:
                operating_leverage = True
        
        return revenue_growth, opex_growth, operating_leverage
    except Exception:
        return None, None, None

def analyze_meet_kevin(ticker_symbol):
    stock = yf.Ticker(ticker_symbol)
    try:
        info = stock.info
    except Exception:
        return None
    
    if not info: return None

    # Data
    gross_margins = info.get('grossMargins', 0) * 100
    total_cash = info.get('totalCash', 0)
    total_debt = info.get('totalDebt', 0)
    current_ratio = info.get('currentRatio', 0)
    peg_ratio = info.get('pegRatio', None)
    insider_ownership = info.get('heldPercentInsiders', 0) * 100
    
    net_cash_positive = total_cash > total_debt
    rev_growth, opex_growth, op_leverage = get_growth_metrics(stock)

    # Scoring
    score = 0
    max_score = 6
    results = {}

    # 1. Pricing Power
    if gross_margins > 40: 
        score += 1
        results['margins'] = {'pass': True, 'val': gross_margins, 'msg': "High (>40%)"}
    elif gross_margins > 20: 
        score += 0.5
        results['margins'] = {'pass': 'partial', 'val': gross_margins, 'msg': "Moderate (>20%)"}
    else:
        results['margins'] = {'pass': False, 'val': gross_margins, 'msg': "Low (<20%)"}

    # 2. Growth
    if rev_growth and rev_growth > 20:
        score += 1
        results['growth'] = {'pass': True, 'val': rev_growth, 'msg': "High (>20%)"}
    elif rev_growth and rev_growth > 10:
        score += 0.5
        results['growth'] = {'pass': 'partial', 'val': rev_growth, 'msg': "Moderate (>10%)"}
    else:
        val = rev_growth if rev_growth else 0
        results['growth'] = {'pass': False, 'val': val, 'msg': "Low (<10%)"}

    # 3. Operating Leverage
    if op_leverage:
        score += 1
        results['oplev'] = {'pass': True, 'msg': "Yes"}
    else:
        results['oplev'] = {'pass': False, 'msg': "No"}

    # 4. Balance Sheet
    if net_cash_positive:
        score += 1
        results['balance'] = {'pass': True, 'msg': "Net Cash +"}
    elif current_ratio > 1.5:
        score += 0.5
        results['balance'] = {'pass': 'partial', 'msg': "Safe Liq"}
    else:
        results['balance'] = {'pass': False, 'msg': "High Debt"}

    # 5. Valuation
    if peg_ratio and peg_ratio < 1.0 and peg_ratio > 0:
        score += 1
        results['val'] = {'pass': True, 'val': peg_ratio, 'msg': "Undervalued"}
    elif peg_ratio and peg_ratio < 1.5:
        score += 0.5
        results['val'] = {'pass': 'partial', 'val': peg_ratio, 'msg': "Fair"}
    else:
        val = peg_ratio if peg_ratio else 0
        results['val'] = {'pass': False, 'val': val, 'msg': "Expensive"}

    # 6. Insider Ownership
    if insider_ownership > 10:
        score += 1
        results['insider'] = {'pass': True, 'val': insider_ownership, 'msg': "High (>10%)"}
    elif insider_ownership > 5:
        score += 0.5
        results['insider'] = {'pass': 'partial', 'val': insider_ownership, 'msg': "Mod (>5%)"}
    else:
        results['insider'] = {'pass': False, 'val': insider_ownership, 'msg': "Low (<5%)"}

    return {
        "score": score,
        "max_score": max_score,
        "results": results
    }

# -----------------------------
# MAIN APP LOGIC
# -----------------------------
def analyze_ticker(ticker, run_fundamental=False):
    # 1. Technical Analysis
    hist = get_history(ticker, '1d')
    if hist.empty:
        return {"error": "No data"}
    
    tech = compute_technical_metrics_from_hist(hist)
    opt = compute_options_metrics(ticker)
    
    price_score = score_price_momentum(tech)
    flow_score = score_volume_flow(tech, opt)
    
    # Simple weighting for Technical Score (Price + Flow)
    tech_final = (price_score * 0.6) + (flow_score * 0.4)
    
    # BTD
    is_btd, btd_pct = detect_buy_the_dip(ticker, tech, hist)
    
    # MTF (Simplified for speed - just check 1h)
    hist_1h = get_history(ticker, '1h')
    tech_1h = compute_technical_metrics_from_hist(hist_1h)
    price_score_1h = score_price_momentum(tech_1h)
    mtf_confirm = price_score_1h > 60

    result = {
        "ticker": ticker,
        "tech_score": round(tech_final, 1),
        "price_score": round(price_score, 1),
        "flow_score": round(flow_score, 1),
        "last_price": round(tech['last_close'], 2),
        "rsi": round(tech['rsi'], 1),
        "btd": is_btd,
        "mtf": mtf_confirm,
        "fundamental": None
    }

    # 2. Fundamental Analysis (Optional)
    if run_fundamental:
        fund_data = analyze_meet_kevin(ticker)
        if fund_data:
            result['fundamental'] = fund_data
            
    return result

# -----------------------------
# STREAMLIT UI
# -----------------------------
st.title("🚀 Ultimate Market Scanner")
st.markdown("Integrates **Advanced Technical Readiness** (Trend, Flow, BTD) with **Meet Kevin's Fundamentals** (Pricing Power, Growth).")

with st.sidebar:
    st.header("Settings")
    
    # Input method
    input_method = st.radio("Input Method", ["Manual List", "S&P 500 Top 50", "Nasdaq 100 Top 20"])
    
    if input_method == "Manual List":
        default_tickers = "TSLA, NVDA, AAPL, PLTR, AMD, F, SPY, QQQ, BTC-USD"
        ticker_input = st.text_area("Enter Tickers (comma separated)", value=default_tickers, height=100)
        tickers = [t.strip().upper() for t in ticker_input.split(',') if t.strip()]
    elif input_method == "S&P 500 Top 50":
        tickers = ["AAPL","MSFT","AMZN","NVDA","GOOGL","META","TSLA","BRK-B","LLY","AVGO","JPM","V","UNH","WMT","MA","XOM","JNJ","PG","HD","COST","ABBV","MRK","ORCL","CVX","BAC","KO","CRM","PEP","AMD","NFLX","TMO","LIN","WFC","MCD","DIS","CSCO","ABT","INTU","CAT","IBM","QCOM","VZ","CMCSA","AMAT","UBER","PFE","GE","DHR","UNP","TXN"]
    else:
        tickers = ["AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA","AVGO","COST","PEP","CSCO","TMUS","CMCSA","INTC","AMD","QCOM","TXN","AMGN","HON","INTU"]

    st.divider()
    run_fundamental = st.checkbox("Run Deep Fundamental Scan?", value=True, help="Fetches financial statements. Slower, but required for Kevin Score.")
    
    run_btn = st.button("Run Scanner", type="primary")

if run_btn:
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, ticker in enumerate(tickers):
        status_text.text(f"Scanning {ticker}...")
        res = analyze_ticker(ticker, run_fundamental=run_fundamental)
        if "error" not in res:
            results.append(res)
        progress_bar.progress((i + 1) / len(tickers))
    
    status_text.empty()
    progress_bar.empty()
    
    if not results:
        st.warning("No results found.")
    else:
        # Convert to DataFrame for main view
        df_data = []
        for r in results:
            row = {
                "Ticker": r['ticker'],
                "Price": r['last_price'],
                "Tech Score": r['tech_score'],
                "RSI": r['rsi'],
                "BTD?": "✅" if r['btd'] else "❌",
                "MTF?": "✅" if r['mtf'] else "❌",
            }
            if r['fundamental']:
                row["Kevin Score"] = f"{r['fundamental']['score']}/{r['fundamental']['max_score']}"
            else:
                row["Kevin Score"] = "N/A"
            df_data.append(row)
        
        df = pd.DataFrame(df_data)
        st.dataframe(df.style.background_gradient(subset=['Tech Score'], cmap='RdYlGn'), use_container_width=True)
        
        # Detailed Cards
        st.subheader("Detailed Analysis")
        
        for r in results:
            with st.expander(f"**{r['ticker']}** - Tech: {r['tech_score']} | Kevin: {r['fundamental']['score'] if r['fundamental'] else 'N/A'}"):
                col1, col2 = st.columns(2)
                
                # Technical Column
                with col1:
                    st.markdown("### 📊 Technical Readiness")
                    st.progress(r['tech_score']/100)
                    st.write(f"**Price Momentum:** {r['price_score']}/100")
                    st.write(f"**Volume/Flow:** {r['flow_score']}/100")
                    if r['btd']:
                        st.success("🔥 Buy The Dip Detected!")
                    if r['mtf']:
                        st.info("✅ Multi-Timeframe Confirmed")
                
                # Fundamental Column
                with col2:
                    st.markdown("### 🧠 Kevin's Fundamentals")
                    if r['fundamental']:
                        f = r['fundamental']
                        st.progress(f['score']/f['max_score'])
                        
                        # Mini grid for fundamentals
                        f_cols = st.columns(3)
                        
                        # Row 1
                        r_m = f['results']['margins']
                        color = "green" if r_m['pass'] == True else "orange" if r_m['pass'] == 'partial' else "red"
                        f_cols[0].markdown(f":{color}[Margins]")
                        f_cols[0].caption(r_m['msg'])
                        
                        r_g = f['results']['growth']
                        color = "green" if r_g['pass'] == True else "orange" if r_g['pass'] == 'partial' else "red"
                        f_cols[1].markdown(f":{color}[Growth]")
                        f_cols[1].caption(r_g['msg'])
                        
                        r_o = f['results']['oplev']
                        color = "green" if r_o['pass'] == True else "red"
                        f_cols[2].markdown(f":{color}[Op Lev]")
                        f_cols[2].caption(r_o['msg'])
                        
                        # Row 2
                        f_cols_2 = st.columns(3)
                        r_b = f['results']['balance']
                        color = "green" if r_b['pass'] == True else "orange" if r_b['pass'] == 'partial' else "red"
                        f_cols_2[0].markdown(f":{color}[Balance]")
                        f_cols_2[0].caption(r_b['msg'])
                        
                        r_v = f['results']['val']
                        color = "green" if r_v['pass'] == True else "orange" if r_v['pass'] == 'partial' else "red"
                        f_cols_2[1].markdown(f":{color}[Valuation]")
                        f_cols_2[1].caption(r_v['msg'])
                        
                        r_i = f['results']['insider']
                        color = "green" if r_i['pass'] == True else "orange" if r_i['pass'] == 'partial' else "red"
                        f_cols_2[2].markdown(f":{color}[Insiders]")
                        f_cols_2[2].caption(r_i['msg'])

                    else:
                        st.write("Fundamental scan skipped or failed.")
