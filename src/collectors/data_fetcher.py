# src/collectors/data_fetcher.py
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time
import json
import os
import numpy as np

class HKStockDataFetcher:
    """Hong Kong Stock Data Fetcher - Hybrid Approach"""
    
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
        """Fetch stock data - tries real data first, then simulated data"""
        cache_key = f"{symbol}_{period}"
        
        # Check cache first
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if (datetime.now() - cached_time).seconds < self.cache_duration:
                print(f"📦 Using cached data for {symbol}")
                return cached_data
        
        print(f"🔄 Fetching data for {symbol}")
        
        # First try to get real data
        real_data = self._fetch_real_data(symbol, period)
        
        if not real_data.empty:
            print(f"✅ Got real data for {symbol}")
            data = real_data
            data_source = "real"
        else:
            print(f"⚠️ No real data for {symbol}, using simulated data")
            data = self._generate_simulated_data(symbol)
            data_source = "simulated"
        
        if not data.empty:
            # Add technical indicators
            data = self._add_technical_indicators(data)
            # Add data source info
            data.attrs['data_source'] = data_source
            # Cache the result
            self.cache[cache_key] = (datetime.now(), data)
        else:
            print(f"❌ All data sources failed for {symbol}")
            
        return data
    
    def _fetch_real_data(self, symbol, period):
        """Try to get real data from yfinance"""
        try:
            print(f"   Trying real data for {symbol}...")
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, timeout=10)
            
            if not data.empty:
                return data
            else:
                return pd.DataFrame()
                
        except Exception as e:
            print(f"   Real data failed for {symbol}: {e}")
            return pd.DataFrame()
    
    def _generate_simulated_data(self, symbol):
        """Generate realistic simulated data"""
        print(f"   Generating simulated data for {symbol}")
        
        # Create date range for the last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Realistic base prices for Hong Kong stocks (approximate)
        base_prices = {
            "0700.HK": 320.0,  # Tencent
            "9988.HK": 85.0,   # Alibaba
            "0005.HK": 60.0,   # HSBC
            "0941.HK": 68.0,   # China Mobile
            "1299.HK": 75.0    # AIA
        }
        
        base_price = base_prices.get(symbol, 50.0)
        current_price = base_price
        
        data = []
        for i, date in enumerate(date_range):
            # Simulate realistic price movements
            volatility = 0.02  # 2% daily volatility
            change = np.random.normal(0, volatility)
            current_price = current_price * (1 + change)
            
            # Generate OHLC data
            open_price = current_price * (1 + np.random.normal(0, 0.005))
            high = max(open_price, current_price) * (1 + abs(np.random.normal(0, 0.01)))
            low = min(open_price, current_price) * (1 - abs(np.random.normal(0, 0.01)))
            close_price = current_price
            
            volume = np.random.randint(1000000, 5000000)
            
            data.append({
                'Open': open_price,
                'High': high,
                'Low': low,
                'Close': close_price,
                'Volume': volume
            })
        
        df = pd.DataFrame(data, index=date_range)
        return df
    
    def _add_technical_indicators(self, data):
        """Add technical indicators to the data"""
        if data.empty:
            return data
            
        try:
            data['Daily_Return'] = data['Close'].pct_change()
            data['MA_5'] = data['Close'].rolling(window=5).mean()
            data['MA_20'] = data['Close'].rolling(window=20).mean()
            data['Volume_Ratio'] = data['Volume'] / data['Volume'].rolling(window=5).mean()
            
            # Calculate RSI
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            data['RSI'] = 100 - (100 / (1 + rs))
            
        except Exception as e:
            print(f"Error adding technical indicators: {e}")
            
        return data
    
    def get_summary(self):
        """Get summary with proper error handling"""
        summary = []
        
        for symbol, name in self.stocks.items():
            try:
                data = self.fetch_stock_data(symbol, period="5d")
                
                if not data.empty and len(data) > 1:
                    latest = data.iloc[-1]
                    prev = data.iloc[-2]
                    
                    price_change = latest['Close'] - prev['Close']
                    change_percent = (price_change / prev['Close']) * 100
                    
                    summary.append({
                        'Symbol': symbol,
                        'Name': name,
                        'Price': round(float(latest['Close']), 2),
                        'Change': round(float(price_change), 2),
                        'Change %': round(float(change_percent), 2),
                        'Volume': int(latest['Volume']),
                        'Data_Source': data.attrs.get('data_source', 'unknown')
                    })
                else:
                    # Fallback data
                    summary.append({
                        'Symbol': symbol,
                        'Name': name,
                        'Price': 0,
                        'Change': 0,
                        'Change %': 0,
                        'Volume': 0,
                        'Data_Source': 'error'
                    })
                    
            except Exception as e:
                print(f"Error in summary for {symbol}: {e}")
                summary.append({
                    'Symbol': symbol,
                    'Name': name,
                    'Price': 0,
                    'Change': 0,
                    'Change %': 0,
                    'Volume': 0,
                    'Data_Source': 'error'
                })
        
        return pd.DataFrame(summary)

# Test the fetcher
if __name__ == "__main__":
    fetcher = HKStockDataFetcher()
    
    print("\n📊 Stock Summary:")
    print("="*60)
    summary = fetcher.get_summary()
    print(summary.to_string(index=False))
    
    print("\n📈 Testing data fetch for Tencent:")
    tencent_data = fetcher.fetch_stock_data("0700.HK", period="1wk")
    print(f"Data points: {len(tencent_data)}")
    print(f"Data source: {tencent_data.attrs.get('data_source', 'unknown')}")
    if not tencent_data.empty:
        print(tencent_data[['Close', 'Volume', 'Daily_Return']].tail())