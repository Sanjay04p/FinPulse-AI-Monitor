# 🚀 AI-Powered Real-Time Stock Analysis
An end-to-end Financial Tech (FinTech) dashboard that combines real-time market data with Sentiment Analysis and AI-driven forecasting.

## Core Features
* Real-Time Sentiment: Analyzes live news headlines using FinBERT, a BERT model specialized for financial context.

* AI Forecasting: Generates a 7-day price projection using Facebook Prophet.

* Interactive Dashboard: Built with Streamlit and Plotly for a seamless user experience.

## Tech Stack
* Language: Python

* APIs: Finnhub (News), Yahoo Finance (Market Data)

* ML Models: HuggingFace Transformers (FinBERT), Prophet

* Deployment: Streamlit Cloud

## 🏗️ System Design & Data Pipeline

The project utilizes a hybrid architecture that correlates quantitative market data with qualitative news sentiment.

![graphviz (1)](https://github.com/user-attachments/assets/19793423-8ab5-4ba4-a567-069b0e0dd1e1)

* **Sentiment Engine:** Leverages `FinBERT` (a domain-specific BERT model) to convert subjective news into a -1 to +1 sentiment score.
* **Forecasting Engine:** Uses `Meta Prophet` to model seasonality and trends for a 7-day lookahead.
* **Correlation Logic:** Merges yFinance price streams with sentiment timestamps to visualize how news "pulses" impact price action.

## Working Sample

https://github.com/user-attachments/assets/2fde8f81-4a15-43da-b618-b7f0285fc317








