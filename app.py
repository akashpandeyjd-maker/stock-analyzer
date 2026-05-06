import streamlit as st
import requests
from bs4 import BeautifulSoup
import feedparser
import urllib.parse

st.set_page_config(page_title="Stock Analyzer", layout="wide")

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
        # Top Gainers
        for row in tables[0].find_all("tr")[1:6]:
            cols = row.find_all("td")
            gainers.append({
                "Stock": cols[0].text.strip(),
                "Price": cols[1].text.strip(),
                "Change": cols[2].text.strip()
            })

        # Top Losers
        for row in tables[1].find_all("tr")[1:6]:
            cols = row.find_all("td")
            losers.append({
                "Stock": cols[0].text.strip(),
                "Price": cols[1].text.strip(),
                "Change": cols[2].text.strip()
            })

    except:
        st.error("⚠️ Error fetching data from Moneycontrol")

    return gainers, losers


# -------------------------------
# Get News (FIXED URL ISSUE)
# -------------------------------
def get_news(stock):
    query = urllib.parse.quote(stock + " stock India")
    url = f"https://news.google.com/rss/search?q={query}"

    try:
        feed = feedparser.parse(url)
        headlines = [entry.title for entry in feed.entries[:3]]
        return headlines if headlines else ["No recent news found"]
    except:
        return ["Error fetching news"]


# -------------------------------
# Analyze Reason
# -------------------------------
def get_reason(news):
    text = " ".join(news).lower()

    if any(word in text for word in ["profit", "earnings", "revenue", "results"]):
        return "📊 Strong Earnings"
    elif any(word in text for word in ["loss", "decline", "fall", "down"]):
        return "⚠️ Weak Performance"
    elif any(word in text for word in ["deal", "acquisition", "merger"]):
        return "🤝 Corporate News"
    elif any(word in text for word in ["upgrade", "buy rating"]):
        return "📈 Positive Sentiment"
    else:
        return "📰 General Market Movement"


# -------------------------------
# Button UI
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
            st.write(f"💰 Price: {stock['Price']}")
            st.write(f"📊 Change: {stock['Change']}")
            st.write(f"🧠 Reason: {reason}")

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
            st.write(f"💰 Price: {stock['Price']}")
            st.write(f"📊 Change: {stock['Change']}")
            st.write(f"🧠 Reason: {reason}")

            with st.expander("📰 News"):
                for n in news:
                    st.write("-", n)
