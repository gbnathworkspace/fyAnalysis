from flask import Flask, render_template, request, jsonify
from DataLoader import DataLoader
from FundamentalAnalyzer import FundamentalAnalyzer
from ResultPresenter import ResultsPresenter, ResultsExporter
from config.config import Config
import os

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze_stocks():
    """Analyze stocks based on uploaded data or symbols"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        
        if not symbols:
            return jsonify({'error': 'No stock symbols provided'}), 400
        
        # Prepare tickers with .NS suffix for NSE
        tickers = DataLoader.prepare_tickers(symbols, '.NS')
        
        # Analyze stocks
        results = FundamentalAnalyzer.analyze_stocks(tickers, top_n=10)
        
        # Format results for JSON response
        formatted_results = []
        for ticker, score, metrics in results:
            formatted_results.append({
                'ticker': ticker,
                'score': round(score, 2),
                'metrics': {k: round(v, 4) if v is not None else None for k, v in metrics.items()}
            })
        
        return jsonify({'results': formatted_results})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export', methods=['POST'])
def export_results():
    """Export analysis results to Excel"""
    try:
        data = request.get_json()
        results_data = data.get('results', [])
        
        if not results_data:
            return jsonify({'error': 'No results to export'}), 400
        
        # Convert JSON data back to the format expected by ResultsExporter
        results = []
        for item in results_data:
            ticker = item['ticker']
            score = item['score']
            metrics = item['metrics']
            results.append((ticker, score, metrics))
        
        # Export to Excel
        DataLoader.check_data_directory()  # Ensure data directory exists
        file_path = ResultsExporter.export_to_excel(results)
        
        if file_path:
            return jsonify({'success': True, 'file_path': file_path})
        else:
            return jsonify({'error': 'Failed to export results'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/hello')
def api_hello():
    return jsonify({'message': 'Financial Analysis API is running!'})

@app.route('/api/echo', methods=['POST'])
def api_echo():
    data = request.get_json()
    return jsonify({'echo': data})

if __name__ == '__main__':
    # For production, set debug=False and host='127.0.0.1'
    app.run(debug=True, host='127.0.0.1', port=5000)