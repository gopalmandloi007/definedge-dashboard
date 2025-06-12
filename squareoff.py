import streamlit as st
from utils import integrate_get, integrate_post

def squareoff_hold_form(holding, qty, tradingsymbols):
    st.markdown(f"### {tradingsymbols[0]['tradingsymbol']} ({qty} Qty)")
    st.write(f"**ISIN:** {tradingsymbols[0].get('isin', '')}")
    st.write(f"**Exchanges:** " + " / ".join([x['exchange'] for x in tradingsymbols]))
    st.write(f"**Avg Buy Price:** ₹{holding.get('avg_buy_price','-')}")
    st.write(f"**DP Quantity:** {holding.get('dp_qty','-')}")
    st.write(f"**T1 Quantity:** {holding.get('t1_qty','-')}")
    st.write(f"**Haircut:** {holding.get('haircut','-')}")

    with st.form(key=f"squareoff_hold_form_{tradingsymbols[0]['tradingsymbol']}"):
        exch_names = [x['exchange'] for x in tradingsymbols]
        exch = st.selectbox("Select Exchange", exch_names)
        ts_info = next(x for x in tradingsymbols if x['exchange'] == exch)
        tradingsymbol = ts_info["tradingsymbol"]

        qty_option = st.radio("Quantity to Square Off", ["Full", "Partial"], horizontal=True)
        if qty_option == "Partial":
            squareoff_qty = st.number_input(
                "Enter quantity to square off", min_value=1, max_value=int(qty), value=1, key=f"qty_{tradingsymbol}"
            )
        else:
            squareoff_qty = int(qty)

        price_option = st.radio("Order Type", ["Market Order", "Limit Order"], horizontal=True)
        if price_option == "Limit Order":
            default_price = float(holding.get("avg_buy_price") or 0)
            squareoff_price = st.number_input("Limit Price (₹)", min_value=0.01, value=round(default_price,2), key=f"price_{tradingsymbol}")
            price_type = "LIMIT"
        else:
            squareoff_price = 0.0
            price_type = "MARKET"

        validity = st.selectbox("Order Validity", ["DAY", "IOC", "EOS"], index=0)
        remarks = st.text_input("Remarks (optional)", key=f"remarks_{tradingsymbol}")

        disclose = st.checkbox("Disclose Partial Quantity?", key=f"disclose_{tradingsymbol}")
        if disclose:
            disclosed_quantity = st.number_input(
                "Disclosed Quantity (optional)", min_value=1, max_value=int(squareoff_qty), value=1, key=f"discloseqty_{tradingsymbol}"
            )
        else:
            disclosed_quantity = None

        # Warn user if default values are being used
        warn = False
        if qty_option == "Partial" and squareoff_qty == 1:
            st.warning("⚠ You have selected Partial but quantity is only 1. Please confirm if this is correct.")
            warn = True
        if price_option == "Limit Order" and squareoff_price == round(default_price,2):
            st.info("ℹ Default limit price is your average buy price. Change if needed.")

        st.markdown("---")
        submitted = st.form_submit_button("🟢 Place Square Off Order")
        if submitted:
            # Final confirmation before placing order
            if st.session_state.get(f"confirm_{tradingsymbol}") is not True:
                st.session_state[f"confirm_{tradingsymbol}"] = True
                st.warning("Please review your inputs and click 'Place Square Off Order' again to confirm.")
            else:
                payload = {
                    "exchange": exch,
                    "tradingsymbol": tradingsymbol,
                    "order_type": "SELL",
                    "quantity": str(squareoff_qty),
                    "price": str(squareoff_price),
                    "price_type": price_type,
                    "product_type": "CNC",
                    "validity": validity,
                }
                if remarks:
                    payload["remarks"] = remarks
                if disclosed_quantity:
                    payload["disclosed_quantity"] = str(disclosed_quantity)
                with st.spinner("Placing order..."):
                    resp = integrate_post("/placeorder", payload)
                status = resp.get('status') or resp.get('message') or resp
                st.success(f"Order Response: {status}")
                st.json(resp)
                st.session_state[f"confirm_{tradingsymbol}"] = False
