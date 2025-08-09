from packages import *
from config.config import Config

class ResultsPresenter:
    """Formats and displays analysis results"""

    @staticmethod
    def print_top_stocks(results: List[Tuple[str, float, Dict[str, float]]]) -> None:
        """
        Display top stocks with their scores and metrics

        Args:
            results: List of tuples (ticker, score, metrics)
        """
        if not results:
            print("No stocks met the criteria.")
            return

        print("\nTop Stocks Based on Fundamental Score:")
        print("-" * 60)

        for rank, (ticker, score, data) in enumerate(results, 1):
            print(f"{rank}. {ticker} | Score: {score:.2f}")

            # Helper to print metric, handling None values
            def print_metric(name, value, fmt=None):
                if value is None:
                    print(f"   {name}: N/A")
                elif fmt:
                    print(f"   {name}: {fmt.format(value)}")
                else:
                    print(f"   {name}: {value:.2f}")

            print_metric("ROE", data.get('roe'), fmt="{:.2%}")
            print_metric("Debt/Equity", data.get('debt_to_equity'))
            print_metric("Net Margin", data.get('net_profit_margin'), fmt="{:.2%}")
            print_metric("Current Ratio", data.get('current_ratio'))
            print_metric("Interest Coverage", data.get('interest_coverage'))
            # Special handling for Free Cash Flow to show in Crores
            fcf_value = data.get('free_cash_flow', None)
            if fcf_value is not None:
                 print(f"   FCF: ₹{fcf_value/1e7:.1f} Cr")
            else:
                 print(f"   FCF: N/A")

            print("-" * 60)
            
            

class ResultsExporter:
    """Exports analysis results to Excel file"""

    @staticmethod
    def export_to_excel(results: List[Tuple[str, float, Dict[str, float]]], output_path: str = None) -> str:
        """
        Export stock analysis results to Excel file

        Args:
            results: List of tuples (ticker, score, metrics)
            output_path: Path to save the Excel file (default: auto-generated based on date)

        Returns:
            Path to the saved Excel file
        """
        if not results:
            print("No results to export.")
            return None

        # Generate default filename with timestamp if not provided
        # if not output_path:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_path = f'data/stock_analysis_{timestamp}.xlsx'

        # Create DataFrame from results
        data = []
        for ticker, score, metrics in results:
            row = {
                'Ticker': ticker,
                'Score': score,
                'ROE': metrics.get('roe', None),
                'Debt/Equity': metrics.get('debt_to_equity', None),
                'Net Profit Margin': metrics.get('net_profit_margin', None),
                'Current Ratio': metrics.get('current_ratio', None),
                'Interest Coverage': metrics.get('interest_coverage', None),
                'Free Cash Flow (Cr)': metrics.get('free_cash_flow', 0) / 1e7  # Convert to Crores
            }
            data.append(row)

        df = pd.DataFrame(data)

        # Format columns
        format_cols = {
            'Score': '{:.2f}',
            'ROE': '{:.2%}',
            'Net Profit Margin': '{:.2%}',
            'Debt/Equity': '{:.2f}',
            'Current Ratio': '{:.2f}',
            'Interest Coverage': '{:.2f}',
            'Free Cash Flow (Cr)': '{:.1f}'
        }

        for col, fmt in format_cols.items():
            if col in df.columns:
                df[col] = df[col].apply(lambda x: fmt.format(x) if pd.notna(x) else 'N/A')

        # Create Excel writer
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Write main results sheet
                df.to_excel(writer, sheet_name='Analysis Results', index=False)

                # Add a metadata sheet with analysis parameters
                metadata_data = [
                    ['Analysis Date', time.strftime("%Y-%m-%d %H:%M:%S")],
                    ['Number of Stocks Analyzed', len(results)],
                    ['', ''],
                    ['Metric Weights', '']
                ]

                # Add weights
                for metric, weight in Config.WEIGHTS.items():
                    metadata_data.append([f'  {metric}', f'{weight:.2f}'])

                metadata_data.append(['', ''])
                metadata_data.append(['Thresholds', ''])

                # Add thresholds
                for metric, threshold in Config.THRESHOLDS.items():
                    if metric == 'free_cash_flow':
                        value = f'₹{threshold/1e7:.1f} Cr'
                    elif metric in ['roe', 'net_profit_margin']:
                        value = f'{threshold:.2%}'
                    else:
                        value = f'{threshold:.2f}'
                    metadata_data.append([f'  {metric}', value])

                metadata_df = pd.DataFrame(metadata_data, columns=['Parameter', 'Value'])
                metadata_df.to_excel(writer, sheet_name='Analysis Parameters', index=False)

            print(f"Results exported to {output_path}")
            return output_path

        except Exception as e:
            print(f"ERROR: Error exporting results: {str(e)}")
            return None