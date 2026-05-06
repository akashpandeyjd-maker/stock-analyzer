import streamlit as st
import yfinance as yf
import pandas as pd
import feedparser
import urllib.parse
import time
from openai import OpenAI

# -------------------------
# CONFIG
# -------------------------
st.set_page_config(page_title="AI Stock Scanner", layout="wide")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.title("📈 AI Stock Scanner (Pro) 🚀")

# -------------------------
# STOCK LIST (expandable)
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

    delta = hist["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    hist["RSI"] = 100 - (100 / (1 + rs))

    hist["Vol_Avg"] = hist["Volume"].rolling(10).mean()
    hist["Vol_Spike"] = hist["Volume"] > (1.5 * hist["Vol_Avg"])

    return hist

# -------------------------
# PERFORMANCE
# -------------------------
@st.cache_data(ttl=300)
def get_performance(period):
    data = []

    for ticker in stocks:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="3mo")

            if len(hist) < 50:
                continue

            hist = calculate_indicators(hist)
            latest = hist.iloc[-1]

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
                "RSI": round(latest["RSI"], 2)
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
# GPT AI REASONING (CACHED)
# -------------------------
@st.cache_data(ttl=600)
def get_ai_reason(stock, price, change, rsi, news):

    prompt = f"""
    Analyze why this stock moved.

    Stock: {stock}
    Price: {price}
    Change: {change}%
    RSI: {rsi}

    News:
    {news}

    Give a short professional explanation (2-3 lines).
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )

        return response.choices[0].message.content

    except:
        return "AI analysis unavailable"

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
        st.subheader("📈 Top 10 Gainers")
        st.dataframe(gainers, use_container_width=True)

    with col2:
        st.subheader("📉 Top 10 Losers")
        st.dataframe(losers, use_container_width=True)

    # -------------------------
    # DETAIL VIEW
    # -------------------------
    st.subheader("🔍 Stock Deep Dive")

    selected = st.selectbox("Select Stock", df["Ticker"])
    row = df[df["Ticker"] == selected].iloc[0]

    news = get_news(selected)

    ai_reason = get_ai_reason(
        selected,
        row["Price"],
        row["Change %"],
        row["RSI"],
        news
    )

    st.write("### 🧠 AI Insight")
    st.write(ai_reason)

    st.write("### 📰 News")
    for n in news:
        st.write("-", n)
