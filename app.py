import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import feedparser

st.title("📈 Stock Analyzer 🚀")

# -------------------------------
# Get Gainers & Losers
# -------------------------------
def get_market_data():
    url = "https://www.moneycontrol.com/stocks/marketstats/index.php"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    tables = soup.find_all("table")

    gainers, losers = [], []

    try:
        for row in tables[0].find_all("tr")[1:6]:
            cols = row.find_all("td")
            gainers.append({
                "Stock": cols[0].text.strip(),
                "Price": cols[1].text.strip(),
                "Change": cols[2].text.strip()
            })

        for row in tables[1].find_all("tr")[1:6]:
            cols = row.find_all("td")
            losers.append({
                "Stock": cols[0].text.strip(),
                "Price": cols[1].text.strip(),
                "Change": cols[2].text.strip()
            })
    except:
        st.error("Error fetching data")

    return gainers, losers


# -------------------------------
# Get News
# -------------------------------
def get_news(stock):
    url = f"https://news.google.com/rss/search?q={stock} stock"
    feed = feedparser.parse(url)
    return [entry.title for entry in feed.entries[:3]]


# -------------------------------
# Analyze Reason
# -------------------------------
def get_reason(news):
    text = " ".join(news).lower()

    if "profit" in text or "earnings" in text:
        return "📊 Strong Earnings"
    elif "loss" in text or "fall" in text:
        return "⚠️ Weak Performance"
    elif "deal" in text or "acquisition" in text:
        return "🤝 Corporate News"
    else:
        return "📰 Market Movement"


# -------------------------------
# Button
# -------------------------------
if st.button("🔄 Fetch Market Data"):

    gainers, losers = get_market_data()

    col1, col2 = st.columns(2)

    # -------- GAINERS --------
    with col1:
        st.subheader("📈 Top Gainers")
        for stock in gainers:
            news = get_news(stock["Stock"])
            reason = get_reason(news)

            st.markdown(f"### {stock['Stock']}")
            st.write(f"Price: {stock['Price']}")
            st.write(f"Change: {stock['Change']}")
            st.write(f"Reason: {reason}")

            with st.expander("📰 News"):
                for n in news:
                    st.write("-", n)

    # -------- LOSERS --------
    with col2:
        st.subheader("📉 Top Losers")
        for stock in losers:
            news = get_news(stock["Stock"])
            reason = get_reason(news)

            st.markdown(f"### {stock['Stock']}")
            st.write(f"Price: {stock['Price']}")
            st.write(f"Change: {stock['Change']}")
            st.write(f"Reason: {reason}")

            with st.expander("📰 News"):
                for n in news:
                    st.write("-", n)
