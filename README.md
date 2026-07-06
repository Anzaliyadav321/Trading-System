NEPSE Trading Signal System

An automated trading assistant for the Nepal Stock Exchange (NEPSE) that scrapes daily market data, calculates technical indicators, generates buy/sell signals, and tracks transactions with full bill-level detail (commissions, CGT, clearance) — all through a FastAPI backend and React frontend.

Features


* Daily Data Pipeline — Scrapes historical and daily OHLCV data for NEPSE-listed stocks and appends it to a master dataset.
* Technical Indicators — Calculates RSI, MACD, MACD Signal, and MA50 per symbol.
* Buy Signal Engine — Sequential rule-based logic (MA50 → RSI → MACD → Volume) with configurable thresholds.
* Sell Signal Engine — Priority-based logic .
* Bill-Level Transaction Tracking — Records full buy/sell bill details including broker commissions, SEBON fees, DP charges, and Capital Gain Tax .
* WT Authentication — Email/OTP-based signup and secure token-based login.
* Scheduled Automation — Background scheduler runs the daily scrape + signal pipeline automatically.
* React Frontend — Ticker views, signal analysis dashboards, order execution, and a bill/receipt viewer (Biller component).
