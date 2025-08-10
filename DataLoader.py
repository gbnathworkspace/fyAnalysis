import os
import pandas as pd
from typing import List


class DataLoader:
    """Handles loading data from various sources"""

    @staticmethod
    def check_data_directory() -> None:
        """Check if data directory exists and create if needed"""
        data_dir = 'data'
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            print(f"Created data directory: {data_dir}")
        else:
            print(f"Data directory exists: {data_dir}")

    @staticmethod
    def load_stock_data(file_path: str) -> pd.DataFrame:
        """
        Load stock data from Excel file

        Args:
            file_path: Path to Excel file containing stock data

        Returns:
            DataFrame with stock information
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            # Read Excel file
            df = pd.read_excel(file_path)

            # Validate required columns
            required_columns = ['stockname', 'category', 'symbol']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                print(f"⚠️ Warning: Missing required columns: {missing_columns}")
                print(f"Available columns: {df.columns.tolist()}")

            # Display a sample of the data
            print("\nSample of loaded stock data:")
            print(df.head())

            return df

        except Exception as e:
            print(f"❌ Error loading data: {str(e)}")
            return pd.DataFrame()

    @staticmethod
    def prepare_tickers(symbols: List[str], suffix: str = '.NS') -> List[str]:
        """
        Prepare ticker symbols with appropriate suffix

        Args:
            symbols: List of stock symbols
            suffix: Suffix to append to symbols (default: '.NS' for NSE)

        Returns:
            List of formatted ticker symbols
        """
        return [f"{sym}{suffix}" for sym in symbols]
