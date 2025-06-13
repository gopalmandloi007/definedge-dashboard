import streamlit as st
import pandas as pd
import plotly.graph_objs as go

def plot_candlestick(df, title="Candlestick Chart"):
    fig = go.Figure(data=[go.Candlestick(
        x=df['Date'],
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Candlestick'
    )])
    fig.update_layout(
        xaxis_rangeslider_visible=False,
        title=title,
        height=400,
        margin=dict(l=10, r=10, t=30, b=10)
    )
    return fig

def show():
    st.header("Simple Candlestick Chart Demo")

    # Sample data (replace with your own DataFrame)
    data = {
        'Date': pd.date_range(end=pd.Timestamp.today(), periods=30),
        'Open': pd.Series(range(30)) + 100,
        'High': pd.Series(range(30)) + 105,
        'Low': pd.Series(range(30)) + 95,
        'Close': pd.Series(range(30)) + 102,
    }
    df = pd.DataFrame(data)

    st.dataframe(df.tail(10))
    st.plotly_chart(plot_candlestick(df), use_container_width=True)
