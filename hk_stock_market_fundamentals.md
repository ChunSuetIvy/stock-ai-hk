# Hong Kong Stock Market Fundamentals - Pre-Project Learning Guide

## 1. Understanding Hong Kong Stock Exchange (HKEX)

### Basic Structure
HKEX (Hong Kong Exchanges and Clearing Limited) is the 9th largest stock exchange globally by market capitalization as of August 2024, and consists of multiple components including the Stock Exchange of Hong Kong (SEHK) for equities trading, Hong Kong Futures Exchange (HKFE) for futures contracts, and various clearinghouses for transaction settlement.

### Key Components:
- **SEHK (Stock Exchange of Hong Kong)**: Main equities trading platform
- **HKFE (Hong Kong Futures Exchange)**: Futures and derivatives trading
- **Clearinghouses**: HKSCC, HKCC, SEOCH, OTC Clear - ensure transaction settlement
- **Regulatory Body**: Securities and Futures Commission (SFC)

---

## 2. Trading Mechanics You Must Know

### Trading Hours (Hong Kong Time, GMT+8)
The regular trading time consists of a Pre-opening Session (9:00-9:30 am), Morning Session (9:30 am-12:00 pm), and Afternoon Session (1:00-4:00 pm), with the pre-opening session divided into order input period (9:00-9:15 am), non-cancelable period (9:15-9:20 am), and random matching period (9:20-9:22 am).

**Daily Schedule:**
- **Pre-opening Session**: 9:00 - 9:30 AM
  - 9:00-9:15: Can place/cancel orders
  - 9:15-9:20: Can place but NOT cancel orders  
  - 9:20-9:22: Random matching for opening price
- **Morning Session**: 9:30 AM - 12:00 PM
- **Lunch Break**: 12:00 - 1:00 PM
- **Afternoon Session**: 1:00 - 4:00 PM
- **Closing Auction Session (CAS)**: 4:00 - 4:10 PM (for eligible securities)

### Key Trading Rules
1. Hong Kong uses T+0 trading mode, allowing stocks purchased on the same day to be sold on the same day with no limit on the number of daily transactions.

2. There is no limit on the trading range of securities in Hong Kong - a stock may rise or fall by 20% or more in one day.

3. Settlement follows T+2 cycle - cash from selling stocks can only be withdrawn two trading days after the sale.

4. **Board Lots**: Stocks trade in specific lot sizes (100, 500, 1000 shares, etc.)

5. Short selling is allowed but naked short selling is prohibited and short sell orders must be properly marked.

---

## 3. Stock Ticker Format

### Critical for Your Project!
For Hong Kong stocks, Yahoo Finance requires users to enter tickers as 4-digit numbers followed by ".HK" - for example, HSBC Holdings with ticker 5 is entered as "0005.HK".

**Examples:**
- Tencent: 0700.HK
- HSBC: 0005.HK  
- Alibaba: 9988.HK
- China Mobile: 0941.HK

**Important**: Always pad with zeros to make 4 digits!

---

## 4. Key Market Indices

### Hang Seng Index (HSI)
- **Symbol**: ^HSI (Yahoo Finance), HSI (most platforms)
- Main benchmark index for Hong Kong market
- Contains about 50 of the largest companies on the exchange
- Tracked by ETF 2800.HK (Tracker Fund)

### Other Important Indices:
- **Hang Seng China Enterprises Index (HSCEI)**: H-shares index
- **Hang Seng Tech Index**: Technology companies
- **Hang Seng Composite Index**: Broader market coverage

---

## 5. Types of Shares

### H-Shares
H-shares refer to securities of companies incorporated in mainland China that are listed on the Hong Kong Stock Exchange, allowing them to be traded internationally.
- Examples: Bank of China (3988.HK), PetroChina (0857.HK)

### Red Chips
- Mainland Chinese companies incorporated outside mainland China
- Examples: China Mobile (0941.HK), CNOOC (0883.HK)

### Blue Chips
- Large, established companies with stable earnings
- Examples: HSBC (0005.HK), CK Hutchison (0001.HK)

---

## 6. Data Sources for Your Project

### Free Data APIs

