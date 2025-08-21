import streamlit as st
from utils import integrate_get, integrate_post

def snap_to_tick(price, tick_size):
    return round(round(price / tick_size) * tick_size, 2)

def extract_first_valid(d, keys, default=""):
    for k in keys:
        v = d.get(k)
        if v not in (None, "", [], {}, "null"):
            return v
    return default

def extract_qty(holding):
    qty = int(float(holding.get("dp_qty", "0") or 0))
    if qty == 0:
        qty = int(float(holding.get("t1_qty", "0") or 0))
    return qty

def is_duplicate_order(symbol, exchange, order_type, price, qty, price_type, orders):
    for o in orders:
        status = str(o.get("order_status", "")).replace(" ", "_").upper()
        if status not in ["OPEN", "PARTIALLY_FILLED"]:
            continue
        if (
            o.get("tradingsymbol", "") == symbol and
            o.get("exchange", "") == exchange and
            o.get("order_type", "") == order_type and
            abs(float(o.get("price", 0)) - float(price)) < 1e-2 and
            int(float(o.get("quantity", 0))) == int(qty) and
            o.get("price_type", "") == price_type
        ):
            return True
    return False

def set_all_selection(row_ids, val=True):
    for k in row_ids:
        st.session_state[f"select_{k}"] = val

def order_row(symbol, entry_price, qty, exchange, product_type, tick_size, price_precision, orders, unique_id, allow_manual_entry=False):
    default_sl_pct = 2.0
    default_t1_pct = 12.0
    default_t2_pct = 25.0
    half_qty = qty // 2
    rem_qty = qty - half_qty

    row_state = {}

    # Selection tick
    row_state["selected"] = st.checkbox("", value=st.session_state.get(f"select_{unique_id}", False), key=f"select_{unique_id}")

    # Stock Name
    st.markdown(f"<b>{symbol}</b>", unsafe_allow_html=True)
    # Entry Price (editable if allow_manual_entry)
    if allow_manual_entry:
        entry_price = st.number_input(
            f"Entry Price for {symbol}", min_value=0.01, value=0.0, format=f"%.{price_precision}f", key=f"entry_{unique_id}"
        )
        if entry_price == 0.0:
            st.markdown(f"<span style='color:red'>Entry Price required</span>", unsafe_allow_html=True)
    else:
        st.markdown(f"₹{entry_price:.{price_precision}f}")

    row_state["entry_price"] = entry_price
    row_state["qty"] = qty

    # SL %
    sl_pct = st.number_input(
        f"SL % for {symbol}", min_value=0.5, max_value=50.0, value=default_sl_pct, format="%.2f", key=f"sl_pct_{unique_id}"
    )
    sl_qty = st.number_input(
        f"SL Qty for {symbol}", min_value=1, max_value=qty, value=qty, key=f"sl_qty_{unique_id}"
    )

    # SL Order Type
    sl_order_type = st.radio(
        f"SL Order Type for {symbol}", ["SL-MARKET", "SL-LIMIT"], horizontal=True, key=f"sl_type_{unique_id}"
    )

    sl_trigger_price = snap_to_tick(entry_price * (1 - sl_pct / 100), tick_size)
    sl_limit_price   = snap_to_tick(entry_price * (1 - (sl_pct + 0.2) / 100), tick_size)
    st.markdown(f'<span style="color:red;font-size:13px;">SL: {sl_pct:.2f}% (Trig: ₹{sl_trigger_price:.{price_precision}f}, Limit: ₹{sl_limit_price:.{price_precision}f})</span>', unsafe_allow_html=True)

    t1_pct = st.number_input(
        f"T1 % for {symbol}", min_value=1.0, max_value=100.0, value=default_t1_pct, format="%.2f", key=f"t1_pct_{unique_id}"
    )
    t1_qty = st.number_input(
        f"T1 Qty for {symbol}", min_value=1, max_value=qty, value=half_qty, key=f"t1_qty_{unique_id}"
    )
    t1_price = snap_to_tick(entry_price * (1 + t1_pct / 100), tick_size)
    st.markdown(f'<span style="color:green;font-size:13px;">T1: {t1_pct:.2f}% (₹{t1_price:.{price_precision}f})</span>', unsafe_allow_html=True)

    t2_pct = st.number_input(
        f"T2 % for {symbol}", min_value=1.0, max_value=100.0, value=default_t2_pct, format="%.2f", key=f"t2_pct_{unique_id}"
    )
    t2_qty = st.number_input(
        f"T2 Qty for {symbol}", min_value=1, max_value=qty, value=rem_qty, key=f"t2_qty_{unique_id}"
    )
    t2_price = snap_to_tick(entry_price * (1 + t2_pct / 100), tick_size)
    st.markdown(f'<span style="color:green;font-size:13px;">T2: {t2_pct:.2f}% (₹{t2_price:.{price_precision}f})</span>', unsafe_allow_html=True)

    amo = st.checkbox("AMO", key=f"amo_{unique_id}")
    remark = "Auto Order"
    st.text_input("Remark", value=remark, key=f"remark_{unique_id}", disabled=True)

    dup_sl = is_duplicate_order(symbol, exchange, "SELL", sl_limit_price, sl_qty, sl_order_type, orders)
    dup_t1 = is_duplicate_order(symbol, exchange, "SELL", t1_price, t1_qty, "LIMIT", orders)
    dup_t2 = is_duplicate_order(symbol, exchange, "SELL", t2_price, t2_qty, "LIMIT", orders)

    row_state.update({
        "symbol": symbol,
        "exchange": exchange,
        "product_type": product_type,
        "tick_size": tick_size,
        "price_precision": price_precision,
        "sl_pct": sl_pct,
        "sl_qty": sl_qty,
        "sl_order_type": sl_order_type,
        "sl_trigger_price": sl_trigger_price,
        "sl_limit_price": sl_limit_price,
        "t1_pct": t1_pct,
        "t1_qty": t1_qty,
        "t1_price": t1_price,
        "t2_pct": t2_pct,
        "t2_qty": t2_qty,
        "t2_price": t2_price,
        "amo": amo,
        "remark": remark,
        "allow_manual_entry": allow_manual_entry,
        "dup_sl": dup_sl, "dup_t1": dup_t1, "dup_t2": dup_t2
    })
    return row_state

