import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from utils import integrate_get
import plotly.express as px
import plotly.graph_objs as go
import io
import numpy as np

# ========== Enhanced Chart Utils ==========
def compute_rsi(data, window=14):
    """Compute Relative Strength Index (RSI)"""
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    
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

# ========== DECISION SUPPORT METRICS ==========
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

# ========== UPDATED HOLDINGS DASHBOARD ==========
def show():
    st.header("📊 Holdings Intelligence Dashboard")
    st.caption("Actionable insights for portfolio decisions - Hold, Add, Reduce, or Exit")

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
            # [Existing code to extract holding details...]
            # ... (keep your existing holding processing logic)

        # ADD PORTFOLIO % CALCULATION
        headers = [
            "Symbol", "LTP", "Avg Buy", "Qty", "P.Close", "%Chg", "Today P&L", "Overall P&L",
            "Realized P&L", "%Chg Avg", "Invested", "Current", "Portfolio %", "Exchange", "ISIN"
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

        # Search/Filter Box for Symbols
        search = st.text_input("🔍 Search Symbol (filter):")
        if search.strip():
            df = df[df['Symbol'].str.contains(search.strip(), case=False, na=False)]

        # Portfolio Summary Cards
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Value", f"₹{portfolio_value:,.0f}")
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
            fig = px.bar(risk_df, x='Symbol', y='Current', color='Risk Score',
                         title="Risk Exposure (Size & Performance)",
                         color_continuous_scale="RdYlGn_r")
            st.plotly_chart(fig, use_container_width=True)

        # Enhanced Holdings Table with Actionable Columns
        st.subheader("Holdings Analysis")
        
        # Color formatting for action column
        def color_action(val):
            if "PROFIT" in val: return 'background-color: #4CAF50; color: white'
            if "REDUCE" in val: return 'background-color: #FF9800'
            if "REVIEW" in val: return 'background-color: #F44336; color: white'
            if "MONITOR" in val: return 'background-color: #FFEB3B'
            return ''
        
        styled_df = df.style.applymap(highlight_pnl, 
            subset=["Today P&L", "Overall P&L", "%Chg", "%Chg Avg"]
        ).applymap(color_action, subset=["Action"])
        
        st.dataframe(
            styled_df,
            use_container_width=True,
            column_order=["Symbol", "LTP", "Avg Buy", "%Chg", "%Chg Avg", 
                          "Today P&L", "Overall P&L", "Portfolio %", "Action"]
        )

        # ========== ENHANCED CHART SECTION ==========
        st.subheader("📈 Technical Analysis for Decision Support")
        holding_symbols = list(symbol_segment_dict.keys())
        
        if holding_symbols:
            col1, col2 = st.columns([1, 2])
            with col1:
                selected_symbol = st.selectbox("Select Holding", sorted(holding_symbols))
                segment = symbol_segment_dict[selected_symbol]
                token = get_token(selected_symbol, segment, master_df)
                
                st.subheader("Technical Settings")
                show_ema = st.checkbox("Moving Averages", value=True)
                show_rsi = st.checkbox("RSI Indicator", value=True)
                show_macd = st.checkbox("MACD", value=True)
                days_back = st.slider("Days to Show", 30, 365, 90)
                
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
                        
                        # Create main price chart
                        fig = go.Figure()
                        fig.add_trace(go.Candlestick(
                            x=chart_df["Date"],
                            open=chart_df["Open"],
                            high=chart_df["High"],
                            low=chart_df["Low"],
                            close=chart_df["Close"],
                            name="Price"
                        ))
                        
                        if show_ema:
                            fig.add_trace(go.Scatter(
                                x=chart_df["Date"],
                                y=chart_df["EMA20"],
                                mode="lines",
                                name="20 EMA",
                                line=dict(color="blue", width=1.5)
                            ))
                            fig.add_trace(go.Scatter(
                                x=chart_df["Date"],
                                y=chart_df["EMA50"],
                                mode="lines",
                                name="50 EMA",
                                line=dict(color="orange", width=1.5)
                            ))
                        
                        fig.update_layout(
                            height=400,
                            title=f"{selected_symbol} Price Analysis",
                            xaxis_rangeslider_visible=False,
                            showlegend=True
                        )
                        
                        # Create subplots if needed
                        subplot_titles = ['Price']
                        if show_rsi or show_macd:
                            fig = make_subplots(
                                rows=2 if show_rsi and show_macd else 1, 
                                cols=1,
                                shared_xaxes=True,
                                vertical_spacing=0.05,
                                row_heights=[0.7, 0.3] if show_rsi and show_macd else [0.7, 0.3]
                            )
                            
                            # Add price chart to first row
                            fig.add_trace(go.Candlestick(
                                x=chart_df["Date"],
                                open=chart_df["Open"],
                                high=chart_df["High"],
                                low=chart_df["Low"],
                                close=chart_df["Close"],
                                name="Price"
                            ), row=1, col=1)
                            
                            if show_ema:
                                fig.add_trace(go.Scatter(
                                    x=chart_df["Date"],
                                    y=chart_df["EMA20"],
                                    mode="lines",
                                    name="20 EMA"
                                ), row=1, col=1)
                                fig.add_trace(go.Scatter(
                                    x=chart_df["Date"],
                                    y=chart_df["EMA50"],
                                    mode="lines",
                                    name="50 EMA"
                                ), row=1, col=1)
                            
                            # Add RSI to second row
                            if show_rsi:
                                fig.add_trace(go.Scatter(
                                    x=chart_df["Date"],
                                    y=chart_df["RSI"],
                                    mode="lines",
                                    name="RSI",
                                    line=dict(color="purple", width=1.5)
                                ), row=2, col=1)
                                fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
                                fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
                            
                            # Add MACD if requested
                            if show_macd:
                                row_pos = 3 if show_rsi else 2
                                fig.add_trace(go.Bar(
                                    x=chart_df["Date"],
                                    y=chart_df["MACD"],
                                    name="MACD",
                                    marker_color=np.where(chart_df['MACD'] > 0, 'green', 'red')
                                ), row=row_pos, col=1)
                                fig.add_trace(go.Scatter(
                                    x=chart_df["Date"],
                                    y=chart_df["Signal"],
                                    mode="lines",
                                    name="Signal",
                                    line=dict(color="blue", width=1.5)
                                ), row=row_pos, col=1)
                            
                            fig.update_layout(
                                height=600,
                                title=f"{selected_symbol} Technical Analysis",
                                showlegend=True
                            )
                        
                        # Display the chart
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Generate technical insights
                        last_row = chart_df.iloc[-1]
                        insights = []
                        
                        if show_ema:
                            if last_row['Close'] > last_row['EMA20'] > last_row['EMA50']:
                                insights.append("✅ Bullish trend (Price > 20EMA > 50EMA)")
                            elif last_row['Close'] < last_row['EMA20'] < last_row['EMA50']:
                                insights.append("❌ Bearish trend (Price < 20EMA < 50EMA)")
                        
                        if show_rsi:
                            if last_row['RSI'] > 70:
                                insights.append("⚠️ Overbought (RSI > 70)")
                            elif last_row['RSI'] < 30:
                                insights.append("⚠️ Oversold (RSI < 30)")
                        
                        if show_macd:
                            if last_row['MACD'] > last_row['Signal']:
                                insights.append("↑ Bullish MACD crossover")
                            else:
                                insights.append("↓ Bearish MACD crossover")
                        
                        if insights:
                            st.subheader("Technical Insights")
                            for insight in insights:
                                st.info(insight)
                        
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
