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