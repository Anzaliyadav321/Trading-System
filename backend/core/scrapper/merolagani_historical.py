#backend/core/scrapper/merolagani_historical.py
import requests
import pandas as pd
import re
import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings('ignore')



class MeroLaganiHistoricalScraper:
    """
    MeroLagani Historical Data Scraper (1 Year)
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
        })
        self.all_data = []

    def clean_number(self, text):
        """Handle numbers with K/M/B suffixes"""
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

    def get_trading_dates(self, start_date, end_date):
        """Generate list of trading days (skip Fri & Sat in Nepal + major holidays)"""
        dates = []
        current = start_date
        holidays = ['2024-01-01', '2024-04-13', '2024-10-24', '2024-11-12']
        while current <= end_date:
            if current.weekday() not in [4, 5]:  # Fri, Sat
                if current.strftime('%Y-%m-%d') not in holidays:
                    dates.append(current)
            current += timedelta(days=1)
        return dates

    def scrape_merolagani_historical(self, date):
        """Scrape MeroLagani data for a given date"""
        date_str = date.strftime('%Y-%m-%d')
        urls = [
            f"https://merolagani.com/LatestMarket.aspx?date={date_str}",
            f"https://www.merolagani.com/LatestMarket.aspx?date={date_str}"
        ]

        for url in urls:
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
                                            'date': date_str,
                                            'symbol': symbol,
                                            'close': self.clean_number(cells[1]),
                                            'change_percent': self.clean_number(cells[2]),
                                            'open': self.clean_number(cells[3]),
                                            'high': self.clean_number(cells[4]),
                                            'low': self.clean_number(cells[5]),
                                            'volume': self.clean_number(cells[6]),
                                            'source': 'merolagani_historical',
                                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                        }
                                        if stock['close'] is not None:
                                            stocks.append(stock)
                            if stocks:
                                return stocks
            except:
                continue
        return None

    def scrape_year_data(self, start_date=None, end_date=None, delay_seconds=2):
        """Fetch 1 year of data"""
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=365)

        trading_dates = self.get_trading_dates(start_date, end_date)
        print(f"\n{'='*80}")
        print(f"STARTING HISTORICAL DATA COLLECTION")
        print(f"{'='*80}")
        print(f"Date Range: {start_date.date()} to {end_date.date()}")
        print(f"Trading Days: {len(trading_dates)}")
        print(f"Estimated Time: ~{len(trading_dates) * delay_seconds / 60:.1f} minutes")
        print(f"{'='*80}\n")
        
        for i, date in enumerate(trading_dates):
            print(f"[{i+1}/{len(trading_dates)}] Scraping {date.strftime('%Y-%m-%d')}...", end=' ')
            day_data = self.scrape_merolagani_historical(date)
            if day_data:
                self.all_data.extend(day_data)
                print(f"Got {len(day_data)} stocks")
            else:
                print("No data")
            time.sleep(delay_seconds)
        
        print(f"\n{'='*80}")
        print(f"COLLECTION COMPLETE")
        print(f"Total Records: {len(self.all_data)}")
        print(f"{'='*80}\n")
        
        return self.get_dataframe()

    def get_dataframe(self):
        """Return cleaned DataFrame with standardized schema"""
        if not self.all_data:
            return pd.DataFrame()
        df = pd.DataFrame(self.all_data)
        df['date'] = pd.to_datetime(df['date'], errors="coerce")
        df = df.drop_duplicates(subset=['symbol', 'date'])
        df = df.sort_values(['date', 'symbol']).reset_index(drop=True)

        # Ensure expected schema
        expected = ["date", "symbol", "open", "high", "low", "close",
                    "volume", "change_percent", "source", "timestamp"]
        df = df[[c for c in expected if c in df.columns]]
        return df

    def save_data(self, df, filename=None):
        """Save standardized historical data"""
        if df.empty:
            print("No data to save")
            return None
        if not filename:
            start_date = df['date'].min().strftime('%Y%m%d')
            end_date = df['date'].max().strftime('%Y%m%d')
            filename = f"MeroLagani_Historical_{start_date}_to_{end_date}.csv"
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")
        print(f"Total records: {len(df)}")
        print(f" Date range: {df['date'].min().date()} to {df['date'].max().date()}")
        print(f" Unique symbols: {df['symbol'].nunique()}")
        return filename

# ------------------ USAGE ------------------
if __name__ == "__main__":
    scraper = MeroLaganiHistoricalScraper()
    
    # Define date range - ONE YEAR for production
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    print("\nNEPSE HISTORICAL DATA SCRAPER")
    print("="*80)
    print(f"Production Mode: Collecting 1 year of data")
    print(f"Start Date: {start_date.date()}")
    print(f"End Date: {end_date.date()}")
    print("="*80)

    # Fetch with custom range
    df = scraper.scrape_year_data(
        start_date=start_date, 
        end_date=end_date, 
        delay_seconds=2  # 2 seconds between requests
    )
    
    if not df.empty:
        # FIXED PATH - Save to correct location
        output_path = "D:/Trading_system/backend/core/data/master_data.csv"
        scraper.save_data(df, filename=output_path)
        
        print("\n" + "="*80)
        print("SUCCESS - Historical data collection complete!")
        print("="*80)
        print(f"\nNext Steps:")
        print("1. Run pipeline to calculate indicators")
        print("2. Test /signals/today endpoint")
        print("3. Verify Component 7 shows data")
        print("="*80 + "\n")
    else:
        print("\n FAILED - No historical data collected")
        print("Check internet connection and try again\n")




# # chukul.com
# # backend/scripts/get_real_data.py
# import requests
# import pandas as pd
# from datetime import datetime, timedelta
# from bs4 import BeautifulSoup
# import time
# import re

# def try_nepse_official():
#     """Try NEPSE official API"""
#     print("\n[1] Trying NEPSE Official API...")
    
#     try:
#         url = "https://www.nepalstock.com/api/nots/nepse-data"
#         response = requests.get(url, timeout=10, verify=False)
        
#         if response.status_code == 200:
#             data = response.json()
#             print(f"✓ Got data from NEPSE Official")
#             return data
#     except:
#         pass
    
#     print("✗ NEPSE Official failed")
#     return None

# def try_merolagani_today():
#     """Try MeroLagani today's data"""
#     print("\n[2] Trying MeroLagani...")
    
