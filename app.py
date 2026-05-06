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

st.set_page_config(page_title="Stock Intelligence Dashboard", layout="wide")

st.title("📊 Stock Intelligence Dashboard 🚀")

# -------------------------
# STOCK LIST
# -------------------------
stocks = [
    "RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS",
    "SBIN.NS","LT.NS","ITC.NS","AXISBANK.NS","KOTAKBANK.NS",
    "BHARTIARTL.NS","MARUTI.NS","ASIANPAINT.NS","SUNPHARMA.NS","TITAN.NS"
]

# -------------------------
# INDICATORS
# -------------------------
def add_indicators(df):
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
# MARKET SCAN
# -------------------------
@st.cache_data(ttl=300)
def scan_market(period):
    data = []

    for t in stocks:
        try:
            df = yf.Ticker(t).history(period="3mo")
            df = add_indicators(df)

            if len(df) < 50:
                continue

            latest = df.iloc[-1]

            if period == "1d":
                prev = df.iloc[-2]["Close"]
            elif period == "15d":
                prev = df.iloc[-15]["Close"]
            else:
                prev = df.iloc[-30]["Close"]

            change = ((latest["Close"] - prev) / prev) * 100

            signal = get_signal(
                latest["RSI"],
                latest["Close"],
                latest["MA20"],
                latest["MA50"],
                latest["Vol_Spike"]
            )

            data.append({
                "Ticker": t,
                "Price": round(latest["Close"],2),
                "Change %": round(change,2),
                "RSI": round(latest["RSI"],2),
                "Signal": signal
            })

        except:
            continue

    df = pd.DataFrame(data)
    return df.sort_values("Change %", ascending=False)

# -------------------------
# NEWS
# -------------------------
def get_news(stock):
    try:
        name = stock.replace(".NS","")
        query = urllib.parse.quote(name + " stock India news")
        url = f"https://news.google.com/rss/search?q={query}"

        feed = feedparser.parse(url)
        return [e.title for e in feed.entries[:5]]
    except:
        return ["No news available"]

# -------------------------
# AI / FALLBACK
# -------------------------
def get_reason(stock, row, news):

    # GPT
    if AI_ENABLED:
        try:
            prompt = f"""
            Explain why this stock moved.

            Stock: {stock}
            Change: {row['Change %']}%
            RSI: {row['RSI']}
            Signal: {row['Signal']}

            News:
            {news}

            Give 2 short lines explanation.
            """

            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role":"user","content":prompt}]
            )

            return res.choices[0].message.content

        except:
            pass

    # fallback logic
    if row["Signal"] == "BUY":
        return "Bullish trend supported by RSI and moving averages."
    elif row["Signal"] == "SELL":
        return "Bearish sentiment with weak RSI."
    else:
        return "Sideways movement with no strong signals."

# -------------------------
# AUTO REFRESH
# -------------------------
if st.checkbox("🔄 Auto Refresh"):
    time.sleep(30)
    st.rerun()

# -------------------------
# UI
# -------------------------
period = st.selectbox("Select Timeframe", ["1d","15d","1mo"])

if st.button("📊 Scan Market"):

    df = scan_market(period)

    if df.empty:
        st.warning("No data")
        st.stop()

    # -------------------------
    # GAINERS / LOSERS
    # -------------------------
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Top Gainers")
        st.dataframe(df.head(10))

    with col2:
        st.subheader("📉 Top Losers")
        st.dataframe(df.tail(10).sort_values("Change %"))

    # -------------------------
    # STOCK ANALYSIS
    # -------------------------
    st.subheader("🔍 Stock Analysis")

    stock = st.selectbox("Select Stock", df["Ticker"])
    row = df[df["Ticker"]==stock].iloc[0]

    hist = yf.Ticker(stock).history(period="3mo")
    hist = add_indicators(hist)
    latest = hist.iloc[-1]

    # Indicators
    st.write("### 📊 Indicators")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("RSI", round(latest["RSI"],2))
    c2.metric("MA20", round(latest["MA20"],2))
    c3.metric("MA50", round(latest["MA50"],2))
    c4.metric("Volume Spike", "Yes" if latest["Vol_Spike"] else "No")

    st.write("### Signal:", row["Signal"])

    # Chart
    st.write("### 📈 Chart")
    fig, ax = plt.subplots()
    ax.plot(hist["Close"], label="Price")
    ax.plot(hist["MA20"], label="MA20")
    ax.plot(hist["MA50"], label="MA50")
    ax.legend()
    st.pyplot(fig)

    # News + Reason
    news = get_news(stock)

    st.write("### 🧠 Why Stock Moved")
    st.write(get_reason(stock, row, news))

    st.write("### 📰 News")
    for n in news:
        st.write("-", n)
