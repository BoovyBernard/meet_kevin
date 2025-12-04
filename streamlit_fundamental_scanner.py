import streamlit as st
import yfinance as yf
import pandas as pd

# Set page config
st.set_page_config(page_title="Meet Kevin Scanner", page_icon="📈", layout="wide")

def get_growth_metrics(ticker_obj):
    """
    Calculates revenue growth and operating leverage.
    """
    try:
        financials = ticker_obj.financials
        if financials.empty:
            return None, None, None

        # Get Revenue
        if 'Total Revenue' in financials.index:
            revenue = financials.loc['Total Revenue']
        elif 'TotalRevenue' in financials.index: # Sometimes keys vary
             revenue = financials.loc['TotalRevenue']
        else:
            return None, None, None

        if len(revenue) < 2:
            return None, None, None
        
        current_rev = revenue.iloc[0]
        prev_rev = revenue.iloc[1]
        
        revenue_growth = ((current_rev - prev_rev) / prev_rev) * 100

        # Get Operating Expenses
        opex_growth = None
        opex = None
        if 'Total Operating Expenses' in financials.index:
            opex = financials.loc['Total Operating Expenses']
        elif 'Operating Expenses' in financials.index:
            opex = financials.loc['Operating Expenses']
        
        if opex is not None and len(opex) >= 2:
            current_opex = opex.iloc[0]
            prev_opex = opex.iloc[1]
            opex_growth = ((current_opex - prev_opex) / prev_opex) * 100

        operating_leverage = False
        if opex_growth is not None:
            # Positive Operating Leverage: Revenue grows faster than expenses
            if revenue_growth > opex_growth:
                operating_leverage = True
        
        return revenue_growth, opex_growth, operating_leverage

    except Exception as e:
        st.error(f"Error calculating growth metrics: {e}")
        return None, None, None

def analyze_stock(ticker_symbol):
    """
    Analyzes a stock and returns a dictionary of results.
    """
    stock = yf.Ticker(ticker_symbol)
    try:
        info = stock.info
    except Exception as e:
        return {"error": f"Could not fetch info: {e}"}
    
    if not info:
        return {"error": "No data found"}

    # --- Data Extraction ---
    gross_margins = info.get('grossMargins', 0) * 100
    total_cash = info.get('totalCash', 0)
    total_debt = info.get('totalDebt', 0)
    current_ratio = info.get('currentRatio', 0)
    peg_ratio = info.get('pegRatio', None)
    ps_ratio = info.get('priceToSalesTrailing12Months', None)
    insider_ownership = info.get('heldPercentInsiders', 0) * 100
    
    net_cash_positive = total_cash > total_debt
    rev_growth, opex_growth, op_leverage = get_growth_metrics(stock)

    # --- Scoring Logic ---
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
        results['oplev'] = {'pass': True, 'msg': "Yes (Rev > Opex)"}
    else:
        results['oplev'] = {'pass': False, 'msg': "No"}

    # 4. Balance Sheet
    if net_cash_positive:
        score += 1
        results['balance'] = {'pass': True, 'msg': "Net Cash Positive"}
    elif current_ratio > 1.5:
        score += 0.5
        results['balance'] = {'pass': 'partial', 'msg': "Safe Liquidity (>1.5)"}
    else:
        results['balance'] = {'pass': False, 'msg': "High Debt / Low Liquidity"}

    # 5. Valuation
    if peg_ratio and peg_ratio < 1.0 and peg_ratio > 0:
        score += 1
        results['val'] = {'pass': True, 'val': peg_ratio, 'msg': "Undervalued (PEG < 1)"}
    elif peg_ratio and peg_ratio < 1.5:
        score += 0.5
        results['val'] = {'pass': 'partial', 'val': peg_ratio, 'msg': "Fair (PEG < 1.5)"}
    else:
        val = peg_ratio if peg_ratio else 0
        results['val'] = {'pass': False, 'val': val, 'msg': "Expensive (PEG > 1.5 or N/A)"}

    # 6. Insider Ownership
    if insider_ownership > 10:
        score += 1
        results['insider'] = {'pass': True, 'val': insider_ownership, 'msg': "High (>10%)"}
    elif insider_ownership > 5:
        score += 0.5
        results['insider'] = {'pass': 'partial', 'val': insider_ownership, 'msg': "Moderate (>5%)"}
    else:
        results['insider'] = {'pass': False, 'val': insider_ownership, 'msg': "Low (<5%)"}

    return {
        "symbol": ticker_symbol.upper(),
        "score": score,
        "max_score": max_score,
        "results": results,
        "raw_data": {
            "total_cash": total_cash,
            "total_debt": total_debt,
            "opex_growth": opex_growth,
            "ps_ratio": ps_ratio
        }
    }

