# setup.py - Enhanced version
import yfinance as yf
import pandas as pd
import os
from datetime import datetime

print("="*50)
print("STOCK AI PROJECT - INITIAL SETUP")
print("="*50)

# 1. Test multiple HK stocks
test_stocks = {
    "0700.HK": "Tencent",
    "9988.HK": "Alibaba",
    "0005.HK": "HSBC",
    "0941.HK": "China Mobile",
    "1299.HK": "AIA Group"
}

print("\n📊 Testing data fetch for 5 major HK stocks:")
print("-"*40)

successful_fetches = []
for symbol, name in test_stocks.items():
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period="5d")
        if not data.empty:
            latest_price = data['Close'].iloc[-1]
            print(f"✓ {name} ({symbol}): Latest price = {latest_price:.2f} HKD")
            successful_fetches.append(symbol)
        else:
            print(f"✗ {name} ({symbol}): No data retrieved")
    except Exception as e:
        print(f"✗ {name} ({symbol}): Error - {str(e)}")

print(f"\nSuccessfully fetched: {len(successful_fetches)}/5 stocks")

# 2. Create project directory structure
print("\n📁 Creating project structure:")
print("-"*40)

directories = [
    "data",
    "data/raw",
    "data/processed",
    "src",
    "src/collectors",
    "src/analyzers",
    "src/api",
    "notebooks",
    "tests",
    "config"
]

for dir_path in directories:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"✓ Created: {dir_path}/")
    else:
        print(f"• Exists: {dir_path}/")

# 3. Test data storage (save sample data)
print("\n💾 Testing data storage:")
print("-"*40)

# Fetch and save Tencent data as sample
tencent = yf.Ticker("0700.HK")
df = tencent.history(period="1mo")

# Save to CSV
csv_path = "data/raw/tencent_sample.csv"
df.to_csv(csv_path)
print(f"✓ Saved sample data to: {csv_path}")
print(f"  Data shape: {df.shape}")
print(f"  Date range: {df.index[0].date()} to {df.index[-1].date()}")

# 4. Display data statistics
print("\n📈 Sample Data Analysis (Tencent last 30 days):")
print("-"*40)
print(f"Average Close Price: {df['Close'].mean():.2f} HKD")
print(f"Highest Price: {df['High'].max():.2f} HKD")
print(f"Lowest Price: {df['Low'].min():.2f} HKD")
print(f"Average Volume: {df['Volume'].mean():,.0f} shares/day")
print(f"Price Change: {((df['Close'].iloc[-1] / df['Close'].iloc[0]) - 1) * 100:.2f}%")

# 5. Check if market is currently open
from datetime import datetime
import pytz

hk_tz = pytz.timezone('Asia/Hong_Kong')
now = datetime.now(hk_tz)
market_open = False

if now.weekday() < 5:  # Monday = 0, Friday = 4
    current_time = now.time()
    if (current_time >= datetime.strptime("09:30", "%H:%M").time() and 
        current_time <= datetime.strptime("12:00", "%H:%M").time()) or \
       (current_time >= datetime.strptime("13:00", "%H:%M").time() and 
        current_time <= datetime.strptime("16:00", "%H:%M").time()):
        market_open = True

print(f"\n⏰ Current Status:")
print("-"*40)
print(f"Hong Kong Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Market Status: {'🟢 OPEN' if market_open else '🔴 CLOSED'}")

# 6. Create requirements.txt
print("\n📦 Creating requirements.txt:")
print("-"*40)

requirements = """yfinance==0.2.18
pandas==2.0.2
numpy==1.24.3
fastapi==0.95.2
uvicorn==0.22.0
transformers==4.30.2
torch==2.0.1
requests==2.31.0
python-dotenv==1.0.0
psycopg2-binary==2.9.6
SQLAlchemy==2.0.15
redis==4.5.5
scikit-learn==1.2.2
ta-lib==0.4.26
plotly==5.14.1
pytz==2023.3
"""

with open("requirements.txt", "w") as f:
    f.write(requirements)
print("✓ Created requirements.txt")

print("\n✅ SETUP COMPLETE!")
print("="*50)
print("\nNext steps:")
print("1. Install dependencies: pip3 install -r requirements.txt")
print("2. Create .env file for API keys")
print("3. Start with data_fetcher.py tomorrow")