import streamlit as st
import yfinance as yf
import pandas as pd
import feedparser
import urllib.parse
import time
import matplotlib.pyplot as plt

# Optional AI
try:
    from openai import OpenAI
    client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY"))
    AI_ENABLED = True
except:
    AI_ENABLED = False

st.set_page_config(page_title="Trading Dashboard", layout="wide")

st.title("📊 Trading Dashboard 🚀")

# -------------------------
# STOCK LIST
# -------------------------
stocks = [
    "RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS",
    "SBIN.NS","LT.NS","ITC.NS","AXISBANK.NS","KOTAKBANK.NS"
]

# -------------------------
# INDICATORS
# -------------------------
def indicators(df):
    df["MA20"] = df["Close"].rolling(20).mean()
    df["MA50"] = df["Close"].rolling(50).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))

    df["Vol_Avg"] = df["Volume"].rolling(10).mean()
    df["Vol_Spike"] = df["Volume"] > 1.5 * df["Vol_Avg"]

    return df

# -------------------------
# SIGNAL
# -------------------------
def get_signal(rsi, price, ma20, ma50, vol):
    if rsi > 60 and price > ma20 and price > ma50 and vol:
        return "BUY"
    elif rsi < 40:
        return "SELL"
    else:
        return "HOLD"

# -------------------------
# DATA
# -------------------------
@st.cache_data(ttl=300)
def get_data():
    rows = []

    for t in stocks:
        try:
            df = yf.Ticker(t).history(period="3mo")
            df = indicators(df)

            latest = df.iloc[-1]

            signal = get_signal(
                latest["RSI"],
                latest["Close"],
                latest["MA20"],
                latest["MA50"],
                latest["Vol_Spike"]
            )

            rows.append({
                "Ticker": t,
                "Price": round(latest["Close"],2),
                "RSI": round(latest["RSI"],2),
                "Signal": signal
            })

        except:
            continue

    return pd.DataFrame(rows)

# -------------------------
# NEWS
# -------------------------
def get_news(stock):
    try:
        name = stock.replace(".NS","")
        query = urllib.parse.quote(name + " India stock news")
        url = f"https://news.google.com/rss/search?q={query}"

        feed = feedparser.parse(url)
        return [e.title for e in feed.entries[:5]]
    except:
        return ["No news"]

# -------------------------
# AI / FALLBACK
# -------------------------
def ai_reason(stock, row, news):

    if AI_ENABLED:
        try:
            prompt = f"""
            Explain stock movement.

            Stock: {stock}
            RSI: {row['RSI']}
            Signal: {row['Signal']}
            News: {news}
            """

            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role":"user","content":prompt}]
            )

            return res.choices[0].message.content
        except:
            pass

    # fallback
    return f"{row['Signal']} signal based on RSI and trend."

# -------------------------
# AUTO REFRESH
# -------------------------
if st.checkbox("🔄 Auto Refresh"):
    time.sleep(30)
    st.rerun()

# -------------------------
# MAIN
# -------------------------
if st.button("📊 Load Dashboard"):

    df = get_data()

    st.subheader("📋 Market Overview")
    st.dataframe(df)

    # -------------------------
    # STOCK DETAIL
    # -------------------------
    stock = st.selectbox("Select Stock", df["Ticker"])

    hist = yf.Ticker(stock).history(period="3mo")
    hist = indicators(hist)

    latest = hist.iloc[-1]

    # -------------------------
    # INDICATORS DISPLAY
    # -------------------------
    st.subheader("📊 Indicators")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("RSI", round(latest["RSI"],2))
    col2.metric("MA20", round(latest["MA20"],2))
    col3.metric("MA50", round(latest["MA50"],2))
    col4.metric("Volume Spike", "Yes" if latest["Vol_Spike"] else "No")

    st.write("### Signal:", get_signal(
        latest["RSI"],
        latest["Close"],
        latest["MA20"],
        latest["MA50"],
        latest["Vol_Spike"]
    ))

    # -------------------------
    # CHART (VERY IMPORTANT)
    # -------------------------
    st.subheader("📈 Price Chart")

    fig, ax = plt.subplots()
    ax.plot(hist["Close"], label="Price")
    ax.plot(hist["MA20"], label="MA20")
    ax.plot(hist["MA50"], label="MA50")
    ax.legend()

    st.pyplot(fig)

    # -------------------------
    # NEWS + AI
    # -------------------------
    news = get_news(stock)

    st.subheader("🧠 Insight")
    st.write(ai_reason(stock, df[df["Ticker"]==stock].iloc[0], news))

    st.subheader("📰 News")
    for n in news:
        st.write("-", n)
