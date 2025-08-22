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

def get_exit_qty(tradingsymbol, exchange, positions):
    """Sum up exited/sold quantity for this symbol from positions/trades."""
    for pos in positions:
        ts = extract_first_valid(pos, ["tradingsymbol", "symbol"], "")
        exch = extract_first_valid(pos, ["exchange"], "")
        net_qty = extract_qty(pos)
        if ts == tradingsymbol and exch == exchange:
            # If net_qty < 0, it's sold/short; if > 0, it's buy/long
            return abs(net_qty) if net_qty < 0 else 0
    return 0

def squareoff_form(item, qty, ts_info, is_position=False):
    # ... (same as your function) ...
    # unchanged, reuse your function as-is
    # ...

def show():
    st.title("⚡ Definedge Integrate Dashboard")
    st.subheader("💼 Square Off Positions & Holdings")
    st.markdown("---")
    # --- Holdings Table ---
    st.header("📦 Holdings")
    data = integrate_get("/holdings")
    holdings = data.get("data", [])

    # Fetch positions for adjustment
    pdata = integrate_get("/positions")
    positions = pdata.get("positions") or pdata.get("data") or []

    hold_cols = ["tradingsymbol", "exchange", "isin", "dp_qty", "t1_qty", "avg_buy_price", "haircut"]
    col_labels = ["Symbol", "Exch", "ISIN", "DP Qty", "T1 Qty", "Avg Price", "Haircut"]
    st.markdown("#### Holdings List")
    columns = st.columns([1.5, 1.2, 1.5, 1.1, 1.1, 1.2, 1.1, 1.2])
    for i, label in enumerate(col_labels):
        columns[i].markdown(f"**{label}**")
    columns[-1].markdown("**Square Off**")

    user_holdings = []
    for h in holdings:
        tradingsymbol = extract_first_valid(h, ["tradingsymbol"], "")
        exchange = extract_first_valid(h, ["exchange"], "")
        qty = int(float(h.get("dp_qty", 0) or 0))
        # Adjust for exited qty from positions
        exit_qty = get_exit_qty(tradingsymbol, exchange, positions)
        remaining_qty = qty - exit_qty
        # Only show if remaining qty > 0
        if remaining_qty > 0:
            ts_info = h if isinstance(h.get("tradingsymbol"), dict) else h
            user_holdings.append((h, remaining_qty, ts_info))
    if not user_holdings:
        st.info("No holdings to square off.")
    else:
        sq_id = st.session_state.get("sq_id", None)
        for idx, (holding, qty, ts_info) in enumerate(user_holdings):
            columns = st.columns([1.5, 1.2, 1.5, 1.1, 1.1, 1.2, 1.1, 1.2])
            for i, key in enumerate(hold_cols):
                val = ts_info.get(key) if key in ts_info else holding.get(key)
                columns[i].write(val)
            if columns[-1].button("Square Off", key=f"squareoff_btn_{ts_info['tradingsymbol']}"):
                st.session_state["sq_id"] = f"HOLD_{idx}"
                st.session_state["sqp_id"] = None
                st.rerun()
            if sq_id == f"HOLD_{idx}":
                squareoff_form(holding, qty, ts_info, is_position=False)

    # --- Positions Table ---
    st.header("📝 Positions")
    col_labels = ["Symbol", "Exch", "Product", "Qty", "Buy Avg", "Sell Avg", "Net Qty", "PnL"]
    st.markdown("#### Positions List")
    columns = st.columns([1.5, 1.2, 1.2, 1, 1.2, 1.2, 1, 1.3, 1.2])
    for i, label in enumerate(col_labels):
        columns[i].markdown(f"**{label}**")
    columns[-1].markdown("**Square Off**")

    user_positions = []
    for p in positions:
        net_qty = extract_qty(p)
        # Only show non-zero net_qty positions
        if net_qty != 0:
            user_positions.append(p)
    sqp_id = st.session_state.get("sqp_id", None)
    if not user_positions:
        st.info("No open positions to square off.")
    else:
        for idx, pos in enumerate(user_positions):
            columns = st.columns([1.5, 1.2, 1.2, 1, 1.2, 1.2, 1, 1.3, 1.2])
            net_qty = extract_qty(pos)
            # Show correct Buy Avg / Sell Avg based on side
            if net_qty > 0:
                buy_avg = extract_first_valid(pos, ["day_buy_avg", "total_buy_avg"], "-")
                sell_avg = "-"
            elif net_qty < 0:
                buy_avg = "-"
                sell_avg = extract_first_valid(pos, ["day_sell_avg", "total_sell_avg"], "-")
            else:
                buy_avg = "-"
                sell_avg = "-"
            col_vals = [
                extract_first_valid(pos, ["tradingsymbol", "symbol"], "-"),
                extract_first_valid(pos, ["exchange"], "-"),
                extract_first_valid(pos, ["product_type", "productType", "Product"], "-"),
                str(abs(net_qty)),
                buy_avg,
                sell_avg,
                str(net_qty),
                extract_first_valid(pos, ["pnl", "unrealized_pnl", "Unrealised P&L"], "-"),
            ]
            for i, val in enumerate(col_vals):
                columns[i].write(val)
            if columns[-1].button("Square Off", key=f"squareoff_btn_pos_{extract_first_valid(pos,['tradingsymbol','symbol'],'')}_{idx}"):
                st.session_state["sqp_id"] = f"POS_{idx}"
                st.session_state["sq_id"] = None
                st.rerun()
            if sqp_id == f"POS_{idx}":
                ts_info = {
                    "tradingsymbol": extract_first_valid(pos, ["tradingsymbol", "symbol"]),
                    "exchange": extract_first_valid(pos, ["exchange"]),
                    "isin": extract_first_valid(pos, ["isin"], ""),
                }
                qty = abs(extract_qty(pos))
                squareoff_form(pos, qty, ts_info, is_position=True)

if __name__ == "__main__":
    show()
