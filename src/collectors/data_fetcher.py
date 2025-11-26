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
    """Hong Kong Stock Data Fetcher - With Alltick API and Fallback Data"""
    
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
        
        # API Keys - Updated for Alltick
        self.alltick_key = os.getenv('ALLTICK_API_KEY', '')
        self.twelve_data_key = os.getenv('TWELVE_DATA_API_KEY', '')
        
    def fetch_stock_data(self, symbol, period="1mo"):
        """Fetch stock data - tries real APIs first, then fallback"""
        cache_key = f"{symbol}_{period}"
        
        # Check cache first
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if (datetime.now() - cached_time).seconds < self.cache_duration:
                print(f"📦 Using cached data for {symbol}")
                return cached_data
        
        print(f"🔄 Fetching data for {symbol}")
        
        # Try multiple REAL data sources in order
        data_sources = [
            self._fetch_alltick_data,    # Primary - Alltick
            self._fetch_twelve_data,     # Secondary - Twelve Data
            self._fetch_yfinance_with_retry,  # Tertiary - yfinance
        ]
        
        data = pd.DataFrame()
        data_source = "none"
        
        for source in data_sources:
            data = source(symbol, period)
            if not data.empty:
                data_source = source.__name__.replace('_fetch_', '')
                print(f"✅ Got {data_source} data for {symbol}")
                break
        
        # If no real data, use fallback data
        if data.empty:
            print(f"⚠️ No real data for {symbol}, using fallback data")
            data = self._generate_fallback_data(symbol)
            data_source = "fallback"
        
        # Add technical indicators
        data = self._add_technical_indicators(data)
        data.attrs['data_source'] = data_source
        
        # Cache the result
        self.cache[cache_key] = (datetime.now(), data)
            
        return data
    
    def _fetch_alltick_data(self, symbol, period):
        """Try multiple Alltick API endpoints"""
        if not self.alltick_key:
            return pd.DataFrame()
        # Try different endpoints
        endpoints = [
            "https://api.alltick.co/v1/historical",
            "https://api.alltick.co/v1/quote",
            "https://api.alltick.co/v1/eod",
            ]
        # Try different symbol formats
        symbol_formats = [
            symbol,  # 0700.HK
            symbol.replace('.HK', ''),  # 0700
            symbol.replace('.HK', '.HKX'),  # 0700.HKX
            ]
        for endpoint in endpoints:
            for sym_format in symbol_formats:
                try:
                    print(f"   Trying {endpoint} with symbol {sym_format}...")
                    params = {
                        'symbol': sym_format,
                        'apikey': self.alltick_key,
                        }
                    # Add period-specific params
                    if 'historical' in endpoint:
                        params.update({'interval': '1d', 'outputsize': 5})
                    elif 'eod' in endpoint:
                        params.update({'limit': 5})
                    
                    response = requests.get(endpoint, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"   ✅ {endpoint} returned data")
                        # Try to parse the data
                        if "data" in data and data["data"]:
                            return self._parse_alltick_data(data["data"])
                        elif "quote" in data:
                            return self._parse_alltick_quote(data["quote"])
                        elif "Time Series" in data:
                            return self._parse_alltick_timeseries(data["Time Series"])
                        else:
                            print(f"   ⚠️ Unknown data format from {endpoint}")
                    else:
                        print(f"   ❌ {endpoint} HTTP {response.status_code}")
                except Exception as e:
                    print(f"   💥 {endpoint} failed: {e}")
        return pd.DataFrame()
        
    def _parse_alltick_data(self, data_list):
        """Parse Alltick data format"""
        records = []
        for item in data_list:
            records.append({
                'Date': item.get('datetime', datetime.now().strftime('%Y-%m-%d')),
                'Open': float(item.get('open', 0)),
                'High': float(item.get('high', 0)),
                'Low': float(item.get('low', 0)),
                'Close': float(item.get('close', 0)),
                'Volume': int(float(item.get('volume', 1000000)))
                })
        df = pd.DataFrame(records)
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.set_index('Date')
        df = df.sort_index()
        return df
    def _parse_alltick_quote(self, quote_data):
        """Parse Alltick quote format"""
        # Create single data point from quote
        date = datetime.now()
        df = pd.DataFrame([{
            'Open': float(quote_data.get('open', 0)),
            'High': float(quote_data.get('high', 0)),
            'Low': float(quote_data.get('low', 0)),
            'Close': float(quote_data.get('price', 0)),
            'Volume': int(float(quote_data.get('volume', 1000000)))
            }], index=[date])
        return df
    
    def _fetch_twelve_data(self, symbol, period):
        """Get real data from Twelve Data API"""
        try:
            if not self.twelve_data_key:
                return pd.DataFrame()
                
            print(f"   Trying Twelve Data for {symbol}...")
            
            # Convert symbol for Twelve Data format
            twelve_symbol = symbol.replace('.HK', ':HKG')
            
            url = "https://api.twelvedata.com/time_series"
            params = {
                'symbol': twelve_symbol,
                'interval': '1day',
                'outputsize': 30,
                'apikey': self.twelve_data_key,
                'format': 'JSON'
            }
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if "values" in data and data["values"]:
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
                            'Volume': int(float(item['volume'])) if item['volume'] else 1000000
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
    
    def _fetch_yfinance_with_retry(self, symbol, period):
        """Try yfinance with multiple attempts"""
        for attempt in range(2):  # Reduced to 2 attempts for speed
            try:
                print(f"   Trying yfinance (attempt {attempt + 1}) for {symbol}...")
                ticker = yf.Ticker(symbol)
                data = ticker.history(period=period, timeout=10)
                
                if not data.empty:
                    return data
                else:
                    print(f"   yfinance returned empty data for {symbol}")
                    
            except Exception as e:
                print(f"   yfinance attempt {attempt + 1} failed: {e}")
                
            time.sleep(1)
            
        return pd.DataFrame()
    
    def _generate_fallback_data(self, symbol):
        """Generate realistic fallback data when APIs fail"""
        print(f"   Generating fallback data for {symbol}")
        
        # Create date range for the last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Realistic base prices for HK stocks
        base_prices = {
            "0700.HK": 320.0,  # Tencent
            "9988.HK": 85.0,   # Alibaba
            "0005.HK": 60.0,   # HSBC
            "0941.HK": 68.0,   # China Mobile
            "1299.HK": 75.0    # AIA Group
        }
        
        base_price = base_prices.get(symbol, 50.0)
        current_price = base_price
        
        data = []
        for i, date in enumerate(date_range):
            # Simulate realistic price movements
            volatility = 0.02
            change = np.random.normal(0, volatility)
            current_price = max(1.0, current_price * (1 + change))  # Prevent negative prices
            
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
        """Add technical indicators to data"""
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
                    prev = data.iloc[-2] if len(data) > 1 else latest
                    
                    price_change = latest['Close'] - prev['Close']
                    change_percent = (price_change / prev['Close']) * 100 if prev['Close'] != 0 else 0
                    
                    summary.append({
                        'Symbol': symbol,
                        'Name': name,
                        'Price': round(float(latest['Close']), 2),
                        'Change': round(float(price_change), 2),
                        'Change %': round(float(change_percent), 2),
                        'Volume': int(latest['Volume']),
                        'Data_Source': data.attrs.get('data_source', 'unknown'),
                        'RSI': round(float(latest.get('RSI', 50)), 1),
                        'has_real_data': data.attrs.get('data_source') != 'fallback'
                    })
                else:
                    # Fallback entry
                    summary.append({
                        'Symbol': symbol,
                        'Name': name,
                        'Price': 0,
                        'Change': 0,
                        'Change %': 0,
                        'Volume': 0,
                        'Data_Source': 'error',
                        'RSI': 50,
                        'has_real_data': False
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
                    'RSI': 50,
                    'has_real_data': False
                })
        
        return pd.DataFrame(summary)

# Test the fetcher
if __name__ == "__main__":
    fetcher = HKStockDataFetcher()
    
    print("\n📊 Stock Data Test:")
    print("="*60)
    summary = fetcher.get_summary()
    
    if summary.empty:
        print("❌ NO DATA AVAILABLE")
    else:
        print(summary.to_string(index=False))
        print(f"\n📈 Data Sources:")
        for _, row in summary.iterrows():
            print(f"   {row['Symbol']}: {row['Data_Source']} (Real: {row['has_real_data']})")