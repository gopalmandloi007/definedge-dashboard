import streamlit as st
from utils import integrate_get, integrate_post

def extract_first_valid(d, keys, default=""):
    for k in keys:
        v = d.get(k)
        if v not in (None, "", [], {}, "null"):
            return v
    return default

def extract_qty(pos):
    for k in ['netqty', 'net_quantity', 'net_qty', 'quantity', 'Qty']:
        v = pos.get(k)
        if v is not None and v != "":
            try:
                return int(float(v))
            except Exception:
                continue
    return 0

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
            float(o.get("price", 0)) == float(price) and
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

    # Calculate prices
    sl_price = round(entry_price * (1 - sl_pct / 100), 2)
    t1_price = round(entry_price * (1 + t1_pct / 100), 2)
    t2_price = round(entry_price * (1 + t2_pct / 100), 2)
    validity = "DAY"

    # Indicate duplicate orders for each type
    dup_sl = is_duplicate_order(symbol, exchange, "SELL", sl_price, sl_qty, "SL-LIMIT", orders)
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

    # Holdings
    hdata = integrate_get("/holdings")
    holdings = hdata.get("data", [])
    for h in holdings:
        qty = int(float(h.get("dp_qty", 0) or 0))
        tradingsymbols = h.get("tradingsymbol", [])
        if qty > 0 and tradingsymbols and isinstance(tradingsymbols, list):
            ts_info = tradingsymbols[0]
            symbol = ts_info['tradingsymbol']
            entry_price = float(extract_first_valid(ts_info, ["avg_buy_price", "average_price", "buy_avg_price"], 0))
            exchange = ts_info['exchange']
            product_type = "CNC"
            unique_id = f"H_{symbol}_{exchange}"

            submit, sl_pct, sl_qty, sl_price, t1_pct, t1_qty, t1_price, t2_pct, t2_qty, t2_price, amo = order_row(
                symbol, entry_price, qty, exchange, product_type, orders, unique_id
            )

            if submit:
                sl_payload = {
                    "exchange": exchange,
                    "tradingsymbol": symbol,
                    "order_type": "SELL",
                    "quantity": str(sl_qty),
                    "price": str(sl_price),
                    "price_type": "SL-LIMIT",
                    "product_type": product_type,
                    "validity": "DAY",
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
                }
                if amo:
                    sl_payload["amo"] = "Yes"
                    t1_payload["amo"] = "Yes"
                    t2_payload["amo"] = "Yes"

                resp_sl = integrate_post("/placeorder", sl_payload)
                resp_t1 = integrate_post("/placeorder", t1_payload)
                resp_t2 = integrate_post("/placeorder", t2_payload)

                st.success(f"{symbol}: SL {sl_price}({sl_pct}%) Qty: {sl_qty} → {resp_sl.get('message', resp_sl)}")
                st.success(f"{symbol}: T1 {t1_price}({t1_pct}%) Qty: {t1_qty} → {resp_t1.get('message', resp_t1)}")
                st.success(f"{symbol}: T2 {t2_price}({t2_pct}%) Qty: {t2_qty} → {resp_t2.get('message', resp_t2)}")
                st.rerun()

    # Positions
    pdata = integrate_get("/positions")
    positions = pdata.get("positions") or pdata.get("data") or []
    for pos in positions:
        net_qty = extract_qty(pos)
        if net_qty > 0:
            symbol = extract_first_valid(pos, ["tradingsymbol", "symbol"])
            exchange = extract_first_valid(pos, ["exchange"])
            entry_price = float(extract_first_valid(pos, ["day_buy_avg", "total_buy_avg"], 0))
            product_type = extract_first_valid(pos, ["product_type", "productType", "Product"], "INTRADAY")
            unique_id = f"P_{symbol}_{exchange}"

            submit, sl_pct, sl_qty, sl_price, t1_pct, t1_qty, t1_price, t2_pct, t2_qty, t2_price, amo = order_row(
                symbol, entry_price, net_qty, exchange, product_type, orders, unique_id
            )

            if submit:
                sl_payload = {
                    "exchange": exchange,
                    "tradingsymbol": symbol,
                    "order_type": "SELL",
                    "quantity": str(sl_qty),
                    "price": str(sl_price),
                    "price_type": "SL-LIMIT",
                    "product_type": product_type,
                    "validity": "DAY",
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
                }
                if amo:
                    sl_payload["amo"] = "Yes"
                    t1_payload["amo"] = "Yes"
                    t2_payload["amo"] = "Yes"

                resp_sl = integrate_post("/placeorder", sl_payload)
                resp_t1 = integrate_post("/placeorder", t1_payload)
                resp_t2 = integrate_post("/placeorder", t2_payload)

                st.success(f"{symbol}: SL {sl_price}({sl_pct}%) Qty: {sl_qty} → {resp_sl.get('message', resp_sl)}")
                st.success(f"{symbol}: T1 {t1_price}({t1_pct}%) Qty: {t1_qty} → {resp_t1.get('message', resp_t1)}")
                st.success(f"{symbol}: T2 {t2_price}({t2_pct}%) Qty: {t2_qty} → {resp_t2.get('message', resp_t2)}")
                st.rerun()

if __name__ == "__main__":
    show()
