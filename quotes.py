import streamlit as st
import pandas as pd
from utils import integrate_get

@st.cache_data
def load_master():
    # Supports both 14 and 15 column master.csv automatically
    df = pd.read_csv("master.csv", sep="\t", header=None)
    if df.shape[1] == 15:
        df.columns = [
            "segment", "token", "symbol", "symbol_series", "series", "unknown1",
            "unknown2", "unknown3", "series2", "unknown4", "unknown5", "unknown6",
            "isin", "unknown7", "company"
        ]
        return df[["segment", "token", "symbol", "symbol_series", "series"]]
    else:  # legacy 14-column
        df.columns = [
            "segment", "token", "symbol", "instrument", "series", "isin1",
            "facevalue", "lot", "something", "zero1", "two1", "one1", "isin", "one2"
        ]
        return df[["segment", "token", "symbol", "instrument", "series"]]

def get_token_by_symbol(symbol, exchange, master_df):
    symbol = symbol.strip().upper()
    exchange = exchange.strip().upper()
    # Try symbol first
    row = master_df[(master_df['symbol'].str.upper() == symbol) & (master_df['segment'].str.upper() == exchange)]
    if not row.empty:
        return row.iloc[0]['token']
    # Try symbol_series (for indices in 15-col)
    if "symbol_series" in master_df.columns:
        row2 = master_df[(master_df['symbol_series'].str.upper() == symbol) & (master_df['segment'].str.upper() == exchange)]
        if not row2.empty:
            return row2.iloc[0]['token']
    # Try instrument (for 14-col)
    if "instrument" in master_df.columns:
        row3 = master_df[(master_df['instrument'].str.upper() == symbol) & (master_df['segment'].str.upper() == exchange)]
        if not row3.empty:
            return row3.iloc[0]['token']
    return None

def show():
    st.header("Get Quotes / Security Info")

    master_df = load_master()
    exchange = st.selectbox("Exchange", sorted(master_df["segment"].unique()), index=0)
    # Symbol dropdown, only for selected exchange, sorted
    df_exch = master_df[master_df["segment"] == exchange]
    symbol_list = sorted(df_exch["symbol"].dropna().unique().tolist())
    symbol = st.selectbox("Symbol", symbol_list, index=0)

    token = get_token_by_symbol(symbol, exchange, master_df)
    if not token:
        st.warning("Symbol-token mapping not found in master file. Try another symbol.")
        return

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Get Quotes"):
            try:
                data = integrate_get(f"/quotes/{exchange}/{token}")
                st.json(data)
            except Exception as e:
                st.error(f"Error fetching quotes: {e}")
    with col2:
        if st.button("Get Security Info"):
            try:
                data = integrate_get(f"/securityinfo/{exchange}/{token}")
                st.json(data)
            except Exception as e:
                st.error(f"Error fetching security info: {e}")

if __name__ == "__main__":
    show()
