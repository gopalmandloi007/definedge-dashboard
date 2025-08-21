import streamlit as st
from utils import integrate_get, integrate_post

# --- Ultra-compact CSS ---
st.markdown("""
<style>
.stApp { max-width: 1750px; }
div[data-testid="column"] { padding-left:2px !important; padding-right:2px !important;}
label, .stNumberInput label, .stRadio label, .stCheckbox label { font-size:10px !important; margin:0px !important; }
.stNumberInput input, .stTextInput input { font-size:10px !important; height:18px !important; padding:1px 2px !important; min-width:28px !important; max-width:46px !important;}
[data-testid="stRadio"], [data-testid="stCheckbox"] label { font-size:10px !important; }
.stMarkdown, .stMarkdown p { font-size:10px !important; margin:0px !important;}
</style>
""", unsafe_allow_html=True)

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
    # Stock name
    cols[1].markdown(f"<span style='font-size:10px'><b>{symbol}</b></span>", unsafe_allow_html=True)
    # Entry
    if allow_manual_entry:
        entry_price = cols[2].number_input(
            "", min_value=0.01, value=0.0, format=f"%.{price_precision}f", key=f"entry_{unique_id}", label_visibility="hidden"
        )
        if entry_price == 0.0:
            cols[2].markdown(f"<span style='color:red;font-size:9px'>Req!</span>", unsafe_allow_html=True)
    else:
        cols[2].markdown(f"<span style='font-size:10px'>₹{entry_price:.{price_precision}f}</span>", unsafe_allow_html=True)
    # Qty
    cols[3].markdown(f"<span style='font-size:10px'>{qty}</span>", unsafe_allow_html=True)

    # SL %
    sl_pct = cols[4].number_input(
        "", min_value=0.5, max_value=50.0, value=default_sl_pct, format="%.2f", key=f"sl_pct_{unique_id}", label_visibility="hidden"
    )
    sl_qty = cols[5].number_input(
        "", min_value=1, max_value=qty, value=qty, key=f"sl_qty_{unique_id}", label_visibility="hidden"
    )
    sl_order_type = cols[6].radio(
        "", ["SL-M", "SL-L"], horizontal=True, key=f"sl_type_{unique_id}", label_visibility="hidden"
    )
    sl_trigger_price = snap_to_tick(entry_price * (1 - sl_pct / 100), tick_size)
    sl_limit_price   = snap_to_tick(entry_price * (1 - (sl_pct + 0.2) / 100), tick_size)
    cols[4].markdown(
        f'<span style="color:red;font-size:10px;">{sl_pct:.2f}%<br>({sl_trigger_price:.{price_precision}f}/{sl_limit_price:.{price_precision}f})</span>',
        unsafe_allow_html=True
    )

    # T1
    t1_pct = cols[7].number_input(
        "", min_value=1.0, max_value=100.0, value=default_t1_pct, format="%.2f", key=f"t1_pct_{unique_id}", label_visibility="hidden"
    )
    t1_qty = cols[8].number_input(
        "", min_value=1, max_value=qty, value=half_qty, key=f"t1_qty_{unique_id}", label_visibility="hidden"
    )
    t1_price = snap_to_tick(entry_price * (1 + t1_pct / 100), tick_size)
    cols[7].markdown(
        f'<span style="color:green;font-size:10px;">{t1_pct:.2f}%<br>({t1_price:.{price_precision}f})</span>',
        unsafe_allow_html=True
    )

    # T2
    t2_pct = cols[9].number_input(
        "", min_value=1.0, max_value=100.0, value=default_t2_pct, format="%.2f", key=f"t2_pct_{unique_id}", label_visibility="hidden"
    )
    t2_qty = cols[10].number_input(
        "", min_value=1, max_value=qty, value=rem_qty, key=f"t2_qty_{unique_id}", label_visibility="hidden"
    )
    t2_price = snap_to_tick(entry_price * (1 + t2_pct / 100), tick_size)
    cols[9].markdown(
        f'<span style="color:green;font-size:10px;">{t2_pct:.2f}%<br>({t2_price:.{price_precision}f})</span>',
        unsafe_allow_html=True
    )

    amo = cols[11].checkbox("", value=st.session_state.get(f"amo_{unique_id}", False), key=f"amo_{unique_id}")
    remark = "Auto Order"
    cols[12].text_input("", value=remark, key=f"remark_{unique_id}", disabled=True, label_visibility="hidden")

    dup_sl = is_duplicate_order(symbol, exchange, "SELL", sl_limit_price, sl_qty, "SL-MARKET" if sl_order_type=="SL-M" else "SL-LIMIT", orders)
    dup_t1 = is_duplicate_order(symbol, exchange, "SELL", t1_price, t1_qty, "LIMIT", orders)
    dup_t2 = is_duplicate_order(symbol, exchange, "SELL", t2_price, t2_qty, "LIMIT", orders)

    msg_col = cols[13]
    dup_msg = []
    if dup_sl:  dup_msg.append('<span style="color:red;"><b>SL!</b></span>')
    if dup_t1:  dup_msg.append('<span style="color:green;"><b>T1!</b></span>')
    if dup_t2:  dup_msg.append('<span style="color:green;"><b>T2!</b></span>')
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
    sl_price_type = "SL-MARKET" if state["sl_order_type"]=="SL-M" else "SL-LIMIT"
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
    st.title("Holdings / Positions")
    st.markdown("All orders in one row. <span style='color:red'><b>SL%</b></span> <span style='color:green'><b>T1/T2%</b></span>", unsafe_allow_html=True)

    orders = []
    try:
        order_data = integrate_get("/orders")
        orders = order_data.get("orders", [])
    except Exception:
        pass

    # Track row IDs for selection
    if "row_ids" not in st.session_state:
        st.session_state["row_ids"] = []

    col_sa, col_da = st.columns([1,1])
    if col_sa.button("Select All"):
        set_all_selection(st.session_state["row_ids"], True)
    if col_da.button("Deselect All"):
        set_all_selection(st.session_state["row_ids"], False)

    with st.form("auto_order_form", clear_on_submit=False):
        hdr = st.columns([0.5, 1.1, 0.7, 0.7, 0.7, 0.7, 0.8, 0.7, 0.8, 0.7, 0.7, 0.6, 0.8, 1.1])
        hdr[0].markdown("**Sel**")
        hdr[1].markdown("**Stock**")
        hdr[2].markdown("**Entry**")
        hdr[3].markdown("**Qty**")
        hdr[4].markdown("**SL%**")
        hdr[5].markdown("**SLQ**")
        hdr[6].markdown("**SLT**")
        hdr[7].markdown("**T1%**")
        hdr[8].markdown("**T1Q**")
        hdr[9].markdown("**T2%**")
        hdr[10].markdown("**T2Q**")
        hdr[11].markdown("**AMO**")
        hdr[12].markdown("**Rem**")
        hdr[13].markdown("**Msg**")

        row_ids = []
        row_states = []

        # POSITIONS
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
            cols = st.columns([0.5, 1.1, 0.7, 0.7, 0.7, 0.7, 0.8, 0.7, 0.8, 0.7, 0.7, 0.6, 0.8, 1.1])
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
                cols = st.columns([0.5, 1.1, 0.7, 0.7, 0.7, 0.7, 0.8, 0.7, 0.8, 0.7, 0.7, 0.6, 0.8, 1.1])
                state = order_row(cols, symbol, entry_price, qty, exchange, product_type, tick_size, price_precision, orders, unique_id, allow_manual_entry)
                row_states.append(state)

        st.session_state["row_ids"] = row_ids

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
                        st.success(f"{state['symbol']}: SL {state['sl_order_type']} Trig {state['sl_trigger_price']} Lim {state['sl_limit_price']} Qty {state['sl_qty']} → {resp['sl'].get('message', resp['sl'])}")
                    if resp.get('t1', {}).get("status") == "ERROR":
                        st.error(f"{state['symbol']}: T1 order failed: {resp['t1'].get('message', resp['t1'])}")
                    elif resp.get('t1'):
                        st.success(f"{state['symbol']}: T1 {state['t1_price']}({state['t1_pct']}%) Qty: {state['t1_qty']} → {resp['t1'].get('message', resp['t1'])}")
                    if resp.get('t2', {}).get("status") == "ERROR":
                        st.error(f"{state['symbol']}: T2 order failed: {resp['t2'].get('message', resp['t2'])}")
                    elif resp.get('t2'):
                        st.success(f"{state['symbol']}: T2 {state['t2_price']}({state['t2_pct']}%) Qty: {state['t2_qty']} → {resp['t2'].get('message', resp['t2'])}")

if __name__ == "__main__":
    show()
