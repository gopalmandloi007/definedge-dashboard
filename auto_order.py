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

def order_row(cols, symbol, entry_price, qty, exchange, product_type, tick_size, price_precision, orders, unique_id, allow_manual_entry=False):
    default_sl_pct = 2.0
    default_t1_pct = 12.0
    default_t2_pct = 25.0
    half_qty = qty // 2
    rem_qty = qty - half_qty

    selected = cols[0].checkbox("", value=st.session_state.get(f"select_{unique_id}", False), key=f"select_{unique_id}")

    cols[1].markdown(f"<b>{symbol}</b>", unsafe_allow_html=True)
    if allow_manual_entry:
        entry_price = cols[2].number_input(
            f"Entry Price {symbol}", min_value=0.01, value=0.0, format=f"%.{price_precision}f", key=f"entry_{unique_id}"
        )
        if entry_price == 0.0:
            cols[2].markdown(f"<span style='color:red'>Entry Price required</span>", unsafe_allow_html=True)
    else:
        cols[2].markdown(f"₹{entry_price:.{price_precision}f}")

    qty_display = cols[3].markdown(f"{qty}")

    sl_pct = cols[4].number_input(
        f"SL % {symbol}", min_value=0.5, max_value=50.0, value=default_sl_pct, format="%.2f", key=f"sl_pct_{unique_id}"
    )
    sl_qty = cols[5].number_input(
        f"SL Qty {symbol}", min_value=1, max_value=qty, value=qty, key=f"sl_qty_{unique_id}"
    )
    sl_order_type = cols[6].radio(
        "", ["SL-MARKET", "SL-LIMIT"], horizontal=True, key=f"sl_type_{unique_id}"
    )
    sl_trigger_price = snap_to_tick(entry_price * (1 - sl_pct / 100), tick_size)
    sl_limit_price   = snap_to_tick(entry_price * (1 - (sl_pct + 0.2) / 100), tick_size)
    cols[4].markdown(f'<span style="color:red;font-size:13px;">{sl_pct:.2f}%<br>({sl_trigger_price:.{price_precision}f}/{sl_limit_price:.{price_precision}f})</span>', unsafe_allow_html=True)

    t1_pct = cols[7].number_input(
        f"T1 % {symbol}", min_value=1.0, max_value=100.0, value=default_t1_pct, format="%.2f", key=f"t1_pct_{unique_id}"
    )
    t1_qty = cols[8].number_input(
        f"T1 Qty {symbol}", min_value=1, max_value=qty, value=half_qty, key=f"t1_qty_{unique_id}"
    )
    t1_price = snap_to_tick(entry_price * (1 + t1_pct / 100), tick_size)
    cols[7].markdown(f'<span style="color:green;font-size:13px;">{t1_pct:.2f}%<br>({t1_price:.{price_precision}f})</span>', unsafe_allow_html=True)

    t2_pct = cols[9].number_input(
        f"T2 % {symbol}", min_value=1.0, max_value=100.0, value=default_t2_pct, format="%.2f", key=f"t2_pct_{unique_id}"
    )
    t2_qty = cols[10].number_input(
        f"T2 Qty {symbol}", min_value=1, max_value=qty, value=rem_qty, key=f"t2_qty_{unique_id}"
    )
    t2_price = snap_to_tick(entry_price * (1 + t2_pct / 100), tick_size)
    cols[9].markdown(f'<span style="color:green;font-size:13px;">{t2_pct:.2f}%<br>({t2_price:.{price_precision}f})</span>', unsafe_allow_html=True)

    amo = cols[11].checkbox("AMO", key=f"amo_{unique_id}")
    remark = "Auto Order"
    cols[12].text_input("", value=remark, key=f"remark_{unique_id}", disabled=True)

    dup_sl = is_duplicate_order(symbol, exchange, "SELL", sl_limit_price, sl_qty, sl_order_type, orders)
    dup_t1 = is_duplicate_order(symbol, exchange, "SELL", t1_price, t1_qty, "LIMIT", orders)
    dup_t2 = is_duplicate_order(symbol, exchange, "SELL", t2_price, t2_qty, "LIMIT", orders)

    msg_col = cols[13]
    dup_msg = []
    if dup_sl:
        dup_msg.append('<span style="color:red;"><b>SL order exists</b></span>')
    if dup_t1:
        dup_msg.append('<span style="color:green;"><b>T1 order exists</b></span>')
    if dup_t2:
        dup_msg.append('<span style="color:green;"><b>T2 order exists</b></span>')
    if dup_msg:
        msg_col.markdown(" | ".join(dup_msg), unsafe_allow_html=True)

    return {
        "selected": selected,
        "symbol": symbol,
        "entry_price": entry_price,
        "qty": qty,
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
    }

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
    st.write("Use Select All/Deselect All buttons to quickly select/deselect stocks before placing orders.")

    orders = []
    try:
        order_data = integrate_get("/orders")
        orders = order_data.get("orders", [])
    except Exception:
        pass

    row_ids = []
    row_states = []

    col_sa, col_da = st.columns([1,1])
    if col_sa.button("Select All Stocks"):
        set_all_selection(row_ids, True)
    if col_da.button("Deselect All Stocks"):
        set_all_selection(row_ids, False)

    with st.form("auto_order_form", clear_on_submit=False):
        # Table header as columns
        hdr = st.columns([0.6, 1.3, 1.0, 1.0, 1.1, 0.9, 1.1, 0.9, 1.1, 0.9, 1.2, 1.1, 1.3, 1.7])
        hdr[0].markdown("**Sel**")
        hdr[1].markdown("**Stock Name**")
        hdr[2].markdown("**Entry Price**")
        hdr[3].markdown("**Qty**")
        hdr[4].markdown("**SL in %**")
        hdr[5].markdown("**SL Qty**")
        hdr[6].markdown("**SL Type**")
        hdr[7].markdown("**T-1 in %**")
        hdr[8].markdown("**T-1 Qty**")
        hdr[9].markdown("**T-2 in %**")
        hdr[10].markdown("**T-2 Qty**")
        hdr[11].markdown("**AMO**")
        hdr[12].markdown("**Remark**")
        hdr[13].markdown("**Status**")
        
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
            cols = st.columns([0.6, 1.3, 1.0, 1.0, 1.1, 0.9, 1.1, 0.9, 1.1, 0.9, 1.2, 1.1, 1.3, 1.7])
            state = order_row(cols, symbol, entry_price, qty, exchange, product_type, tick_size, price_precision, orders, unique_id)
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
                cols = st.columns([0.6, 1.3, 1.0, 1.0, 1.1, 0.9, 1.1, 0.9, 1.1, 0.9, 1.2, 1.1, 1.3, 1.7])
                state = order_row(cols, symbol, entry_price, qty, exchange, product_type, tick_size, price_precision, orders, unique_id, allow_manual_entry)
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
