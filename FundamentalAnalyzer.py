# === Financial Analysis Module ===
from typing import Dict, List, Tuple
from config.config import Config
from FinancialDataLoader import FinancialDataRetriever
import yfinance as yf

class FundamentalAnalyzer:
    """Analyzes stocks based on fundamental metrics"""

    @staticmethod
    def get_fundamental_data(ticker: str) -> Dict[str, float]:
        """
        Get comprehensive fundamental data from multiple sources

        Args:
            ticker: Stock ticker symbol with exchange suffix

        Returns:
            Dictionary of fundamental metrics
        """
        print(f"\nAnalyzing fundamental data for {ticker}...")

        try:
            # Initialize metrics dictionary
            metrics = {
                'roe': None,
                'debt_to_equity': None,
                'net_profit_margin': None,
                'current_ratio': None,
                'interest_coverage': None,
                'free_cash_flow': None
            }

            # Try all data sources in order of preference
            for source in Config.DATA_SOURCES:
                try:
                    if source == 'yfinance_info':
                        FundamentalAnalyzer._fetch_yfinance_data(ticker, metrics)
                    elif source == 'yfinance_calculated':
                        FundamentalAnalyzer._fetch_calculated_metrics(ticker, metrics)
                    elif source == 'screener':
                        FundamentalAnalyzer._fetch_screener_data(ticker, metrics)

                    # Check if all metrics are now available
                    if all(v is not None for v in metrics.values()):
                        break

                except Exception as e:
                    print(f"WARNING: Failed {source} for {ticker} - {str(e)}")
                    continue

            # Clean up and validate metrics
            FundamentalAnalyzer._validate_and_cleanup_metrics(metrics)
            
            # Display results
            FundamentalAnalyzer._display_metrics(ticker, metrics)

            return metrics

        except Exception as e:
            print(f"ERROR: Error getting fundamental data: {str(e)}")
            return {}

    @staticmethod
    def _fetch_yfinance_data(ticker: str, metrics: Dict[str, float]) -> None:
        """
        Fetch additional metrics from Yahoo Finance if not already present
        Args:
            ticker: Stock ticker symbol with exchange suffix
            metrics: Dictionary of existing metrics to update
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            yf_metrics = {
                'roe' : info.get('returnOnEquity'),
                'debt_to_equity': info.get('debtToEquity'),
                'net_profit_margin': info.get('profitMargins'),
                'current_ratio': info.get('currentRatio'),
                'interest_coverage': info.get('interestCoverage'),
                'free_cash_flow': info.get('freeCashflow')
            }
            for k, v in yf_metrics.items():
                if metrics[k] is None and v is not None:
                    metrics[k] = v
            
        except Exception as e:
            print(f"WARNING: Error fetching data from Yahoo Finance for {ticker}: {str(e)}")

    @staticmethod
    def _fetch_calculated_metrics(ticker: str, metrics: Dict[str, float]) -> None:
        """
        Fetch calculated metrics from financial statements and update metrics dict

        Args:
            ticker: Stock ticker symbol
            metrics: Metrics dictionary to update
        """
        try:
            calculated = FinancialDataRetriever.get_calculated_metrics(ticker)
            if calculated:
                for k, v in calculated.items():
                    if metrics[k] is None and v is not None:
                        metrics[k] = v
        except Exception as e:
            print(f"WARNING: Error fetching calculated metrics for {ticker}: {str(e)}")
            
    def _fetch_screener_data(ticker: str, metrics: Dict[str, float]) -> None:
        """
        Fetch metrics from Screener.in and update metrics dict
        Args:
            ticker: Stock ticker symbol
            metrics: Metrics dictionary to update
        """
        try:
            screener_metrics = FinancialDataRetriever.get_screener_data(ticker.replace('.NS', ''))
            if screener_metrics:
                for k, v in screener_metrics.items():
                    if metrics[k] is None and v is not None:
                        metrics[k] = v
        except Exception as e:
            print(f"WARNING: Error fetching Screener.in data for {ticker}: {str(e)}")
    
    @staticmethod
    def _validate_and_cleanup_metrics(metrics: Dict[str, float]) -> None:
        """
        Clean up and validate metrics, setting defaults for missing values
        
        Args:
            metrics: Metrics dictionary to validate and clean up
        """
        # Set minimum defaults for critical metrics
        for k in ['roe', 'net_profit_margin']:
            if metrics[k] is None:
                metrics[k] = 0  # Set minimum defaults
        
        # Convert free cash flow to appropriate type
        try:
            metrics['free_cash_flow'] = float(metrics['free_cash_flow']) if metrics['free_cash_flow'] else 0
        except (TypeError, ValueError):
            metrics['free_cash_flow'] = 0

    @staticmethod
    def _display_metrics(ticker: str, metrics: Dict[str, float]) -> None:
        """
        Display metrics in a formatted way
        
        Args:
            ticker: Stock ticker symbol
            metrics: Metrics dictionary to display
        """
        print(f"\nFinal metrics for {ticker}:")
        for k, v in metrics.items():
            if k == 'free_cash_flow':
                print(f"  • {k}: ₹{v/1e7:.2f} Cr")
            elif k in ['roe', 'net_profit_margin']:
                print(f"  • {k}: {v*100:.2f}%")
            else:
                print(f"  • {k}: {v:.2f}")
        line = '|'.join(str(metrics[k]) for k in [
            'roe',
            'debt_to_equity',
            'net_profit_margin',
            'current_ratio',
            'interest_coverage',
            'free_cash_flow'
        ])
        print(line)

    @staticmethod
    def calculate_score(metrics: Dict[str, float]) -> float:
        """
        Calculate stock score based on fundamental metrics

        Args:
            metrics: Dictionary of fundamental metrics

        Returns:
            Score on a 0-100 scale for the stock
        """
        # Initialize base score at 0
        score = 0
        total_possible_points = 0

        for metric, value in metrics.items():
            if value is None:
                continue  # Skip missing metrics

            weight = Config.WEIGHTS[metric]
            threshold = Config.THRESHOLDS[metric]
            total_possible_points += weight * 100  # Maximum possible contribution for this metric

            # Calculate metric score based on direction
            if Config.METRIC_DIRECTION[metric] == 'higher':
                # For metrics where higher is better
                if value <= 0:
                    # Negative or zero values get 0 points
                    metric_score = 0
                elif value >= threshold * 2:
                    # Cap the maximum bonus at 2x the threshold to avoid extreme outliers dominating
                    metric_score = 100
                else:
                    # Scale the score based on how close it is to the threshold
                    # At threshold exactly = 50 points, at 2x threshold = 100 points
                    metric_score = min(100, 50 + 50 * (value - threshold) / threshold)

            else:  # 'lower' is better
                if value <= 0 and metric != 'debt_to_equity':
                    # For most "lower is better" metrics, 0 is ideal (except debt_to_equity where 0 might not be optimal)
                    metric_score = 100
                elif value <= threshold / 2:
                    # Well below threshold gets high score
                    metric_score = 100
                elif value <= threshold:
                    # Below threshold scales from 50-100
                    metric_score = 50 + 50 * (threshold - value) / (threshold / 2)
                else:
                    # Above threshold scales from 0-50
                    # Capped at 2x threshold to avoid extreme penalties
                    metric_score = max(0, 50 - 50 * min(1, (value - threshold) / threshold))

            # Add weighted metric score to total
            score += metric_score * weight

        # Return percentage score (0-100 scale)
        if total_possible_points > 0:
            return (score / total_possible_points) * 100
        return 0

    @classmethod
    def analyze_stocks(cls, tickers: List[str], top_n: int = 10) -> List[Tuple[str, float, Dict[str, float]]]:
        """
        Analyze multiple stocks and rank them by fundamental score

        Args:
            tickers: List of stock ticker symbols
            top_n: Number of top stocks to return

        Returns:
            List of tuples (ticker, score, metrics) for top stocks
        """
        stock_scores = []

        for ticker in tickers:
            print(f"\n{'='*50}")
            print(f"Analyzing {ticker}")
            print(f"{'='*50}")

            data = cls.get_fundamental_data(ticker)

            if data:
                score = cls.calculate_score(data)
                print(f"Score: {score:.4f}")
                stock_scores.append((ticker, score, data))

        # Sort by score (descending) and return top N
        stock_scores.sort(key=lambda x: x[1], reverse=True)
        return stock_scores[:top_n]