import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import sqlite3
import json
import os
import datetime
from pathlib import Path
import traceback


# ============================================================
# SAFE GETTER  (Fixes ALL .get() bugs permanently)
# ============================================================
def safe(x, key, default=None):
    try:
        if isinstance(x, dict):
            return x.get(key, default)
        if isinstance(x, pd.Series):
            return x[key] if key in x else default
        if hasattr(x, key):
            return getattr(x, key)
        return default
    except:
        return default


# ============================================================
# AI BUY/SELL RECOMMENDATION (NO OPENAI NEEDED)
# ============================================================
def ai_recommendation(score, pe, pb, fcf, ma_signal, rsi):
    reasons = []

    # fundamentals
    if pe and pe > 0 and pe < 20:
        reasons.append("PE ratio attractive")
    if pb and pb < 3:
        reasons.append("Price-to-book reasonable")
    if fcf and fcf > 0:
        reasons.append("Positive free cash flow")

    # technicals
    if ma_signal:
        reasons.append("Trend bullish (MA50 > MA200)")
    if rsi and rsi < 70:
        reasons.append("RSI neutral (no overbought risk)")

    # ----- Decision -----
    if score >= 5:
        decision = "BUY"
    elif 3 <= score < 5:
        decision = "WATCH / HOLD"
    else:
        decision = "SELL / AVOID"

    # ----- Kevin-style commentary -----
    kevin_note = ""
    if decision == "BUY":
        kevin_note = (
            "🔥 *This looks like a classic Meet Kevin-style opportunity: solid fundamentals, "
            "healthy cashflow, and technical confirmation.*"
        )
    elif decision == "WATCH / HOLD":
        kevin_note = (
            "⚠️ *This stock shows potential but needs more momentum or fundamental depth. "
            "Put it on a watchlist; don't yolo in yet.*"
        )
    elif decision == "SELL / AVOID":
        kevin_note = (
            "🚫 *Risk not worth the reward. Fundamentals or technicals are not aligned.*"
        )

    return decision, reasons, kevin_note


# ============================================================
# SCANNER ENGINE
# ============================================================
def scan_stock(ticker):
    try:
        stock = yf.Ticker(ticker)
        fast = stock.fast_info

        result = {"ticker": ticker}

        # ---- BASIC FUNDAMENTALS ----
        result["market_cap"] = safe(fast, "market_cap")
        result["pe"] = safe(fast, "pe_ratio")
        result["pb"] = safe(fast, "price_to_book")
        result["eps"] = safe(fast, "eps")
        result["dividend_yield"] = safe(fast, "dividend_yield")

        # ---- FINANCIAL STATEMENTS ----
        try:
            bal = stock.balance_sheet
            fin = stock.financials
            cf = stock.cashflow
        except:
            bal = fin = cf = None

        result["revenue"] = safe(
            bal.loc["Total Revenue"] if bal is not None and "Total Revenue" in bal.index else None,
            0
        )
        result["net_income"] = safe(
            fin.loc["Net Income"] if fin is not None and "Net Income" in fin.index else None,
            0
        )
        result["free_cash_flow"] = safe(
            cf.loc["Free Cash Flow"] if cf is not None and "Free Cash Flow" in cf.index else None,
            0
        )

        # ---- TECHNICALS ----
        hist = stock.history(period="1y")

        if hist is None or len(hist) < 50:
            result["ma_signal"] = False
            result["rsi"] = None
        else:
            hist["MA50"] = hist["Close"].rolling(50).mean()
            hist["MA200"] = hist["Close"].rolling(200).mean()

            # RSI
            delta = hist["Close"].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            hist["RSI"] = 100 - (100 / (1 + rs))

            result["ma_signal"] = hist["MA50"].iloc[-1] > hist["MA200"].iloc[-1]
            result["rsi"] = float(hist["RSI"].iloc[-1])

        # ---- SCORE SYSTEM ----
        score = 0
        if result["pe"] and 0 < result["pe"] < 25: score += 1
        if result["pb"] and result["pb"] < 3: score += 1
        if result["eps"] and result["eps"] > 0: score += 1
        if result["free_cash_flow"] and result["free_cash_flow"] > 0: score += 1
        if result["ma_signal"]: score += 1
        if result["rsi"] and result["rsi"] < 70: score += 1
        result["score"] = score

        # ---- AI RECOMMENDATION ----
        decision, reasons, commentary = ai_recommendation(
            score,
            result["pe"],
            result["pb"],
            result["free_cash_flow"],
            result["ma_signal"],
            result["rsi"]
        )

        result["recommendation"] = decision
        result["reasons"] = "; ".join(reasons)
        result["kevin_note"] = commentary

        return result

    except Exception as e:
        print("Error scanning:", ticker, e)
        print(traceback.format_exc())
        return {"ticker": ticker, "score": 0, "recommendation": "ERROR"}


