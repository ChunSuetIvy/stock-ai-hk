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
    """Hong Kong Stock Data Fetcher - Real Data Only"""
    
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
        
        # API Keys - GET THESE FREE KEYS
        self.twelve_data_key = os.getenv('TWELVE_DATA_API_KEY', '')
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY', '')
        
    def fetch_stock_data(self, symbol, period="1mo"):
        """Fetch REAL stock data only - no simulation"""
        cache_key = f"{symbol}_{period}"
        
        # Check cache first
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if (datetime.now() - cached_time).seconds < self.cache_duration:
                print(f"📦 Using cached data for {symbol}")
                return cached_data
        
        print(f"🔄 Fetching REAL data for {symbol}")
        
        # Try multiple REAL data sources
        data_sources = [
            self._fetch_twelve_data,  # Best for international stocks
            self._fetch_alpha_vantage,
            self._fetch_yfinance_with_retry,
        ]
        
        data = pd.DataFrame()
        data_source = "none"
        
        for source in data_sources:
            data = source(symbol, period)
            if not data.empty:
                data_source = source.__name__.replace('_fetch_', '')
                print(f"✅ Got {data_source} data for {symbol}")
                break
        
        if data.empty:
            print(f"❌ NO REAL DATA AVAILABLE for {symbol}")
            # Return empty DataFrame instead of fake data
            return pd.DataFrame()
        
        # Add technical indicators
        data = self._add_technical_indicators(data)
        data.attrs['data_source'] = data_source
        
        # Cache the result
        self.cache[cache_key] = (datetime.now(), data)
            
        return data
    
    def _fetch_twelve_data(self, symbol, period):
        """Get real data from Twelve Data API (BEST for HK stocks)"""
        try:
            if not self.twelve_data_key:
                return pd.DataFrame()
                
            print(f"   Trying Twelve Data for {symbol}...")
            
            # Twelve Data API endpoint
            url = "https://api.twelvedata.com/time_series"
            params = {
                'symbol': symbol,
                'interval': '1day',
                'outputsize': 30,  # Last 30 days
                'apikey': self.twelve_data_key,
                'format': 'JSON'
            }
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if "values" in data:
                    values = data["values"]
                    
                    # Convert to DataFrame
                    records = []
                    for item in values:
                        records.append({
                            'Date': item['datetime'],
                            'Open': float(item['open']),
                            'High': float(item['high']),
                            'Low': float(item['low']),
                            'Close': float(item['close']),
                            'Volume': int(float(item['volume']))
                        })
                    
                    df = pd.DataFrame(records)
                    df['Date'] = pd.to_datetime(df['Date'])
                    df = df.set_index('Date')
                    df = df.sort_index()
                    
                    return df
                else:
                    print(f"   Twelve Data: No values for {symbol}")
                    return pd.DataFrame()
            else:
                print(f"   Twelve Data API error: {response.status_code}")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"   Twelve Data failed for {symbol}: {e}")
            return pd.DataFrame()
    
    def _fetch_alpha_vantage(self, symbol, period):
        """Get real data from Alpha Vantage"""
        try:
            if not self.alpha_vantage_key:
                return pd.DataFrame()
                
            print(f"   Trying Alpha Vantage for {symbol}...")
            
            # Alpha Vantage API endpoint
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': symbol,
                'apikey': self.alpha_vantage_key,
                'outputsize': 'compact'
            }
            
            response = requests.get(url, params=params, timeout=15)
            
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
                    
                    # Get only last 30 days
                    if len(df) > 30:
                        df = df.tail(30)
                    
                    return df
                else:
                    print(f"   Alpha Vantage: No time series for {symbol}")
                    return pd.DataFrame()
            else:
                print(f"   Alpha Vantage API error: {response.status_code}")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"   Alpha Vantage failed for {symbol}: {e}")
            return pd.DataFrame()
    
    def _fetch_yfinance_with_retry(self, symbol, period):
        """Try yfinance with multiple attempts"""
        for attempt in range(3):
            try:
                print(f"   Trying yfinance (attempt {attempt + 1}) for {symbol}...")
                ticker = yf.Ticker(symbol)
                data = ticker.history(period=period, timeout=15)
                
                if not data.empty:
                    return data
                else:
                    print(f"   yfinance returned empty data for {symbol}")
                    
            except Exception as e:
                print(f"   yfinance attempt {attempt + 1} failed: {e}")
                
            time.sleep(1)  # Wait before retry
            
        return pd.DataFrame()
    
    def _add_technical_indicators(self, data):
        """Add technical indicators to real data"""
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
        """Get summary - returns empty if no real data"""
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
                        'RSI': round(float(latest.get('RSI', 0)), 1),
                        'has_real_data': True
                    })
                else:
                    # NO DATA - don't include in summary
                    print(f"❌ No real data for {symbol}, skipping...")
                    continue
                    
            except Exception as e:
                print(f"Error in summary for {symbol}: {e}")
                continue
        
        if not summary:
            print("⚠️ NO REAL DATA AVAILABLE FOR ANY STOCK")
            
        return pd.DataFrame(summary)

# Test with real data only
if __name__ == "__main__":
    fetcher = HKStockDataFetcher()
    
    print("\n📊 REAL Stock Data Test:")
    print("="*60)
    summary = fetcher.get_summary()
    
    if summary.empty:
        print("❌ NO REAL DATA AVAILABLE")
        print("💡 Get free API keys from:")
        print("   - Twelve Data: https://twelvedata.com/apikey")
        print("   - Alpha Vantage: https://www.alphavantage.co/support/#api-key")
    else:
        print(summary.to_string(index=False))