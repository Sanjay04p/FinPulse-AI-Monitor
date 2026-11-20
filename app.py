import os
from dotenv import load_dotenv
load_dotenv()
FINNHUB_KEY = os.getenv("finnhub_API")

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

import data
import model
import forecast_model

# --- CONFIG ---
st.set_page_config(page_title="AI Stock Monitor", layout="wide")

# --- CACHING ---
@st.cache_resource
def get_ai_model():
    return model.load_finbert()

@st.cache_resource
def get_api_client():
    return data.init_finnhub(FINNHUB_KEY)


# --- RESOURCE INITIALIZATION ---
finbert = None
client = None
resource_errors = []

try:
    finbert = get_ai_model()
except Exception:
    resource_errors.append("The sentiment-analysis model could not be loaded. News sentiment analysis is unavailable.")


try:
    if not FINNHUB_KEY:
        resource_errors.append("Finnhub API key is missing. Stock news and related API data may be unavailable.")
    client = get_api_client()
except Exception:
    resource_errors.append("The market-data service could not be initialized. Please check your API key or try again later.")

for message in resource_errors:
    st.warning(message)


# --- SIDEBAR ---
st.sidebar.header("⚙️ Dashboard Settings")
try:
    available_tickers = data.get_ticker_list()
    if not available_tickers:
        st.error("No assets are currently available. Please try again later.")
        st.stop()
except Exception:
    st.error("Unable to load the asset list right now. Please refresh the page or try again later.")
    st.stop()


ticker = st.sidebar.selectbox(
    "Select Asset",
    options=available_tickers,
    index=available_tickers.index("GOOG") if "GOOG" in available_tickers else 0
)
days = st.sidebar.slider("Analysis Window (Days)", 30, 365, 90)


# --- DATA LOADING ---
st.title(f"🚀 {ticker} AI-Powered Analyst")
prices = None
raw_news = None
analyzed_news = []
forecast = None

with st.spinner("Crunching numbers..."):
    try:
        prices = data.get_historical_prices(ticker, days)
        if prices is None or getattr(prices, "empty", True):
            prices = None
            st.warning("No historical price data was found for this asset. Try another asset or a different analysis window.")
    except Exception:
        prices = None
        st.warning("We couldn't retrieve historical prices right now. Please try again later.")

    # News retrieval and sentiment analysis are independent from price/forecast display.
    try:
        if client is not None:
            raw_news = data.get_latest_news(client, ticker)
        else:
            raw_news = None
    except Exception:
        raw_news = None
        st.info("Latest news is temporarily unavailable.")

    try:
        if raw_news and finbert is not None:
            analyzed_news = model.analyze_news_list(raw_news, finbert) or []
        elif raw_news and finbert is None:
            st.info("News was retrieved, but sentiment analysis is unavailable because the model could not be loaded.")
        else:
            analyzed_news = []
    except Exception:
        analyzed_news = []
        st.info("We couldn't analyze news sentiment right now. The rest of the dashboard can still be used.")

    try:
        if prices is not None:
            forecast = forecast_model.generate_forecast(prices, days=7)
            if forecast is None or getattr(forecast, "empty", True):
                forecast = None
                st.warning("The forecast is currently unavailable for this asset.")
        else:
            forecast = None
    except Exception:
        forecast = None
        st.warning("We couldn't generate the forecast right now. Historical price information may still be available.")


