# bot_app.py (Debug Version)

import os
import requests
from flask import Flask
import pandas as pd
import yfinance as yf

from config import N8N_WEBHOOK_URL, SCORE_THRESHOLD, DAYS_OF_DATA
from scanner import analyze_and_score_stock
from charting import generate_annotated_chart, generate_datasheet_image, create_composite_image

app = Flask(__name__)

def get_market_data(ticker: str) -> pd.DataFrame | None:
    """Fetches and validates historical market data for a given ticker."""
    print(f"--- Inside get_market_data for {ticker} ---")
    data = yf.download(
        tickers=f"{ticker}.NS",
        period="6mo",
        progress=False,
        timeout=10,
        auto_adjust=True
    )

    # --- CRUCIAL DEBUG STEP ---
    print(f"Data type returned for {ticker} is: {type(data)}")

    if isinstance(data, pd.DataFrame) and not data.empty:
        if len(data) < 51:
            print(f"DEBUG: Not enough data for {ticker}. Rows: {len(data)}")
            return None

        data.columns = [col.lower() for col in data.columns]
        print(f"DEBUG: Successfully processed DataFrame for {ticker}.")
        return data
    else:
        print(f"DEBUG: Skipping {ticker} because it is not a valid DataFrame.")
        return None

def run_scan_and_report_to_n8n():
    """Scans stocks and reports the top 5 to n8n."""
    print("--- Inside run_scan_and_report_to_n8n ---")

    try:
        df_watchlist = pd.read_csv("nifty500.csv")
        watchlist = df_watchlist['Symbol'].tolist()
        print(f"DEBUG: Successfully loaded {len(watchlist)} stocks.")
    except FileNotFoundError:
        return "ERROR: nifty500.csv not found."

    scored_candidates = []

    for ticker in watchlist:
        print(f"--- Processing ticker: {ticker} ---")
        df = get_market_data(ticker)

        if df is not None:
            print(f"DEBUG: Data for {ticker} is valid. Proceeding to score.")
            score = analyze_and_score_stock(df.copy())
            if score >= SCORE_THRESHOLD:
                # ... (rest of the logic for appending candidates) ...
                pass
        else:
            print(f"DEBUG: No valid data for {ticker}. Skipping.")

    # ... (rest of your ranking and reporting logic) ...
    return "Scan finished. Check logs for details."

@app.route('/execute_scan', methods=['GET', 'POST'])
def trigger_scan_from_n8n():
    """Public endpoint to trigger the scan."""
    print("--- /execute_scan endpoint was hit ---")
    result = run_scan_and_report_to_n8n()
    return result
