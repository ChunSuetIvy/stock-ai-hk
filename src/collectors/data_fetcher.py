# src/collectors/data_fetcher.py
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time
import json
import os
import numpy as np
import requests

class HKStockDataFetcher:
    """Hong Kong Stock Data Fetcher with Real Data Sources"""
    
    def __init__(self):
        self.stocks = {
            "0700.HK": "Tencent",
            "9988.HK": "Alibaba", 
            "0005.HK": "HSBC",
            "0941.HK": "China Mobile",
            "1299.HK": "AIA Group"
        }
        
        # Cache to avoid hitting API limits
        self.cache = {}
        self.cache_duration = 300
        
        # Alpha Vantage API Key (FREE - get from https://www.alphavantage.co/support/#api-key)
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
        
    def fetch_stock_data(self, symbol, period="1mo"):
        """Fetch stock data - tries multiple real data sources"""
        cache_key = f"{symbol}_{period}"
        
        # Check cache first
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if (datetime.now() - cached_time).seconds < self.cache_duration:
                print(f"📦 Using cached data for {symbol}")
                return cached_data
        
        print(f"🔄 Fetching data for {symbol}")
        
        # Try multiple real data sources in order
        data_sources = [
            self._fetch_alpha_vantage,
            self._fetch_yfinance,
            self._generate_simulated_data  # Last resort
        ]
        
        for data_source in data_sources:
            data = data_source(symbol, period)
            if not data.empty:
                data_source_name = data_source.__name__.replace('_fetch_', '').replace('_generate_', '')
                print(f"✅ Got {data_source_name} data for {symbol}")
                break
        else:
            print(f"❌ All data sources failed for {symbol}")
            return pd.DataFrame()
        
        if not data.empty:
            # Add technical indicators
            data = self._add_technical_indicators(data)
            # Add data source info
            data.attrs['data_source'] = data_source_name
            # Cache the result
            self.cache[cache_key] = (datetime.now(), data)
            
        return data
    
    def _fetch_alpha_vantage(self, symbol, period):
        """Get real data from Alpha Vantage API"""
        try:
            if self.alpha_vantage_key == 'demo':
                return pd.DataFrame()  # Skip if using demo key
                
            print(f"   Trying Alpha Vantage for {symbol}...")
            
            # Convert symbol for Alpha Vantage (remove .HK)
            av_symbol = symbol.replace('.HK', '')
            
            # Alpha Vantage API endpoint
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': av_symbol,
                'apikey': self.alpha_vantage_key,
                'outputsize': 'compact'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if "Time Series (Daily)" in data:
                    time_series = data["Time Series (Daily)"]
                    
                    # Convert to DataFrame
                    records = []
                    for date, values in time_series.items():
                        records.append({
                            'Date': date,
                            'Open': float(values['1. open']),
                            'High': float(values['2. high']),
                            'Low': float(values['3. low']),
                            'Close': float(values['4. close']),
                            'Volume': int(values['5. volume'])
                        })
                    
                    df = pd.DataFrame(records)
                    df['Date'] = pd.to_datetime(df['Date'])
                    df = df.set_index('Date')
                    df = df.sort_index()
                    
                    return df
                else:
                    print(f"   Alpha Vantage: No time series data for {symbol}")
                    return pd.DataFrame()
            else:
                print(f"   Alpha Vantage API error: {response.status_code}")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"   Alpha Vantage failed for {symbol}: {e}")
            return pd.DataFrame()
    
    def _fetch_yfinance(self, symbol, period):
        """Try yfinance as fallback"""
        try:
            print(f"   Trying yfinance for {symbol}...")
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, timeout=10)
            return data
        except Exception as e:
            print(f"   yfinance failed for {symbol}: {e}")
            return pd.DataFrame()
    
    def _generate_simulated_data(self, symbol, period):
        """Generate simulated data as last resort"""
        print(f"   Generating simulated data for {symbol}")
        
        # Create date range for the last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Realistic base prices
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
        for date in date_range:
            # Realistic price movements
            volatility = 0.02
            change = np.random.normal(0, volatility)
            current_price = current_price * (1 + change)
            
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
        """Add technical indicators"""
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
        """Get summary with data source information"""
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
                        'Data_Source': data.attrs.get('data_source', 'unknown'),
                        'RSI': round(float(latest.get('RSI', 50)), 1)
                    })
                else:
                    summary.append({
                        'Symbol': symbol,
                        'Name': name,
                        'Price': 0,
                        'Change': 0,
                        'Change %': 0,
                        'Volume': 0,
                        'Data_Source': 'error',
                        'RSI': 50
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
                    'Data_Source': 'error',
                    'RSI': 50
                })
        
        return pd.DataFrame(summary)

if __name__ == "__main__":
    fetcher = HKStockDataFetcher()
    
    print("\n📊 Stock Summary:")
    print("="*60)
    summary = fetcher.get_summary()
    print(summary.to_string(index=False))