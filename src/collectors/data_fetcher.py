# src/collectors/data_fetcher.py
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
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
        
        # Better Railway detection - check multiple environment variables
        self.is_railway = any([
            os.getenv('RAILWAY_ENVIRONMENT_NAME'),
            os.getenv('RAILWAY_PUBLIC_DOMAIN'),
            os.getenv('RAILWAY_PROJECT_NAME'),
            os.getenv('RAILWAY_SERVICE_NAME')
        ])
        
        if self.is_railway:
            print("🚂 Running on Railway - will use simulated data")
        else:
            print("💻 Running locally - will use yfinance for real data")
    
    def fetch_stock_data(self, symbol, period="1mo"):
        """Fetch stock data - real locally, simulated on Railway"""
        print(f"🔄 Fetching data for {symbol} (Railway: {self.is_railway})")
        
        # LOCAL: Try yfinance first
        if not self.is_railway:
            data = self._fetch_yfinance_data(symbol, period)
            if not data.empty:
                print(f"✅ Got real yfinance data for {symbol}")
                return self._add_technical_indicators(data)
            else:
                print(f"⚠️ yfinance failed, using fallback for {symbol}")
        
        # RAILWAY or FALLBACK: Use simulated data
        print(f"📊 Using simulated data for {symbol}")
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
        """Generate realistic fallback data with proper variation"""
        
        # Use current time for seed to get variation
        hour_seed = datetime.now().hour + datetime.now().day
        np.random.seed(hour_seed + hash(symbol) % 1000)
        
        # Create date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Realistic base prices for HK stocks (Nov 2024 levels)
        base_prices = {
            "0700.HK": 620.0,  # Tencent
            "9988.HK": 155.0,  # Alibaba
            "0005.HK": 107.0,  # HSBC
            "0941.HK": 87.0,   # China Mobile
            "1299.HK": 79.0    # AIA Group
        }
        
        base_price = base_prices.get(symbol, 100.0)
        
        # Add some trend based on symbol
        if symbol == "9988.HK":  # Alibaba trending up
            trend = 0.002
        elif symbol == "0005.HK":  # HSBC slightly down
            trend = -0.001
        else:
            trend = 0.0005
        
        # Generate realistic OHLCV data
        data = []
        current_price = base_price
        
        for i, date in enumerate(date_range):
            # Daily movement with trend
            daily_change = np.random.normal(trend, 0.02)
            current_price = current_price * (1 + daily_change)
            
            # Realistic OHLC
            open_price = current_price * (1 + np.random.normal(0, 0.005))
            high = max(open_price, current_price) * (1 + abs(np.random.normal(0, 0.01)))
            low = min(open_price, current_price) * (1 - abs(np.random.normal(0, 0.01)))
            
            # Volume with weekly patterns
            base_volume = 20000000
            day_of_week = date.dayofweek
            if day_of_week in [1, 2, 3]:  # Tue-Thu higher volume
                volume_multiplier = np.random.uniform(1.2, 2.0)
            else:
                volume_multiplier = np.random.uniform(0.7, 1.3)
            volume = int(base_volume * volume_multiplier)
            
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
            rs = gain / (loss + 1e-10)
            data['RSI'] = 100 - (100 / (1 + rs))
            
            # SMA for indicators
            data['SMA_20'] = data['Close'].rolling(window=20).mean()
            
        except Exception as e:
            print(f"   Warning: Error adding indicators: {e}")
            
        return data