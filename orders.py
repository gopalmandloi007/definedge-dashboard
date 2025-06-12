import streamlit as st
from utils import integrate_post
import requests

def get_ltp(tradingsymbol, exchange, api_session_key):
    # Example LTP fetcher, update endpoint as needed
    # You can replace with your own LTP fetch function
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
    st.header("Place / Modify / Cancel Order")

    st.markdown("### 🛒 Quick Order (by Amount)")
    with st.form("place_order", clear_on_submit=False):
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
        confirm = st.radio("Confirm Order?", ["Yes", "No"], horizontal=True, key="conf")
        submit = st.form_submit_button("Submit Order")

        if submit:
            # If confirmed, place order
            if confirm == "Yes":
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
            else:
                # Let user choose what to modify
                st.warning("Order Not Confirmed.")
                modify_field = st.radio("What do you want to modify?", 
                    ["Quantity", "Price", "Order Type", "Product", "Price Type", "Market/Limit"], horizontal=True, key="mod_field")
                st.info(f"Modify {modify_field} above and re-submit!")
