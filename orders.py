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
    .stApp {
        max-width: 950px;
        margin: auto;
    }
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
        amount = st.number_input("₹ Amt", min_value=0.0, value=0.0, step=100.0, key="amt", format="%.2f")
        price = st.number_input("Price", min_value=0.0, value=0.0, step=0.05, key="pr", format="%.2f")

    api_session_key = st.secrets.get("integrate_api_session_key", "")

    ltp = 0.0
    qty_auto = 1
    if amount > 0 and tradingsymbol and exchange:
        ltp = get_ltp(tradingsymbol, exchange, api_session_key)
        if ltp > 0:
            qty_auto = int(amount // ltp)
            st.caption(f"Auto-Qty at LTP ₹{ltp:.2f}: {qty_auto}")
        else:
            st.caption("LTP fetch failed, enter qty manually.")

    colQ, colT, colD, colA = st.columns([2,2,2,2], gap="large")
    with colQ:
        qty = st.number_input("Qty", min_value=1, value=qty_auto, step=1, key="qty")
    with colT:
        trigger_price = st.number_input("Trig Price", min_value=0.0, value=0.0, step=0.05, key="tr_pr", format="%.2f")
    with colD:
        disclosed_quantity = st.number_input("Disc Qty", min_value=0, value=0, step=1, key="dis_qty")
    with colA:
        amo = st.checkbox("AMO?", key="amo")
    
    remarks = st.text_input("Remarks (optional)", key="rem")

    st.markdown('</div>', unsafe_allow_html=True)

    # Preview summary
    if tradingsymbol and qty and order_type and price_type:
        st.markdown('<div class="order-summary">', unsafe_allow_html=True)
        st.markdown(
            f"<b>Preview:</b> {order_type} {qty} x <b>{tradingsymbol}</b> @ ₹{price} ({price_type}, {product_type})<br>"
            f"Exch: {exchange} | Validity: {validity} | AMO: {'Yes' if amo else 'No'}",
            unsafe_allow_html=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

    if "order_confirm_popup" not in st.session_state:
        st.session_state.order_confirm_popup = False
    if "pending_order_data" not in st.session_state:
        st.session_state.pending_order_data = None

    if st.button("Review & Place Order", use_container_width=True, type="primary"):
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
        st.session_state.pending_order_data = data
        st.session_state.order_confirm_popup = True
        st.experimental_rerun()

    if st.session_state.get("order_confirm_popup", False):
        st.markdown("""
        <style>
        .popup-bg {
            position: fixed;
            left: 0; top: 0; width: 100vw; height: 100vh;
            background: rgba(0,0,0,0.30);
            display: flex; align-items: center; justify-content: center;
            z-index: 99999;
        }
        .popup-content {
            background: #fff;
            border-radius: 12px;
            padding: 26px 16px 16px 16px;
            box-shadow: 0 2px 20px #888;
            max-width: 310px;
            width: 96%;
            text-align: center;
        }
        .popup-btn {
            margin: 12px 10px 0 10px;
            min-width: 80px;
        }
        </style>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class="popup-bg">
            <div class="popup-content">
                <h5>Confirm Order</h5>
                <p>Place <b>{side}</b> {qty} x <b>{symb}</b> @ ₹{price}?</p>
            </div>
        </div>
        """.format(
            side=st.session_state.pending_order_data["order_type"],
            qty=st.session_state.pending_order_data["quantity"],
            symb=st.session_state.pending_order_data["tradingsymbol"],
            price=st.session_state.pending_order_data["price"]
        ), unsafe_allow_html=True)

        colc1, colc2 = st.columns(2)
        with colc1:
            if st.button("Yes, Place", key="yes_place"):
                resp = integrate_post("/placeorder", st.session_state.pending_order_data)
                st.success("Order submitted!")
                st.json(resp)
                st.session_state.order_confirm_popup = False
                st.session_state.pending_order_data = None
                st.experimental_rerun()
        with colc2:
            if st.button("No, Edit", key="no_edit"):
                st.session_state.order_confirm_popup = False
                st.session_state.pending_order_data = None
                st.info("Order cancelled. You can edit order details.")
                st.experimental_rerun()
