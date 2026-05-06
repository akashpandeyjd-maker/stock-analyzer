import streamlit as st
import yfinance as yf
import pandas as pd
import feedparser
import urllib.parse

st.set_page_config(page_title="Pro Stock Analyzer", layout="wide")

st.title("📈 Pro Stock Analyzer 🚀")

# -------------------------
# NSE STOCK LIST (You can expand later)
# -------------------------
stocks = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS",
    "ICICIBANK.NS", "SBIN.NS", "LT.NS", "ITC.NS",
    "AXISBANK.NS", "BHARTIARTL.NS"
]

# -------------------------
# PERFORMANCE FUNCTION (FIXED)
# -------------------------
def get_performance(period):
    data = []

    for ticker in stocks:
        try:
            stock = yf.Ticker(ticker)

            # FIX for 1 day issue
            if period == "1d":
                hist = stock.history(period="2d")
            else:
                hist = stock.history(period=period)

            if hist is None or len(hist) < 2:
                continue

            start = hist["Close"].iloc[0]
            end = hist["Close"].iloc[-1]

            change = ((end - start) / start) * 100

            data.append({
                "Ticker": ticker,
                "Price": round(end, 2),
                "Change %": round(change, 2)
            })

        except:
            continue

    # Safety check
    if not data:
        return pd.DataFrame(columns=["Ticker", "Price", "Change %"])

    df = pd.DataFrame(data)

    # Ensure column exists before sorting
    if "Change %" in df.columns:
        df = df.sort_values("Change %", ascending=False)

    return df


# -------------------------
# NEWS FUNCTION (FIXED URL)
# -------------------------
def get_news(stock):
    try:
        query = urllib.parse.quote(stock + " stock India")
        url = f"https://news.google.com/rss/search?q={query}"

        feed = feedparser.parse(url)

        headlines = [entry.title for entry in feed.entries[:3]]

        if not headlines:
            return ["No recent news found"]

        return headlines

    except:
        return ["Error fetching news"]


# -------------------------
# FUNDAMENTALS FUNCTION
# -------------------------
def get_fundamentals(ticker):
    try:
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

    except:
        return {"Error": "Unable to fetch fundamentals"}


# -------------------------
# REASON ANALYSIS
# -------------------------
def get_reason(news):
    text = " ".join(news).lower()

    if any(word in text for word in ["profit", "earnings", "results"]):
        return "📊 Earnings Driven Move"
    elif any(word in text for word in ["loss", "fall", "decline"]):
        return "⚠️ Weak Performance"
    elif any(word in text for word in ["deal", "merger", "acquisition"]):
        return "🤝 Corporate Action"
    elif any(word in text for word in ["upgrade", "buy rating"]):
        return "📈 Positive Sentiment"
    else:
        return "📰 General Market Movement"


# -------------------------
# UI
# -------------------------
period = st.selectbox(
    "Select Time Range",
    ["1d", "15d", "1mo"]
)

if st.button("🔄 Fetch Data"):

    df = get_performance(period)

    # Prevent crash
    if df.empty:
        st.warning("No data available. Try again later.")
        st.stop()

    gainers = df.head(10)
    losers = df.tail(10).sort_values("Change %")

    col1, col2 = st.columns(2)

    # -------- GAINERS --------
    with col1:
        st.subheader("📈 Top 10 Gainers")
        st.dataframe(gainers, use_container_width=True)

    # -------- LOSERS --------
    with col2:
        st.subheader("📉 Top 10 Losers")
        st.dataframe(losers, use_container_width=True)

    # -------------------------
    # DETAILED ANALYSIS
    # -------------------------
    st.subheader("📊 Stock Detailed Analysis")

    selected = st.selectbox("Select Stock", df["Ticker"])

    # Fundamentals
    fundamentals = get_fundamentals(selected)

    st.write("### 📊 Fundamentals")
    st.json(fundamentals)

    # News
    st.write("### 📰 Latest News")
    news = get_news(selected)

    for n in news:
        st.write("-", n)

    # Reason
    reason = get_reason(news)
    st.write("### 🧠 Reason")
    st.write(reason)
