class Config:
    """Configuration settings for stock analysis"""

    # Paths
    EXCEL_FILE_PATH = 'data/input.xlsx'

    # Fundamental metrics configuration
    WEIGHTS = {
        'roe': 0.25,              # Return on Equity
        'debt_to_equity': 0.15,   # Debt-to-Equity Ratio
        'net_profit_margin': 0.20,# Net Profit Margin
        'current_ratio': 0.10,    # Current Ratio
        'interest_coverage': 0.15,# Interest Coverage Ratio
        'free_cash_flow': 0.15    # Free Cash Flow
    }

    THRESHOLDS = {
        'roe': 0.12,              # Min ROE (12%)
        'debt_to_equity': 2.0,    # Max Debt/Equity
        'net_profit_margin': 0.08,# Min Profit Margin (8%)
        'current_ratio': 1.2,     # Min Current Ratio
        'interest_coverage': 2.0, # Min Interest Coverage
        'free_cash_flow': -1e9    # Min Free Cash Flow
    }

    METRIC_DIRECTION = {
        'roe': 'higher',
        'debt_to_equity': 'lower',
        'net_profit_margin': 'higher',
        'current_ratio': 'higher',
        'interest_coverage': 'higher',
        'free_cash_flow': 'higher'
    }

    # Data sources priority
    DATA_SOURCES = [
        'yfinance_info',
        'yfinance_calculated',
        'screener'
    ]

    # Request headers for web scraping
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # Scraper rate limiting (seconds)
    SCRAPER_DELAY = 3

    # Display settings
    TOP_N_STOCKS = 10  # Number of top stocks to display