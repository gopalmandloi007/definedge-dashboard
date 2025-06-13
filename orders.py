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
    st.header("Broker Terminal - Place / Modify / Cancel Order")

    st.markdown("""
    <style>
        .order-panel {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 20px 25px 10px 25px;
            box-shadow: 0 2px 8px #d6d6d6;
            margin-bottom: 24px;
        }
        .order-summary {
            background-color: #e7f3ff;
            border-radius: 8px;
            padding: 16px;
            margin-top: 16px;
            font-size: 1.05rem;
        }
        .stRadio > label {
            font-weight: 600;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("### 🚀 Broker Terminal Order Entry")

    if "order_confirm_popup" not in st.session_state:
        st.session_state.order_confirm_popup = False
    if "pending_order_data" not in st.session_state:
        st.session_state.pending_order_data = None

    with st.form("place_order", clear_on_submit=False):
        with st.container():
            st.markdown('<div class="order-panel">', unsafe_allow_html=True)
            tradingsymbol = st.text_input("Trading Symbol", key="ts")
            exchange = st.radio("Exchange", ["NSE", "BSE", "NFO", "BFO", "CDS", "MCX"], horizontal=True, key="exch")
            order_type = st.radio("Order Type", ["BUY", "SELL"], horizontal=True, key="ot")
            price_type = st.radio("Price Type", ["LIMIT", "MARKET", "SL-LIMIT", "SL-MARKET"], horizontal=True, key="pt")
            product_type = st.radio("Product", ["CNC", "INTRADAY", "NORMAL"], horizontal=True, key="prod")
            validity = st.radio("Validity", ["DAY", "EOS", "IOC"], horizontal=True, key="val")
            amount = st.number_input("₹ Amount", min_value=0.0, value=0.0, step=100.0, key="amt")
            api_session_key = st.secrets.get("integrate_api_session_key", "")

            ltp = 0.0
            qty = 0
            price = st.number_input("Price", min_value=0.0, value=0.0, step=0.05, key="pr")
            if amount > 0 and tradingsymbol and exchange:
                ltp = get_ltp(tradingsymbol, exchange, api_session_key)
                if ltp > 0:
                    qty = int(amount // ltp)
                    st.markdown(f"Auto-calculated Qty at LTP ₹{ltp:.2f}: **{qty}**")
                else:
                    st.warning("Could not fetch LTP. Please enter qty manually.")

            qty = st.number_input("Quantity", min_value=1, value=qty if qty > 0 else 1, step=1, key="qty")
            trigger_price = st.number_input("Trigger Price", min_value=0.0, value=0.0, step=0.05, key="tr_pr")
            disclosed_quantity = st.number_input("Disclosed Qty", min_value=0, value=0, step=1, key="dis_qty")
            amo = st.checkbox("After Market Order (AMO)?", key="amo")
            remarks = st.text_input("Remarks (optional)", key="rem")
            st.markdown('</div>', unsafe_allow_html=True)

        show_summary = tradingsymbol and qty and order_type and price_type
        if show_summary:
            st.markdown('<div class="order-summary">', unsafe_allow_html=True)
            st.markdown(f"""
            <b>Order Preview</b>  
            <ul>
                <li><b>Symbol:</b> {tradingsymbol}</li>
                <li><b>Exchange:</b> {exchange}</li>
                <li><b>Type:</b> <span style='color:{"green" if order_type=="BUY" else "red"}'>{order_type}</span></li>
                <li><b>Product:</b> {product_type}</li>
                <li><b>Qty:</b> {qty}</li>
                <li><b>Price Type:</b> {price_type}</li>
                <li><b>Price:</b> ₹{price}</li>
                <li><b>Validity:</b> {validity}</li>
                <li><b>Trigger Price:</b> {trigger_price}</li>
                <li><b>Disclosed Qty:</b> {disclosed_quantity}</li>
                <li><b>AMO:</b> {"Yes" if amo else "No"}</li>
                <li><b>Remarks:</b> {remarks or "-"}</li>
            </ul>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        submit = st.form_submit_button("Place Order")

        if submit:
            # Store order data and open confirmation popup
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

    # Confirmation popup
    if st.session_state.get("order_confirm_popup", False):
        st.markdown("""
        <style>
        .popup-bg {
            position: fixed;
            left: 0; top: 0; width: 100vw; height: 100vh;
            background: rgba(0,0,0,0.3);
            display: flex; align-items: center; justify-content: center;
            z-index: 99999;
        }
        .popup-content {
            background: #fff;
            border-radius: 12px;
            padding: 32px 32px 12px 32px;
            box-shadow: 0 2px 20px #888;
            max-width: 400px;
            width: 90%;
            text-align: center;
        }
        .popup-btn {
            margin: 16px 18px 0 18px;
            min-width: 90px;
        }
        </style>
        """, unsafe_allow_html=True)
        popup_code = """
        <div class="popup-bg">
            <div class="popup-content">
                <h4>Confirm Order Submission</h4>
                <p>Are you sure you want to place this order?</p>
            </div>
        </div>
        """
        st.markdown(popup_code, unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, Place Order", key="yes_place"):
                resp = integrate_post("/placeorder", st.session_state.pending_order_data)
                st.success("Order submitted!")
                st.json(resp)
                st.session_state.order_confirm_popup = False
                st.session_state.pending_order_data = None
                st.experimental_rerun()
        with col2:
            if st.button("No, Modify", key="no_modify"):
                st.session_state.order_confirm_popup = False
                st.session_state.pending_order_data = None
                st.info("Order Not Confirmed. Modify the fields above and resubmit.")
                st.experimental_rerun()
