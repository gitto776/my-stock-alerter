import mplfinance as mpf
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os

# Define a temporary directory for saving images
WRITABLE_DIR = "/tmp/"

def generate_annotated_chart(df, ticker, entry_price, sl_price, tgt_price):
    filename = os.path.join(WRITABLE_DIR, f"{ticker}_chart.png")
    
    buy_marker = [np.nan] * len(df)
    buy_marker[-1] = df['low'].iloc[-1] * 0.98
    buy_plot = mpf.make_addplot(buy_marker, type='scatter', marker='^', color='green', markersize=200)

    mpf.plot(df, type='candle', style='yahoo', title=f'{ticker} - Daily Chart Plan',
             volume=True, mav=(21, 50), addplot=buy_plot,
             hlines=dict(hlines=[tgt_price, sl_price], colors=['g', 'r'], linestyle='--'),
             savefig=filename)
    return filename

def generate_datasheet_image(ticker, score, pattern, sl, tgt):
    filename = os.path.join(WRITABLE_DIR, f"{ticker}_datasheet.png")
    img = Image.new('RGB', (800, 150), color='white')
    d = ImageDraw.Draw(img)
    
    try:
        title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 28)
        body_font = ImageFont.truetype("DejaVuSans.ttf", 22)
    except IOError:
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()

    d.text((10,10), f"Analysis for: {ticker}", fill='black', font=title_font)
    d.line((10, 50, 790, 50), fill='black', width=1)
    d.text((20, 60), f"Score: {score}/100", fill='green', font=body_font)
    d.text((20, 90), f"Pattern: {pattern}", fill='black', font=body_font)
    d.text((400, 60), f"Target: {tgt:.2f}", fill='darkgreen', font=body_font)
    d.text((400, 90), f"Stop-Loss: {sl:.2f}", fill='darkred', font=body_font)
    img.save(filename)
    return filename

def create_composite_image(chart_file, datasheet_file, ticker):
    filename = os.path.join(WRITABLE_DIR, f"{ticker}_composite.png")
    img1 = Image.open(chart_file)
    img2 = Image.open(datasheet_file)

    composite_img = Image.new('RGB', (img1.width, img1.height + img2.height), 'white')
    composite_img.paste(img1, (0, 0))
    composite_img.paste(img2, (0, img1.height))
    composite_img.save(filename)
    
    os.remove(chart_file)
    os.remove(datasheet_file)
    
    return filename