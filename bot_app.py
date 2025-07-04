import os
import requests
from flask import Flask
import pandas as pd
import yfinance as yf

# Import from your custom modules
from config import N8N_WEBHOOK_URL, SCORE_THRESHOLD, DAYS_OF_DATA
from scanner import analyze_and_score_stock
from charting import generate_annotated_chart, generate_datasheet_image, create_composite_image

# Initialize the Flask App
app = Flask(__name__)


def get_market_data(ticker: str) -> pd.DataFrame | None:
    """
    Fetches and validates historical market data for a given ticker from Yahoo Finance.
    """
    # yfinance can sometimes print its own errors; we will handle the return value.
    data = yf.download(
        tickers=f"{ticker}.NS",
        period="6mo",
        progress=False,
        timeout=10,
        auto_adjust=True
    )
    
    # Only proceed if the returned object is a non-empty pandas DataFrame.
    if isinstance(data, pd.DataFrame) and not data.empty:
        # Check for sufficient data length after confirming it's a DataFrame
        if len(data) < 51:
            print(f"Not enough historical data for {ticker}.")
            return None
        
        # Now it's safe to access .columns
        data.columns = [col.lower() for col in data.columns]
        return data
    
    # If yfinance returns anything else, fail safely.
    print(f"Could not retrieve valid DataFrame for {ticker}.")
    return None


def run_scan_and_report_to_n8n():
    """Scans a dynamic list of stocks and reports the top 5 to the n8n webhook."""
    print("Scan triggered. Analyzing market...")

    # --- DYNAMIC WATCHLIST LOADING ---
    try:
        df_watchlist = pd.read_csv("nifty500.csv")
        watchlist = df_watchlist['Symbol'].tolist()
        print(f"Successfully loaded {len(watchlist)} stocks.")
    except FileNotFoundError:
        error_message = "ERROR: nifty500.csv not found in the project folder."
        print(error_message)
        return error_message
    
    scored_candidates = []
    
    for ticker in watchlist:
        df = get_market_data(ticker)
        if df is not None:
            score = analyze_and_score_stock(df.copy())
            if score >= SCORE_THRESHOLD:
                latest = df.iloc[-1]
                stop_loss = latest['low'] * 0.95
                target = latest['close'] + (latest['close'] - stop_loss) * 2
                scored_candidates.append({
                    "ticker":
