import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from utils import integrate_get, integrate_post

def get_definedge_ltp_and_yclose(exchange, token, session_key, max_days_lookback=10):
    # LTP
    ltp = None
    try:
        url = f"https://integrate.definedgesecurities.com/dart/v1/quotes/{exchange}/{token}"
        headers = {'Authorization': session_key}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            ltp = float(data.get('ltp')) if data.get('ltp') not in (None, "null", "") else None
    except Exception:
        pass

    # Previous Close (yesterday's close from historical data)
    yclose = None
    closes = []
    for offset in range(1, max_days_lookback+1):
        dt = datetime.now() - timedelta(days=offset-1)
        date_str = dt.strftime('%d%m%Y')
        from_time = f"{date_str}0000"
        to_time = f"{date_str}1530"
        url = f"https://data.definedgesecurities.com/sds/history/{exchange}/{token}/day/{from_time}/{to_time}"
        headers = {'Authorization': session_key}
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                lines = resp.text.strip().splitlines()
                for line in lines:
                    fields = line.split(',')
                    if len(fields) >= 5:
                        closes.append(float(fields[4]))
                if len(closes) >= 2:
                    break
        except Exception:
            pass
        if len(closes) >= 2:
            break
    closes = list(dict.fromkeys(closes))
    if len(closes) >= 2:
        yclose = closes[-2]
    else:
        yclose = None
    return ltp, yclose

def place_squareoff_order(exchange, tsym, qty, session_key):
    order_data = {
        "exchange": exchange,
        "order_type": "SELL",
        "price": 0,
        "price_type": "MARKET",
        "product_type": "CNC",
        "quantity": int(qty),
        "tradingsymbol": tsym
    }
    try:
        # Do not pass session_key as param; integrate_post should use context/global/session or add header internally
        resp = integrate_post("/orders", data=order_data)
        return resp
    except Exception as e:
        return f"Order error: {e}"

def show():
    st.header("=========== Holdings ===========")
    session_key = st.secrets["integrate_api_session_key"]
    data = integrate_get("/holdings")
    holdings = data.get("data", [])
    if not holdings:
        st.info("No holdings found.")
        return

    rows = []
    total_today_pnl = 0
    total_overall_pnl = 0
    total_invested = 0
    total_current = 0

    st.markdown("### NSE Holdings (with Square Off option)")
    for idx, h in enumerate(holdings):
        ts = h.get("tradingsymbol")
        if isinstance(ts, list) and ts and isinstance(ts[0], dict):
            tsym = ts[0].get("tradingsymbol", "N/A")
            exch = ts[0].get("exchange", "NSE")
            isin = ts[0].get("isin", "")
            token = ts[0].get("token", "")
        else:
            tsym = ts if isinstance(ts, str) else "N/A"
            exch = h.get("exchange", "NSE")
            isin = h.get("isin", "")
            token = h.get("token", "")
        qty = float(h.get("dp_qty", 0) or 0)
        avg_buy = float(h.get("avg_buy_price", 0) or 0)
        invested = qty * avg_buy

        # LIVE LTP and yclose
        ltp, prev_close = get_definedge_ltp_and_yclose(exch, token, session_key)
        current = qty * ltp if ltp is not None else 0

        today_pnl = (ltp - prev_close) * qty if (ltp is not None and prev_close not in (None, 0)) else 0
        overall_pnl = (ltp - avg_buy) * qty if (ltp is not None and avg_buy not in (None, 0)) else 0
        pct_chg = ((ltp - prev_close) / prev_close * 100) if (ltp is not None and prev_close not in (None, 0)) else 0
        pct_chg_avg = ((ltp - avg_buy) / avg_buy * 100) if (ltp is not None and avg_buy not in (None, 0)) else 0

        row = {
            "Symbol": tsym,
            "LTP": round(ltp, 2) if ltp is not None else "N/A",
            "Avg Buy": round(avg_buy, 2),
            "Qty": int(qty),
            "P.Close": round(prev_close, 2) if prev_close is not None else "N/A",
            "%Chg": round(pct_chg, 2),
            "Today P&L": round(today_pnl, 2),
            "Overall P&L": round(overall_pnl, 2),
            "%Chg Avg": round(pct_chg_avg, 2),
            "Invested": round(invested, 2),
            "Current": round(current, 2),
            "Exchange": exch,
            "ISIN": isin,
            "T1": h.get("t1_qty", 0),
            "Haircut": h.get("haircut", 0),
            "Coll Qty": h.get("collateral_qty", 0),
            "Sell Amt": h.get("sell_amt", 0),
            "Trade Qty": h.get("trade_qty", 0)
        }
        rows.append(row)

        # --- SINGLE-LINE, SMALL Square Off BUTTON ---
        cols = st.columns([6, 1])
        info_str = f"{tsym} | Qty: {int(qty)} | LTP: {row['LTP']} | Today P&L: {row['Today P&L']} | Overall P&L: {row['Overall P&L']}"
        with cols[0]:
            st.write(info_str)
        with cols[1]:
            if st.button("Square Off", key=f"squareoff_{idx}_{tsym}"):
                if qty > 0:
                    resp = place_squareoff_order(exch, tsym, qty, session_key)
                    st.success(f"Square off order placed for {tsym}: {resp}")
                else:
                    st.warning("No holding quantity to square off.")

        total_today_pnl += today_pnl
        total_overall_pnl += overall_pnl
        total_invested += invested
        total_current += current

    df = pd.DataFrame(rows)
    st.markdown("""
**Summary**
|            | Amount   | Total Invested value | Total current value |
|------------|----------|---------------------|--------------------|
| Today P&L  | {:.2f}   | {:.2f}              | {:.2f}             |
| Overall P&L| {:.2f}   |                     |                    |
""".format(total_today_pnl, total_invested, total_current, total_overall_pnl)
    )

    st.markdown(f"**Total NSE Holdings: {len(df)}**")
    st.dataframe(df, use_container_width=True)
