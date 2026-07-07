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
import time
import random
import datetime as dt

def init_finnhub(api_key):
    return finnhub.Client(api_key=api_key)

@st.cache_data(ttl=900)
def get_historical_prices(ticker, days=30,max_retries=3):
    """
    Fetches stock price data.
    FIX: Uses .history() to avoid the 'MultiIndex' bug in yfinance.
    """
    end_date = dt.datetime.now()
    start_date = end_date - dt.timedelta(days=days)

    for attempt in range(max_retries):
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(start=start_date, end=end_date, interval="1d")

            if df.empty:
                print(f"No data returned for {ticker} (attempt {attempt + 1})")
            else:
                return df

        except Exception as e:
            print(f"Error fetching prices for {ticker} (attempt {attempt + 1}): {e}")

        if attempt < max_retries - 1:
            time.sleep((2 ** attempt) + random.uniform(0, 1))  # exponential backoff + jitter

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
    url = "https://www.sec.gov/files/company_tickers.json"
    
    headers = {
        "User-Agent": "FinPulse_AI_Project developer@finpulse.local"
    }

    try:
        # 1. Send GET request with headers
        response = requests.get(url, headers=headers)
        response.raise_for_status() 
        
        # 2. Parse the JSON response directly
        data = response.json()
        
        # 3. The SEC returns a dictionary of dictionaries. 
        # We can easily convert this nested structure into a Pandas DataFrame.
        df = pd.DataFrame.from_dict(data, orient='index')
        
        # 4. Extract just the 'ticker' column and convert it to a sorted list
        tickers = df['ticker'].tolist()
        return sorted(tickers)
        
    except Exception as e:
        print(f"Failed to fetch from SEC: {e}")
        return ["NVDA", "TSLA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "AMD", "NFLX"]

  