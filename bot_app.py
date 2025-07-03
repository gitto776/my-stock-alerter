# ===================================================================
# 1. Imports
# ===================================================================
import os
import requests
from flask import Flask
import pandas as pd
import yfinance as yf

# Import from your custom modules
from config import N8N_WEBHOOK_URL, SCORE_THRESHOLD, DAYS_OF_DATA
from scanner import analyze_and_score_stock
from charting import generate_annotated_chart, generate_datasheet_image, create_composite_image

# ===================================================================
# 2. Initialization
# ===================================================================
app = Flask(__name__)


# ===================================================================
# 3. Data Fetching Function
# ===================================================================
def get_market_data(ticker: str) -> pd.DataFrame | None:
    """Fetches historical market data for a given ticker from Yahoo Finance."""
    try:
        # Appends .NS for National Stock Exchange tickers
        data = yf.download(f"{ticker}.NS", period="6mo", progress=False, timeout=10)
        if data.empty or len(data) < 51: return None # Ensure enough data for 50-day EMA
        data.columns = [col.lower() for col in data.columns]
        return data
    except Exception as e:
        print(f"Error fetching market data for {ticker}: {e}")
        return None


# ===================================================================
# 4. Main Scan and Report