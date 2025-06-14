import streamlit as st
import pandas as pd
import numpy as np
from utils import integrate_get
import plotly.express as px

st.title("🔒 Bulk Stop Loss & Allocation Manager")

api_session_key = st.secrets.get("integrate_api_session_key", "")

def safe_float(val):
    try:
        return float(val)
    except Exception:
        return 0.0

# Fetch holdings data
data = integrate_get("/holdings")
holdings = data.get("data", [])
if not holdings:
    st.warning("No holdings found.")
    st.stop()

# Prepare data
rows = []
for h in holdings:
    ts = h.get("tradingsymbol")
    exch = h.get("exchange", "NSE")
    if isinstance(ts, list) and len(ts) > 0 and isinstance(ts[0], dict):
        tsym = ts[0].get("tradingsymbol", "N/A")
        qty = safe_float(ts[0].get("dp_qty", h.get("dp_qty", 0)))
        avg_buy = safe_float(ts[0].get("avg_buy_price", h.get("avg_buy_price", 0)))
    else:
        tsym = ts if isinstance(ts, str) else "N/A"
        qty = safe_float(h.get("dp_qty", 0))
        avg_buy = safe_float(h.get("avg_buy_price", 0))
    if qty > 0:
        invested = avg_buy * qty
        rows.append({
            "Symbol": tsym,
            "Exchange": exch,
            "Qty": qty,
            "Avg Buy": avg_buy,
            "Invested": invested,
        })

df = pd.DataFrame(rows)

if df.empty:
    st.warning("No active holdings with quantity > 0.")
    st.stop()

# --- Capital Management (top, not sidebar) ---
if "total_capital" not in st.session_state:
    st.session_state.total_capital = 650000.0

st.subheader("💰 Capital Management")
total_capital = st.number_input(
    "Total Capital (Invested + Cash)",
    min_value=1.0,  # Avoid zero for division
    value=st.session_state.total_capital,
    step=10000.0,
    key="total_capital_input"
)
st.session_state.total_capital = total_capital

# Recalculate invested, cash and allocation %
total_invested = df["Invested"].sum()
cash_in_hand = max(st.session_state.total_capital - total_invested, 0)
allocation_percent = (total_invested / st.session_state.total_capital * 100) if st.session_state.total_capital else 0

colA, colB, colC = st.columns(3)
colA.metric("Total Capital", f"₹{st.session_state.total_capital:,.0f}")
colB.metric("Invested", f"₹{total_invested:,.0f}", f"{allocation_percent:.1f}%")
colC.metric("Cash in Hand", f"₹{cash_in_hand:,.0f}")

# --- Pie Chart: Allocation (at the top) ---
st.subheader("Portfolio Allocation Pie")
fig = px.pie(
    df, 
    names="Symbol", 
    values="Invested", 
    title="Allocation by Stock", 
    hole=0.3
)
fig.update_traces(textinfo='label+percent')
st.plotly_chart(fig, use_container_width=True)

# --- Stop Loss Table ---
st.subheader("🛑 Bulk Stop Loss Table (Editable)")
if "sl_dict" not in st.session_state:
    st.session_state.sl_dict = {}

# Prepare editable SL column with default (entry -2%)
df["Default SL"] = (df["Avg Buy"] * 0.98).round(2)
df["Stop Loss"] = df.apply(lambda x: st.session_state.sl_dict.get(x["Symbol"], x["Default SL"]), axis=1)

# Editable SLs
edited_df = st.data_editor(
    df[["Symbol", "Avg Buy", "Qty", "Invested", "Stop Loss"]],
    column_config={
        "Stop Loss": st.column_config.NumberColumn("Stop Loss", format="%.2f"),
    },
    use_container_width=True,
    key="holdings_sl_editor"
)

# Save SLs to session state
if st.button("💾 Save Stop Losses"):
    for i, row in edited_df.iterrows():
        st.session_state.sl_dict[row["Symbol"]] = row["Stop Loss"]
    st.success("All stop losses updated!")

# Reset all SLs to default
if st.button("↩️ Reset All to Default SL (-2% Entry)"):
    for symbol in df["Symbol"]:
        st.session_state.sl_dict[symbol] = df[df["Symbol"] == symbol]["Default SL"].values[0]
    st.experimental_rerun()

# --- Open Risk Calculation ---
edited_df["Open Risk"] = (edited_df["Stop Loss"] - edited_df["Avg Buy"]) * edited_df["Qty"]
total_risk = edited_df["Open Risk"].sum()

st.subheader("Risk Analysis")
col1, col2 = st.columns(2)
col1.metric("Total Open Risk", f"₹{total_risk:,.0f}")
col2.metric("Risk % of Total Capital", f"{(total_risk/st.session_state.total_capital*100):.2f}%" if st.session_state.total_capital else "0%")

# --- Pie Chart: Risk Distribution ---
st.subheader("Risk Distribution Pie")
fig2 = px.pie(
    edited_df, 
    names="Symbol", 
    values="Open Risk", 
    title="Open Risk by Stock", 
    hole=0.3
)
fig2.update_traces(textinfo='label+percent')
st.plotly_chart(fig2, use_container_width=True)

# --- Download CSV Option ---
csv = edited_df.to_csv(index=False)
st.download_button("Download as CSV", csv, "holdings_sl_table.csv", "text/csv")

# --- Table with color highlights ---
st.subheader("Summary Table (Profit/Risk Highlighted)")
def highlight_risk(val):
    if val < 0:
        return "background-color: #ffcccc"  # Red risk
    elif val > 0:
        return "background-color: #c6f5c6"  # Green profit
    return ""
st.dataframe(
    edited_df.style.applymap(highlight_risk, subset=["Open Risk"]),
    use_container_width=True,
)

st.info("You can edit all stop losses above and click Save. Reset sets all to -2% of entry. Download for record keeping.")