def place_order(state):
    sl_price_type = state["sl_order_type"]
    sl_payload = {
        "exchange": state["exchange"],
        "tradingsymbol": state["symbol"],
        "order_type": "SELL",
        "quantity": str(state["sl_qty"]),
        "price": 0.0 if sl_price_type == "SL-MARKET" else str(state["sl_limit_price"]),
        "trigger_price": str(state["sl_trigger_price"]),
        "price_type": sl_price_type,
        "product_type": state["product_type"],
        "validity": "DAY",
        "remarks": state["remark"]
    }
    t1_payload = {
        "exchange": state["exchange"],
        "tradingsymbol": state["symbol"],
        "order_type": "SELL",
        "quantity": str(state["t1_qty"]),
        "price": str(state["t1_price"]),
        "price_type": "LIMIT",
        "product_type": state["product_type"],
        "validity": "DAY",
        "remarks": state["remark"]
    }
    t2_payload = {
        "exchange": state["exchange"],
        "tradingsymbol": state["symbol"],
        "order_type": "SELL",
        "quantity": str(state["t2_qty"]),
        "price": str(state["t2_price"]),
        "price_type": "LIMIT",
        "product_type": state["product_type"],
        "validity": "DAY",
        "remarks": state["remark"]
    }
    if state["amo"]:
        sl_payload["amo"] = "Yes"
        t1_payload["amo"] = "Yes"
        t2_payload["amo"] = "Yes"
    resp = {}
    if state["sl_qty"] > 0 and state["sl_limit_price"] > 0 and not state["dup_sl"]:
        resp['sl'] = integrate_post("/placeorder", sl_payload)
    if state["t1_qty"] > 0 and state["t1_price"] > 0 and not state["dup_t1"]:
        resp['t1'] = integrate_post("/placeorder", t1_payload)
    if state["t2_qty"] > 0 and state["t2_price"] > 0 and not state["dup_t2"]:
        resp['t2'] = integrate_post("/placeorder", t2_payload)
    return resp

