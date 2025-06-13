import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from utils import integrate_get
import plotly.express as px

def safe_float(val):
    try:
        return float(val)
    except Exception:
        return 0.0

def get_ltp(exchange, token, api_session_key):
    if not exchange or not token:
        return 0.0
    url = f"https://integrate.definedgesecurities.com/dart/v1/quotes/{exchange}/{token}"
    headers = {"Authorization": api_session_key}
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            return safe_float(resp.json().get("ltp", 0))
    except Exception:
        pass
    return 0.0

def get_prev_close(exchange, token, api_session_key):
    today = datetime.now()
    for i in range(1, 5):
        prev_day = today - timedelta(days=i)
        if prev_day.weekday() < 5:
            break
    else:
        prev_day = today - timedelta(days=1)
    from_str = prev_day.strftime("%d%m%Y0000")
    to_str = today.strftime("%d%m%Y1530")
    url = f"https://data.definedgesecurities.com/sds/history/{exchange}/{token}/day/{from_str}/{to_str}"
    headers = {"Authorization": api_session_key}
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            rows = resp.text.strip().split("\n")
            if len(rows) >= 2:
                prev_row = rows[-2]
                prev_close = safe_float(prev_row.split(",")[4])
                return prev_close
            elif len(rows) == 1:
                prev_close = safe_float(rows[0].split(",")[4])
                return prev_close
    except Exception:
        pass
    return 0.0

def highlight_pnl(val):
    try:
        val = float(val)
        if val > 0:
            return 'color: green'
        elif val < 0:
            return 'color: red'
    except:
        pass
    return 'color: black'

def get_gtt_stoploss_dict():
    # Fetch all GTT+OCO orders and build a dict: {symbol: stoploss_price}
    data = integrate_get("/gttorders")
    gttlist = data.get("pendingGTTOrderBook", [])
    stoploss_dict = dict()
    for order in gttlist:
        symbol = order.get('tradingsymbol')
        # Single-leg GTT stoploss
        if order.get('order_type') == 'SELL' and order.get('condition') == 'LTP_BELOW':
            price = safe_float(order.get('alert_price'))
            # If multiple, keep the lowest stoploss price
            if symbol in stoploss_dict:
                stoploss_dict[symbol] = min(stoploss_dict[symbol], price)
            else:
                stoploss_dict[symbol] = price
        # OCO stoploss
        if 'stoploss_price' in order and safe_float(order.get('stoploss_price')) > 0:
            price = safe_float(order.get('stoploss_price'))
            if symbol in stoploss_dict:
                stoploss_dict[symbol] = min(stoploss_dict[symbol], price)
            else:
                stoploss_dict[symbol] = price
    return stoploss_dict

def show():
    st.header("=========== Holdings Dashboard with Open Risk & Allocation ===========")
    api_session_key = st.secrets.get("integrate_api_session_key", "")

    try:
        # GTT+OCO Stoploss data
        stoploss_dict = get_gtt_stoploss_dict()

        data = integrate_get("/holdings")
        holdings = data.get("data", [])
        if not holdings:
            st.info("No holdings found.")
            return

        active_holdings = []
        for h in holdings:
            qty = 0.0
            ts = h.get("tradingsymbol")
            if isinstance(ts, list) and len(ts) > 0 and isinstance(ts[0], dict):
                qty = safe_float(ts[0].get("dp_qty", h.get("dp_qty", 0)))
            else:
                qty = safe_float(h.get("dp_qty", 0))
            if qty > 0:
                active_holdings.append(h)

        rows = []
        total_today_pnl = 0.0
        total_overall_pnl = 0.0
        total_invested = 0.0
        total_current = 0.0
        total_open_risk = 0.0

        for h in active_holdings:
            ts = h.get("tradingsymbol")
            exch = h.get("exchange", "NSE")
            token = None
            isin = ""
            if isinstance(ts, list) and len(ts) > 0 and isinstance(ts[0], dict):
                tsym = ts[0].get("tradingsymbol", "N/A")
                exch = ts[0].get("exchange", exch)
                token = ts[0].get("token")
                isin = ts[0].get("isin", "")
                qty = safe_float(ts[0].get("dp_qty", h.get("dp_qty", 0)))
            else:
                tsym = ts if isinstance(ts, str) else "N/A"
                token = h.get("token")
                isin = h.get("isin", "")
                qty = safe_float(h.get("dp_qty", 0))

            avg_buy = safe_float(h.get("avg_buy_price", 0))
            ltp = get_ltp(exch, token, api_session_key) if token else 0.0
            prev_close = get_prev_close(exch, token, api_session_key) if token else 0.0

            invested = avg_buy * qty
            current = ltp * qty

            today_pnl = (ltp - prev_close) * qty if prev_close else 0.0
            overall_pnl = (ltp - avg_buy) * qty if avg_buy else 0.0
            pct_chg = ((ltp - prev_close) / prev_close * 100) if prev_close else 0.0
            pct_chg_avg = ((ltp - avg_buy) / avg_buy * 100) if avg_buy else 0.0

            # OPEN RISK calculation
            stoploss_price = stoploss_dict.get(tsym)
            if stoploss_price is not None and ltp > 0:
                open_risk = max(0, (ltp - stoploss_price) * qty)
            else:
                open_risk = ""

            total_today_pnl += today_pnl
            total_overall_pnl += overall_pnl
            total_invested += invested
            total_current += current
            if isinstance(open_risk, (int, float)):
                total_open_risk += open_risk

            rows.append([
                tsym,
                round(ltp, 2),
                round(avg_buy, 2),
                int(qty),
                round(prev_close, 2),
                round(pct_chg, 2),
                round(today_pnl, 2),
                round(overall_pnl, 2),
                round(pct_chg_avg, 2),
                round(invested, 2),
                round(current, 2),
                exch,
                isin,
                round(stoploss_price, 2) if stoploss_price is not None else "",
                round(open_risk, 2) if isinstance(open_risk, (int, float)) else "",
            ])

        headers = [
            "Symbol", "LTP", "Avg Buy", "Qty", "P.Close", "%Chg", "Today P&L", "Overall P&L",
            "%Chg Avg", "Invested", "Current", "Exchange", "ISIN", "Stoploss", "Open Risk"
        ]

        df = pd.DataFrame(rows, columns=headers)
        df = df.sort_values("Invested", ascending=False)

        # Allocation Pie Chart
        st.subheader("Portfolio Allocation")
        fig = px.pie(df, names="Symbol", values="Invested", title="Allocation by Invested Amount")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(f"**Total NSE Holdings: {len(df)}**")
        st.dataframe(
            df.style.applymap(highlight_pnl, subset=["Today P&L", "Overall P&L", "%Chg", "%Chg Avg"]),
            use_container_width=True
        )

        st.markdown(f"### Total Open Risk: <span style='color:red'>{total_open_risk:,.2f}</span>", unsafe_allow_html=True)

        # Download button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Download Holdings as CSV",
            data=csv,
            file_name='holdings_with_open_risk.csv',
            mime='text/csv',
        )

        # Timestamp
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        st.error(f"Error loading holdings or GTT/OCO orders: {e}")

if __name__ == "__main__":
    show()
