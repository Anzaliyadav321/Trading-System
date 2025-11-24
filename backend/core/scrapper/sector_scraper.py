
"""
Sector Scraper for Merolagani
==============================
One-time script to scrape sector information for all NEPSE symbols.

Generates:
1. sectors.json - Complete sector-to-symbol mapping
2. sector_list.json - Simple list for dropdown
3. Updates Master_data.csv with sector column

"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
from pathlib import Path
from datetime import datetime

# Configuration
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MASTER_CSV = DATA_DIR / "Master_data.csv"
SECTORS_JSON = DATA_DIR / "sectors.json"
SECTOR_LIST_JSON = DATA_DIR / "sector_list.json"

BASE_URL = "https://merolagani.com/CompanyDetail.aspx?symbol={}"
REQUEST_DELAY = 2  # Seconds between requests (be nice to server)

# Sector name normalization (Merolagani might have variations)
SECTOR_ALIASES = {
    "Commercial Bank": "Commercial Banks",
    "Development Bank": "Development Banks",
    "Finance": "Finance Companies",
    "Hydro Power": "Hydro Power",
    "HydroPower": "Hydro Power",
    "Hotels": "Hotels And Tourism",
    "Hotel": "Hotels And Tourism",
    "Manufacturing": "Manufacturing And Processing",
    "Life Insurance": "Life Insurance",
    "Non Life Insurance": "Non-Life Insurance",
    "Non-life Insurance": "Non-Life Insurance",
    "Micro Finance": "Microfinance",
    "MicroFinance": "Microfinance",
    "Mutual Fund": "Mutual Funds",
    "Investment": "Investment Companies",
    "Trading": "Trading",
    "Others": "Others"
}


def normalize_sector_name(sector):
    """Normalize sector name to standard format"""
    if not sector:
        return "Others"
    
    sector = sector.strip()
    
    # Check if it's an alias
    for alias, standard in SECTOR_ALIASES.items():
        if alias.lower() in sector.lower():
            return standard
    
    return sector


def scrape_sector_for_symbol(symbol):
    """
    Scrape sector information for a single symbol.
    
    Returns:
        str: Sector name or 'Others' if not found
    """
    url = BASE_URL.format(symbol)
    
    try:
        print(f"  Fetching {symbol}...", end=" ")
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Strategy 1: Look for "Sector:" label in tables
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                for i, cell in enumerate(cells):
                    cell_text = cell.get_text(strip=True)
                    if 'sector' in cell_text.lower() and i + 1 < len(cells):
                        sector = cells[i + 1].get_text(strip=True)
                        sector = normalize_sector_name(sector)
                        print(f"✓ {sector}")
                        return sector
        
        # Strategy 2: Look for div with sector info
        sector_divs = soup.find_all('div', class_=['sector', 'company-sector'])
        if sector_divs:
            sector = sector_divs[0].get_text(strip=True)
            sector = normalize_sector_name(sector)
            print(f"✓ {sector}")
            return sector
        
        # Strategy 3: Look for "Sector" in any text
        all_text = soup.get_text()
        if 'Sector:' in all_text:
            # Try to extract sector after "Sector:"
            lines = all_text.split('\n')
            for i, line in enumerate(lines):
                if 'Sector:' in line:
                    # Check next few lines for sector name
                    for j in range(i, min(i+3, len(lines))):
                        potential_sector = lines[j].replace('Sector:', '').strip()
                        if potential_sector and len(potential_sector) > 2:
                            sector = normalize_sector_name(potential_sector)
                            print(f"{sector}")
                            return sector
        
        print("⚠ Not found, marking as 'Others'")
        return "Others"
        
    except requests.exceptions.RequestException as e:
        print(f"✗ Error: {e}")
        return "Others"
    except Exception as e:
        print(f"✗ Parse Error: {e}")
        return "Others"


def test_scraper():
    """Test scraper with a few known symbols"""
    print("\n" + "="*80)
    print("TESTING SCRAPER WITH SAMPLE SYMBOLS")
    print("="*80 + "\n")
    
    test_symbols = ["NABIL", "UPPER", "OHL", "CHDC", "GBIME"]
    
    for symbol in test_symbols:
        sector = scrape_sector_for_symbol(symbol)
        print(f"  Result: {symbol} → {sector}\n")
        time.sleep(REQUEST_DELAY)
    
    print("\n" + "="*80)
    response = input("Does the above look correct? (yes/no): ")
    
    return response.lower() in ['yes', 'y']


def scrape_all_sectors():
    """
    Main scraping function.
    Scrapes all symbols from Master_data.csv
    """
    print("\n" + "="*80)
    print("SECTOR SCRAPER - FULL RUN")
    print("="*80 + "\n")
    
    # Load symbols from Master_data.csv
    if not MASTER_CSV.exists():
        print(f"[ERROR] Master_data.csv not found at {MASTER_CSV}")
        print("Please run historical scraper first!")
        return None
    
    print(f"[INFO] Loading symbols from {MASTER_CSV}...")
    df = pd.read_csv(MASTER_CSV)
    
    if 'symbol' not in df.columns:
        print("[ERROR] 'symbol' column not found in Master_data.csv")
        return None
    
    symbols = df['symbol'].unique()
    total = len(symbols)
    
    print(f"[INFO] Found {total} unique symbols\n")
    print(f"[INFO] Estimated time: {total * REQUEST_DELAY / 60:.1f} minutes")
    print(f"[INFO] Start time: {datetime.now().strftime('%H:%M:%S')}\n")
    
    response = input("Ready to start scraping? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Aborted by user")
        return None
    
    print("\n" + "="*80)
    print("SCRAPING IN PROGRESS...")
    print("="*80 + "\n")
    
    # Dictionary to store symbol → sector mapping
    symbol_to_sector = {}
    failed_symbols = []
    
    for i, symbol in enumerate(symbols, 1):
        print(f"[{i}/{total}]", end=" ")
        
        sector = scrape_sector_for_symbol(symbol)
        symbol_to_sector[symbol] = sector
        
        if sector == "Others":
            failed_symbols.append(symbol)
        
        # Rate limiting
        time.sleep(REQUEST_DELAY)
        
        # Progress update every 20 symbols
        if i % 20 == 0:
            elapsed = i * REQUEST_DELAY / 60
            remaining = (total - i) * REQUEST_DELAY / 60
            print(f"\n  Progress: {i}/{total} ({i/total*100:.1f}%)")
            print(f"  Elapsed: {elapsed:.1f} min, Remaining: ~{remaining:.1f} min\n")
    
    print("\n" + "="*80)
    print("SCRAPING COMPLETE!")
    print("="*80 + "\n")
    
    print(f"[INFO] Successfully scraped: {total - len(failed_symbols)} symbols")
    print(f"[INFO] Failed/Unknown: {len(failed_symbols)} symbols")
    
    if failed_symbols:
        print(f"\n[WARNING] Symbols marked as 'Others': {', '.join(failed_symbols[:10])}")
        if len(failed_symbols) > 10:
            print(f"          ... and {len(failed_symbols) - 10} more")
    
    return symbol_to_sector


def build_sector_mapping(symbol_to_sector):
    """
    Build sector → symbols mapping from symbol → sector mapping
    
    Returns:
        dict: {sector: {symbols: [...], count: N, description: "..."}}
    """
    sectors = {}
    
    for symbol, sector in symbol_to_sector.items():
        if sector not in sectors:
            sectors[sector] = {
                "symbols": [],
                "count": 0,
                "description": ""
            }
        
        sectors[sector]["symbols"].append(symbol)
        sectors[sector]["count"] += 1
    
    # Sort symbols within each sector
    for sector in sectors:
        sectors[sector]["symbols"].sort()
    
    # Add descriptions
    descriptions = {
        "Commercial Banks": "Commercial banking institutions",
        "Development Banks": "Development banking institutions",
        "Finance Companies": "Finance and leasing companies",
        "Hydro Power": "Hydroelectric power generation companies",
        "Hotels And Tourism": "Hotels and tourism services",
        "Manufacturing And Processing": "Manufacturing and processing industries",
        "Life Insurance": "Life insurance companies",
        "Non-Life Insurance": "General insurance companies",
        "Microfinance": "Microfinance institutions",
        "Mutual Funds": "Mutual fund schemes",
        "Investment Companies": "Investment and holding companies",
        "Trading": "Trading companies",
        "Others": "Other companies"
    }
    
    for sector in sectors:
        if sector in descriptions:
            sectors[sector]["description"] = descriptions[sector]
    
    return sectors


def save_outputs(symbol_to_sector, sectors):
    """
    Save all output files:
    1. sectors.json
    2. sector_list.json
    3. Update Master_data.csv
    """
    print("\n" + "="*80)
    print("SAVING OUTPUT FILES...")
    print("="*80 + "\n")
    
    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Save sectors.json (complete mapping)
    print("[1/3] Saving sectors.json...")
    with open(SECTORS_JSON, 'w', encoding='utf-8') as f:
        json.dump(sectors, f, indent=2, ensure_ascii=False)
    print(f"      Saved to {SECTORS_JSON}")
    
    # 2. Save sector_list.json (just sector names)
    print("[2/3] Saving sector_list.json...")
    sector_names = sorted([s for s in sectors.keys() if s != "Others"]) + ["Others"]
    with open(SECTOR_LIST_JSON, 'w', encoding='utf-8') as f:
        json.dump(sector_names, f, indent=2, ensure_ascii=False)
    print(f"      Saved to {SECTOR_LIST_JSON}")
    
    # 3. Update Master_data.csv with sector column
    print("[3/3] Updating Master_data.csv with sector column...")
    df = pd.read_csv(MASTER_CSV)
    
    # Add sector column by mapping symbols
    df['sector'] = df['symbol'].map(symbol_to_sector)
    
    # Fill any missing sectors with "Others"
    df['sector'].fillna("Others", inplace=True)
    
    # Save back to CSV
    df.to_csv(MASTER_CSV, index=False)
    print(f"      Updated {MASTER_CSV} with sector column")
    
    print("\n" + "="*80)
    print("ALL FILES SAVED SUCCESSFULLY!")
    print("="*80 + "\n")


def print_summary(sectors):
    """Print summary statistics"""
    print("\n" + "="*80)
    print("SECTOR SUMMARY")
    print("="*80 + "\n")
    
    # Sort sectors by symbol count (descending)
    sorted_sectors = sorted(sectors.items(), key=lambda x: x[1]["count"], reverse=True)
    
    total_symbols = sum(s[1]["count"] for s in sorted_sectors)
    
    print(f"Total Sectors: {len(sorted_sectors)}")
    print(f"Total Symbols: {total_symbols}\n")
    
    print(f"{'Sector':<35} {'Symbols':>8}")
    print("-" * 45)
    
    for sector, data in sorted_sectors:
        print(f"{sector:<35} {data['count']:>8}")
    
    print("\n" + "="*80)


def main():
    """Main execution flow"""
    print("\n" + "="*80)
    print("MEROLAGANI SECTOR SCRAPER")
    print("="*80)
    print("\nThis script will:")
    print("  1. Test scraper with 5 sample symbols")
    print("  2. Scrape sectors for all symbols in Master_data.csv")
    print("  3. Generate sectors.json (complete mapping)")
    print("  4. Generate sector_list.json (dropdown data)")
    print("  5. Update Master_data.csv with sector column")
    print("\n" + "="*80 + "\n")
    
    # Test first
    if not test_scraper():
        print("\n[INFO] Scraper test failed or aborted by user")
        return
    
    # Full scrape
    symbol_to_sector = scrape_all_sectors()
    
    if not symbol_to_sector:
        print("[ERROR] Scraping failed")
        return
    
    # Build sector mapping
    sectors = build_sector_mapping(symbol_to_sector)
    
    # Save outputs
    save_outputs(symbol_to_sector, sectors)
    
    # Print summary
    print_summary(sectors)
    
    print("\n SECTOR SCRAPING COMPLETE!")
   


if __name__ == "__main__":
    main()