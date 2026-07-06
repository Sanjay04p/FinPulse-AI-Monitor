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
import json

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
def get_all_us_tickers():
    """
    Fetches a comprehensive list of all publicly traded US tickers directly from the SEC.
    Returns a sorted list of thousands of ticker symbols.
    """
    # The SEC's official and public JSON file for company tickers
    url = "https://www.sec.gov/files/company_tickers.json"
    
    # The SEC strictly requires a User-Agent to prevent bot spam. 
    # It's best practice to use a format like: "YourName your@email.com"
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
        # Fallback to a few major ones just in case of failure
        return ["NVDA", "TSLA", "AAPL", "MSFT", "GOOGL"]

  