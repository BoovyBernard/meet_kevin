import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# -------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------
def safe_div(a, b):
    try:
        return a / b
    except Exception:
        return np.nan

def pct_change(a, b):
    if pd.isna(a) or pd.isna(b) or b == 0:
        return np.nan
    return (a - b) / abs(b) * 100.0

def score_metric(value, thresholds):
    """
    thresholds: (good_cutoff, neutral_cutoff)
    Returns +1 / 0 / -1
    """
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return 0
    good, neutral = thresholds
    if value >= good:
        return 1
    if value >= neutral:
        return 0
    return -1

# -------------------------------------------------------------------
# Main analyzer
# -------------------------------------------------------------------
def analyze_ticker(ticker):
    t = yf.Ticker(ticker)
    info = t.info if hasattr(t, "info") else {}
    hist = t.history(period="1y")

    price = info.get("currentPrice", np.nan)
    market_cap = info.get("marketCap", np.nan)
    pe = info.get("trailingPE", np.nan)
    forward_pe = info.get("forwardPE", np.nan)
    peg = info.get("pegRatio", np.nan)
    ps = info.get("priceToSalesTrailing12Months", np.nan)
    dividend_yield = info.get("dividendYield") or 0.0

    # Financial statements
    fin = t.financials
    bal = t.balance_sheet
    cf = t.cashflow
    earnings = t.earnings if hasattr(t, "earnings") else pd.DataFrame()

    # Revenue, earnings, margins
    try:
        revenue_ttm = fin.loc["Total Revenue"].iloc[0]
    except Exception:
        revenue_ttm = np.nan

    try:
        net_income_ttm = fin.loc["Net Income"].iloc[0]
    except Exception:
        net_income_ttm = np.nan

    try:
        operating_income = fin.loc["Operating Income"].iloc[0]
    except Exception:
        operating_income = np.nan

    gross_profit = fin.loc["Gross Profit"].iloc[0] if "Gross Profit" in fin.index else np.nan

    gross_margin = safe_div(gross_profit, revenue_ttm)
    op_margin = safe_div(operating_income, revenue_ttm)
    net_margin = safe_div(net_income_ttm, revenue_ttm)

    # Growth
    revenue_yoy = np.nan
    netinc_yoy = np.nan
    if fin.shape[1] >= 2:
        try:
            revenue_yoy = pct_change(fin.loc["Total Revenue"].iloc[0],
                                     fin.loc["Total Revenue"].iloc[1])
        except:
            pass
    if not earnings.empty and earnings.shape[0] >= 2:
        netinc_yoy = pct_change(earnings["Earnings"].iloc[-1],
                                earnings["Earnings"].iloc[-2])

    # Cash Flow
    try:
        cfo = cf.loc["Total Cash From Operating Activities"].iloc[0]
    except Exception:
        cfo = np.nan

    capex = cf.loc["Capital Expenditures"].iloc[0] if "Capital Expenditures" in cf.index else np.nan
    free_cash_flow = cfo + capex if not pd.isna(cfo) and not pd.isna(capex) else np.nan

    fcf_yield = safe_div(free_cash_flow, market_cap) * 100 if not pd.isna(market_cap) else np.nan

    # Score metrics ---------------------------------------------------
    scores = {}
    scores["PE"] = score_metric(-pe if not pd.isna(pe) else np.nan, (-15, -25))
    scores["PEG"] = score_metric(-peg if not pd.isna(peg) else np.nan, (-1.5, -2.5))
    scores["P/S"] = score_metric(-ps if not pd.isna(ps) else np.nan, (-3, -5))
    scores["FCF Yield"] = score_metric(fcf_yield, (5, 3))
    scores["Revenue YoY"] = score_metric(revenue_yoy, (10, 3))
    scores["Net Income YoY"] = score_metric(netinc_yoy, (10, 0))
    scores["Op Margin"] = score_metric(op_margin * 100 if not pd.isna(op_margin) else np.nan, (15, 5))

    total_score = (sum(scores.values()) + 7) / 14 * 100  # normalize to 0-100

    if total_score >= 65:
        rating = "BUY"
        color = "green"
    elif total_score >= 45:
        rating = "HOLD"
        color = "orange"
    else:
        rating = "SELL"
        color = "red"

    result = {
        "ticker": ticker.upper(),
        "price": price,
        "market_cap": market_cap,
        "pe": pe,
        "forward_pe": forward_pe,
        "peg": peg,
        "ps": ps,
        "dividend_yield": dividend_yield * 100,
        "gross_margin": gross_margin * 100 if not pd.isna(gross_margin) else np.nan,
        "op_margin": op_margin * 100 if not pd.isna(op_margin) else np.nan,
        "net_margin": net_margin * 100 if not pd.isna(net_margin) else np.nan,
        "revenue_yoy": revenue_yoy,
        "netinc_yoy": netinc_yoy,
        "fcf_yield": fcf_yield,
        "score": round(total_score, 2),
        "rating": rating,
        "rating_color": color,
        "scores": scores,
    }

    return result

# -------------------------------------------------------------------
# STREAMLIT UI
# -------------------------------------------------------------------

st.set_page_config(page_title="Fundamental Stock Scanner", layout="wide")

st.title("📊 Meet-Kevin Style Fundamental Stock Scanner")

st.sidebar.header("Scan Settings")

tickers = st.sidebar.text_area(
    "Enter tickers (comma separated):",
    "AAPL, MSFT, TSLA, AMZN"
)

tickers = [t.strip().upper() for t in tickers.split(",") if t.strip()]

if st.sidebar.button("Run Scan"):
    results = []
    for t in tickers:
        with st.spinner(f"Scanning {t}..."):
            try:
                res = analyze_ticker(t)
                results.append(res)
            except Exception as e:
                st.error(f"Error scanning {t}: {e}")

    if results:
        df = pd.DataFrame(results)
        st.success("Scan Complete!")

        # Results Table
        st.subheader("📌 Summary Table")
        st.dataframe(df[["ticker", "price", "score", "rating"]])

        # Detailed Cards
        st.subheader("📌 Detailed Analysis")
        for res in results:
            st.markdown(f"## {res['ticker']} — **{res['rating']}**")
            st.markdown(f"<span style='color:{res['rating_color']};font-size:24px'><b>{res['rating']}</b></span>", unsafe_allow_html=True)

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Price", f"${res['price']}")
            col2.metric("Score", f"{res['score']}/100")
            col3.metric("PE", res["pe"])
            col4.metric("FCF Yield", f"{res['fcf_yield']:.2f}%" if not pd.isna(res["fcf_yield"]) else "N/A")

            with st.expander("Full Metric Breakdown"):
                st.write(res)

        # Download button
        csv = df.to_csv(index=False)
        st.download_button("Download Results as CSV", csv, "scan_results.csv", "text/csv")

else:
    st.info("Enter tickers on the left and click **Run Scan**.")
