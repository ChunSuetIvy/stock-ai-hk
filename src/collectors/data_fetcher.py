# src/collectors/data_fetcher.py
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time
import json

class HKStockDataFetcher:
    """Your main data collection class"""
    
    def __init__(self):
        # Your 5 target stocks
        self.stocks = {
            "0700.HK": "Tencent",
            "9988.HK": "Alibaba", 
            "0005.HK": "HSBC",
            "0941.HK": "China Mobile",
            "1299.HK": "AIA Group"
        }
        
        # Cache to avoid hitting API limits
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        
    def fetch_stock_data(self, symbol, period="1mo"):
        """Fetch stock data with caching"""
        # Skip cache in production (Railway)
        import os
        if os.getenv('RAILWAY_ENVIRONMENT_NAME'):
            # In Railway - always fetch fresh data
            print(f"🔄 Fetching fresh data for {symbol}")
            try:
                ticker = yf.Ticker(symbol)
                data = ticker.history(period=period)
                if not data.empty:
                    # Add calculated fields
                    data['Daily_Return'] = data['Close'].pct_change()
                    data['MA_5'] = data['Close'].rolling(window=5).mean()
                    data['Volume_Ratio'] = data['Volume'] / data['Volume'].rolling(window=5).mean()
                return data
            except Exception as e:
                print(f"❌ Error fetching {symbol}: {str(e)}")
                return pd.DataFrame()
        # Local development - use cache
        cache_key = f"{symbol}_{period}"
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if (datetime.now() - cached_time).seconds < self.cache_duration:
                print(f"📦 Using cached data for {symbol}")
                return cached_data
            # Fetch fresh data
        
        print(f"🔄 Fetching fresh data for {symbol}")
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            if not data.empty:
                # Add calculated fields
                data['Daily_Return'] = data['Close'].pct_change()
                data['MA_5'] = data['Close'].rolling(window=5).mean()
                data['Volume_Ratio'] = data['Volume'] / data['Volume'].rolling(window=5).mean()
            else:
                print(f"⚠️ Empty data returned for {symbol}")
            return data
        except Exception as e:
            print(f"❌ Error fetching {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def fetch_all_stocks(self):
        """Fetch data for all stocks with rate limiting"""
        all_data = {}
        
        for symbol, name in self.stocks.items():
            print(f"Fetching {name}...")
            data = self.fetch_stock_data(symbol)
            if not data.empty:
                all_data[symbol] = data
                # Rate limiting - be nice to the API
                time.sleep(1)
        
        return all_data
    
    def get_summary(self):
        """Get a summary of all stocks"""
        summary = []
        
        for symbol, name in self.stocks.items():
            data = self.fetch_stock_data(symbol, period="5d")
            if not data.empty:
                latest = data.iloc[-1]
                prev = data.iloc[-2] if len(data) > 1 else latest
                
                summary.append({
                    'Symbol': symbol,
                    'Name': name,
                    'Price': round(latest['Close'], 2),
                    'Change': round(latest['Close'] - prev['Close'], 2),
                    'Change %': round(((latest['Close'] / prev['Close']) - 1) * 100, 2),
                    'Volume': int(latest['Volume'])
                })
        
        return pd.DataFrame(summary)

# Test the fetcher
if __name__ == "__main__":
    fetcher = HKStockDataFetcher()
    
    print("\n📊 Stock Summary:")
    print("="*60)
    summary = fetcher.get_summary()
    print(summary.to_string(index=False))
    
    print("\n📈 Fetching detailed data for Tencent:")
    tencent_data = fetcher.fetch_stock_data("0700.HK", period="1wk")
    print(tencent_data.tail())