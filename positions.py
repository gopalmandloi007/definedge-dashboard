import streamlit as st
import pandas as pd
from utils import integrate_get
import plotly.express as px
from datetime import datetime

def highlight_pnl(val):
    try:
        val = float(val)
        if val > 0:
            return 'color: green'
        elif val < 0:
            return 'color: red'
    except Exception:
        pass
    return 'color: black'

def show():
    st.header("Positions Book (Pro)")

    data = integrate_get("/positions")
    positions = data.get("positions", [])
    if not positions:
        st.info("No positions found.")
        return

    df = pd.DataFrame(positions)
    if df.empty:
        st.info("No positions to display.")
        return

    # Optional: convert P&L columns to float for easy calculations
    df["realized_pnl"] = pd.to_numeric(df.get("realized_pnl", 0), errors="coerce")
    df["unrealized_pnl"] = pd.to_numeric(df.get("unrealized_pnl", 0), errors="coerce")
    df["quantity"] = pd.to_numeric(df.get("quantity", 0), errors="coerce")
    df["buy_value"] = pd.to_numeric(df.get("buy_value", 0), errors="coerce")
    df["sell_value"] = pd.to_numeric(df.get("sell_value", 0), errors="coerce")
    df["mtm"] = pd.to_numeric(df.get("mtm", 0), errors="coerce")

    # 3. Search/Filter Box for Symbols
    search = st.text_input("🔍 Search Symbol (filter):")
    if search.strip() and "symbol" in df.columns:
        df = df[df["symbol"].str.contains(search.strip(), case=False, na=False)]

    # 4. Sort by MTM or position size
    if "mtm" in df.columns:
        df = df.sort_values("mtm", ascending=False)
    elif "buy_value" in df.columns:
        df = df.sort_values("buy_value", ascending=False)

    # 7. P&L totals
    total_realized = df["realized_pnl"].sum() if "realized_pnl" in df.columns else 0
    total_unrealized = df["unrealized_pnl"].sum() if "unrealized_pnl" in df.columns else 0
    st.markdown(f"**Total Realized P&L:** <span style='color:green'>{total_realized:,.2f}</span>", unsafe_allow_html=True)
    st.markdown(f"**Total Unrealized P&L:** <span style='color:orange'>{total_unrealized:,.2f}</span>", unsafe_allow_html=True)

    # 5. Pie chart by position (MTM or buy value)
    with st.expander("Show Pie Chart by Position Size"):
        if "mtm" in df.columns and df["mtm"].abs().sum() > 0:
            fig = px.pie(df, names="symbol", values="mtm", title="Allocation by MTM")
        elif "buy_value" in df.columns and df["buy_value"].abs().sum() > 0:
            fig = px.pie(df, names="symbol", values="buy_value", title="Allocation by Buy Value")
        else:
            fig = None
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Insufficient data for pie chart.")

    # 6. Show Last updated time
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. Color coding for P&L columns
    pnl_columns = [col for col in ["realized_pnl", "unrealized_pnl", "mtm"] if col in df.columns]
    st.dataframe(
        df.style.applymap(highlight_pnl, subset=pnl_columns),
        use_container_width=True
    )

    # 2. Download CSV
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ Download Positions as CSV",
        data=csv,
        file_name='positions.csv',
        mime='text/csv',
    )

    # 9. Expander for all columns/raw table
    with st.expander("Show Full Table (All Columns)"):
        st.dataframe(df, use_container_width=True)

if __name__ == "__main__":
    show()
