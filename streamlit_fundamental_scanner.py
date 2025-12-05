import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import sqlite3
import json
from datetime import datetime, timedelta
import pytz
import plotly.express as px

# --------------------------------------------------------
# DATABASE SETUP
# --------------------------------------------------------
conn = sqlite3.connect("scanner_data.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS watchlist (
    symbol TEXT PRIMARY KEY
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS scan_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT,
    timestamp TEXT,
    score REAL,
    data_json TEXT
)
""")
conn.commit()

# --------------------------------------------------------
# STYLE
# --------------------------------------------------------
st.set_page_config(page_title="Fundamental Scanner", layout="wide")

st.markdown("""
<style>
.metric-box {
    padding: 15px;
    border-radius: 12px;
    background-color: #111111;
    color: white;
    border: 1px solid #333;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------------
# SAFE EXTRACTION HELPERS
# --------------------------------------------------------
def safe_dict(d, key, default=None):
    if d is None:
        return default
    return d[key] if key in d and d[key] not in ["", None, float("nan")] else default

def safe_num(x):
    try:
        return float(x)
    except:
        return None

# --------------------------------------------------------
# TECHNICAL INDICATORS
# --------------------------------------------------------
def compute_technicals(df):
    df["MA20"] = df["Close"].rolling(20).mean()
    df["MA50"] = df["Close"].rolling(50).mean()
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df

# --------------------------------------------------------
# AI BUY/SELL RECOMMENDATION
# --------------------------------------------------------
def ai_recommendation(score, fundamentals, techs):
    commentary = []

    if score >= 80:
        grade = "STRONG BUY"
        commentary.append("Strong revenue growth, high margins, and stable balance sheet.")
    elif score >= 65:
        grade = "BUY"
        commentary.append("Good fundamentals with room for improvement.")
    elif score >= 50:
        grade = "HOLD"
        commentary.append("Fair valuation but mixed indicators.")
    else:
        grade = "SELL"
        commentary.append("Weak fundamentals or negative growth trends.")

    # Kevin-style commentary
    if fundamentals.get("rev_growth") and fundamentals["rev_growth"] > 0:
        commentary.append("🚀 Revenue trending upward — very Kevin-approved.")
    else:
        commentary.append("⚠ Revenue stagnation — Kevin would dig deeper.")

    if techs.get("RSI") and techs["RSI"] < 30:
        commentary.append("RSI oversold — potential reversal zone.")
    elif techs.get("RSI") and techs["RSI"] > 70:
        commentary.append("RSI overbought — caution.")

    return grade, " ".join(commentary)

# --------------------------------------------------------
# FUNDAMENTAL ANALYSIS (Kevin-style)
# --------------------------------------------------------
def analyze_symbol(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.get_info()

        # Extract fundamentals safely
        revenue = safe_dict(info, "totalRevenue")
        gross_margin = safe_dict(info, "grossMargins")
        profit_margin = safe_dict(info, "profitMargins")
        debt_equity = safe_dict(info, "debtToEquity")
        pe = safe_dict(info, "forwardPE")

        hist = ticker.history(period="1y")
        if hist.empty:
            return None

        hist = compute_technicals(hist)

        # Scoring
        score = 0
        fundamentals = {}

        if revenue:
            fundamentals["revenue"] = revenue
            score += 20

        if gross_margin:
            fundamentals["gross_margin"] = gross_margin
            score += 15

        if profit_margin:
            fundamentals["profit_margin"] = profit_margin
            score += 15

        if debt_equity and debt_equity < 150:
            score += 10

        if pe and pe < 30:
            score += 10

        # Technical scoring
        rsi_latest = hist["RSI"].iloc[-1]
        fundamentals["rev_growth"] = safe_num(info.get("revenueGrowth"))

        techs = {"RSI": rsi_latest}
        if rsi_latest < 30:
            score += 10
        elif rsi_latest > 70:
            score -= 5

        # AI recommendation
        grade, commentary = ai_recommendation(score, fundamentals, techs)

        return {
            "symbol": symbol,
            "score": score,
            "grade": grade,
            "commentary": commentary,
            "fundamentals": fundamentals,
            "technicals": techs,
            "history": hist
        }

    except Exception as e:
        st.error(f"Error scanning {symbol}: {e}")
        return None

# --------------------------------------------------------
# SAVE SCAN HISTORY
# --------------------------------------------------------
def save_history(res):
    cur.execute("""
        INSERT INTO scan_history (symbol, timestamp, score, data_json)
        VALUES (?, ?, ?, ?)
    """, (res["symbol"], datetime.now().isoformat(), res["score"], json.dumps(res)))
    conn.commit()

# --------------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------------
page = st.sidebar.radio("Navigation", ["Scanner", "Scan History"])

# --------------------------------------------------------
# PAGE 1 — SCANNER
# --------------------------------------------------------
if page == "Scanner":
    st.title("📊 Fundamental Scanner — Kevin Style")

    tickers = st.text_input("Enter tickers (comma separated):", "AAPL, MSFT, AMZN")

    if st.button("Run Scan"):
        symbols = [t.strip().upper() for t in tickers.split(",")]
        results = []

        for sym in symbols:
            res = analyze_symbol(sym)
            if res:
                save_history(res)
                results.append(res)

        if results:
            df = pd.DataFrame([{
                "Symbol": r["symbol"],
                "Score": r["score"],
                "AI Recommendation": r["grade"],
                "Commentary": r["commentary"]
            } for r in results])

            st.dataframe(df, use_container_width=True)

# --------------------------------------------------------
# PAGE 2 — SCAN HISTORY VIEWER
# --------------------------------------------------------
if page == "Scan History":
    st.title("📜 Scan History Viewer")

    cur.execute("SELECT symbol, timestamp, score, data_json FROM scan_history ORDER BY timestamp DESC")
    rows = cur.fetchall()

    if rows:
        hist_df = pd.DataFrame([{
            "Symbol": r[0],
            "Timestamp": r[1],
            "Score": r[2],
        } for r in rows])

        st.dataframe(hist_df)

        # Plot score over time
        fig = px.line(hist_df, x="Timestamp", y="Score", color="Symbol", title="Score Over Time")
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("No scan history found yet.")

