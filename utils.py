from yahooquery import Ticker, Screener
import pandas as pd

from datetime import datetime, timedelta
from dotenv import load_dotenv
import yaml
import os
import logging
import warnings

load_dotenv()

warnings.filterwarnings("ignore")

logging.basicConfig(
    level=int(os.getenv('LOGGING_LEVEL')),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logging.getLogger("urllib3").setLevel(logging.ERROR)

with open("prompts.yaml", 'r', encoding="utf-8") as file:
    prompts = yaml.safe_load(file)

os.makedirs("data", exist_ok=True)


def get_top_n_companies(n=250):
    """
    Retrieves the top N most active companies from Yahoo Finance.
    
    Args:
        n (int, optional): Number of companies to retrieve. Defaults to 250.
        
    Returns:
        dict: Dictionary mapping company symbols to company names
    """
    s = Screener()
    results = s.get_screeners(['most_actives'], count=n)
    quotes = results['most_actives']['quotes']

    available_companies = {}
    for quote in quotes:
        symbol = quote.get('symbol', 'N/A')
        company_name = quote.get('shortName', 'N/A')
        available_companies[symbol] = company_name
        # logging.debug(f"{symbol}: {company_name}")
    return available_companies


def get_company_data(symbol):
    """
    Fetches comprehensive financial and market data for a company.
    
    Args:
        symbol (str): Stock symbol of the company
        
    Returns:
        dict: Company data including financial statements, market data, and historical prices
    """
    ticker = Ticker(symbol)
    modules = ["summaryDetail", "financialData", "quoteType", "defaultKeyStatistics", "earnings", "price",
               "recommendationTrend", "assetProfile"]
    data = ticker.get_modules(modules)
    data[symbol]['income_statement'] = ticker.income_statement(frequency='q', trailing=False)
    data[symbol]['balance_sheet'] = ticker.balance_sheet(frequency='q', trailing=False)
    data[symbol]['cash_flow'] = ticker.cash_flow(frequency='q', trailing=False)
    data[symbol]['historical_price'] = ticker.history(period='1y', interval='1d').reset_index()
    return data


def define_trend(regularMarketChange):
    """
    Determines market trend based on price change.
    
    Args:
        regularMarketChange (float): Daily market price change
        
    Returns:
        str: 'Uptrend', 'Downtrend', or 'Neutral'
    """
    if regularMarketChange > 0:
        return "Uptrend"
    elif regularMarketChange < 0:
        return "Downtrend"
    else:
        return "Neutral"


def get_eps_trend(df):
    """
    Extracts Basic EPS trends from income statement data.
    
    Args:
        df (DataFrame): Income statement DataFrame
        
    Returns:
        dict: Mapping of dates to Basic EPS values, excluding TTM periods
    """
    result = {
        row['asOfDate']: row['BasicEPS']
        for _, row in df.iterrows()
        if row['periodType'] != "TTM" and not pd.isna(row['BasicEPS'])
    }
    return result


def compute_financial_metrics(balance_sheet_df, cashflow_df):
    """
    Calculates key financial metrics from balance sheet and cash flow data.
    
    Args:
        balance_sheet_df (DataFrame): Balance sheet data
        cashflow_df (DataFrame): Cash flow data
        
    Returns:
        dict: Financial ratios and metrics including debt-to-equity, liquidity ratios,
              and cash flow metrics indexed by date
    """
    # Merge both DataFrames on 'asOfDate' to align data
    merged_df = pd.merge(balance_sheet_df, cashflow_df, on="asOfDate", how="inner")

    # Compute financial ratios
    new_df = {
        'asOfDate': merged_df.get("asOfDate", 0),
        'Debt-to-Equity': merged_df.get("TotalDebt", 0) / merged_df.get("StockholdersEquity", 0),
        "Current Ratio": merged_df.get("CurrentAssets", 0) / merged_df.get("CurrentLiabilities", 0),
        "Quick Ratio": (merged_df.get("CurrentAssets", 0) - merged_df.get("Inventory", 0)) / merged_df.get("CurrentLiabilities", 0),
        "Total assets": merged_df.get("TotalAssets", 0), "liabilities": merged_df.get("TotalLiabilitiesNetMinorityInterest", 0),
        "Free cash flow (FCF)": merged_df.get("OperatingCashFlow", 0) - merged_df.get("CapitalExpenditure", 0),
        "operating cash flow": merged_df.get("OperatingCashFlow", 0)
    }

    # Compute debt levels
    short_term_debt = merged_df.get("CurrentDebt", 0)
    long_term_debt = merged_df.get("LongTermDebt", 0)
    total_debt = short_term_debt + long_term_debt
    new_df["debt levels"] = [
        {"Short-Term Debt": std, "Long-Term Debt": ltd, "Total Debt": td}
        for std, ltd, td in zip(short_term_debt, long_term_debt, total_debt)
    ]

    new_df = pd.DataFrame(new_df)
    threshold = int(0.5 * new_df.shape[1])  # 50% of total columns
    new_df = new_df.dropna(thresh=threshold)

    result_dict = new_df.set_index("asOfDate").to_dict(orient="index")

    return result_dict


def define_sentiment(historical_data, threshold=1.05):
    """
    Determines market sentiment using moving averages.
    
    Args:
        historical_data (DataFrame): Historical price data with SMA calculations
        threshold (float, optional): Threshold for sentiment determination. Defaults to 1.05.
        
    Returns:
        str: 'Bullish', 'Bearish', or 'Neutral'
    """
    six_months_ago = (datetime.today() - timedelta(days=6 * 30)).date()
    filtered_df = historical_data[historical_data['date'] >= six_months_ago]
    bearish_score = filtered_df['SMA_200'].mean()
    bullish_score = filtered_df['SMA_50'].mean()
    if bullish_score > bearish_score * threshold:
        sentiment = "Bullish"
    elif threshold * bullish_score < bearish_score:
        sentiment = "Bearish"
    else:
        sentiment = "Neutral"
    return sentiment


def process_historical_data(real_historical_data):
    """
    Processes historical price data to calculate technical indicators.
    
    Args:
        real_historical_data (DataFrame): Raw historical price data
        
    Returns:
        DataFrame: Processed data with daily returns, volatility, and moving averages
    """
    historical_data = real_historical_data.copy()
    historical_data['date'] = pd.to_datetime(historical_data['date'], utc=True).dt.tz_convert(None)
    historical_data['date'] = historical_data['date'].dt.date
    historical_data['daily_return'] = historical_data['close'].pct_change()
    historical_data['rolling_volatility'] = historical_data['daily_return'].rolling(window=30).std() * (252 ** 0.5)
    historical_data['SMA_50'] = historical_data['close'].rolling(window=50).mean()
    historical_data['SMA_200'] = historical_data['close'].rolling(window=200).mean()

    return historical_data


def filter_financial_summary(historical_data):
    """
    Extracts key financial metrics from historical data.
    
    Args:
        historical_data (DataFrame): Processed historical price data
        
    Returns:
        dict: Transposed dictionary of date, close price, daily return, and volatility
    """
    result = historical_data[['date', 'close', 'daily_return', 'rolling_volatility']]
    return result.dropna().T.to_dict()