# ============================================================
# SQLITE WATCHLIST
# ============================================================
def init_db():
    conn = sqlite3.connect("watchlist.db")
    conn.execute("CREATE TABLE IF NOT EXISTS watchlist (ticker TEXT PRIMARY KEY)")
    conn.commit()
    conn.close()

def add_to_watchlist(ticker):
    conn = sqlite3.connect("watchlist.db")
    conn.execute("INSERT OR IGNORE INTO watchlist VALUES (?)", (ticker,))
    conn.commit()
    conn.close()

def get_watchlist():
    conn = sqlite3.connect("watchlist.db")
    df = pd.read_sql("SELECT * FROM watchlist", conn)
    conn.close()
    return df


# ============================================================
# SCAN HISTORY (JSON FILES)
# ============================================================
def save_scan(df):
    Path("scan_history").mkdir(exist_ok=True)
    f = f"scan_history/{datetime.date.today()}.json"
    df.to_json(f, orient="records")

def load_history():
    folder = Path("scan_history")
    if not folder.exists():
        return {}
    history = {}
    for file in folder.glob("*.json"):
        date = file.stem
        history[date] = pd.read_json(file)
    return history


# ============================================================
# STREAMLIT UI
# ============================================================
st.set_page_config(layout="wide", page_title="Meet Kevin Fundamental Scanner")

st.sidebar.title("📊 Navigation")
page = st.sidebar.radio("Select Page", ["Scanner", "Watchlist", "History"])

init_db()

# ==========================================
# PAGE 1 — SCANNER
# ==========================================
if page == "Scanner":
    st.title("📈 Meet Kevin Fundamental Scanner + AI Recommendations")

    tickers = st.text_area("Enter tickers (comma separated)", "AAPL, MSFT, AMZN")
    tickers = [t.strip().upper() for t in tickers.split(",")]

    if st.button("Run Scan"):
        rows = [scan_stock(t) for t in tickers]
        df = pd.DataFrame(rows).sort_values("score", ascending=False)

        st.dataframe(df)

        save_scan(df)

        st.subheader("Add to Watchlist")
        for t in df["ticker"]:
            if st.button(f"Add {t}", key=f"wl_{t}"):
                add_to_watchlist(t)
                st.success(f"{t} added.")

# ==========================================
# PAGE 2 — WATCHLIST
# ==========================================
elif page == "Watchlist":
    st.title("⭐ Watchlist")

    w = get_watchlist()
    st.dataframe(w)

    if st.button("Rescan Watchlist"):
        rows = [scan_stock(t) for t in w["ticker"]]
        df = pd.DataFrame(rows).sort_values("score", ascending=False)
        st.dataframe(df)

# ==========================================
# PAGE 3 — HISTORY
# ==========================================
elif page == "History":
    st.title("📅 Historical Scan Browser")

    history = load_history()
    if not history:
        st.info("No scan history yet.")
    else:
        date_sel = st.selectbox("Select date", list(history.keys()))
        df = history[date_sel]
        st.dataframe(df)

        # --- Score over Time ---
        tickers = sorted({t for d in history.values() for t in d["ticker"]})
        ticker_sel = st.selectbox("Select ticker to chart", tickers)

        dates = []
        scores = []
        for d, df_day in history.items():
            row = df_day[df_day["ticker"] == ticker_sel]
            if not row.empty:
                dates.append(d)
                scores.append(int(row["score"].iloc[0]))

        chart_df = pd.DataFrame({"date": dates, "score": scores})
        chart_df["date"] = pd.to_datetime(chart_df["date"])
        chart_df = chart_df.sort_values("date")

        st.line_chart(chart_df.set_index("date"))
