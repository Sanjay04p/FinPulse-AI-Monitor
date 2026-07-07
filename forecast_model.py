import pandas as pd
from prophet import Prophet

def generate_forecast(df, days=7):
    """
    Takes a dataframe with 'Date' and 'Close' prices.
    Returns a dataframe with the next 'days' predicted.
    """

    if df is None or df.empty:
        print("Warning: Received empty DataFrame for forecasting.")
        return None
    # 1. Prepare Data
    df_prophet = df.reset_index()[['Date', 'Close']]
    df_prophet.columns = ['ds', 'y']
    df_prophet['ds'] = pd.to_datetime(df_prophet['ds']).dt.tz_localize(None)

    # 2. Train the Model
    m = Prophet(daily_seasonality=True)
    m.fit(df_prophet)
    
    # 3. Create Future Dates
    future = m.make_future_dataframe(periods=days)
    
    # 4. Predict
    forecast = m.predict(future)
    
    return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]