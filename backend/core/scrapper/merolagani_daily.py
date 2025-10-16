#!/usr/bin/env python
# coding: utf-8

# In[1]:


import requests
import pandas as pd
import re
from datetime import datetime
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings('ignore')


# In[2]:


class MeroLaganiDailyScraper:
    """
    MeroLagani Daily Scraper (latest market data for today)
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
        })

    def clean_number(self, text):
        """Convert numbers like 2.5K into numeric"""
        if not text or text in ['', '-', 'N/A', 'null', None, '--', 'n/a']:
            return None
        try:
            text_str = str(text).strip().upper()
            multiplier = 1
            if text_str.endswith('K'):
                multiplier = 1000
                text_str = text_str[:-1]
            elif text_str.endswith('M'):
                multiplier = 1000000
                text_str = text_str[:-1]
            elif text_str.endswith('B'):
                multiplier = 1000000000
                text_str = text_str[:-1]
            cleaned = re.sub(r'[^\d.-]', '', text_str)
            if cleaned and cleaned not in ['-', '.', '']:
                return float(cleaned) * multiplier
        except:
            pass
        return None

    def scrape_today(self):
        """Scrape MeroLagani latest market data for today"""
        today = datetime.now().strftime('%Y-%m-%d')
        url = "https://merolagani.com/LatestMarket.aspx"

        try:
            response = self.session.get(url, timeout=20)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                tables = soup.find_all('table')

                for table in tables:
                    rows = table.find_all('tr')
                    if len(rows) > 5:
                        stocks = []
                        header_found = False
                        for row in rows:
                            cells = [c.get_text(strip=True) for c in row.find_all(['td', 'th'])]
                            if not cells:
                                continue
                            if any("symbol" in c.lower() for c in cells):
                                header_found = True
                                continue
                            if header_found and len(cells) >= 7:
                                symbol = None
                                if re.match(r'^[A-Z]{3,10}$', cells[0].strip()):
                                    symbol = cells[0].strip()
                                if symbol:
                                    stock = {
                                        'date': today,
                                        'symbol': symbol,
                                        'close': self.clean_number(cells[1]),
                                        'change_percent': self.clean_number(cells[2]),
                                        'open': self.clean_number(cells[3]),
                                        'high': self.clean_number(cells[4]),
                                        'low': self.clean_number(cells[5]),
                                        'volume': self.clean_number(cells[6]),
                                        'source': 'merolagani_daily',
                                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                    }
                                    if stock['close'] is not None:
                                        stocks.append(stock)
                        if stocks:
                            return pd.DataFrame(stocks)
        except Exception as e:
            print("Daily scrape error:", e)
            return pd.DataFrame()

        return pd.DataFrame()

    def save_data(self, df, filename=None):
        """Save today’s data"""
        if df.empty:
            print("No daily data to save")
            return None
        if not filename:
            today = datetime.now().strftime('%Y%m%d')
            filename = f"MeroLagani_Daily_{today}.csv"
        df.to_csv(filename, index=False)
        print(f"Daily data saved to {filename}")
        return filename


# In[3]:


# ------------------ USAGE ------------------
if __name__ == "__main__":
    scraper = MeroLaganiDailyScraper()
    df = scraper.scrape_today()
    if not df.empty:
        print(f"Collected {len(df)} records for today")
        scraper.save_data(df, filename="D:/TRADING_SYSTEM/backend/core/data/MeroLagani_Daily.csv")
        print(df.head())
    else:
        print("Failed to fetch daily data")


# In[ ]:




