
#

import os

# --- Load API Keys and Webhook URL from Environment Variables ---
# These must be set in your Railway project's "Variables" tab
N8N_WEBHOOK_URL = os.environ.get('https://primary-production-b310e.up.railway.app/webhook-test/https://himanshualpha.pythonanywhere.com/execute_scan')
NEWS_API_KEY = os.environ.get('ab97fe8369364379bb283f77cf2a31c0') # Kept for potential future use

# --- Strategy Parameters ---
SCORE_THRESHOLD = 75
DAYS_OF_DATA = 120 # For chart generation