import streamlit as st
import yfinance as yf
import pandas as pd
import feedparser
import urllib.parse
import time

st.set_page_config(page_title="AI Stock Scanner", layout="wide")

st.title("📈 AI Stock Scanner 🚀")

# -------------------------
# STOCK LIST
# -------------------------
stocks = [
    "RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS",
    "SBIN.NS","LT.NS","ITC.NS","AXISBANK.NS","KOTAKBANK.NS",
    "HCLTECH.NS","WIPRO.NS","BHARTIARTL.NS","MARUTI.NS","ASIANPAINT.NS"
]

# -------------------------
# TECHNICAL INDICATORS
# -------------------------
def calculate_indicators(hist):

    hist["MA20"] = hist["Close"].rolling(20).mean()
    hist["MA50"] = hist["Close"].rolling(50).mean()

    # RSI
    delta = hist["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    hist["RSI"] = 100 - (100 / (1 + rs))

    # Volume spike
    hist["Vol_Avg"] = hist["Volume"].rolling(10).mean()
    hist["Vol_Spike"] = hist["Volume"] > (1.5 * hist["Vol_Avg"])

    return hist


# -------------------------
# AI REASONING
# -------------------------
def generate_reason(data):
    reason = []

    if data["RSI"] > 60:
        reason.append("Strong RSI (Bullish)")
    elif data["RSI"] < 40:
        reason.append("Weak RSI (Bearish)")

    if data["Close"] > data["MA20"] and data["Close"] > data["MA50"]:
        reason.append("Above Moving Averages (Uptrend)")

    if data["Vol_Spike"]:
        reason.append("High Volume Activity")

    if not reason:
        return "No strong signals"

    return ", ".join(reason)


# -------------------------
# PERFORMANCE
# -------------------------
@st.cache_data(ttl=300)
def get_performance(period):
    data = []

    for ticker in stocks:
        try:
            stock = yf.Ticker(ticker)

            hist = stock.history(period="3mo")  # needed for indicators
            hist = calculate_indicators(hist)

            if len(hist) < 50:
                continue

            latest = hist.iloc[-1]

            # Period change
            if period == "1d":
                prev = hist.iloc[-2]["Close"]
            elif period == "15d":
                prev = hist.iloc[-15]["Close"]
            else:
                prev = hist.iloc[-30]["Close"]

            change = ((latest["Close"] - prev) / prev) * 100

            data.append({
                "Ticker": ticker,
                "Price": round(latest["Close"], 2),
                "Change %": round(change, 2),
                "RSI": round(latest["RSI"], 2),
                "Reason": generate_reason(latest)
            })

        except:
            continue

    df = pd.DataFrame(data)

    if df.empty:
        return df

    return df.sort_values("Change %", ascending=False)


# -------------------------
# NEWS
# -------------------------
def get_news(stock):
    try:
        clean = stock.replace(".NS","")
        query = urllib.parse.quote(clean + " stock India")
        url = f"https://news.google.com/rss/search?q={query}"

        feed = feedparser.parse(url)
        return [e.title for e in feed.entries[:3]]
    except:
        return ["No news available"]


# -------------------------
# AUTO REFRESH
# -------------------------
refresh = st.checkbox("🔄 Auto Refresh (30 sec)")

if refresh:
    time.sleep(30)
    st.rerun()


# -------------------------
# UI
# -------------------------
period = st.selectbox("Select Period", ["1d", "15d", "1mo"])

if st.button("📊 Scan Market") or refresh:

    df = get_performance(period)

    if df.empty:
        st.warning("No data available")
        st.stop()

    gainers = df.head(10)
    losers = df.tail(10).sort_values("Change %")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Top Gainers")
        st.dataframe(gainers)

    with col2:
        st.subheader("📉 Top Losers")
        st.dataframe(losers)

    # -------------------------
    # DETAIL VIEW
    # -------------------------
    st.subheader("🔍 Stock Deep Dive")

    selected = st.selectbox("Select Stock", df["Ticker"])

    st.write("### 🧠 AI Insight")
    st.write(df[df["Ticker"] == selected]["Reason"].values[0])

    st.write("### 📰 News")
    news = get_news(selected)

    for n in news:
        st.write("-", n)
