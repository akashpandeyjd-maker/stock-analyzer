import streamlit as st
import yfinance as yf
import pandas as pd
import feedparser
import urllib.parse
from datetime import datetime, timedelta

st.set_page_config(page_title="Pro Stock Analyzer", layout="wide")

st.title("📈 Pro Stock Analyzer")

# -------------------------
# Sample NSE stocks
# -------------------------
stocks = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS",
    "ICICIBANK.NS", "SBIN.NS", "LT.NS", "ITC.NS",
    "AXISBANK.NS", "BHARTIARTL.NS"
]


# -------------------------
# Get performance
# -------------------------
def get_performance(period):
    data = []

    for ticker in stocks:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)

        if len(hist) >= 2:
            start = hist["Close"].iloc[0]
            end = hist["Close"].iloc[-1]
            change = ((end - start) / start) * 100

            data.append({
                "Ticker": ticker,
                "Price": round(end, 2),
                "Change %": round(change, 2)
            })

    df = pd.DataFrame(data)
    return df.sort_values("Change %", ascending=False)


# -------------------------
# News
# -------------------------
def get_news(stock):
    query = urllib.parse.quote(stock + " stock India")
    url = f"https://news.google.com/rss/search?q={query}"

    feed = feedparser.parse(url)
    return [entry.title for entry in feed.entries[:3]]


# -------------------------
# Fundamentals
# -------------------------
def get_fundamentals(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info

    return {
        "Market Cap": info.get("marketCap", "N/A"),
        "PE Ratio": info.get("trailingPE", "N/A"),
        "EPS": info.get("trailingEps", "N/A"),
        "ROE": info.get("returnOnEquity", "N/A"),
        "Debt/Equity": info.get("debtToEquity", "N/A"),
        "52W High": info.get("fiftyTwoWeekHigh", "N/A"),
        "52W Low": info.get("fiftyTwoWeekLow", "N/A")
    }


# -------------------------
# Time filter
# -------------------------
period = st.selectbox(
    "Select Time Range",
    ["1d", "15d", "1mo"]
)

if st.button("Fetch Data"):

    df = get_performance(period)

    gainers = df.head(10)
    losers = df.tail(10).sort_values("Change %")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Top 10 Gainers")
        st.dataframe(gainers)

    with col2:
        st.subheader("📉 Top 10 Losers")
        st.dataframe(losers)

    st.subheader("📊 Detailed Analysis")

    selected = st.selectbox(
        "Select Stock",
        df["Ticker"]
    )

    fundamentals = get_fundamentals(selected)

    st.write("### Fundamentals")
    st.json(fundamentals)

    st.write("### Latest News")
    news = get_news(selected)

    for n in news:
        st.write("-", n)
