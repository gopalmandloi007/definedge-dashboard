import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from utils import integrate_get
import plotly.express as px
import plotly.graph_objs as go
import io

# ========== Chart Utils (from your code) ==========

@st.cache_data
def load_master():
    df = pd.read_csv("master.csv", sep="\t", header=None)
    df.columns = [
        "segment", "token", "symbol", "instrument", "series", "isin1",
        "facevalue", "lot", "something", "zero1", "two1", "one1", "isin", "one2"
    ]
    return df[["segment", "token", "symbol", "instrument"]]

def get_token(symbol, segment, master_df):
    symbol = symbol.strip().upper()
    segment = segment.strip().upper()
    row = master_df[(master_df['symbol'] == symbol) & (master_df['segment'] == segment)]
    if not row.empty:
        return row.iloc[0]['token']
    row2 = master_df[(master_df['instrument'] == symbol) & (master_df['segment'] == segment)]
    if not row2.empty:
        return row2.iloc[0]['token']
    return None

def fetch_candles_definedge(segment, token, from_dt, to_dt, api_key):
    url = f"https://data.definedgesecurities.com/sds/history/{segment}/{token}/day/{from_dt}/{to_dt}"
    headers = {"Authorization": api_key}
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        raise Exception(f"API error: {resp.status_code} {resp.text}")
    cols = ["Dateandtime", "Open", "High", "Low", "Close", "Volume", "OI"]
    df = pd.read_csv(io.StringIO(resp.text), header=None, names=cols)
    df = df[df["Dateandtime"].notnull()]
    df = df[df["Dateandtime"].astype(str).str.strip() != ""]
    # Parse date, only keep rows with valid dates
    df["Date"] = pd.to_datetime(df["Dateandtime"], format="%d%m%Y%H%M", errors="coerce")
    df = df.dropna(subset=["Date"])
    # Only keep dates up to today (no future dates!)
    df = df[df["Date"] <= pd.Timestamp.now()]
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def get_time_range(days, endtime="1530"):
    now = datetime.now()
    to = now.replace(hour=15, minute=30, second=0, microsecond=0)
    if to > now:
        to = now
    frm = to - timedelta(days=days)
    return frm.strftime("%d%m%Y%H%M"), to.strftime("%d%m%Y%H%M")

# ========== Holdings Dashboard Pro (with chart integration) ==========

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
        else:
            return None
    except Exception:
        return None

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