# --- TOP ROW: KPI METRICS ---
if prices is not None and not prices.empty:
    try:
        current_price = float(prices["Close"].iloc[-1])
        predicted_price = float(forecast["yhat"].iloc[-1]) if forecast is not None and "yhat" in forecast.columns and not forecast.empty else None
        price_change = ((predicted_price - current_price) / current_price) * 100 if predicted_price is not None and current_price else None

        avg_score = 0
        if analyzed_news:
            scores = [
                n["score"] if n["label"] == "positive" else
                -n["score"] if n["label"] == "negative" else 0
                for n in analyzed_news
            ]
            avg_score = sum(scores) / len(scores) if scores else 0

        m1, m2, m3 = st.columns(3)
        m1.metric("Current Price", f"${current_price:.2f}")
        if predicted_price is not None:
            m2.metric("AI 7-Day Target", f"${predicted_price:.2f}", f"{price_change:.2f}%" if price_change is not None else None)
        else:
            m2.metric("AI 7-Day Target", "Unavailable")
        m3.metric("Market Sentiment", "Bullish" if avg_score > 0.1 else "Bearish" if avg_score < -0.1 else "Neutral", f"{avg_score:.2f}")
    except Exception:
        st.warning("Some dashboard metrics couldn't be calculated. The charts and other available information may still be displayed.")

    st.divider()
    # --- TABS ---
    tab1, tab2 = st.tabs(["📈 Price & Forecast", "🧠 Sentiment Analysis"])

    with tab1:
        st.subheader("Price Action + AI Prediction")
        try:
            fig_main = go.Figure()
            fig_main.add_trace(go.Candlestick(
                x=prices.index,
                open=prices["Open"], high=prices["High"],
                low=prices["Low"], close=prices["Close"],
                name="Actual History"
            ))

            if forecast is not None and all(c in forecast.columns for c in ["ds", "yhat", "yhat_upper", "yhat_lower"]):
                last_real_date = prices.index[-1]
                if getattr(last_real_date, "tzinfo", None) is not None:
                    last_real_date = last_real_date.tz_localize(None)
                future_data = forecast[forecast["ds"] > last_real_date]

                fig_main.add_trace(go.Scatter(
                    x=future_data["ds"], y=future_data["yhat"],
                    mode="lines+markers", name="AI Prediction",
                    line=dict(color="#00ffcc", width=3, dash="dash")
                ))
                fig_main.add_trace(go.Scatter(
                    x=future_data["ds"], y=future_data["yhat_upper"],
                    mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip"
                ))
                fig_main.add_trace(go.Scatter(
                    x=future_data["ds"], y=future_data["yhat_lower"],
                    fill="tonexty", mode="lines", line=dict(width=0),
                    fillcolor="rgba(0, 255, 204, 0.1)", name="Confidence Range"
                ))
            else:
                st.info("The forecast chart is unavailable, but historical price data is shown.")


            fig_main.update_layout(
                template="plotly_dark", height=600,
                xaxis_rangeslider_visible=False,
                legend=dict(orientation="h", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_main, width="stretch")
            st.warning("⚠️ **Disclaimer:** This forecast is generated by an AI model based solely on historical price patterns. It does not account for real-world news, earnings reports, or macroeconomic events. **Do not trade based on this data.**")
        except Exception:
            st.error("The price chart couldn't be displayed. Please try refreshing the app.")

    with tab2:
        col_sent_graph, col_news = st.columns([2, 1])

        with col_sent_graph:
            st.subheader("Sentiment Trend (Last 7 Days)")
            if analyzed_news:
                try:
                    df_news = pd.DataFrame(analyzed_news)
                    required_columns = {"datetime", "score", "label"}
                    if not required_columns.issubset(df_news.columns):
                        st.info("The news data is incomplete, so the sentiment trend can't be displayed.")
                    else:
                        df_news["date"] = pd.to_datetime(df_news["datetime"], unit="s", errors="coerce")
                        df_news["val"] = df_news.apply(
                            lambda x: x["score"] if x["label"] == "positive" else -x["score"] if x["label"] == "negative" else 0,
                            axis=1
                        )
                        df_news = df_news.dropna(subset=["date", "val"])
                        if not df_news.empty:
                            daily_sentiment = df_news.groupby(df_news["date"].dt.date)["val"].mean()
                            fig_sent = go.Figure()
                            fig_sent.add_trace(go.Scatter(
                                x=daily_sentiment.index, y=daily_sentiment.values,
                                mode="lines+markers", name="Sentiment Score",
                                line=dict(color="#ff9900", width=3), marker=dict(size=8)
                            ))
                            fig_sent.add_hline(y=0, line_dash="dot", line_color="gray")
                            fig_sent.update_layout(template="plotly_dark", height=500)
                            st.plotly_chart(fig_sent, width="stretch")
                        else:
                            st.info("No usable sentiment data is available for the trend chart.")
                except Exception:
                    st.info("The sentiment trend chart is temporarily unavailable.")
            else:
                st.info("Not enough news data to build a trend line.")

        with col_news:
            st.subheader("Latest Headlines")
            with st.container(height=500):
                if analyzed_news:
                    for item in analyzed_news:
                        try:
                            label = item.get("label", "neutral")
                            color = "green" if label == "positive" else "red" if label == "negative" else "gray"
                            headline = item.get("headline", "Headline unavailable")
                            score = item.get("score")
                            st.markdown(f"**{headline[:60]}...**")
                            st.caption(f":{color}[{label.upper()}] • Conf: {score:.2f}" if isinstance(score, (int, float)) else f":{color}[{label.upper()}] • Confidence unavailable")
                            url = item.get("url")
                            if url:
                                st.markdown(f"[Read Source]({url})")
                            st.divider()
                        except Exception:
                            st.caption("A news item couldn't be displayed.")
                else:
                    st.info("News headlines are currently unavailable.")
else:
    st.warning("No data found for this ticker. Please try another asset or check back later.")
