import streamlit as st
import pandas as pd
from integrate import ConnectToIntegrate, IntegrateOrders
import requests
from datetime import datetime, timedelta

def get_definedge_ltp_and_yclose(segment, token, session_key, max_days_lookback=10):
    headers = {'Authorization': session_key}
    ltp = None
    try:
        url = f"https://integrate.definedgesecurities.com/dart/v1/quotes/{segment}/{token}"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            ltp = float(data.get('ltp')) if data.get('ltp') not in (None, "null", "") else None
    except Exception:
        pass

    yclose = None
    closes = []
    for offset in range(1, max_days_lookback+1):
        dt = datetime.now() - timedelta(days=offset-1)
        date_str = dt.strftime('%d%m%Y')
        from_time = f"{date_str}0000"
        to_time = f"{date_str}1530"
        url = f"https://data.definedgesecurities.com/sds/history/{segment}/{token}/day/{from_time}/{to_time}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                lines = response.text.strip().splitlines()
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
    return ltp, yclose

def build_master_mapping_from_holdings(holdings_book):
    mapping = {}
    raw = holdings_book.get('data', [])
    if not isinstance(raw, list):
        return mapping
    for h in raw:
        tradingsymbols = h.get("tradingsymbol")
        if isinstance(tradingsymbols, list):
            for ts in tradingsymbols:
                exch = ts.get("exchange", "NSE")
                tsym = ts.get("tradingsymbol", "")
                token = ts.get("token", "")
                if exch and tsym and token:
                    mapping[(exch, tsym)] = {'segment': exch, 'token': token}
    return mapping

def holdings_tabular(holdings_book, master_mapping, session_key):
    raw = holdings_book.get('data', [])
    table = []
    total_today_pnl = 0
    total_overall_pnl = 0
    total_invested = 0
    total_current = 0
    total_realized_today = 0
    total_realized_overall = 0

    headers = [
        "Symbol", "LTP", "Avg Buy", "Qty", "P.Close", "%Chg", "Today P&L", "Overall P&L",
        "Realized P&L", "%Chg Avg", "Invested", "Current", "Exchange", "ISIN", "T1", "Haircut", "Coll Qty", "Sell Amt", "Trade Qty"
    ]

    for h in raw:
        dp_qty = float(h.get("dp_qty", 0) or 0)
        avg_buy_price = float(h.get("avg_buy_price", 0) or 0)
        t1_qty = h.get("t1_qty", "N/A")
        haircut = h.get("haircut", "N/A")
        collateral_qty = h.get("collateral_qty", "N/A")
        sell_amt = float(h.get("sell_amt", 0) or 0)
        trade_qty = float(h.get("trade_qty", 0) or 0)
        tradingsymbols = h.get("tradingsymbol")
        realized_pnl = 0.0

        if isinstance(tradingsymbols, list) and tradingsymbols:
            for ts in tradingsymbols:
                exch = ts.get("exchange", "NSE")
                if exch != "NSE":
                    continue
                tsym = ts.get("tradingsymbol", "N/A")
                isin = ts.get("isin", "N/A")
                key = (exch, tsym)
                segment_token = master_mapping.get(key)
                if not segment_token:
                    ltp, yest_close = None, None
                else:
                    ltp, yest_close = get_definedge_ltp_and_yclose(segment_token['segment'], segment_token['token'], session_key)
                exited = (sell_amt > 0 and trade_qty > 0)
                holding_qty = dp_qty if dp_qty > 0 else 0
                exited_qty = trade_qty if exited else 0

                if exited and exited_qty > 0:
                    sell_price = sell_amt / exited_qty if exited_qty else 0
                    realized_pnl = (sell_price - avg_buy_price) * exited_qty
                    total_realized_today += realized_pnl
                    total_realized_overall += realized_pnl
                else:
                    realized_pnl = 0

                if holding_qty > 0:
                    invested = avg_buy_price * holding_qty
                    current = (ltp or 0) * holding_qty if ltp is not None else 0
                    today_pnl = (ltp - yest_close) * holding_qty if ltp is not None and yest_close is not None else 0
                    overall_pnl = (ltp - avg_buy_price) * holding_qty if ltp is not None else 0
                    pct_change = ((ltp - yest_close) / yest_close * 100) if ltp is not None and yest_close not in (None, 0) else "N/A"
                    pct_change_avg = ((ltp - avg_buy_price) / avg_buy_price * 100) if ltp is not None and avg_buy_price not in (None, 0) else "N/A"
                else:
                    invested = 0
                    current = 0
                    today_pnl = 0
                    overall_pnl = 0
                    pct_change = "N/A"
                    pct_change_avg = "N/A"

                # Totals only from holding qty (unrealized)
                total_today_pnl += today_pnl
                total_overall_pnl += overall_pnl
                total_invested += invested
                total_current += current

                # For display: realized P&L as column
                table.append([
                    tsym,
                    f"{ltp:.2f}" if ltp is not None else "N/A",
                    f"{avg_buy_price:.2f}",
                    int(holding_qty),
                    f"{yest_close:.2f}" if yest_close is not None else "N/A",
                    f"{pct_change:.2f}" if isinstance(pct_change, float) else pct_change,
                    f"{today_pnl:.2f}" if isinstance(today_pnl, float) else today_pnl,
                    f"{overall_pnl:.2f}" if isinstance(overall_pnl, float) else overall_pnl,
                    f"{realized_pnl:.2f}" if realized_pnl else "",
                    f"{pct_change_avg:.2f}" if isinstance(pct_change_avg, float) else pct_change_avg,
                    f"{invested:.2f}",
                    f"{current:.2f}",
                    exch,
                    isin,
                    t1_qty,
                    haircut,
                    collateral_qty,
                    f"{sell_amt:.2f}",
                    int(trade_qty)
                ])

    # Add realized P&L from exited qty to totals
    total_today_pnl += total_realized_today
    total_overall_pnl += total_realized_overall

    df = pd.DataFrame(table, columns=headers)
    summary = {
        "Today P&L": round(total_today_pnl, 2),
        "Overall P&L": round(total_overall_pnl, 2),
        "Total Invested": round(total_invested, 2),
        "Total Current": round(total_current, 2)
    }
    return df, summary

def show():
    # --- Load secrets
    api_token = st.secrets["integrate_api_token"]
    api_secret = st.secrets["integrate_api_secret"]
    uid = st.secrets["integrate_uid"]
    actid = st.secrets["integrate_actid"]
    api_session_key = st.secrets["integrate_api_session_key"]
    ws_session_key = st.secrets["integrate_ws_session_key"]

    conn = ConnectToIntegrate()
    conn.login(api_token, api_secret)
    conn.set_session_keys(uid, actid, api_session_key, ws_session_key)
    io = IntegrateOrders(conn)

    st.header("Holdings")
    try:
        holdings_book = io.holdings()
        if not holdings_book.get("data"):
            st.info("No holdings found or API returned: " + str(holdings_book))
        else:
            master_mapping = build_master_mapping_from_holdings(holdings_book)
            df_hold, summary = holdings_tabular(holdings_book, master_mapping, api_session_key)
            st.write("**Summary**")
            st.write(summary)
            st.write(f"**Total NSE Holdings: {len(df_hold)}**")
            st.dataframe(df_hold)
    except Exception as e:
        st.error(f"Failed to get holdings: {e}")
