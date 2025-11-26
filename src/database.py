# src/database.py
import pandas as pd
import json
from datetime import datetime
import os
import sys

# Add parent directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class StockDatabase:
    """Simple file-based database to start (we'll upgrade to PostgreSQL later)"""
    
    def __init__(self, data_dir="data"):
        # Use absolute path
        if not os.path.isabs(data_dir):
            # Get project root directory
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(project_root, data_dir)
            
        self.data_dir = data_dir
        self.processed_dir = f"{data_dir}/processed"
        
        # Create directories if they don't exist
        os.makedirs(self.processed_dir, exist_ok=True)
        
    def save_price_data(self, symbol, df):
        """Save price data to CSV"""
        filename = f"{self.processed_dir}/{symbol.replace('.', '_')}_prices.csv"
        df.to_csv(filename)
        print(f"💾 Saved {symbol} price data to {filename}")
        return filename
        
    def load_price_data(self, symbol):
        """Load price data from CSV"""
        filename = f"{self.processed_dir}/{symbol.replace('.', '_')}_prices.csv"
        if os.path.exists(filename):
            df = pd.read_csv(filename, index_col='Date', parse_dates=True)
            return df
        return None
        
    def save_metadata(self, symbol, metadata):
        """Save stock metadata (name, sector, etc.)"""
        filename = f"{self.processed_dir}/{symbol.replace('.', '_')}_meta.json"
        with open(filename, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"📝 Saved {symbol} metadata")
        
    def get_latest_prices(self):
        """Get latest price for all stocks"""
        latest = {}
        for file in os.listdir(self.processed_dir):
            if file.endswith('_prices.csv'):
                symbol = file.replace('_prices.csv', '').replace('_', '.')
                df = self.load_price_data(symbol)
                if df is not None and not df.empty:
                    latest[symbol] = {
                        'price': df['Close'].iloc[-1],
                        'date': df.index[-1].strftime('%Y-%m-%d'),
                        'change': df['Daily_Return'].iloc[-1] * 100 if 'Daily_Return' in df.columns else 0
                    }
        return latest

# Test it
if __name__ == "__main__":
    db = StockDatabase()
    
    # Import the data fetcher correctly
    from collectors.data_fetcher import HKStockDataFetcher
    
    fetcher = HKStockDataFetcher()
    
    # Save all stock data
    print("📊 Saving stock data to database...")
    for symbol in fetcher.stocks:
        data = fetcher.fetch_stock_data(symbol)
        if not data.empty:
            db.save_price_data(symbol, data)
            
    # Get latest prices
    print("\n📊 Latest Prices from Database:")
    latest = db.get_latest_prices()
    for symbol, info in latest.items():
        print(f"{symbol}: ${info['price']:.2f} ({info['change']:+.2f}%)")