import streamlit as st
from session_utils import get_session_key, api_call_with_auto_refresh

st.title("Definedge Integrate Demo (Auto-refresh Session)")

# Example usage: Get holdings
if st.button("Fetch Holdings"):
    holdings_url = "https://api.definedge.com/holdings"   # Update as per your actual API endpoint
    data = api_call_with_auto_refresh(holdings_url)
    if data:
        st.json(data)
    else:
        st.error("Failed to fetch holdings.")

# Example usage: Place order (POST)
st.markdown("---")
st.subheader("Place Order Example")
order_symbol = st.text_input("Symbol", value="SBIN-EQ")
order_qty = st.number_input("Quantity", min_value=1, value=1)
if st.button("Place Dummy Order"):
    order_url = "https://api.definedge.com/placeorder"  # Update as needed
    payload = {
        "exchange": "NSE",
        "tradingsymbol": order_symbol,
        "order_type": "BUY",
        "quantity": str(order_qty),
        "price": "0",
        "price_type": "MARKET",
        "product_type": "CNC",
        "validity": "DAY"
    }
    data = api_call_with_auto_refresh(order_url, payload=payload, method="POST")
    if data:
        st.success("Order Response:")
        st.json(data)
    else:
        st.error("Order placement failed.")
