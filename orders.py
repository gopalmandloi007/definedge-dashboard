import streamlit as st
from utils import integrate_post
import requests

def get_ltp(tradingsymbol, exchange, api_session_key):
    try:
        url = f"https://integrate.definedgesecurities.com/dart/v1/quotes/{exchange}/{tradingsymbol}"
        headers = {"Authorization": api_session_key}
        resp = requests.get(url, headers=headers, timeout=3)
        if resp.status_code == 200:
            return float(resp.json().get("ltp", 0))
    except Exception:
        pass
    return 0

def show():
    st.markdown("""
    <style>
    .stApp { max-width: 950px; margin: auto; }
    .order-box {
        background: #f8fafd;
        border-radius: 10px;
        box-shadow: 0 2px 6px #e0e8f0;
        padding: 22px 28px 10px 28px;
        margin: 0 0 16px 0;
    }
    .order-summary {
        background: #e6f3ff;
        border-radius: 7px;
        padding: 12px 16px;
        font-size: 1.01rem;
        margin-bottom: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="order-box">', unsafe_allow_html=True)
    st.header("Order Place", divider="rainbow")

    col1, col2, col3, col4 = st.columns([2,2,2,2], gap="large")

    with col1:
        tradingsymbol = st.text_input("Symbol", key="ts", placeholder="RELIANCE", label_visibility="visible")
        price_type = st.selectbox("Type", ["LIMIT", "MARKET", "SL-LIMIT", "SL-MARKET"], key="pt")
    with col2:
        exchange = st.selectbox("Exch", ["NSE", "BSE", "NFO", "BFO", "CDS", "MCX"], key="exch")
        validity = st.selectbox("Validity", ["DAY", "IOC", "EOS"], key="val")
    with col3:
        order_type = st.selectbox("Side", ["BUY", "SELL"], key="ot")
        product_type = st.selectbox("Product", ["CNC", "INTRADAY", "NORMAL"], key="prod")
    with col4:
        qty_or_amt = st.radio("Order By", ["Qty", "Amt"], horizontal=True, key="qty_or_amt")
        qty_default = 1
        amt_default = 0.0

    api_session_key = st.secrets.get("integrate_api_session_key", "")

    # Amount/Qty input logic
    ltp = 0.0
    qty = qty_default
    amount = amt_default
    price = st.number_input("Price", min_value=0.0, value=0.0, step=0.05, key="pr", format="%.2f")
    if tradingsymbol and exchange:
        ltp = get_ltp(tradingsymbol, exchange, api_session_key)
    colQ, colA, colT, colD, colAMO = st.columns([2,2,2,2,2], gap="large")
    if qty_or_amt == "Amt":
        with colA:
            amount = st.number_input("₹ Amt", min_value=0.0, value=0.0, step=100.0, key="amt", format="%.2f")
        with colQ:
            if ltp > 0 and amount > 0:
                qty_auto = int(amount // ltp)
                st.caption(f"Auto-Qty at LTP ₹{ltp:.2f}: {qty_auto}")
            else:
                qty_auto = qty_default
            qty = st.number_input("Qty", min_value=1, value=qty_auto, step=1, key="qty")
    else:
        with colQ:
            qty = st.number_input("Qty", min_value=1, value=qty_default, step=1, key="qty")
        with colA:
            if ltp > 0:
                st.caption(f"LTP: ₹{ltp:.2f}")
            amount = qty * ltp if ltp > 0 else 0.0

    with colT:
        trigger_price = st.number_input("Trig Price", min_value=0.0, value=0.0, step=0.05, key="tr_pr", format="%.2f")
    with colD:
        disclosed_quantity = st.number_input("Disc Qty", min_value=0, value=0, step=1, key="dis_qty")
    with colAMO:
        amo = st.checkbox("AMO?", key="amo")
    remarks = st.text_input("Remarks (optional)", key="rem")

    st.markdown('</div>', unsafe_allow_html=True)

    # Preview summary
    if tradingsymbol and qty and order_type and price_type:
        st.markdown('<div class="order-summary">', unsafe_allow_html=True)
        st.markdown(
            f"<b>Preview:</b> {order_type} {qty} x <b>{tradingsymbol}</b> @ ₹{price} ({price_type}, {product_type})<br>"
            f"Exch: {exchange} | Validity: {validity} | AMO: {'Yes' if amo else 'No'}<br>"
            f"Order By: <b>{qty_or_amt}</b> | ₹ Amt: <b>{amount:.2f}</b>",
            unsafe_allow_html=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # Place order directly, no popup/confirmation
    if st.button("Place Order", use_container_width=True, type="primary"):
        data = {
            "tradingsymbol": tradingsymbol,
            "exchange": exchange,
            "order_type": order_type,
            "quantity": int(qty),
            "price_type": price_type,
            "price": float(price),
            "product_type": product_type,
            "validity": validity
        }
        if trigger_price:
            data["trigger_price"] = float(trigger_price)
        if remarks:
            data["remarks"] = remarks
        if disclosed_quantity:
            data["disclosed_quantity"] = int(disclosed_quantity)
        if amo:
            data["amo"] = "Yes"
        resp = integrate_post("/placeorder", data)
        st.success("Order submitted!")
        st.json(resp)
