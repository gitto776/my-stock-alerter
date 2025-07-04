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


# In bot_app.py

# In bot_app.py

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

    # This is the most important check:
    # Only proceed if the returned object is a non-empty pandas DataFrame.
    if isinstance(data, pd.DataFrame) and not data.empty:
        # Check for sufficient data length after confirming it's a DataFrame
        if len(data) < 51:
            print(f"Not enough historical data for {ticker}.")
            return None

        # Now it's safe to access .columns
        data.columns = [col.lower() for col in data.columns]
        return data

    # If yfinance returns anything else (a tuple, None, empty DataFrame), fail safely.
    print(f"Could not retrieve valid DataFrame for {ticker}.")
    return None


def run_scan_and_report_to_n8n():
    """Scans a dynamic list of stocks and reports the top 5 to the n8n webhook."""
    print("Scan triggered. Analyzing market...")

    # This watchlist is now read from nifty500.csv
    try:
        df_watchlist = pd.read_csv("nifty500.csv")
        watchlist = df_watchlist['Symbol'].tolist()
        print(f"Successfully loaded {len(watchlist)} stocks.")
    except FileNotFoundError:
        print("ERROR: nifty500.csv not found.")
        return "ERROR: nifty500.csv not found."

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
                    "ticker": ticker, "score": score, "pattern": "Consolidation/Squeeze",
                    "price": latest['close'], "stop_loss": stop_loss, "target": target, "data": df
                })
    
    if not scored_candidates:
        print("Scan complete. No setups found.")
        return "Scan complete. No setups found."

    ranked_list = sorted(scored_candidates, key=lambda x: x['score'], reverse=True)
    top_5_watchlist = ranked_list[:5]

    print(f"Found {len(top_5_watchlist)} candidates. Sending to n8n...")
    
    for stock in top_5_watchlist:
        try:
            # Generate and upload images, then post to n8n
            chart_file = generate_annotated_chart(stock['data'][-DAYS_OF_DATA:], stock['ticker'], stock['price'], stock['stop_loss'], stock['target'])
            datasheet_file = generate_datasheet_image(stock['ticker'], stock['score'], stock['pattern'], stock['stop_loss'], stock['target'])
            composite_file = create_composite_image(chart_file, datasheet_file, stock['ticker'])
            
            with open(composite_file, 'rb') as f:
                upload_response = requests.post('https://tmpfiles.org/api/v1/upload', files={'file': f})
            
            if upload_response.status_code == 200:
                image_url = upload_response.json()['data']['url']
                caption = f"⚡️ Potential Breakout: ${stock['ticker']} (Score: {stock['score']})"
                n8n_payload = {"image_url": image_url, "caption": caption}
                
                if N8N_WEBHOOK_URL:
                    requests.post(N8N_WEBHOOK_URL, json=n8n_payload)
                else:
                    print("N8N_WEBHOOK_URL not set. Skipping notification.")

            os.remove(composite_file)
        except Exception as e:
            print(f"Failed to process {stock['ticker']}: {e}")

    return f"Scan complete. Sent {len(top_5_watchlist)} alerts to n8n."


# This is the single endpoint for n8n to trigger the scan.
# It now accepts GET requests so you can test it in a browser.
@app.route('/execute_scan', methods=['GET', 'POST'])
def trigger_scan_from_n8n():
    """A public endpoint for n8n to trigger the daily scan."""
    result = run_scan_and_report_to_n8n()
    return result