def show():
    st.header("=========== Holdings Dashboard Pro ===========")

    api_session_key = st.secrets.get("integrate_api_session_key", "")
    auto_refresh = st.checkbox("Auto-refresh every 30 seconds", value=False)

    # Load master for chart lookup
    master_df = load_master()

    try:
        data = integrate_get("/holdings")
        holdings = data.get("data", [])
        if not holdings:
            st.info("No holdings found.")
            return

        # Filter only ACTIVE holdings (qty > 0)
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

        symbol_segment_dict = {}

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
            ltp = get_ltp(exch, token, api_session_key) if token else None
            prev_close = get_prev_close(exch, token, api_session_key) if token else None

            invested = avg_buy * qty if avg_buy is not None else 0.0
            current = ltp * qty if ltp is not None else 0.0

            today_pnl = (ltp - prev_close) * qty if (ltp is not None and prev_close) else 0.0
            overall_pnl = (ltp - avg_buy) * qty if (ltp is not None and avg_buy) else 0.0
            pct_chg = ((ltp - prev_close) / prev_close * 100) if (ltp is not None and prev_close) else 0.0
            pct_chg_avg = ((ltp - avg_buy) / avg_buy * 100) if (ltp is not None and avg_buy) else 0.0
            realized_pnl = 0.0

            total_today_pnl += today_pnl
            total_overall_pnl += overall_pnl
            total_invested += invested
            total_current += current

            rows.append([
                tsym,
                round(ltp, 2) if ltp is not None else "N/A",
                round(avg_buy, 2) if avg_buy is not None else "N/A",
                int(qty),
                round(prev_close, 2) if prev_close is not None else "N/A",
                round(pct_chg, 2) if ltp is not None else "N/A",
                round(today_pnl, 2) if ltp is not None else "N/A",
                round(overall_pnl, 2) if ltp is not None else "N/A",
                round(realized_pnl, 2) if realized_pnl else "",
                round(pct_chg_avg, 2) if ltp is not None else "N/A",
                round(invested, 2) if invested else "N/A",
                round(current, 2) if current else "N/A",
                exch,
                isin,
            ])

            # For chart selectbox
            symbol_segment_dict[tsym] = exch

        headers = [
            "Symbol", "LTP", "Avg Buy", "Qty", "P.Close", "%Chg", "Today P&L", "Overall P&L",
            "Realized P&L", "%Chg Avg", "Invested", "Current", "Exchange", "ISIN"
        ]

        df = pd.DataFrame(rows, columns=headers)
        df = df.sort_values("Invested", ascending=False)

        # Search/Filter Box for Symbols
        search = st.text_input("🔍 Search Symbol (filter):")
        if search.strip():
            df = df[df['Symbol'].str.contains(search.strip(), case=False, na=False)]

        # Pie Chart of Allocation
        with st.expander("Show Portfolio Allocation Pie-Chart"):
            fig = px.pie(df, names="Symbol", values="Invested", title="Allocation by Invested Amount")
            st.plotly_chart(fig, use_container_width=True)

        # Portfolio Return Summary
        if total_invested > 0:
            total_return = (total_current / total_invested - 1) * 100
            st.markdown(f"**Overall Portfolio Return: {total_return:.2f}%**")

        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        st.markdown(f"**Total NSE Holdings: {len(df)}**")
        st.dataframe(
            df.style.applymap(
                highlight_pnl,
                subset=["Today P&L", "Overall P&L", "%Chg", "%Chg Avg"]
            ),
            use_container_width=True
        )

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Download Holdings as CSV",
            data=csv,
            file_name='holdings.csv',
            mime='text/csv',
        )

        with st.expander("Show Detailed Holdings Table"):
            st.dataframe(df, use_container_width=True)

        # ============ HOLDINGS CHART SECTION ============
        st.subheader("📈 Chart: See Candlestick for your Holdings")
        holding_symbols = list(symbol_segment_dict.keys())
        if holding_symbols:
            selected_symbol = st.selectbox("Select Holding Symbol for Chart", sorted(holding_symbols))
            segment = symbol_segment_dict[selected_symbol]
            token = get_token(selected_symbol, segment, master_df)
            if token:
                show_ema20 = st.checkbox("Show 20 EMA", value=True, key="ema20_chart")
                show_ema50 = st.checkbox("Show 50 EMA", value=True, key="ema50_chart")
                from_dt, to_dt = get_time_range(120)
                try:
                    chart_df = fetch_candles_definedge(segment, token, from_dt, to_dt, api_key=api_session_key)
                    chart_df = chart_df.sort_values("Date")
                    chart_df = chart_df.tail(60).copy()
                    if show_ema20:
                        chart_df['EMA20'] = chart_df['Close'].ewm(span=20, adjust=False).mean()
                    if show_ema50:
                        chart_df['EMA50'] = chart_df['Close'].ewm(span=50, adjust=False).mean()
                    fig = go.Figure()
                    fig.add_trace(go.Candlestick(
                        x=chart_df["Date"].dt.strftime("%Y-%m-%d"),
                        open=chart_df["Open"],
                        high=chart_df["High"],
                        low=chart_df["Low"],
                        close=chart_df["Close"],
                        name="Candles"
                    ))
                    if show_ema20:
                        fig.add_trace(go.Scatter(
                            x=chart_df["Date"].dt.strftime("%Y-%m-%d"),
                            y=chart_df["EMA20"],
                            mode="lines",
                            name="20 EMA",
                            line=dict(color="blue", width=1.5)
                        ))
                    if show_ema50:
                        fig.add_trace(go.Scatter(
                            x=chart_df["Date"].dt.strftime("%Y-%m-%d"),
                            y=chart_df["EMA50"],
                            mode="lines",
                            name="50 EMA",
                            line=dict(color="orange", width=1.5)
                        ))
                    fig.update_layout(
                        height=400,
                        margin=dict(l=10, r=10, t=30, b=10),
                        xaxis_rangeslider_visible=False,
                        title=f"{selected_symbol} Daily Candlestick Chart",
                        xaxis=dict(type="category")
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    st.dataframe(chart_df[["Date", "Open", "High", "Low", "Close"]].tail(15))
                except Exception as e:
                    st.error(f"Error fetching chart data: {e}")
            else:
                st.warning("This symbol/token not found in master file for charting.")
        else:
            st.info("No active holding symbols to chart.")

    except Exception as e:
        st.error(f"Error loading holdings: {e}")

if __name__ == "__main__":
    show()
