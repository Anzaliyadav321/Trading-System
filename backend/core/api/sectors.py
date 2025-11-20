"""
Sector API Endpoints
====================
Provides sector information to frontend for industry preferences feature.

Endpoints:
- GET /sectors/list - Get all sector names
- GET /sectors/symbols - Get symbols in a specific sector
- GET /sectors/info - Get sector info for a symbol
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
import json
from pathlib import Path

# Initialize router
router = APIRouter(prefix="/sectors", tags=["sectors"])

# Paths to data files
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SECTORS_JSON = DATA_DIR / "sectors.json"
SECTOR_LIST_JSON = DATA_DIR / "sector_list.json"

# In-memory cache (loaded on startup)
SECTORS_DATA = None
SECTOR_LIST = None


def load_sector_data():
    """Load sector data from JSON files into memory"""
    global SECTORS_DATA, SECTOR_LIST
    
    try:
        # Load complete sectors mapping
        if SECTORS_JSON.exists():
            with open(SECTORS_JSON, 'r', encoding='utf-8') as f:
                SECTORS_DATA = json.load(f)
            print(f"[INFO] Loaded {len(SECTORS_DATA)} sectors from sectors.json")
        else:
            print(f"[WARNING] sectors.json not found at {SECTORS_JSON}")
            SECTORS_DATA = {}
        
        # Load sector list
        if SECTOR_LIST_JSON.exists():
            with open(SECTOR_LIST_JSON, 'r', encoding='utf-8') as f:
                SECTOR_LIST = json.load(f)
            print(f"[INFO] Loaded {len(SECTOR_LIST)} sector names from sector_list.json")
        else:
            print(f"[WARNING] sector_list.json not found at {SECTOR_LIST_JSON}")
            SECTOR_LIST = list(SECTORS_DATA.keys()) if SECTORS_DATA else []
        
    except Exception as e:
        print(f"[ERROR] Failed to load sector data: {e}")
        SECTORS_DATA = {}
        SECTOR_LIST = []


# Load data on module import
load_sector_data()


@router.get("/list")
async def get_sector_list() -> List[str]:
    """
    Get list of all sector names.
    
    Used by: Frontend dropdown in industry preferences
    
    Returns:
        List of sector names (sorted alphabetically)
    
    Example:
        GET /sectors/list
        
        Response:
        [
          "Commercial Banks",
          "Development Banks",
          "Finance Companies",
          "Hydro Power",
          ...
        ]
    """
    if not SECTOR_LIST:
        raise HTTPException(
            status_code=503,
            detail="Sector data not available. Please run sector scraper."
        )
    
    return SECTOR_LIST


@router.get("/symbols")
async def get_sector_symbols(sector: str) -> Dict:
    """
    Get all symbols in a specific sector.
    
    Used by: Modal popup when user clicks sector in sidebar
    
    Args:
        sector: Sector name (e.g., "Commercial Banks")
    
    Returns:
        Dictionary with sector info and symbol list
    
    Example:
        GET /sectors/symbols?sector=Commercial%20Banks
        
        Response:
        {
          "sector": "Commercial Banks",
          "symbols": ["NABIL", "SCB", "GBIME", ...],
          "count": 25,
          "description": "Commercial banking institutions"
        }
    """
    if not SECTORS_DATA:
        raise HTTPException(
            status_code=503,
            detail="Sector data not available. Please run sector scraper."
        )
    
    if sector not in SECTORS_DATA:
        raise HTTPException(
            status_code=404,
            detail=f"Sector '{sector}' not found"
        )
    
    sector_data = SECTORS_DATA[sector]
    
    return {
        "sector": sector,
        "symbols": sector_data.get("symbols", []),
        "count": sector_data.get("count", 0),
        "description": sector_data.get("description", "")
    }


@router.get("/info")
async def get_symbol_sector(symbol: str) -> Dict:
    """
    Get sector information for a specific symbol.
    
    Used by: Stock details, tooltips, signal cards
    
    Args:
        symbol: Stock symbol (e.g., "NABIL")
    
    Returns:
        Dictionary with symbol and its sector
    
    Example:
        GET /sectors/info?symbol=NABIL
        
        Response:
        {
          "symbol": "NABIL",
          "sector": "Commercial Banks",
          "description": "Commercial banking institutions"
        }
    """
    if not SECTORS_DATA:
        raise HTTPException(
            status_code=503,
            detail="Sector data not available. Please run sector scraper."
        )
    
    # Search for symbol in all sectors
    for sector_name, sector_data in SECTORS_DATA.items():
        if symbol in sector_data.get("symbols", []):
            return {
                "symbol": symbol,
                "sector": sector_name,
                "description": sector_data.get("description", "")
            }
    
    # Symbol not found in any sector
    raise HTTPException(
        status_code=404,
        detail=f"Symbol '{symbol}' not found in any sector"
    )


@router.get("/stats")
async def get_sector_stats() -> Dict:
    """
    Get statistics about all sectors.
    
    Used by: Admin dashboard, analytics
    
    Returns:
        Dictionary with sector statistics
    
    Example:
        GET /sectors/stats
        
        Response:
        {
          "total_sectors": 13,
          "total_symbols": 210,
          "sectors": [
            {"name": "Commercial Banks", "count": 25},
            {"name": "Hydro Power", "count": 18},
            ...
          ]
        }
    """
    if not SECTORS_DATA:
        raise HTTPException(
            status_code=503,
            detail="Sector data not available. Please run sector scraper."
        )
    
    sector_stats = []
    total_symbols = 0
    
    for sector_name, sector_data in SECTORS_DATA.items():
        count = sector_data.get("count", 0)
        total_symbols += count
        sector_stats.append({
            "name": sector_name,
            "count": count,
            "description": sector_data.get("description", "")
        })
    
    # Sort by count (descending)
    sector_stats.sort(key=lambda x: x["count"], reverse=True)
    
    return {
        "total_sectors": len(SECTORS_DATA),
        "total_symbols": total_symbols,
        "sectors": sector_stats
    }


@router.post("/reload")
async def reload_sector_data() -> Dict:
    """
    Reload sector data from JSON files.
    
    Used by: Admin operations after updating sector files
    
    Returns:
        Status message
    
    Example:
        POST /sectors/reload
        
        Response:
        {
          "status": "success",
          "sectors_loaded": 13,
          "total_symbols": 210
        }
    """
    try:
        load_sector_data()
        
        total_symbols = sum(
            data.get("count", 0) 
            for data in SECTORS_DATA.values()
        ) if SECTORS_DATA else 0
        
        return {
            "status": "success",
            "sectors_loaded": len(SECTORS_DATA),
            "total_symbols": total_symbols,
            "message": "Sector data reloaded successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reload sector data: {str(e)}"
        )