#     try:
#         url = "https://merolagani.com/handlers/TechnicalChartHandler.ashx?type=get_market_summary"
#         response = requests.get(url, timeout=10)
        
#         if response.status_code == 200:
#             data = response.json()
            
#             stocks = []
#             today = datetime.now().strftime('%Y-%m-%d')
            
#             for item in data:
#                 try:
#                     stock = {
#                         'date': today,
#                         'symbol': item.get('s', ''),
#                         'open': float(item.get('o', 0) or 0),
#                         'high': float(item.get('h', 0) or 0),
#                         'low': float(item.get('l', 0) or 0),
#                         'close': float(item.get('c', 0) or 0),
#                         'volume': float(item.get('v', 0) or 0),
#                         'change_percent': float(item.get('ch', 0) or 0),
#                         'source': 'merolagani',
#                         'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#                     }
                    
#                     if stock['symbol'] and stock['close'] > 0:
#                         stocks.append(stock)
#                 except:
#                     continue
            
#             if stocks:
#                 print(f"✓ Got {len(stocks)} stocks from MeroLagani")
#                 return stocks
                
#     except Exception as e:
#         print(f"✗ MeroLagani failed: {e}")
    
#     return None

# def try_sharesansar():
#     """Try ShareSansar"""
#     print("\n[3] Trying ShareSansar...")
    
#     try:
#         url = "https://www.sharesansar.com/today-share-price"
#         headers = {
#             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
#         }
        
#         response = requests.get(url, headers=headers, timeout=15)
        
#         if response.status_code == 200:
#             soup = BeautifulSoup(response.content, 'html.parser')
            
#             # Find table with stock data
#             tables = soup.find_all('table')
            
#             for table in tables:
#                 rows = table.find_all('tr')
                
#                 if len(rows) < 10:
#                     continue
                
#                 stocks = []
#                 today = datetime.now().strftime('%Y-%m-%d')
                
#                 for row in rows[1:]:
#                     cells = [c.get_text(strip=True) for c in row.find_all('td')]
                    
#                     if len(cells) < 5:
#                         continue
                    
#                     symbol = cells[0].strip()
                    
#                     if not re.match(r'^[A-Z]{3,10}$', symbol):
#                         continue
                    
#                     def clean_num(val):
#                         if not val or val == '-':
#                             return 0
#                         val = re.sub(r'[^\d.]', '', val)
#                         return float(val) if val else 0
                    
#                     stock = {
#                         'date': today,
#                         'symbol': symbol,
#                         'close': clean_num(cells[1]) if len(cells) > 1 else 0,
#                         'open': clean_num(cells[2]) if len(cells) > 2 else 0,
#                         'high': clean_num(cells[3]) if len(cells) > 3 else 0,
#                         'low': clean_num(cells[4]) if len(cells) > 4 else 0,
#                         'volume': clean_num(cells[5]) if len(cells) > 5 else 100000,
#                         'change_percent': 0,
#                         'source': 'sharesansar',
#                         'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#                     }
                    
#                     if stock['close'] > 0:
#                         stocks.append(stock)
                
#                 if len(stocks) > 20:
#                     print(f"✓ Got {len(stocks)} stocks from ShareSansar")
#                     return stocks
                    
#     except Exception as e:
#         print(f"✗ ShareSansar failed: {e}")
    
#     return None

# def generate_historical_from_today(today_data, days=90):
#     """
#     Generate historical data from today's snapshot
#     Creates realistic variations going backwards
#     """
#     print(f"\n[4] Generating {days} days of historical data from today's snapshot...")
    
#     all_data = []
    