def show():
    st.title("🚀 Auto Order (% Based SL & Target) for Holdings / Positions")
    st.markdown("""
        <style>
        .stNumberInput label {font-size:13px;}
        </style>
        """, unsafe_allow_html=True)
    st.markdown("#### All orders in one row. <span style='color:red'><b>SL %</b></span> <span style='color:green'><b>T1/T2 %</b></span>", unsafe_allow_html=True)
    st.write("")

    orders = []
    try:
        order_data = integrate_get("/orders")
        orders = order_data.get("orders", [])
    except Exception:
        pass

    row_ids = []
    row_states = []

    # Select/Deselect all buttons OUTSIDE the form
    col_sa, col_da = st.columns([1,1])
    if col_sa.button("Select All Stocks"):
        set_all_selection(row_ids, True)
    if col_da.button("Deselect All Stocks"):
        set_all_selection(row_ids, False)

    with st.form("auto_order_form", clear_on_submit=False):
        st.write("Tick stocks, set details below, then click 'Place All Selected Orders'.")

        # POSITIONS first
        pdata = integrate_get("/positions")
        positions = pdata.get("positions") or pdata.get("data") or []
        for p in positions:
            symbol = extract_first_valid(p, ["tradingsymbol", "symbol"])
            qty = int(float(extract_first_valid(p, ["net_quantity", "netqty", "quantity", "Qty"], "0")))
            if qty <= 0:
                continue
            exchange = extract_first_valid(p, ["exchange"])
            product_type = extract_first_valid(p, ["product_type", "productType", "Product"], "INTRADAY")
            entry_price = float(extract_first_valid(p, ["day_buy_avg", "total_buy_avg"], "0.0"))
            tick_size = float(extract_first_valid(p, ["ticksize"], "0.05"))
            price_precision = int(extract_first_valid(p, ["price_precision"], "2"))
            unique_id = f"P_{symbol}_{exchange}"
            row_ids.append(unique_id)
            state = order_row(
                symbol, entry_price, qty, exchange, product_type, tick_size, price_precision, orders, unique_id
            )
            row_states.append(state)

        # HOLDINGS (NSE only)
        hdata = integrate_get("/holdings")
        holdings = hdata.get("data", [])
        for h in holdings:
            avg_buy_price = float(h.get("avg_buy_price", "0.0"))
            qty = extract_qty(h)
            if qty <= 0:
                continue
            for ts_info in h.get("tradingsymbol", []):
                if ts_info.get("exchange") != "NSE":
                    continue
                symbol = ts_info.get("tradingsymbol", "")
                exchange = ts_info.get("exchange", "")
                tick_size = float(ts_info.get("ticksize", "0.05"))
                price_precision = int(ts_info.get("price_precision", "2"))
                product_type = "CNC"
                unique_id = f"H_{symbol}_{exchange}"
                row_ids.append(unique_id)
                allow_manual_entry = (avg_buy_price == 0.0)
                entry_price = avg_buy_price if avg_buy_price > 0.0 else 0.0
                state = order_row(
                    symbol, entry_price, qty, exchange, product_type, tick_size, price_precision, orders, unique_id, allow_manual_entry
                )
                row_states.append(state)

        submitted = st.form_submit_button("Place All Selected Orders")
        if submitted:
            for state in row_states:
                if state["selected"]:
                    if state["allow_manual_entry"] and state["entry_price"] == 0.0:
                        st.error(f"{state['symbol']}: Entry price required for order!")
                        continue
                    resp = place_order(state)
                    if resp.get('sl', {}).get("status") == "ERROR":
                        st.error(f"{state['symbol']}: SL order failed: {resp['sl'].get('message', resp['sl'])}")
                    elif resp.get('sl'):
                        st.success(f"{state['symbol']}: SL {state['sl_order_type']} Trigger {state['sl_trigger_price']}, Limit {state['sl_limit_price']}({state['sl_pct']}%) Qty: {state['sl_qty']} → {resp['sl'].get('message', resp['sl'])}")
                    if resp.get('t1', {}).get("status") == "ERROR":
                        st.error(f"{state['symbol']}: T1 order failed: {resp['t1'].get('message', resp['t1'])}")
                    elif resp.get('t1'):
                        st.success(f"{state['symbol']}: T1 {state['t1_price']}({state['t1_pct']}%) Qty: {state['t1_qty']} → {resp['t1'].get('message', resp['t1'])}")
                    if resp.get('t2', {}).get("status") == "ERROR":
                        st.error(f"{state['symbol']}: T2 order failed: {resp['t2'].get('message', resp['t2'])}")
                    elif resp.get('t2'):
                        st.success(f"{state['symbol']}: T2 {state['t2_price']}({state['t2_pct']}%) Qty: {state['t2_qty']} → {resp['t2'].get('message', resp['t2'])}")
            st.rerun()

if __name__ == "__main__":
    show()
