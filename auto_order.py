import streamlit as st
from utils import integrate_get, integrate_post

def snap_to_tick(price, tick_size):
    """Snap price to nearest valid tick."""
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
    """Check if an OPEN or PARTIALLY_FILLED order with same key fields exists."""
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

def order_row(symbol, entry_price, qty, exchange, product_type, tick_size, price_precision, orders, unique_id, allow_manual_entry=False):
    default_sl_pct = 2.0
    default_t1_pct = 12.0
    default_t2_pct = 25.0
    half_qty = qty // 2
    rem_qty = qty - half_qty

    cols = st.columns([1.3, 1.0, 1.0, 1.1, 0.9, 1.1, 0.9, 1.1, 0.9, 1.2, 1.1, 1.3])
    # Stock Name
    cols[0].markdown(f"<b>{symbol}</b>", unsafe_allow_html=True)
    # Entry Price (editable if allow_manual_entry)
    if allow_manual_entry:
        entry_price = cols[1].number_input(
            f"Entry Price", min_value=0.01, value=0.0, format=f"%.{price_precision}f", key=f"entry_{unique_id}"
        )
        if entry_price == 0.0:
            cols[1].markdown(f"<span style='color:red'>Entry Price required</span>", unsafe_allow_html=True)
    else:
        cols[1].markdown(f"₹{entry_price:.{price_precision}f}")
    # Qty
    cols[2].markdown(f"{qty}")

    # SL %
    sl_pct = cols[3].number_input(
        f"SL %", min_value=0.5, max_value=50.0, value=default_sl_pct, format="%.2f", key=f"sl_pct_{unique_id}"
    )
    sl_qty = cols[4].number_input(
        f"SL Qty", min_value=1, max_value=qty, value=qty, key=f"sl_qty_{unique_id}"
    )
    t1_pct = cols[5].number_input(
        f"T1 %", min_value=1.0, max_value=100.0, value=default_t1_pct, format="%.2f", key=f"t1_pct_{unique_id}"
    )
    t1_qty = cols[6].number_input(
        f"T1 Qty", min_value=1, max_value=qty, value=half_qty, key=f"t1_qty_{unique_id}"
    )
    t2_pct = cols[7].number_input(
        f"T2 %", min_value=1.0, max_value=100.0, value=default_t2_pct, format="%.2f", key=f"t2_pct_{unique_id}"
    )
    t2_qty = cols[8].number_input(
        f"T2 Qty", min_value=1, max_value=qty, value=rem_qty, key=f"t2_qty_{unique_id}"
    )
    amo = cols[9].checkbox("AMO", key=f"amo_{unique_id}")
    remark = "Auto Order"
    cols[10].text_input("Remark", value=remark, key=f"remark_{unique_id}", disabled=True)
    submit = cols[11].button("Place Orders", key=f"place_btn_{unique_id}")

    cols[3].markdown(f'<span style="color:red;"><b>{sl_pct:.2f}%</b></span>', unsafe_allow_html=True)
    cols[5].markdown(f'<span style="color:green;"><b>{t1_pct:.2f}%</b></span>', unsafe_allow_html=True)
    cols[7].markdown(f'<span style="color:green;"><b>{t2_pct:.2f}%</b></span>', unsafe_allow_html=True)

    # Calculate prices, snapped to tick
    sl_trigger_price = snap_to_tick(entry_price * (1 - sl_pct / 100), tick_size)
    sl_limit_price   = snap_to_tick(entry_price * (1 - (sl_pct + 0.2) / 100), tick_size)
    t1_price = snap_to_tick(entry_price * (1 + t1_pct / 100), tick_size)
    t2_price = snap_to_tick(entry_price * (1 + t2_pct / 100), tick_size)
    validity = "DAY"

    dup_sl = is_duplicate_order(symbol, exchange, "SELL", sl_limit_price, sl_qty, "SL-LIMIT" if not amo else "SL-MARKET", orders)
    dup_t1 = is_duplicate_order(symbol, exchange, "SELL", t1_price, t1_qty, "LIMIT", orders)
    dup_t2 = is_duplicate_order(symbol, exchange, "SELL", t2_price, t2_qty, "LIMIT", orders)

    dup_msg = []
    if dup_sl:
        dup_msg.append('<span style="color:red;"><b>SL order exists</b></span>')
    if dup_t1:
        dup_msg.append('<span style="color:green;"><b>T1 order exists</b></span>')
    if dup_t2:
        dup_msg.append('<span style="color:green;"><b>T2 order exists</b></span>')
    if dup_msg:
        cols[11].markdown(" | ".join(dup_msg), unsafe_allow_html=True)

    if (dup_sl or dup_t1 or dup_t2) and submit:
        st.warning("Some orders already in OPEN state. Avoiding duplicate orders.")
        submit = False

    return submit, sl_pct, sl_qty, sl_trigger_price, sl_limit_price, t1_pct, t1_qty, t1_price, t2_pct, t2_qty, t2_price, amo, remark, entry_price

