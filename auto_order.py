import streamlit as st
from utils import integrate_get, integrate_post

TICK_SIZE = 0.05  # NSE/BSE equity tick size

def snap_to_tick(price, tick_size=TICK_SIZE):
    """Snap price to nearest valid tick."""
    return round(round(price / tick_size) * tick_size, 2)

def extract_first_valid(d, keys, default=""):
    for k in keys:
        v = d.get(k)
        if v not in (None, "", [], {}, "null"):
            return v
    return default

def extract_qty(pos):
    for k in ['netqty', 'net_quantity', 'net_qty', 'quantity', 'Qty', 'dp_qty']:
        v = pos.get(k)
        if v is not None and v != "":
            try:
                return int(float(v))
            except Exception:
                continue
    return 0

def get_entry_price(symbol, holdings, positions):
    # Try positions first, fallback to holdings
    for p in positions:
        if extract_first_valid(p, ["tradingsymbol", "symbol"]) == symbol:
            ep = extract_first_valid(p, ["day_buy_avg", "total_buy_avg"], None)
            if ep and float(ep) > 0:
                return float(ep)
    for h in holdings:
        ts_info = h.get("tradingsymbol", [{}])[0] if h.get("tradingsymbol", None) else h
        if ts_info.get("tradingsymbol", "") == symbol:
            ep = extract_first_valid(ts_info, ["avg_buy_price", "average_price", "buy_avg_price"], None)
            if ep and float(ep) > 0:
                return float(ep)
    return 0.0

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

def order_row(symbol, entry_price, qty, exchange, product_type, orders, unique_id):
    # Defaults
    default_sl_pct = 2.0
    default_t1_pct = 12.0
    default_t2_pct = 25.0
    half_qty = qty // 2
    rem_qty = qty - half_qty

    cols = st.columns([1.3, 1.0, 1.0, 1.1, 0.9, 1.1, 0.9, 1.1, 0.9, 1.3, 1.1])
    # Stock Name
    cols[0].markdown(f"<b>{symbol}</b>", unsafe_allow_html=True)
    # Entry Price
    cols[1].markdown(f"₹{entry_price:.2f}")
    # Qty
    cols[2].markdown(f"{qty}")

    # SL %
    sl_pct = cols[3].number_input(
        f"SL %", min_value=0.5, max_value=50.0, value=default_sl_pct, format="%.2f", key=f"sl_pct_{unique_id}"
    )
    # SL Qty
    sl_qty = cols[4].number_input(
        f"SL Qty", min_value=1, max_value=qty, value=qty, key=f"sl_qty_{unique_id}"
    )

    # T1 %
    t1_pct = cols[5].number_input(
        f"T1 %", min_value=1.0, max_value=100.0, value=default_t1_pct, format="%.2f", key=f"t1_pct_{unique_id}"
    )
    # T1 Qty
    t1_qty = cols[6].number_input(
        f"T1 Qty", min_value=1, max_value=qty, value=half_qty, key=f"t1_qty_{unique_id}"
    )

    # T2 %
    t2_pct = cols[7].number_input(
        f"T2 %", min_value=1.0, max_value=100.0, value=default_t2_pct, format="%.2f", key=f"t2_pct_{unique_id}"
    )
    # T2 Qty
    t2_qty = cols[8].number_input(
        f"T2 Qty", min_value=1, max_value=qty, value=rem_qty, key=f"t2_qty_{unique_id}"
    )

    # AMO Checkbox
    amo = cols[9].checkbox("AMO", key=f"amo_{unique_id}")

    # Place Order Button
    submit = cols[10].button("Place Orders", key=f"place_btn_{unique_id}")

    # Show colored % values
    cols[3].markdown(f'<span style="color:red;"><b>{sl_pct:.2f}%</b></span>', unsafe_allow_html=True)
    cols[5].markdown(f'<span style="color:green;"><b>{t1_pct:.2f}%</b></span>', unsafe_allow_html=True)
    cols[7].markdown(f'<span style="color:green;"><b>{t2_pct:.2f}%</b></span>', unsafe_allow_html=True)

    # Calculate prices, snapped to tick
    sl_price = snap_to_tick(entry_price * (1 - sl_pct / 100))
    t1_price = snap_to_tick(entry_price * (1 + t1_pct / 100))
    t2_price = snap_to_tick(entry_price * (1 + t2_pct / 100))
    validity = "DAY"

    # Indicate duplicate orders for each type
    dup_sl = is_duplicate_order(symbol, exchange, "SELL", sl_price, sl_qty, "SL-LIMIT" if not amo else "SL-MARKET", orders)
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
        cols[10].markdown(" | ".join(dup_msg), unsafe_allow_html=True)

    # Button only enabled if all orders are not duplicate
    if (dup_sl or dup_t1 or dup_t2) and submit:
        st.warning("Some orders already in OPEN state. Avoiding duplicate orders.")
        submit = False

    return submit, sl_pct, sl_qty, sl_price, t1_pct, t1_qty, t1_price, t2_pct, t2_qty, t2_price, amo

