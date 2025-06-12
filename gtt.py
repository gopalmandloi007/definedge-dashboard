import streamlit as st
from utils import integrate_get, integrate_post

def show():
    st.header("GTT Orders")
    st.write("View and place GTT orders.")
    st.subheader("GTT Book")
    data = integrate_get("/gttorders")
    gttlist = data.get("pendingGTTOrderBook", [])
    st.dataframe(gttlist)
    st.subheader("Place GTT Order")
    with st.form("gtt_place"):
        tradingsymbol = st.text_input("Trading Symbol", key="gtt_ts")
        exchange = st.text_input("Exchange", value="NSE", key="gtt_exch")
        condition = st.selectbox("Condition", ["LTP_ABOVE", "LTP_BELOW"])
        alert_price = st.number_input("Alert Price")
        order_type = st.selectbox("Order Type", ["BUY", "SELL"])
        price = st.number_input("Order Price")
        quantity = st.number_input("Quantity", step=1)
        submit = st.form_submit_button("Place GTT Order")
        if submit:
            data = {
                "exchange": exchange,
                "tradingsymbol": tradingsymbol,
                "condition": condition,
                "alert_price": str(alert_price),
                "order_type": order_type,
                "price": str(price),
                "quantity": str(quantity),
            }
            resp = integrate_post("/gttplaceorder", data)
            st.write(resp)
