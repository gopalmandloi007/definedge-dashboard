import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from utils import integrate_get
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import numpy as np

# Initialize session state variables
if 'deployed_capital' not in st.session_state:
    st.session_state.deployed_capital = 650000.0
if 'target_capital' not in st.session_state:
    st.session_state.target_capital = 650000.0
if 'stop_losses' not in st.session_state:
    st.session_state.stop_losses = {}
if 'trailing_stops' not in st.session_state:
    st.session_state.trailing_stops = {}

# ========== Enhanced Chart Utils ==========
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
    df["Date"] = pd.to_datetime(df["Dateandtime"], format="%d%m%Y%H%M", errors="coerce")
    df = df.dropna(subset=["Date"])
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

def compute_rsi(data, window=14):
    """Compute Relative Strength Index (RSI)"""
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    # Handle case where avg_loss is 0 to avoid division by zero
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    avg_loss = avg_loss.replace(0, 1e-10)  # Avoid division by zero
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_macd(data, slow=26, fast=12, signal=9):
    """Compute MACD indicator"""
    ema_slow = data['Close'].ewm(span=slow, adjust=False).mean()
    ema_fast = data['Close'].ewm(span=fast, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd, signal_line

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

def highlight_risk(val):
    try:
        val = float(val)
        if val > 0:
            return 'background-color: #FFEB3B; color: black'  # Yellow for risk
        elif val < 0:
            return 'background-color: #F44336; color: white'  # Red for below SL
    except:
        pass
    return ''

def generate_insights(row, portfolio_value):
    """Generate actionable insights based on position metrics"""
    insights = []
    
    # Position sizing analysis
    position_size = (row['Current'] / portfolio_value) * 100
    if position_size > 15:
        insights.append("⚠️ Position too large (>15% of portfolio)")
    elif position_size < 3:
        insights.append("⚖️ Position too small (<3% of portfolio)")
    
    # Profitability analysis
    if row['Overall P&L'] > 0:
        if row['%Chg Avg'] > 25:
            insights.append("💰 Consider taking partial profits (gains >25%)")
    else:
        if row['%Chg Avg'] < -15:
            insights.append("❗ Significant unrealized loss (>15%)")
    
    # Momentum analysis
    if row['%Chg'] > 5:
        insights.append("📈 Strong positive momentum today")
    elif row['%Chg'] < -5:
        insights.append("📉 Strong negative momentum today")
    
    return insights

# ====== Minervini Sell Signals Analysis ======
def minervini_sell_signals(df, lookback_days=15):
    """
    Analyze stock data for Minervini's "Sell into Strength" signals
    Returns: dictionary of signals and warnings
    """
    if len(df) < lookback_days:
        return {"error": "Insufficient data for analysis"}
    
    # Use the last lookback_days for analysis
    recent = df.tail(lookback_days).copy()
    
    # Calculate daily price change and spread
    recent['change'] = recent['Close'].pct_change() * 100
    recent['spread'] = recent['High'] - recent['Low']
    
    # Initialize signals dictionary
    signals = {
        'up_days': 0,
        'down_days': 0,
        'up_day_percent': 0,
        'largest_up_day': 0,
        'largest_spread': 0,
        'exhaustion_gap': False,
        'high_volume_reversal': False,
        'churning': False,
        'heavy_volume_down': False,
        'warnings': []
    }
    
    # Count up vs down days
    for i in range(1, len(recent)):
        if recent['Close'].iloc[i] > recent['Close'].iloc[i-1]:
            signals['up_days'] += 1
        elif recent['Close'].iloc[i] < recent['Close'].iloc[i-1]:
            signals['down_days'] += 1
    
    signals['up_day_percent'] = (signals['up_days'] / lookback_days) * 100
    
    # Identify largest up day and spread
    signals['largest_up_day'] = recent['change'].max()
    signals['largest_spread'] = recent['spread'].max()
    
    # Exhaustion gap detection
    recent['gap_up'] = recent['Open'] > recent['High'].shift(1)
    recent['gap_down'] = recent['Open'] < recent['Low'].shift(1)
    recent['gap_filled'] = False
    
    for i in range(1, len(recent)):
        if recent['gap_up'].iloc[i]:
            if recent['Low'].iloc[i] <= recent['High'].shift(1).iloc[i]:
                recent.at[recent.index[i], 'gap_filled'] = True
                signals['exhaustion_gap'] = True
    
    # Volume analysis
    avg_volume = recent['Volume'].mean()
    max_vol_idx = recent['Volume'].idxmax()
    
    # High-volume reversal
    for i in range(1, len(recent)):
        if recent['Volume'].iloc[i] > avg_volume * 1.5:
            # Bearish reversal: higher high but close near low
            range_ = recent['High'].iloc[i] - recent['Low'].iloc[i]
            if (recent['High'].iloc[i] > recent['High'].iloc[i-1] and
                (recent['Close'].iloc[i] - recent['Low'].iloc[i]) < range_ * 0.25):
                signals['high_volume_reversal'] = True
                break
    
    # Churning (high volume without progress)
    if recent['Volume'].iloc[-1] > avg_volume * 1.8:
        price_change = abs(recent['Close'].iloc[-1] - recent['Open'].iloc[-1])
        if price_change < recent['spread'].iloc[-1] * 0.15:
            signals['churning'] = True
    
    # Heavy volume down day
    if recent['Volume'].iloc[-1] > avg_volume * 1.5 and recent['change'].iloc[-1] < -3:
        signals['heavy_volume_down'] = True
    
    # Generate warnings based on Minervini rules
    if signals['up_day_percent'] >= 70:
        signals['warnings'].append(
            f"⚠️ {signals['up_day_percent']:.0f}% up days ({signals['up_days']}/{lookback_days}) - "
            "Consider selling into strength"
        )
    
    if signals['largest_up_day'] > 5:  # >5% up day
        signals['warnings'].append(
            f"⚠️ Largest up day: {signals['largest_up_day']:.2f}% - "
            "Potential climax run"
        )
    
    if signals['exhaustion_gap']:
        signals['warnings'].append("⚠️ Exhaustion gap detected - Potential reversal signal")
    
    if signals['high_volume_reversal']:
        signals['warnings'].append("⚠️ High-volume reversal - Institutional selling")
    
    if signals['churning']:
        signals['warnings'].append("⚠️ Churning detected (high volume, low progress) - Distribution likely")
    
    if signals['heavy_volume_down']:
        signals['warnings'].append("⚠️ Heavy volume down day - Consider exiting position")
    
    return signals

def show():
    st.set_page_config(layout="wide")  # Set full-screen layout
    
    st.header("📊 Portfolio Intelligence Dashboard")
    st.caption("Advanced portfolio management with capital allocation and Minervini exit signals")

    api_session_key = st.secrets.get("integrate_api_session_key", "")
    auto_refresh = st.checkbox("Auto-refresh every 30 seconds", value=False)

    # Capital Management Section
    st.sidebar.header("💰 Capital Management")
    deployed_capital = st.sidebar.number_input(
        "Total Deployed Capital (₹)", 
        min_value=0.0, 
        value=st.session_state.deployed_capital, 
        step=10000.0,
        key='deployed_capital_input'
    )
    st.session_state.deployed_capital = deployed_capital
    
    target_capital = st.sidebar.number_input(
        "Target Deployment (₹)", 
        min_value=0.0, 
        value=st.session_state.target_capital, 
        step=10000.0,
        key='target_capital_input'
    )
    st.session_state.target_capital = target_capital
    
    # Stop Loss Management
    st.sidebar.header("🛑 Stop Loss Management")
    st.sidebar.info("Default stop loss is 2% below entry price")
    
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
        total_risk_amount = 0.0

        symbol_segment_dict = {}
        symbol_data = {}  # Store data for batch Minervini analysis

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
            pct_chg = ((ltp - prev_close) / prev_close * 100) if (ltp is not None and prev_close and prev_close != 0) else 0.0
            pct_chg_avg = ((ltp - avg_buy) / avg_buy * 100) if (ltp is not None and avg_buy and avg_buy != 0) else 0.0
            realized_pnl = 0.0

            total_today_pnl += today_pnl
            total_overall_pnl += overall_pnl
            total_invested += invested
            total_current += current

            # Initialize stop loss if not set
            if tsym not in st.session_state.stop_losses:
                st.session_state.stop_losses[tsym] = avg_buy * 0.98  # 2% below entry
            
            # Calculate risk
            risk_amount = (ltp - st.session_state.stop_losses[tsym]) * qty if ltp else 0
            risk_percent = (risk_amount / invested * 100) if invested else 0
            total_risk_amount += risk_amount

            # Store for Minervini analysis
            symbol_data[tsym] = {
                'exchange': exch,
                'token': token,
                'avg_buy': avg_buy,
                'qty': qty
            }

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
                round(st.session_state.stop_losses[tsym], 2),
                round(risk_amount, 2),
                round(risk_percent, 2),
                exch,
                isin,
            ])

            # For chart selectbox
            symbol_segment_dict[tsym] = exch

        headers = [
            "Symbol", "LTP", "Avg Buy", "Qty", "P.Close", "%Chg", "Today P&L", "Overall P&L",
            "Realized P&L", "%Chg Avg", "Invested", "Current", "Stop Loss", "Risk Amt", "Risk %",
            "Exchange", "ISIN"
        ]

        df = pd.DataFrame(rows, columns=headers)
        df = df.sort_values("Invested", ascending=False)
        
        # Calculate portfolio percentage
        portfolio_value = df['Current'].sum()
        df['Portfolio %'] = (df['Current'] / portfolio_value * 100).round(2)

        # ADD ACTION COLUMN BASED ON METRICS
        df['Action'] = "HOLD"
        df.loc[df['%Chg Avg'] > 25, 'Action'] = "CONSIDER PARTIAL PROFIT"
        df.loc[df['%Chg Avg'] < -15, 'Action'] = "REVIEW STOP LOSS"
        df.loc[df['Portfolio %'] > 15, 'Action'] = "CONSIDER REDUCE"
        df.loc[(df['%Chg'] < -5) & (df['%Chg Avg'] < -10), 'Action'] = "MONITOR CLOSELY"

        # ADD INSIGHTS COLUMN
        df['Insights'] = df.apply(lambda row: generate_insights(row, portfolio_value), axis=1)

        # Calculate cash position and allocation metrics
        cash_in_hand = st.session_state.deployed_capital - total_invested
        allocation_percent = (portfolio_value / st.session_state.deployed_capital * 100)
        additional_needed = max(0, st.session_state.target_capital - st.session_state.deployed_capital)
        
        # Capital Allocation Summary
        st.subheader("💰 Capital Allocation")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Deployed Capital", f"₹{st.session_state.deployed_capital:,.0f}")
        col2.metric("Target Capital", f"₹{st.session_state.target_capital:,.0f}", 
                   f"₹{additional_needed:,.0f} needed" if additional_needed > 0 else "Target reached")
        col3.metric("Cash in Hand", f"₹{cash_in_hand:,.0f}", 
                   f"{cash_in_hand/st.session_state.deployed_capital*100:.1f}%" if st.session_state.deployed_capital else "0%")
        col4.metric("Allocation %", f"{allocation_percent:.1f}%", 
                   f"₹{portfolio_value:,.0f} invested")
        
        # Risk Summary
        st.subheader("🚨 Risk Exposure")
        col5, col6, col7 = st.columns(3)
        col5.metric("Total At Risk", f"₹{total_risk_amount:,.0f}")
        col6.metric("Risk % of Portfolio", f"{total_risk_amount/portfolio_value*100:.1f}%" if portfolio_value else "0%")
        col7.metric("Risk % of Deployed", f"{total_risk_amount/st.session_state.deployed_capital*100:.1f}%" if st.session_state.deployed_capital else "0%")

        # Search/Filter Box for Symbols
        search = st.text_input("🔍 Search Symbol (filter):")
        if search.strip():
            df = df[df['Symbol'].str.contains(search.strip(), case=False, na=False)]

        # Portfolio Summary Cards
        st.subheader("📊 Portfolio Summary")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Portfolio Value", f"₹{portfolio_value:,.0f}")
        col2.metric("Total P&L", f"₹{total_overall_pnl:,.0f}", 
                   f"{total_overall_pnl/total_invested*100:.1f}%" if total_invested else "0%")
        col3.metric("Today's P&L", f"₹{total_today_pnl:,.0f}")
        col4.metric("Holdings", len(df))

        # Portfolio Allocation and Risk Distribution
        col1, col2 = st.columns(2)
        with col1:
            fig = px.pie(df, names="Symbol", values="Current", 
                         title="Portfolio Allocation", hole=0.3)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Risk exposure visualization
            risk_df = df.copy()
            risk_df['Risk Score'] = np.where(
                risk_df['%Chg Avg'] < -10, 3, 
                np.where(risk_df['Portfolio %'] > 10, 2, 1)
            )
            fig = px.bar(risk_df, x='Symbol', y='Risk Amt', color='Risk Score',
                         title="Risk Exposure by Stock",
                         color_continuous_scale="RdYlGn_r")
            st.plotly_chart(fig, use_container_width=True)

        # Enhanced Holdings Table with Actionable Columns
        st.subheader("📝 Holdings Analysis")
        
        # Color formatting
        def color_action(val):
            if "PROFIT" in val: return 'background-color: #4CAF50; color: white'
            if "REDUCE" in val: return 'background-color: #FF9800'
            if "REVIEW" in val: return 'background-color: #F44336; color: white'
            if "MONITOR" in val: return 'background-color: #FFEB3B'
            return ''
        
        styled_df = df.style.applymap(highlight_pnl, 
            subset=["Today P&L", "Overall P&L", "%Chg", "%Chg Avg"]
        ).applymap(color_action, subset=["Action"]
        ).applymap(highlight_risk, subset=["Risk Amt", "Risk %"])
        
        st.dataframe(
            styled_df,
            use_container_width=True,
            height=800,
            column_order=["Symbol", "LTP", "Avg Buy", "Stop Loss", "Risk Amt", "Risk %", 
                          "%Chg", "%Chg Avg", "Portfolio %", "Action"]
        )

        # Batch Minervini Analysis for All Holdings
        st.subheader("🔔 Batch Minervini Analysis for All Holdings")
        
        if st.button("Run Minervini Analysis for All Stocks"):
            minervini_results = []
            progress_bar = st.progress(0)
            
            symbols = list(symbol_data.keys())
            for i, symbol in enumerate(symbols):
                data = symbol_data[symbol]
                segment = data['exchange']
                token = data['token']
                
                # Update progress
                progress_bar.progress((i + 1) / len(symbols))
                
                if token:
                    from_dt, to_dt = get_time_range(90)  # 90 days lookback
                    try:
                        chart_df = fetch_candles_definedge(segment, token, from_dt, to_dt, api_key=api_session_key)
                        signals = minervini_sell_signals(chart_df, 15)
                        
                        if signals.get('error'):
                            minervini_results.append({
                                'Symbol': symbol,
                                'Status': 'Error',
                                'Warnings': signals['error'],
                                'Signal Count': 0
                            })
                        else:
                            minervini_results.append({
                                'Symbol': symbol,
                                'Status': 'Success',
                                'Warnings': " | ".join(signals['warnings']),
                                'Signal Count': len(signals['warnings'])
                            })
                    except Exception as e:
                        minervini_results.append({
                            'Symbol': symbol,
                            'Status': 'Error',
                            'Warnings': str(e),
                            'Signal Count': 0
                        })
                else:
                    minervini_results.append({
                        'Symbol': symbol,
                        'Status': 'Error',
                        'Warnings': 'Token not found',
                        'Signal Count': 0
                    })
            
            # Display results
            results_df = pd.DataFrame(minervini_results)
            results_df = results_df.sort_values("Signal Count", ascending=False)
            
            st.subheader("Analysis Results")
            st.dataframe(results_df, use_container_width=True, height=500)
            
            # Highlight stocks with warnings
            if not results_df.empty:
                warning_stocks = results_df[results_df['Signal Count'] > 0]
                if not warning_stocks.empty:
                    st.warning("### Stocks with Sell Signals")
                    for _, row in warning_stocks.iterrows():
                        st.error(f"**{row['Symbol']}**: {row['Warnings']}")

        # ========== ENHANCED CHART SECTION ==========
        st.subheader("📈 Technical Analysis for Decision Support")
        holding_symbols = list(symbol_segment_dict.keys())
        
        if holding_symbols:
            col1, col2 = st.columns([1, 3])
            with col1:
                selected_symbol = st.selectbox("Select Holding", sorted(holding_symbols))
                segment = symbol_segment_dict[selected_symbol]
                token = get_token(selected_symbol, segment, master_df)
                
                st.subheader("Technical Settings")
                show_ema = st.checkbox("Moving Averages", value=True)
                show_rsi = st.checkbox("RSI Indicator", value=True)
                show_macd = st.checkbox("MACD", value=True)
                days_back = st.slider("Days to Show", 30, 365, 90)
                
                # Stop Loss Configuration
                st.subheader("Stop Loss Configuration")
                current_sl = st.session_state.stop_losses.get(selected_symbol, 0)
                new_sl = st.number_input("Stop Loss Price", 
                                        value=current_sl, 
                                        step=0.5,
                                        key=f"sl_{selected_symbol}")
                
                if st.button("Update Stop Loss"):
                    st.session_state.stop_losses[selected_symbol] = new_sl
                    st.success(f"Stop loss updated for {selected_symbol}!")
                
                # Trailing Stop Configuration
                st.subheader("Trailing Stop")
                trailing_active = st.checkbox("Enable Trailing Stop", 
                                            value=st.session_state.trailing_stops.get(selected_symbol, {}).get('active', False))
                trail_percent = st.number_input("Trail Percentage", 
                                              min_value=0.1, 
                                              max_value=20.0, 
                                              value=st.session_state.trailing_stops.get(selected_symbol, {}).get('percent', 3.0),
                                              step=0.5)
                
                if st.button("Update Trailing Stop"):
                    st.session_state.trailing_stops[selected_symbol] = {
                        'active': trailing_active,
                        'percent': trail_percent
                    }
                    st.success(f"Trailing stop updated for {selected_symbol}!")
                
                if token:
                    from_dt, to_dt = get_time_range(days_back)
                    try:
                        chart_df = fetch_candles_definedge(segment, token, from_dt, to_dt, api_key=api_session_key)
                        chart_df = chart_df.sort_values("Date")
                        
                        # Calculate technical indicators
                        if show_ema:
                            chart_df['EMA20'] = chart_df['Close'].ewm(span=20, adjust=False).mean()
                            chart_df['EMA50'] = chart_df['Close'].ewm(span=50, adjust=False).mean()
                        if show_rsi:
                            chart_df['RSI'] = compute_rsi(chart_df)
                        if show_macd:
                            macd, signal = compute_macd(chart_df)
                            chart_df['MACD'] = macd
                            chart_df['Signal'] = signal
                        
                        # Determine subplot configuration
                        rows = 1
                        row_heights = [1.0]
                        specs = [[{"secondary_y": True}]]
                        
                        if show_rsi and show_macd:
                            rows = 3
                            row_heights = [0.6, 0.2, 0.2]
                            specs = [[{"secondary_y": True}], [{}], [{}]]
                        elif show_rsi or show_macd:
                            rows = 2
                            row_heights = [0.7, 0.3]
                            specs = [[{"secondary_y": True}], [{}]]
                        
                        # Create figure with subplots
                        fig = make_subplots(
                            rows=rows, 
                            cols=1,
                            shared_xaxes=True,
                            vertical_spacing=0.05,
                            row_heights=row_heights,
                            specs=specs
                        )
                        
                        # Price Chart (Candles + EMAs)
                        fig.add_trace(
                            go.Candlestick(
                                x=chart_df["Date"],
                                open=chart_df["Open"],
                                high=chart_df["High"],
                                low=chart_df["Low"],
                                close=chart_df["Close"],
                                name="Price"
                            ),
                            row=1, col=1
                        )
                        
                        # Add stop loss line
                        fig.add_hline(
                            y=new_sl, 
                            line_dash="dash", 
                            line_color="red",
                            name="Stop Loss",
                            row=1, col=1
                        )
                        
                        if show_ema:
                            fig.add_trace(
                                go.Scatter(
                                    x=chart_df["Date"],
                                    y=chart_df["EMA20"],
                                    mode="lines",
                                    name="20 EMA",
                                    line=dict(color="blue", width=1.5)
                                ),
                                row=1, col=1
                            )
                            fig.add_trace(
                                go.Scatter(
                                    x=chart_df["Date"],
                                    y=chart_df["EMA50"],
                                    mode="lines",
                                    name="50 EMA",
                                    line=dict(color="orange", width=1.5)
                                ),
                                row=1, col=1
                            )
                        
                        # Add RSI to second row
                        if show_rsi:
                            rsi_row = 2 if not show_macd else 2
                            fig.add_trace(
                                go.Scatter(
                                    x=chart_df["Date"],
                                    y=chart_df["RSI"],
                                    mode="lines",
                                    name="RSI",
                                    line=dict(color="purple", width=1.5)
                                ),
                                row=rsi_row, col=1
                            )
                            fig.add_hline(
                                y=30, line_dash="dash", line_color="green",
                                row=rsi_row, col=1
                            )
                            fig.add_hline(
                                y=70, line_dash="dash", line_color="red",
                                row=rsi_row, col=1
                            )
                        
                        # Add MACD if requested
                        if show_macd:
                            macd_row = 2 if not show_rsi else 3
                            fig.add_trace(
                                go.Bar(
                                    x=chart_df["Date"],
                                    y=chart_df["MACD"],
                                    name="MACD",
                                    marker_color=np.where(chart_df['MACD'] > 0, 'green', 'red')
                                ),
                                row=macd_row, col=1
                            )
                            fig.add_trace(
                                go.Scatter(
                                    x=chart_df["Date"],
                                    y=chart_df["Signal"],
                                    mode="lines",
                                    name="Signal",
                                    line=dict(color="blue", width=1.5)
                                ),
                                row=macd_row, col=1
                            )
                        
                        # Update layout
                        fig.update_layout(
                            height=600,
                            title=f"{selected_symbol} Technical Analysis",
                            showlegend=True,
                            xaxis_rangeslider_visible=False
                        )
                        
                        # Display the chart
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Generate technical insights
                        last_row = chart_df.iloc[-1]
                        insights = []
                        
                        if show_ema:
                            if 'EMA20' in chart_df.columns and 'EMA50' in chart_df.columns:
                                if last_row['Close'] > last_row['EMA20'] > last_row['EMA50']:
                                    insights.append("✅ Bullish trend (Price > 20EMA > 50EMA)")
                                elif last_row['Close'] < last_row['EMA20'] < last_row['EMA50']:
                                    insights.append("❌ Bearish trend (Price < 20EMA < 50EMA)")
                        
                        if show_rsi and 'RSI' in chart_df.columns:
                            if last_row['RSI'] > 70:
                                insights.append("⚠️ Overbought (RSI > 70)")
                            elif last_row['RSI'] < 30:
                                insights.append("⚠️ Oversold (RSI < 30)")
                        
                        if show_macd and 'MACD' in chart_df.columns and 'Signal' in chart_df.columns:
                            if last_row['MACD'] > last_row['Signal']:
                                insights.append("↑ Bullish MACD crossover")
                            else:
                                insights.append("↓ Bearish MACD crossover")
                        
                        if insights:
                            st.subheader("Technical Insights")
                            for insight in insights:
                                st.info(insight)
                        
                        # ====== MINERVINI SELL SIGNALS ANALYSIS ======
                        st.subheader("🔔 Minervini Sell Signals Analysis")
                        
                        # Use the same lookback period as the chart
                        minervini_lookback = st.slider("Analysis Lookback (days)", 7, 30, 15, key="minervini_lookback")
                        
                        try:
                            signals = minervini_sell_signals(chart_df, minervini_lookback)
                            
                            if signals.get('error'):
                                st.warning(signals['error'])
                            else:
                                # Display key metrics
                                col1, col2, col3 = st.columns(3)
                                col1.metric("Up Days", f"{signals['up_days']}/{minervini_lookback}")
                                col2.metric("Up Day %", f"{signals['up_day_percent']:.1f}%")
                                col3.metric("Largest Up Day", f"{signals['largest_up_day']:.2f}%")
                                
                                col4, col5, col6 = st.columns(3)
                                col4.metric("Largest Spread", f"₹{signals['largest_spread']:.2f}")
                                col5.metric("Exhaustion Gap", "Yes" if signals['exhaustion_gap'] else "No")
                                col6.metric("Volume Reversal", "Yes" if signals['high_volume_reversal'] else "No")
                                
                                # Display warnings
                                if signals['warnings']:
                                    st.error("## Sell Signals Detected")
                                    for warning in signals['warnings']:
                                        st.error(warning)
                                    
                                    st.markdown("""
                                    ### Minervini's Sell Recommendations:
                                    - **Sell into strength** when these signals appear
                                    - Consider **partial profits** on large gains
                                    - **Exit completely** if multiple signals confirm
                                    """)
                                else:
                                    st.success("No strong sell signals detected")
                                    st.info("""
                                    ### Minervini's Strength Indicators:
                                    - Stock is showing healthy price action
                                    - Continue monitoring for sell signals
                                    - Consider holding until signals appear
                                    """)
                                    
                                # Show recent price action table
                                with st.expander("View Recent Price Action"):
                                    recent = chart_df.tail(minervini_lookback).copy()
                                    recent['Change'] = recent['Close'].pct_change() * 100
                                    recent['Spread'] = recent['High'] - recent['Low']
                                    st.dataframe(recent[['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Change', 'Spread']])
                                    
                        except Exception as e:
                            st.error(f"Error in Minervini analysis: {e}")
                        
                    except Exception as e:
                        st.error(f"Error fetching chart data: {e}")
                else:
                    st.warning("Token not found for selected symbol")
        
        # Position Management Recommendations
        st.subheader("📋 Position Management Guide")
        st.write("""
        - **HOLD**: Fundamentals intact, technicals neutral/positive  
        - **CONSIDER PARTIAL PROFIT**: Significant gains (>25%), consider taking some profits  
        - **REVIEW STOP LOSS**: Significant unrealized loss (>15%), review risk management  
        - **CONSIDER REDUCE**: Position >15% of portfolio, high concentration risk  
        - **MONITOR CLOSELY**: Negative momentum and negative performance  
        """)

    except Exception as e:
        st.error(f"Error loading holdings: {e}")

if __name__ == "__main__":
    show()