def show():
    st.title("🚀 Auto Order (% Based SL & Target) for Holdings / Positions")
    st.markdown("""
        <style>
        .stNumberInput label {font-size:13px;}
        </style>
        """, unsafe_allow_html=True)
    st.markdown("#### All orders in one row. <span style='color:red'><b>SL %</b></span> <span style='color:green'><b>T1/T2 %</b></span>", unsafe_allow_html=True)
    st.write("")

    # Table Header
    hdr = st.columns([1.3, 1.0, 1.0, 1.1, 0.9, 1.1, 0.9, 1.1, 0.9, 1.3, 1.1])
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
    hdr[10].markdown("**Action**")

    # Get current open orders
    orders = []
    try:
        order_data = integrate_get("/orders")
        orders = order_data.get("orders", [])
    except Exception:
        pass

    # Load all positions and holdings
    hdata = integrate_get("/holdings")
    holdings = hdata.get("data", [])
    pdata = integrate_get("/positions")
    positions = pdata.get("positions") or pdata.get("data") or []

    # Build symbol list: combine all stocks from positions/holdings
    symbols_info = {}
    for p in positions:
        symbol = extract_first_valid(p, ["tradingsymbol", "symbol"])
        qty = extract_qty(p)
        exchange = extract_first_valid(p, ["exchange"])
        product_type = extract_first_valid(p, ["product_type", "productType", "Product"], "INTRADAY")
        entry_price = get_entry_price(symbol, holdings, positions)
        if qty > 0 and entry_price > 0:
            symbols_info[symbol] = {
                "symbol": symbol,
                "qty": qty,
                "exchange": exchange,
                "product_type": product_type,
                "entry_price": entry_price,
                "source": "Position"
            }
    for h in holdings:
        ts_info = h.get("tradingsymbol", [{}])[0] if h.get("tradingsymbol", None) else h
        symbol = ts_info.get("tradingsymbol", "")
        qty = extract_qty(h)
        exchange = ts_info.get("exchange", "")
        product_type = "CNC"
        entry_price = get_entry_price(symbol, holdings, positions)
        if qty > 0 and entry_price > 0 and symbol not in symbols_info:
            symbols_info[symbol] = {
                "symbol": symbol,
                "qty": qty,
                "exchange": exchange,
                "product_type": product_type,
                "entry_price": entry_price,
                "source": "Holding"
            }

    for symbol, info in symbols_info.items():
        unique_id = f"{info['source'][0]}_{symbol}_{info['exchange']}"
        submit, sl_pct, sl_qty, sl_price, t1_pct, t1_qty, t1_price, t2_pct, t2_qty, t2_price, amo = order_row(
            symbol, info["entry_price"], info["qty"], info["exchange"], info["product_type"], orders, unique_id
        )

        if submit:
            # SL-LIMIT not allowed for AMO, so switch to SL-MARKET for AMO
            sl_price_type = "SL-MARKET" if amo else "SL-LIMIT"
            sl_payload = {
                "exchange": info["exchange"],
                "tradingsymbol": symbol,
                "order_type": "SELL",
                "quantity": str(sl_qty),
                "price": 0.0 if sl_price_type == "SL-MARKET" else str(sl_price),
                "trigger_price": str(sl_price),
                "price_type": sl_price_type,
                "product_type": info["product_type"],
                "validity": "DAY",
            }
            t1_payload = {
                "exchange": info["exchange"],
                "tradingsymbol": symbol,
                "order_type": "SELL",
                "quantity": str(t1_qty),
                "price": str(t1_price),
                "price_type": "LIMIT",
                "product_type": info["product_type"],
                "validity": "DAY",
            }
            t2_payload = {
                "exchange": info["exchange"],
                "tradingsymbol": symbol,
                "order_type": "SELL",
                "quantity": str(t2_qty),
                "price": str(t2_price),
                "price_type": "LIMIT",
                "product_type": info["product_type"],
                "validity": "DAY",
            }
            if amo:
                sl_payload["amo"] = "Yes"
                t1_payload["amo"] = "Yes"
                t2_payload["amo"] = "Yes"
            # Place orders
            resp = {}
            if sl_qty > 0 and sl_price > 0:
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
            # Show result
            if resp.get('sl', {}).get("status") == "ERROR":
                st.error(f"{symbol}: SL order failed: {resp['sl'].get('message', resp['sl'])}")
            else:
                st.success(f"{symbol}: SL {sl_price}({sl_pct}%) Qty: {sl_qty} → {resp['sl'].get('message', resp['sl'])}")
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