def show():
    st.title("🚀 Auto Order (% Based SL & Target) for Holdings / Positions")
    st.markdown("""
        <style>
        .stNumberInput label {font-size:13px;}
        </style>
        """, unsafe_allow_html=True)
    st.markdown("#### All orders in one row. <span style='color:red'><b>SL %</b></span> <span style='color:green'><b>T1/T2 %</b></span>", unsafe_allow_html=True)
    st.write("")

    hdr = st.columns([1.3, 1.0, 1.0, 1.1, 0.9, 1.1, 0.9, 1.1, 0.9, 1.2, 1.1, 1.3])
    hdr[0].markdown("**Stock Name**")
    hdr[1].markdown("**Entry Price**")
    hdr[2].markdown("**Qty**")
    hdr[3].markdown("**SL in %**")
    hdr[4].markdown("**SL Qty**")
    hdr[5].markdown("**T-1 in %**")
    hdr[6].markdown("**T-1 Qty**")
    hdr[7].markdown("**T-2 in %**")
    hdr[8].markdown("**T-2 Qty**")
    hdr[9].markdown("**AMO**")
    hdr[10].markdown("**Remark**")
    hdr[11].markdown("**Action**")

    # Get current open orders
    orders = []
    try:
        order_data = integrate_get("/orders")
        orders = order_data.get("orders", [])
    except Exception:
        pass

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
        submit, sl_pct, sl_qty, sl_trigger_price, sl_limit_price, t1_pct, t1_qty, t1_price, t2_pct, t2_qty, t2_price, amo, remark, entry_price = order_row(
            symbol, entry_price, qty, exchange, product_type, tick_size, price_precision, orders, unique_id
        )
        if submit:
            sl_price_type = "SL-MARKET" if amo else "SL-LIMIT"
            sl_payload = {
                "exchange": exchange,
                "tradingsymbol": symbol,
                "order_type": "SELL",
                "quantity": str(sl_qty),
                "price": 0.0 if sl_price_type == "SL-MARKET" else str(sl_limit_price),
                "trigger_price": str(sl_trigger_price),
                "price_type": sl_price_type,
                "product_type": product_type,
                "validity": "DAY",
                "remarks": remark
            }
            t1_payload = {
                "exchange": exchange,
                "tradingsymbol": symbol,
                "order_type": "SELL",
                "quantity": str(t1_qty),
                "price": str(t1_price),
                "price_type": "LIMIT",
                "product_type": product_type,
                "validity": "DAY",
                "remarks": remark
            }
            t2_payload = {
                "exchange": exchange,
                "tradingsymbol": symbol,
                "order_type": "SELL",
                "quantity": str(t2_qty),
                "price": str(t2_price),
                "price_type": "LIMIT",
                "product_type": product_type,
                "validity": "DAY",
                "remarks": remark
            }
            if amo:
                sl_payload["amo"] = "Yes"
                t1_payload["amo"] = "Yes"
                t2_payload["amo"] = "Yes"
            resp = {}
            if sl_qty > 0 and sl_limit_price > 0:
                resp_sl = integrate_post("/placeorder", sl_payload)
                resp['sl'] = resp_sl
            else:
                resp['sl'] = {"status": "ERROR", "message": "SL price or qty invalid"}
            if t1_qty > 0 and t1_price > 0:
                resp_t1 = integrate_post("/placeorder", t1_payload)
                resp['t1'] = resp_t1
            if t2_qty > 0 and t2_price > 0:
                resp_t2 = integrate_post("/placeorder", t2_payload)
                resp['t2'] = resp_t2
            if resp.get('sl', {}).get("status") == "ERROR":
                st.error(f"{symbol}: SL order failed: {resp['sl'].get('message', resp['sl'])}")
            else:
                st.success(f"{symbol}: SL Trigger {sl_trigger_price}, Limit {sl_limit_price}({sl_pct}%) Qty: {sl_qty} → {resp['sl'].get('message', resp['sl'])}")
            if resp.get('t1', {}).get("status") == "ERROR":
                st.error(f"{symbol}: T1 order failed: {resp['t1'].get('message', resp['t1'])}")
            else:
                st.success(f"{symbol}: T1 {t1_price}({t1_pct}%) Qty: {t1_qty} → {resp['t1'].get('message', resp['t1'])}")
            if resp.get('t2', {}).get("status") == "ERROR":
                st.error(f"{symbol}: T2 order failed: {resp['t2'].get('message', resp['t2'])}")
            else:
                st.success(f"{symbol}: T2 {t2_price}({t2_pct}%) Qty: {t2_qty} → {resp['t2'].get('message', resp['t2'])}")
            st.rerun()

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
                continue  # Only NSE
            symbol = ts_info.get("tradingsymbol", "")
            exchange = ts_info.get("exchange", "")
            tick_size = float(ts_info.get("ticksize", "0.05"))
            price_precision = int(ts_info.get("price_precision", "2"))
            product_type = "CNC"
            unique_id = f"H_{symbol}_{exchange}"
            allow_manual_entry = (avg_buy_price == 0.0)
            entry_price = avg_buy_price if avg_buy_price > 0.0 else 0.0
            submit, sl_pct, sl_qty, sl_trigger_price, sl_limit_price, t1_pct, t1_qty, t1_price, t2_pct, t2_qty, t2_price, amo, remark, entry_price = order_row(
                symbol, entry_price, qty, exchange, product_type, tick_size, price_precision, orders, unique_id, allow_manual_entry
            )
            if submit:
                if entry_price == 0.0:
                    st.error(f"{symbol}: Entry price required for order!")
                    continue
                sl_price_type = "SL-MARKET" if amo else "SL-LIMIT"
                sl_payload = {
                    "exchange": exchange,
                    "tradingsymbol": symbol,
                    "order_type": "SELL",
                    "quantity": str(sl_qty),
                    "price": 0.0 if sl_price_type == "SL-MARKET" else str(sl_limit_price),
                    "trigger_price": str(sl_trigger_price),
                    "price_type": sl_price_type,
                    "product_type": product_type,
                    "validity": "DAY",
                    "remarks": remark
                }
                t1_payload = {
                    "exchange": exchange,
                    "tradingsymbol": symbol,
                    "order_type": "SELL",
                    "quantity": str(t1_qty),
                    "price": str(t1_price),
                    "price_type": "LIMIT",
                    "product_type": product_type,
                    "validity": "DAY",
                    "remarks": remark
                }
                t2_payload = {
                    "exchange": exchange,
                    "tradingsymbol": symbol,
                    "order_type": "SELL",
                    "quantity": str(t2_qty),
                    "price": str(t2_price),
                    "price_type": "LIMIT",
                    "product_type": product_type,
                    "validity": "DAY",
                    "remarks": remark
                }
                if amo:
                    sl_payload["amo"] = "Yes"
                    t1_payload["amo"] = "Yes"
                    t2_payload["amo"] = "Yes"
                resp = {}
                if sl_qty > 0 and sl_limit_price > 0:
                    resp_sl = integrate_post("/placeorder", sl_payload)
                    resp['sl'] = resp_sl
                else:
                    resp['sl'] = {"status": "ERROR", "message": "SL price or qty invalid"}
                if t1_qty > 0 and t1_price > 0:
                    resp_t1 = integrate_post("/placeorder", t1_payload)
                    resp['t1'] = resp_t1
                if t2_qty > 0 and t2_price > 0:
                    resp_t2 = integrate_post("/placeorder", t2_payload)
                    resp['t2'] = resp_t2
                if resp.get('sl', {}).get("status") == "ERROR":
                    st.error(f"{symbol}: SL order failed: {resp['sl'].get('message', resp['sl'])}")
                else:
                    st.success(f"{symbol}: SL Trigger {sl_trigger_price}, Limit {sl_limit_price}({sl_pct}%) Qty: {sl_qty} → {resp['sl'].get('message', resp['sl'])}")
                if resp.get('t1', {}).get("status") == "ERROR":
                    st.error(f"{symbol}: T1 order failed: {resp['t1'].get('message', resp['t1'])}")
                else:
                    st.success(f"{symbol}: T1 {t1_price}({t1_pct}%) Qty: {t1_qty} → {resp['t1'].get('message', resp['t1'])}")
                if resp.get('t2', {}).get("status") == "ERROR":
                    st.error(f"{symbol}: T2 order failed: {resp['t2'].get('message', resp['t2'])}")
                else:
                    st.success(f"{symbol}: T2 {t2_price}({t2_pct}%) Qty: {t2_qty} → {resp['t2'].get('message', resp['t2'])}")
                st.rerun()

if __name__ == "__main__":
    show()