#### 1. **yfinance (Recommended for Starting)**
```python
import yfinance as yf

# Get HK stock data
hsbc = yf.Ticker("0005.HK")
hist = hsbc.history(period="1mo")

# Get Hang Seng Index
hsi = yf.Ticker("^HSI")
```

**Pros:**
- US stock price and index data are free, accepts stock tickers directly when requesting data, and provides meta data and stock statistics.
- Easy to use, well-documented
- Includes dividends, stock splits

**Cons:**
- Yahoo Finance data is not completely accurate, especially for Hong Kong stocks, particularly when involving dividend adjustments or Hong Kong ETFs like 2800.
- Rate limited for high-frequency requests

#### 2. **Alpha Vantage**
- Free tier: 5 API calls/minute, 500/day
- Good for fundamental data
- Requires API key

#### 3. **IEX Cloud**
- Limited HK stock coverage
- Better for US stocks
- Free tier available

### News Data Sources

#### For Sentiment Analysis:
1. **NewsAPI**: General news, free tier available
2. **Reddit API**: r/HongKong, r/stocks sentiment
3. **HKEX News**: Official announcements (web scraping needed)
4. **Finnhub**: Some free real-time news

---

## 7. Market Terminology

### Essential Terms:
- **Bid/Ask Spread**: Difference between buy and sell prices
- **Market Depth**: Available buy/sell orders at different prices
- **Turnover**: Total value of shares traded
- **Market Cap**: Total value of company's shares
- **P/E Ratio**: Price-to-earnings ratio
- **Dividend Yield**: Annual dividends / share price

### HK-Specific Terms:
- **Board Lot**: Minimum trading unit
- **Stamp Duty**: 0.13% tax on stock transactions
- **SFC**: Securities and Futures Commission (regulator)
- **CCASS**: Central Clearing and Settlement System

---

## 8. Technical Indicators Relevant to HK Market

### Volume-Based (Important for HK)
- **Volume Weighted Average Price (VWAP)**: Critical for HK trading
- **On-Balance Volume (OBV)**: Track accumulation/distribution
- **Money Flow Index**: Combines price and volume

### Trend Indicators
- **Moving Averages**: 10, 20, 50, 250-day commonly used
- **MACD**: Popular in HK trading community
- **Bollinger Bands**: Volatility indicator

### HK Trader Favorites
- **RSI**: Overbought/oversold conditions
- **Stochastic Oscillator**: Momentum indicator
- **Ichimoku Cloud**: Popular with Asian traders

---

## 9. Practical Coding Considerations

### Data Pipeline Architecture
```python
# Basic structure for HK stock data collection
class HKStockDataPipeline:
    def __init__(self):
        self.symbols = ["0700.HK", "0005.HK", "9988.HK"]  # Start with few
        self.cache = {}  # Store data to avoid rate limits
        
    def fetch_price_data(self, symbol, period="1mo"):
        # Add 4-digit padding
        formatted_symbol = self.format_hk_symbol(symbol)
        # Implement caching logic
        # Handle connection errors
        
    def format_hk_symbol(self, symbol):
        # Ensure 4 digits + .HK format
        if not symbol.endswith(".HK"):
            symbol = f"{int(symbol):04d}.HK"
        return symbol
```

### Rate Limiting Strategy
```python
import time
from functools import wraps

def rate_limit(calls_per_second=1):
    min_interval = 1.0 / calls_per_second
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        return wrapper
    return decorator
```

### Handling Market Hours
```python
import pytz
from datetime import datetime, time

def is_hk_market_open():
    hk_tz = pytz.timezone('Asia/Hong_Kong')
    now = datetime.now(hk_tz)
    
    # Check if weekend
    if now.weekday() > 4:  # Saturday = 5, Sunday = 6
        return False
    
    # Check trading hours
    current_time = now.time()
    morning_start = time(9, 30)
    morning_end = time(12, 0)
    afternoon_start = time(13, 0)
    afternoon_end = time(16, 0)
    
    return (morning_start <= current_time <= morning_end) or \
           (afternoon_start <= current_time <= afternoon_end)
```

---

## 10. Database Schema Suggestions

### Core Tables for Your Project

