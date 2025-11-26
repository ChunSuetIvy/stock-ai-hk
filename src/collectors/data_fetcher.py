# src/collectors/data_fetcher.py
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time
import json
import os
import numpy as np

class HKStockDataFetcher:
    """Hong Kong Stock Data Fetcher - Real data locally, simulated on Railway"""
    
    def __init__(self):
        self.stocks = {
            "0700.HK": "Tencent",
            "9988.HK": "Alibaba", 
            "0005.HK": "HSBC",
            "0941.HK": "China Mobile",
            "1299.HK": "AIA Group"
        }
        
        # Detect if we're on Railway
        self.is_railway = os.getenv('RAILWAY_ENVIRONMENT_NAME') is not None
        
        if self.is_railway:
            print("🚂 Running on Railway - will use fallback data")
        else:
            print("💻 Running locally - will use yfinance")
        
    def fetch_stock_data(self, symbol, period="1mo"):
        """Fetch stock data - real locally, simulated on Railway"""
        print(f"🔄 Fetching data for {symbol}")
        
        # LOCAL: Use yfinance
        if not self.is_railway:
            data = self._fetch_yfinance_data(symbol, period)
            if not data.empty:
                print(f"✅ Got real yfinance data for {symbol}")
                return self._add_technical_indicators(data)
        
        # RAILWAY: Use fallback data
        print(f"📊 Using fallback data for {symbol} (Railway environment)")
        data = self._generate_fallback_data(symbol)
        return self._add_technical_indicators(data)
    
    def _fetch_yfinance_data(self, symbol, period):
        """Fetch real data from yfinance (local only)"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            
            if not data.empty:
                print(f"   ✅ yfinance returned {len(data)} days for {symbol}")
                return data
            else:
                print(f"   ⚠️ yfinance returned empty data for {symbol}")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"   ❌ yfinance error for {symbol}: {e}")
            return pd.DataFrame()
    
    def _generate_fallback_data(self, symbol):
        """Generate realistic fallback data for Railway"""
        
        # Use current hour as seed for consistency
        hour_seed = datetime.now().hour
        np.random.seed(hour_seed + hash(symbol) % 1000)
        
        # Create date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Realistic base prices
        base_prices = {
            "0700.HK": 620.0,  # Tencent
            "9988.HK": 155.0,  # Alibaba
            "0005.HK": 107.0,  # HSBC
            "0941.HK": 87.0,   # China Mobile
            "1299.HK": 79.0    # AIA Group
        }
        
        base_price = base_prices.get(symbol, 100.0)
        
        # Add some trend
        if symbol == "9988.HK":  # Alibaba trending up
            trend = 0.002
        elif symbol == "0005.HK":  # HSBC slightly down
            trend = -0.001
        else:
            trend = 0.0005
        
        # Generate prices
        data = []
        current_price = base_price
        
        for date in date_range:
            # Daily movement with trend
            daily_change = np.random.normal(trend, 0.02)
            current_price = current_price * (1 + daily_change)
            
            # OHLC values
            open_price = current_price * (1 + np.random.normal(0, 0.005))
            high = max(open_price, current_price) * (1 + abs(np.random.normal(0, 0.01)))
            low = min(open_price, current_price) * (1 - abs(np.random.normal(0, 0.01)))
            
            # Realistic volume
            base_volume = 20000000
            volume = int(base_volume * np.random.uniform(0.5, 2.0))
            
            data.append({
                'Open': open_price,
                'High': high,
                'Low': low,
                'Close': current_price,
                'Volume': volume
            })
        
        df = pd.DataFrame(data, index=date_range)
        return df
    
    def _add_technical_indicators(self, data):
        """Add technical indicators to data"""
        if data.empty:
            return data
            
        try:
            # Basic indicators
            data['Daily_Return'] = data['Close'].pct_change()
            data['MA_5'] = data['Close'].rolling(window=5).mean()
            data['MA_20'] = data['Close'].rolling(window=20).mean()
            data['Volume_Ratio'] = data['Volume'] / data['Volume'].rolling(window=5).mean()
            
            # RSI calculation
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / (loss + 1e-10)  # Avoid division by zero
            data['RSI'] = 100 - (100 / (1 + rs))
            
        except Exception as e:
            print(f"   Warning: Error adding indicators: {e}")
            
        return data
    
    def fetch_all_stocks(self):
        """Fetch data for all stocks"""
        all_data = {}
        
        for symbol, name in self.stocks.items():
            print(f"Fetching {name}...")
            data = self.fetch_stock_data(symbol)
            if not data.empty:
                all_data[symbol] = data
                time.sleep(0.5)  # Be nice to APIs
        
        return all_data
    
    def get_summary(self):
        """Get summary of all stocks"""
        summary = []
        
        for symbol, name in self.stocks.items():
            try:
                data = self.fetch_stock_data(symbol, period="5d")
                
                if not data.empty and len(data) > 1:
                    latest = data.iloc[-1]
                    prev = data.iloc[-2]
                    
                    summary.append({
                        'Symbol': symbol,
                        'Name': name,
                        'Price': round(float(latest['Close']), 2),
                        'Change': round(float(latest['Close'] - prev['Close']), 2),
                        'Change %': round(((latest['Close'] - prev['Close']) / prev['Close']) * 100, 2),
                        'Volume': int(latest['Volume']),
                        'Data_Source': 'yfinance' if not self.is_railway else 'simulated'
                    })
            except Exception as e:
                print(f"Error getting summary for {symbol}: {e}")
                
        return pd.DataFrame(summary)

# Test
if __name__ == "__main__":
    fetcher = HKStockDataFetcher()
    print("\n📊 Stock Summary:")
    print("="*60)
    summary = fetcher.get_summary()
    print(summary)