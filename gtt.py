import streamlit as st
import pandas as pd
from utils import get_integrate_client

def show():
    st.header("GTT Orders")
    conn, io = get_integrate_client()

    st.subheader("Place GTT Order")
    gtt_type = st.radio("Type", ["Single", "OCO"])
    with st.form("place_gtt_form"):
        tradingsymbol = st.text_input("Symbol", value="SBIN-EQ")
        exchange = st.selectbox("Exchange", ["NSE", "BSE"])
        order_type = st.selectbox("Order Type", ["BUY", "SELL"])
        if gtt_type == "Single":
            quantity = st.number_input("Quantity", min_value=1, value=1)
            trigger_price = st.number_input("Trigger Price", value=600.0)
            price = st.number_input("Order Price", value=605.0)
        else:
            target_quantity = st.number_input("Target Quantity", min_value=1, value=5)
            stoploss_quantity = st.number_input("Stoploss Quantity", min_value=1, value=5)
            target_price = st.number_input("Target Price", value=700.0)
            stoploss_price = st.number_input("Stoploss Price", value=550.0)
        remarks = st.text_input("Remarks", value="")
        submitted = st.form_submit_button("Place GTT")
        if submitted:
            try:
                if gtt_type == "Single":
                    resp = io.place_gtt_order(
                        tradingsymbol=tradingsymbol,
                        exchange=conn.EXCHANGE_TYPE_NSE if exchange == "NSE" else conn.EXCHANGE_TYPE_BSE,
                        order_type=conn.ORDER_TYPE_BUY if order_type == "BUY" else conn.ORDER_TYPE_SELL,
                        quantity=str(int(quantity)),
                        alert_price=str(trigger_price),
                        price=str(price),
                        condition="LTP_BELOW"
                    )
                else:
                    resp = io.place_oco_order(
                        tradingsymbol=tradingsymbol,
                        exchange=conn.EXCHANGE_TYPE_NSE if exchange == "NSE" else conn.EXCHANGE_TYPE_BSE,
                        order_type=conn.ORDER_TYPE_BUY if order_type == "BUY" else conn.ORDER_TYPE_SELL,
                        target_quantity=str(int(target_quantity)),
                        stoploss_quantity=str(int(stoploss_quantity)),
                        target_price=str(target_price),
                        stoploss_price=str(stoploss_price),
                        remarks=remarks
                    )
                st.success(f"GTT Placed: {resp}")
            except Exception as e:
                st.error(f"GTT placement failed: {e}")
    # GTT Book
    st.subheader("GTT Order Book")
    orders = io.get_gtt_order_book()
    if not orders:
        st.info("No GTT orders found.")
    else:
        df = pd.DataFrame(orders)
        show_cols = ["alert_id", "tradingsymbol", "order_type", "quantity", "price", "trigger_price", "order_time"]
        st.dataframe(df[show_cols], use_container_width=True)
        idx = st.selectbox("Select GTT to modify/cancel", options=list(range(len(df))), format_func=lambda x: f"{df.iloc[x]['tradingsymbol']} ({df.iloc[x]['alert_id']})" if len(df) else "")
        selected = df.iloc[idx]
        with st.form("modify_gtt_form"):
            qty = st.number_input("Quantity", min_value=1, value=int(selected["quantity"]), key="gtt_qty")
            price = st.number_input("Price", value=float(selected["price"]), key="gtt_price")
            trigger = st.number_input("Trigger Price", value=float(selected["trigger_price"]), key="gtt_trig")
            submitted = st.form_submit_button("Modify GTT")
            if submitted:
                try:
                    resp = io.modify_gtt_order(
                        alert_id=selected["alert_id"],
                        tradingsymbol=selected["tradingsymbol"],
                        order_type=selected["order_type"],
                        quantity=str(int(qty)),
                        price=str(price),
                        alert_price=str(trigger),
                        exchange=selected["exchange"]
                    )
                    st.success(f"GTT Modified: {resp}")
                except Exception as e:
                    st.error(f"GTT modify failed: {e}")
        if st.button("Cancel GTT"):
            try:
                resp = io.cancel_gtt_order(alert_id=selected["alert_id"])
                st.success(f"GTT Cancelled: {resp}")
            except Exception as e:
                st.error(f"GTT cancel failed: {e}")
