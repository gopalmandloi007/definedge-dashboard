import streamlit as st
from utils import integrate_get, integrate_post
import requests

def show():
    st.header("Orders Book & Manage")

    # Fetch orders
    data = integrate_get("/orders")
    orderlist = data.get("orders", [])

    # Normalize statuses: replace spaces with underscores and uppercase
    open_statuses = {"OPEN", "PARTIALLY_FILLED"}
    def norm_status(s):
        return str(s).replace(" ", "_").upper()

    open_orders = [o for o in orderlist if norm_status(o.get("order_status", "")) in open_statuses]

    if not open_orders:
        st.info("No open/partial orders found.")
        return

    # Table columns to show
    cols = [
        "order_id", "tradingsymbol", "order_type", "quantity", "price_type", "price",
        "product_type", "order_status", "exchange", "validity"
    ]
    col_labels = [
        "Order ID", "Symbol", "Side", "Qty", "Type", "Price", "Product",
        "Status", "Exch", "Validity"
    ]

    # Track which order is being modified
    modify_id = st.session_state.get("modify_id", None)

    # Show table
    columns = st.columns([1.5, 1.5, 1, 1, 1, 1.3, 1.3, 1.3, 1, 1, 1.6, 1.3])
    for i, label in enumerate(col_labels):
        columns[i].markdown(f"**{label}**")
    columns[-2].markdown("**Modify**")
    columns[-1].markdown("**Cancel**")
    for order in open_orders:
        columns = st.columns([1.5, 1.5, 1, 1, 1, 1.3, 1.3, 1.3, 1, 1, 1.6, 1.3])
        for i, key in enumerate(cols):
            columns[i].write(order.get(key, ""))
        if columns[-2].button("Modify", key=f"mod_btn_{order['order_id']}"):
            st.session_state["modify_id"] = order["order_id"]
            st.rerun()
        if columns[-1].button("Cancel", key=f"cancel_btn_{order['order_id']}"):
            api_session_key = st.secrets.get("integrate_api_session_key", "")
            url = f"https://integrate.definedgesecurities.com/dart/v1/cancel/{order['order_id']}"
            headers = {"Authorization": api_session_key}
            resp = requests.get(url, headers=headers)
            try:
                result = resp.json()
            except Exception:
                result = {"status": "ERROR", "message": "Invalid API response"}
            if result.get("status") == "ERROR":
                st.error(f"Cancel Failed: {result.get('message','Error')}")
            else:
                st.success("Order cancelled!")
            st.rerun()

    # Show full-width modify form below table if any
    if modify_id:
        order = next((o for o in open_orders if o["order_id"] == modify_id), None)
        if order:
            st.markdown("---")
            st.subheader(f"Modify Order: {order['tradingsymbol']} ({order['order_id']})")

            # Price type options
            price_type_options = ["LIMIT", "MARKET", "SL-LIMIT", "SL-MARKET"]
            # Normalize order price_type for matching (handle variations)
            def match_price_type(pt):
                pt_norm = str(pt).replace("_", "-").replace(" ", "-").upper()
                for idx, opt in enumerate(price_type_options):
                    if pt_norm == opt:
                        return idx
                # Fallback: try to match ignoring hyphens
                pt_simple = pt_norm.replace("-", "")
                for idx, opt in enumerate(price_type_options):
                    if pt_simple == opt.replace("-", ""):
                        return idx
                return 0  # Default to first option

            price_type_idx = match_price_type(order.get("price_type", "LIMIT"))

            product_options = ["CNC", "INTRADAY", "NORMAL"]
            product_idx = product_options.index(order.get("product_type", "CNC")) if order.get("product_type", "CNC") in product_options else 0

            validity_options = ["DAY", "EOS", "IOC"]
            validity_idx = validity_options.index(order.get("validity", "DAY")) if order.get("validity", "DAY") in validity_options else 0

            with st.form(f"mod_form_{order['order_id']}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    new_qty = st.number_input("Qty", min_value=1, value=int(order["quantity"]), key=f"qty_{order['order_id']}")
                    new_price = st.number_input("Price", min_value=0.0, value=float(order["price"]), key=f"price_{order['order_id']}")
                with col2:
                    new_price_type = st.selectbox(
                        "Type", price_type_options, index=price_type_idx, key=f"ptype_{order['order_id']}"
                    )
                    new_product = st.selectbox(
                        "Product", product_options, index=product_idx, key=f"prod_{order['order_id']}"
                    )
                with col3:
                    new_validity = st.selectbox(
                        "Validity", validity_options, index=validity_idx, key=f"val_{order['order_id']}"
                    )
                submit = st.form_submit_button("✓ Confirm")
                cancel = st.form_submit_button("✗ Cancel")
                if submit:
                    payload = {
                        "exchange": order.get('exchange', ''),
                        "order_id": order['order_id'],
                        "tradingsymbol": order.get('tradingsymbol', ''),
                        "quantity": str(new_qty),
                        "price": str(new_price),
                        "product_type": new_product,
                        "order_type": order.get('order_type', ''),
                        "price_type": new_price_type,
                        "validity": new_validity
                    }
                    resp = integrate_post("/modify", payload)
                    if resp.get("status") == "ERROR":
                        st.error(f"Modify Failed: {resp.get('message','Error')}")
                    else:
                        st.success("Order modification submitted!")
                    st.session_state["modify_id"] = None
                    st.rerun()
                if cancel:
                    st.session_state["modify_id"] = None
                    st.rerun()