#     for stock in today_data:
#         symbol = stock['symbol']
#         current_price = stock['close']
#         current_volume = stock['volume']
        
#         # Generate backwards from today
#         for i in range(days):
#             date = (datetime.now() - timedelta(days=days-1-i)).strftime('%Y-%m-%d')
#             date_obj = datetime.strptime(date, '%Y-%m-%d')
            
#             # Skip weekends
#             if date_obj.weekday() in [4, 5]:
#                 continue
            
#             # Create realistic price movement
#             # More variation in the past, converging to current price
#             days_from_today = days - i
#             max_variation = 0.15 * (days_from_today / days)  # Up to 15% variation
            
#             import random
#             price_factor = 1 + random.uniform(-max_variation, max_variation)
#             daily_noise = random.uniform(-0.02, 0.02)
            
#             close = current_price * price_factor * (1 + daily_noise)
            
#             # OHLC
#             intraday_range = random.uniform(0.005, 0.015)
#             open_p = close * (1 + random.uniform(-0.01, 0.01))
#             high = max(open_p, close) * (1 + random.uniform(0, intraday_range))
#             low = min(open_p, close) * (1 - random.uniform(0, intraday_range))
            
#             # Volume variation
#             volume = current_volume * random.uniform(0.5, 1.5)
            
#             historical_stock = {
#                 'date': date,
#                 'symbol': symbol,
#                 'open': round(open_p, 2),
#                 'high': round(high, 2),
#                 'low': round(low, 2),
#                 'close': round(close, 2),
#                 'volume': round(volume, 0),
#                 'change_percent': 0,
#                 'source': stock['source'] + '_historical',
#                 'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#             }
            
#             all_data.append(historical_stock)
    
#     print(f"✓ Generated {len(all_data)} historical records")
#     return all_data

# def main():
#     """
#     Try multiple sources and generate historical data
#     """
#     print("="*80)
#     print("MULTI-SOURCE REAL DATA COLLECTOR")
#     print("="*80)
    
#     # Try to get today's data from any source
#     today_data = None
    
#     sources = [
#         try_merolagani_today,
#         try_sharesansar,
#         try_nepse_official
#     ]
    
#     for source_func in sources:
#         result = source_func()
#         if result:
#             today_data = result
#             break
    
#     if not today_data:
#         print("\n❌ All data sources failed!")
#         print("\nPlease check:")
#         print("1. Internet connection")
#         print("2. Try again in a few minutes")
#         print("3. Or use the test data generator from earlier")
#         return None
    
#     print(f"\n✓ Successfully got today's data with {len(today_data)} stocks")
    
#     # Generate historical data
#     historical_data = generate_historical_from_today(today_data, days=90)
    
#     # Combine
#     all_data = historical_data + today_data
    
#     # Create DataFrame
#     df = pd.DataFrame(all_data)
#     df['date'] = pd.to_datetime(df['date'])
    
#     # Calculate change_percent
#     df = df.sort_values(['symbol', 'date'])
#     df['prev_close'] = df.groupby('symbol')['close'].shift(1)
#     df['change_percent'] = ((df['close'] - df['prev_close']) / df['prev_close'] * 100).round(2)
#     df = df.drop('prev_close', axis=1)
    
#     # Remove duplicates
#     df = df.drop_duplicates(subset=['symbol', 'date'])
#     df = df.sort_values(['date', 'symbol']).reset_index(drop=True)
    
#     # Save
#     output_path = "D:/Trading_system/backend/core/data/master_data.csv"
#     df.to_csv(output_path, index=False)
    
#     print(f"\n{'='*80}")
#     print("✅ DATA SAVED SUCCESSFULLY")
#     print(f"{'='*80}")
#     print(f"File: {output_path}")
#     print(f"Total records: {len(df)}")
#     print(f"Symbols: {df['symbol'].nunique()}")
#     print(f"Trading days: {df['date'].nunique()}")
#     print(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    
#     # Validate
#     print(f"\n{'='*80}")
#     print("DATA QUALITY - PO'S STOCKS")
#     print(f"{'='*80}")
    
#     for symbol in ['NMB', 'SCB', 'NABBC', 'RNLI', 'SARBTM', 'SONA']:
#         if symbol in df['symbol'].values:
#             symbol_data = df[df['symbol'] == symbol]
#             print(f"{symbol}: {len(symbol_data)} days, Latest: ₹{symbol_data['close'].iloc[-1]:.2f}")
    
#     print(f"\n{'='*80}")
#     print("NEXT STEPS")
#     print(f"{'='*80}")
#     print("\n1. Delete old signal files:")
#     print("   del backend\\core\\data\\all_signals.csv")
#     print("   del backend\\core\\data\\buy_signals.csv")
#     print("\n2. Run signal generation script")
#     print("\n3. Start backend: python -m uvicorn backend.main:app --reload --port 8000")
#     print("\n4. Start frontend: cd frontend && npm start")
#     print("="*80)
    
#     return df

# if __name__ == "__main__":
#     main()