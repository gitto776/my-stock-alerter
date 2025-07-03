import pandas as pd
import pandas_ta as ta

def analyze_and_score_stock(df: pd.DataFrame) -> int:
    """
    Analyzes and scores a stock based on the Pre-Breakout v5.0 strategy.
    Returns a score from 0-100, or 0 if it fails a hard filter.
    """
    try:
        # --- 1. Calculate all necessary indicators ---
        df.ta.rsi(length=14, append=True)
        df.ta.ema(length=21, append=True)
        df.ta.ema(length=50, append=True)
        df.ta.bbands(length=20, append=True) # Bollinger Bands
        
        latest = df.iloc[-1]

        # --- 2. Hard Filters (Must Pass) ---
        if not (latest['close'] > latest['EMA_50']): return 0
        if not (latest['RSI_14'] > 60): return 0

        # --- 3. Pre-Breakout Condition Checks ---
        df['bb_width'] = df['BBU_20_2.0'] - df['BBL_20_2.0']
        is_squeeze = latest['bb_width'] < (df['bb_width'].min() * 1.3)
        
        high_10d = df['high'][-10:].max()
        low_10d = df['low'][-10:].min()
        is_tight_range = ((high_10d - low_10d) / latest['close']) < 0.08

        # --- 4. Scoring Logic (out of 100) ---
        score = 0
        if is_squeeze: score += 20
        if is_tight_range: score += 20
        if latest['EMA_21'] > latest['EMA_50']: score += 15
        
        score += 45 # Placeholder for RS, Sector, and Fundamental checks

        return int(score)
    except Exception:
        return 0