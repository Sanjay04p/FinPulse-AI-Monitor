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

def init_finnhub(api_key):
    return finnhub.Client(api_key=api_key)

def get_historical_prices(ticker_symbol, days=30):
    """
    Fetches historical daily price data using the Finnhub Stock Candles endpoint.
    Formats the output to perfectly mimic a yfinance DataFrame structure.
    """
    # Reuse the Finnhub API Key already configured for news extraction
    api_key = os.getenv("FINNHUB_API_KEY") or st.secrets.get("FINNHUB_API_KEY")
    
    if not api_key:
        print("Error: FINNHUB_API_KEY is missing from environment secrets.")
        return None

    # Finnhub requires UNIX timestamps for range boundaries
    end_timestamp = int(time.time())
    # Add an extra 10-day buffer to guarantee enough trading days after filtering weekends
    start_timestamp = end_timestamp - (days + 10) * 86400 

    url = "https://finnhub.io/api/v1/stock/candle"
    params = {
        "symbol": ticker_symbol.upper(),
        "resolution": "D",  # 'D' specifies Daily intervals
        "from": start_timestamp,
        "to": end_timestamp,
        "token": api_key
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Finnhub returns {"s": "no_data"} if the ticker is invalid or unlisted
        if data.get("s") != "ok":
            print(f"Finnhub API returned status: {data.get('s')} for ticker {ticker_symbol}")
            return None

        # Finnhub returns raw lists compressed into single-letter keys:
        # t = timestamp, c = close, o = open, h = high, l = low, v = volume
        df = pd.DataFrame({
            "Date": pd.to_datetime(data["t"], unit="s"),
            "Close": data["c"],
            "Open": data["o"],
            "High": data["h"],
            "Low": data["l"],
            "Volume": data["v"]
        })

        # Set the 'Date' column as the index to match historical yfinance outputs
        df.set_index("Date", inplace=True)
        
        # Strip timezones right away to keep Prophet's training function happy
        df.index = df.index.tz_localize(None)

        # Return exactly the number of rows requested by the user interface
        return df.tail(days)

    except Exception as e:
        print(f"Finnhub historical candle lookup failed: {e}")
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

  