# --- UI Layout ---

st.title("🚀 Meet Kevin Fundamental Scanner")
st.markdown("Automated checklist based on Kevin Paffrath's investment criteria: **Pricing Power, Innovation, & Financials**.")

with st.sidebar:
    st.header("Input")
    ticker_input = st.text_input("Enter Ticker Symbols (comma separated)", value="TSLA, ENPH, PLTR")
    run_btn = st.button("Run Scan")
    st.markdown("---")
    st.markdown("### Legend")
    st.success("✅ Pass (+1)")
    st.warning("⚠️ Partial (+0.5)")
    st.error("❌ Fail (+0)")

if run_btn:
    tickers = [t.strip() for t in ticker_input.split(',')]
    
    for ticker in tickers:
        if not ticker: continue
        
        with st.spinner(f"Analyzing {ticker}..."):
            data = analyze_stock(ticker)
        
        if "error" in data:
            st.error(f"{ticker}: {data['error']}")
            continue

        # Display Result Card
        with st.expander(f"**{data['symbol']}** - Score: {data['score']}/{data['max_score']}", expanded=True):
            
            # Score Progress Bar
            score_pct = data['score'] / data['max_score']
            st.progress(score_pct, text=f"Kevin Score: {data['score']} / {data['max_score']}")
            
            col1, col2, col3 = st.columns(3)
            
            # Row 1
            with col1:
                r = data['results']['margins']
                color = "green" if r['pass'] == True else "orange" if r['pass'] == 'partial' else "red"
                st.markdown(f":{color}[**1. Pricing Power**]")
                st.metric("Gross Margins", f"{r['val']:.1f}%", delta=r['msg'], delta_color="off")
            
            with col2:
                r = data['results']['growth']
                color = "green" if r['pass'] == True else "orange" if r['pass'] == 'partial' else "red"
                st.markdown(f":{color}[**2. Growth**]")
                st.metric("Revenue Growth", f"{r['val']:.1f}%", delta=r['msg'], delta_color="off")

            with col3:
                r = data['results']['oplev']
                color = "green" if r['pass'] == True else "red"
                st.markdown(f":{color}[**3. Operating Leverage**]")
                st.metric("Op Leverage", r['msg'])

            st.divider()
            col4, col5, col6 = st.columns(3)

            # Row 2
            with col4:
                r = data['results']['balance']
                color = "green" if r['pass'] == True else "orange" if r['pass'] == 'partial' else "red"
                st.markdown(f":{color}[**4. Balance Sheet**]")
                st.caption(f"Cash: ${data['raw_data']['total_cash']/1e9:.1f}B | Debt: ${data['raw_data']['total_debt']/1e9:.1f}B")
                st.write(f"**{r['msg']}**")

            with col5:
                r = data['results']['val']
                color = "green" if r['pass'] == True else "orange" if r['pass'] == 'partial' else "red"
                st.markdown(f":{color}[**5. Valuation**]")
                val_display = f"{r['val']:.2f}" if r['val'] else "N/A"
                st.metric("PEG Ratio", val_display, delta=r['msg'], delta_color="inverse")

            with col6:
                r = data['results']['insider']
                color = "green" if r['pass'] == True else "orange" if r['pass'] == 'partial' else "red"
                st.markdown(f":{color}[**6. Skin in the Game**]")
                st.metric("Insider Own", f"{r['val']:.1f}%", delta=r['msg'], delta_color="off")