```sql
-- Stock master data
CREATE TABLE stocks (
    symbol VARCHAR(10) PRIMARY KEY,  -- e.g., "0700.HK"
    name VARCHAR(100),
    sector VARCHAR(50),
    market_cap DECIMAL(20,2),
    listing_date DATE
);

-- Price data (OHLCV)
CREATE TABLE price_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10),
    date DATE,
    open DECIMAL(10,2),
    high DECIMAL(10,2),
    low DECIMAL(10,2),
    close DECIMAL(10,2),
    volume BIGINT,
    FOREIGN KEY (symbol) REFERENCES stocks(symbol),
    UNIQUE(symbol, date)
);

-- News sentiment
CREATE TABLE news_sentiment (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10),
    headline TEXT,
    source VARCHAR(100),
    published_at TIMESTAMP,
    sentiment_score DECIMAL(3,2),  -- -1 to 1
    confidence DECIMAL(3,2),
    FOREIGN KEY (symbol) REFERENCES stocks(symbol)
);

-- Technical indicators
CREATE TABLE technical_indicators (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10),
    date DATE,
    indicator_name VARCHAR(50),  -- 'RSI', 'MACD', etc.
    value DECIMAL(10,4),
    FOREIGN KEY (symbol) REFERENCES stocks(symbol)
);
```

---

## 11. Quick Reference - Top HK Stocks to Track

### For Your Initial Testing (Start with these):

| Symbol | Company | Why Important |
|--------|---------|--------------|
| 0700.HK | Tencent | Largest tech stock, high volume |
| 0005.HK | HSBC | Banking sector leader |
| 9988.HK | Alibaba | Dual-listed, high volatility |
| 0941.HK | China Mobile | Telecom giant, stable |
| 2318.HK | Ping An | Insurance leader |
| 0388.HK | HKEx | The exchange itself |
| 1299.HK | AIA | Insurance, international |
| 0939.HK | CCB | Major Chinese bank |

---

## 12. Common Pitfalls to Avoid

1. **Data Quality Issues**
   - Always validate Yahoo Finance data
   - Check for adjusted vs. unadjusted prices
   - Handle missing data gracefully

2. **Time Zone Confusion**
   - HK is GMT+8, no daylight saving
   - Convert all timestamps consistently
   - Store in UTC, display in HK time

3. **Symbol Format Errors**
   - Always use 4-digit format for HK stocks
   - Don't forget the .HK suffix for Yahoo Finance
   - Some APIs use different formats (just numbers)

4. **Market Hours**
   - Remember lunch break (12:00-13:00)
   - Check for HK public holidays
   - Half-day trading before major holidays

5. **Currency**
   - HK stocks trade in HKD
   - 1 USD ≈ 7.8 HKD (pegged)
   - Consider currency in calculations

---

## 13. Recommended Learning Sequence

### Week 0 (Before Starting Project):
1. **Day 1-2**: Understand HKEX structure and trading rules
2. **Day 3**: Test yfinance with 5 HK stocks, verify data quality
3. **Day 4**: Learn about HSI index composition
4. **Day 5**: Understand sentiment analysis basics for financial text
5. **Day 6-7**: Design your database schema and data pipeline

### Quick Experiments to Try:
```python
# 1. Fetch and compare data
import yfinance as yf
tencent = yf.Ticker("0700.HK")
print(tencent.info)  # Check what data is available
print(tencent.history(period="1w"))  # Get week of data

# 2. Check market hours
from datetime import datetime
import pytz
hk_time = datetime.now(pytz.timezone('Asia/Hong_Kong'))
print(f"HK Time: {hk_time}")

# 3. Calculate basic indicators
import pandas as pd
df = tencent.history(period="1mo")
df['SMA_10'] = df['Close'].rolling(window=10).mean()
df['RSI'] = calculate_rsi(df['Close'])  # Implement this

# 4. Test news API
# Try NewsAPI with query "Hong Kong stocks"
```

---

## Next Steps

1. **Set up development environment** with Python, PostgreSQL, Redis
2. **Register for API keys**: NewsAPI, Alpha Vantage (backup)
3. **Create GitHub repo** with proper .gitignore for API keys
4. **Start with data collection** before moving to analysis
5. **Focus on 5-10 stocks initially** to keep scope manageable

Remember: The goal is to demonstrate AI/ML capabilities applied to finance, not to build a production trading system. Focus on clean code, good documentation, and impressive visualizations for your portfolio!
