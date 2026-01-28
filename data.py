import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("finnhub_API")
import finnhub
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import streamlit as st
import requests       
import io

def init_finnhub(api_key):
    return finnhub.Client(api_key=api_key)

def get_historical_prices(ticker, days=30):
    """
    Fetches stock price data.
    FIX: Uses .history() to avoid the 'MultiIndex' bug in yfinance.
    """
    try:
        
        stock = yf.Ticker(ticker)
        df = stock.history(period=f"{days}d", interval="1d")
        if df.empty:
            return None
            
        return df
    except Exception as e:
        print(f"Error fetching prices: {e}")
        return None

def get_latest_news(client, ticker):
    """Fetches the last 7 days of news from Finnhub."""
    try:
        # Dynamic dates based on "today"
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        return client.company_news(ticker, _from=start_date, to=end_date)
    except Exception as e:
        print(f"Error fetching news: {e}")
        return []

@st.cache_data
def get_ticker_list():
    """
    Fetches S&P 500 tickers using a 'User-Agent' to avoid 403 Forbidden errors.
    """
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        # 1. Send GET request with headers
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Check if request was successful
        
        # 3. Pass the HTML text to pandas
        tables = pd.read_html(io.StringIO(response.text))
        
        # 4. Extract symbols
        df = tables[0]
        tickers = df['Symbol'].tolist()
        return sorted(tickers)
        
    except Exception as e:
        print(f"Scraping failed: {e}")
        return ["NVDA", "TSLA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "AMD", "NFLX"]

  