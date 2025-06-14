import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from utils import integrate_get
import numpy as np
import plotly.express as px

st.set_page_config(layout="wide")

# Session state for capital management
if 'deployed_capital' not in st.session_state:
    st.session_state.deployed_capital = 650000.0
if 'target_capital' not in st.session_state:
    st.session_state.target_capital = 650000.0
if 'stop_losses' not in st.session_state:
    st.session_state.stop_losses = {}

def safe_float(val):
    try:
        return float(val)
    except Exception:
        return 0.0

def highlight_pnl(val):
    try:
        val = float(val)
        if val > 0:
            return 'color: green'
        elif val < 0:
            return 'color: red'
    except:
        pass
    return 'color: black'

def highlight_risk(val):
    try:
        val = float(val)
        if val > 0:
            return 'background-color: #FFEB3B; color: black'
        elif val < 0:
            return 'background-color: #F44336; color: white'
    except:
        pass
    return ''

def generate_insights(row, portfolio_value):
    insights = []
    position_size = (row['Current'] / portfolio_value) * 100
    if position_size > 15:
        insights.append("⚠️ Position too large (>15% of portfolio)")
    elif position_size < 3:
        insights.append("⚖️ Position too small (<3% of portfolio)")
    if row['Overall P&L'] > 0:
        if row['%Chg Avg'] > 25:
            insights.append("💰 Consider taking partial profits (gains >25%)")
    else:
        if row['%Chg Avg'] < -15:
            insights.append("❗ Significant unrealized loss (>15%)")
    if row['%Chg'] > 5:
        insights.append("📈 Strong positive momentum today")
    elif row['%Chg'] < -5:
        insights.append("📉 Strong negative momentum today")
    return insights

def show():
    st.header("📊 Portfolio Holdings Overview")
    api_session_key = st.secrets.get("integrate_api_session_key", "")

    st.sidebar.header("💰 Capital Management")
    deployed_capital = st.sidebar.number_input(
        "Total Deployed Capital (₹)", 
        min_value=0.0, 
        value=st.session_state.deployed_capital, 
        step=10000.0,
        key='deployed_capital_input'
    )
    st.session_state.deployed_capital = deployed_capital

    target_capital = st.sidebar.number_input(
        "Target Deployment (₹)", 
        min_value=0.0, 
        value=st.session_state.target_capital, 
        step=10000.0,
        key='target_capital_input'
    )
    st.session_state.target_capital = target_capital

    st.sidebar.header("🛑 Stop Loss Management")
    st.sidebar.info("Stop loss management is available in detailed view.")

    try:
        data = integrate_get("/holdings")
        holdings = data.get("data", [])
        if not holdings:
            st.info("No holdings found.")
            return

        active_holdings = []
        for h in holdings:
            qty = 0.0
            ts = h.get("tradingsymbol")
            if isinstance(ts, list) and len(ts) > 0 and isinstance(ts[0], dict):
                qty = safe_float(ts[0].get("dp_qty", h.get("dp_qty", 0)))
            else:
                qty = safe_float(h.get("dp_qty", 0))
            if qty > 0:
                active_holdings.append(h)

        rows = []
        total_today_pnl = 0.0
        total_overall_pnl = 0.0
        total_invested = 0.0
        total_current = 0.0
        total_risk_amount = 0.0

        for h in active_holdings:
            ts = h.get("tradingsymbol")
            exch = h.get("exchange", "NSE")
            token = None
            isin = ""
            if isinstance(ts, list) and len(ts) > 0 and isinstance(ts[0], dict):
                tsym = ts[0].get("tradingsymbol", "N/A")
                exch = ts[0].get("exchange", exch)
                token = ts[0].get("token")
                isin = ts[0].get("isin", "")
                qty = safe_float(ts[0].get("dp_qty", h.get("dp_qty", 0)))
            else:
                tsym = ts if isinstance(ts, str) else "N/A"
                token = h.get("token")
                isin = h.get("isin", "")
                qty = safe_float(h.get("dp_qty", 0))
            avg_buy = safe_float(h.get("avg_buy_price", 0))
            # LTP, prev_close, etc. koi details nahi calculate karenge yaha
            invested = avg_buy * qty if avg_buy is not None else 0.0
            current = None  # details me calculate hoga
            today_pnl = None
            overall_pnl = None
            pct_chg = None
            pct_chg_avg = None
            realized_pnl = None
            stop_loss = st.session_state.stop_losses.get(tsym, avg_buy*0.98 if avg_buy else 0)
            risk_amount = None
            risk_percent = None

            rows.append([
                tsym, exch, isin, round(avg_buy, 2) if avg_buy is not None else "N/A", int(qty), stop_loss
            ])
            total_invested += invested

        headers = [
            "Symbol", "Exchange", "ISIN", "Avg Buy", "Qty", "Stop Loss"
        ]
        df = pd.DataFrame(rows, columns=headers)

        st.subheader("💰 Capital Allocation")
        portfolio_value = total_invested  # Details me real value
        cash_in_hand = st.session_state.deployed_capital - total_invested
        allocation_percent = (portfolio_value / st.session_state.deployed_capital * 100) if st.session_state.deployed_capital else 0
        additional_needed = max(0, st.session_state.target_capital - st.session_state.deployed_capital)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Deployed Capital", f"₹{st.session_state.deployed_capital:,.0f}")
        col2.metric("Target Capital", f"₹{st.session_state.target_capital:,.0f}", 
                   f"₹{additional_needed:,.0f} needed" if additional_needed > 0 else "Target reached")
        col3.metric("Cash in Hand", f"₹{cash_in_hand:,.0f}", 
                   f"{cash_in_hand/st.session_state.deployed_capital*100:.1f}%" if st.session_state.deployed_capital else "0%")
        col4.metric("Allocation %", f"{allocation_percent:.1f}%", 
                   f"₹{portfolio_value:,.0f} invested")

        st.subheader("Holdings Table (Click row for details in next page)")
        st.dataframe(df, use_container_width=True)

        st.info("To view technicals and analytics, open 'Holdings Details' page.")

    except Exception as e:
        st.error(f"Error loading holdings: {e}")

if __name__ == "__main__":
    show()
