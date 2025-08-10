import time
from typing import Dict, List, Optional
import yfinance as yf
from bs4 import BeautifulSoup
import pandas as pd
import requests
from config.config import Config

class FinancialDataRetriever:
    """Retrieves financial data from multiple sources"""

    @staticmethod
    def get_screener_data(symbol: str) -> Dict[str, float]:
        """
        Scrape financial data from Screener.in

        Args:
            symbol: Stock symbol without exchange suffix

        Returns:
            Dictionary of financial metrics
        """
        try:
            url = f"https://www.screener.in/company/{symbol}/"
            print(f"Fetching data from Screener.in for {symbol}...")

            response = requests.get(url, headers=Config.HEADERS)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            def extract_metric(testid: str, is_percent: bool = False, is_cash: bool = False) -> Optional[float]:
                """Extract specific metric from HTML"""
                try:
                    container = soup.find('li', {'data-testid': testid})
                    if not container:
                        return None

                    value = container.find('span', class_='number').text.strip()

                    if is_percent:
                        return float(value.replace('%', '')) / 100
                    if is_cash:
                        multipliers = {'Cr': 1e7, 'L': 1e5}
                        for unit, mult in multipliers.items():
                            if unit in value:
                                return float(value.replace(unit, '').strip()) * mult
                        return float(value)

                    return float(value)
                except Exception as e:
                    print(f"WARNING: Error extracting {testid}: {str(e)}")
                    return None

            metrics = {
                'roe': extract_metric('roe', is_percent=True),
                'debt_to_equity': extract_metric('debt-to-equity'),
                'net_profit_margin': extract_metric('net-profit-margin', is_percent=True),
                'current_ratio': extract_metric('current-ratio'),
                'interest_coverage': extract_metric('interest-coverage'),
                'free_cash_flow': extract_metric('free-cash-flow', is_cash=True)
            }

            print(f"Successfully retrieved {sum(1 for v in metrics.values() if v is not None)} metrics from Screener.in")
            return metrics

        except Exception as e:
            print(f"ERROR: Error scraping {symbol}: {str(e)}")
            return {}
        finally:
            # Rate limiting to avoid being blocked
            time.sleep(Config.SCRAPER_DELAY)

    @staticmethod
    def get_calculated_metrics(ticker: str) -> Dict[str, float]:
        """
        Calculate financial metrics from Yahoo Finance statements

        Args:
            ticker: Stock ticker symbol with exchange suffix

        Returns:
            Dictionary of calculated financial metrics
        """
        try:
            print(f"Calculating metrics from Yahoo Finance statements for {ticker}...")
            stock = yf.Ticker(ticker)

            # Get financial statements
            balance_sheet = stock.balance_sheet
            income_stmt = stock.income_stmt
            cash_flow = stock.cashflow

            metrics = {
                'roe': None,
                'debt_to_equity': None,
                'net_profit_margin': None,
                'current_ratio': None,
                'interest_coverage': None,
                'free_cash_flow': None
            }

            # Helper function to safely get financial values
            def get_value(df: pd.DataFrame, keys: List[str], position: int = 0) -> Optional[float]:
                """Safely extract value from financial statement"""
                for key in keys:
                    try:
                        return df.loc[key].iloc[position]
                    except KeyError:
                        continue
                return None

            # Calculate Return on Equity (ROE)
            try:
                net_income = get_value(income_stmt, ['Net Income', 'Net Income From Continuing Operations'])
                shareholders_equity = get_value(balance_sheet, [
                    'Total Equity Gross Minority Interest',
                    'Stockholders Equity',
                    'Total Shareholder Equity'
                ])

                if shareholders_equity and shareholders_equity != 0:
                    metrics['roe'] = net_income / shareholders_equity
            except Exception as e:
                print(f"WARNING: ROE calculation error: {str(e)}")

            # Calculate Debt-to-Equity Ratio
            try:
                total_debt = get_value(balance_sheet, ['Total Debt'])
                if not total_debt:
                    # Calculate total debt as current debt + long term debt
                    current_debt = get_value(balance_sheet, ['Current Debt'])
                    long_term_debt = get_value(balance_sheet, ['Long Term Debt'])
                    total_debt = (current_debt or 0) + (long_term_debt or 0)

                if shareholders_equity and shareholders_equity != 0:
                    metrics['debt_to_equity'] = total_debt / shareholders_equity
            except Exception as e:
                print(f"WARNING: Debt/Equity calculation error: {str(e)}")

            # Calculate Net Profit Margin
            try:
                total_revenue = get_value(income_stmt, ['Total Revenue', 'Operating Revenue'])
                if total_revenue and total_revenue != 0:
                    metrics['net_profit_margin'] = net_income / total_revenue
            except Exception as e:
                print(f"WARNING: Net Margin calculation error: {str(e)}")

            # Calculate Current Ratio
            try:
                current_assets = get_value(balance_sheet, ['Current Assets', 'Total Current Assets'])
                current_liabilities = get_value(balance_sheet, ['Current Liabilities', 'Total Current Liabilities'])
                if current_liabilities and current_liabilities != 0:
                    metrics['current_ratio'] = current_assets / current_liabilities
            except Exception as e:
                print(f"WARNING: Current Ratio calculation error: {str(e)}")

            # Calculate Interest Coverage Ratio
            try:
                ebit = get_value(income_stmt, [
                    'EBIT',
                    'Operating Income',
                    'Earnings Before Interest and Taxes',
                    'EBIT - Financial Statement'
                ])

                interest_expense = get_value(income_stmt, [
                    'Interest Expense',
                    'Interest Expense, Net',
                    'Interest and Debt Expense',
                    'Finance Cost'
                ])

                if ebit is not None and interest_expense not in (None, 0):
                    metrics['interest_coverage'] = ebit / abs(interest_expense)
            except Exception as e:
                print(f"WARNING: Interest Coverage calculation error: {str(e)}")

            # Calculate Free Cash Flow
            try:
                # Try to get directly from cash flow statement
                fcf = get_value(cash_flow, ['Free Cash Flow'])
                if not fcf:
                    # Calculate manually: Operating Cash Flow - Capital Expenditures
                    op_cash_flow = get_value(cash_flow, ['Operating Cash Flow', 'Cash Flow From Continuing Operating Activities'])
                    capex = get_value(cash_flow, ['Capital Expenditure', 'Capital Expenditures'])
                    if op_cash_flow and capex:
                        fcf = op_cash_flow - abs(capex)
                metrics['free_cash_flow'] = fcf
            except Exception as e:
                print(f"WARNING: FCF calculation error: {str(e)}")

            print(f"Successfully calculated {sum(1 for v in metrics.values() if v is not None)} metrics from statements")
            return {k: (v if v is None else round(v, 4)) for k, v in metrics.items()}

        except Exception as e:
            print(f"ERROR: Error calculating metrics for {ticker}: {str(e)}")
            return {}


        stock_scores.sort(key=lambda x: x[1], reverse=True)
        return stock_scores[:top_n]