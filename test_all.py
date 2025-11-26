# test_all.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.collectors.data_fetcher import HKStockDataFetcher
from src.database import StockDatabase
from src.analyzers.indicators import TechnicalIndicators

def test_system():
    print("="*60)
    print(" "*20 + "TESTING STOCK AI SYSTEM")
    print("="*60)
    
    # Initialize components
    fetcher = HKStockDataFetcher()
    db = StockDatabase()
    analyzer = TechnicalIndicators()
    
    # Test each stock
    for symbol, name in fetcher.stocks.items():
        print(f"\n📊 Processing {name} ({symbol})")
        print("-"*40)
        
        # Fetch data
        data = fetcher.fetch_stock_data(symbol, period="1mo")
        
        if not data.empty:
            # Save to database
            db.save_price_data(symbol, data)
            
            # Analyze
            analyzed = analyzer.analyze_stock(data)
            
            # Get signals
            signals = analyzer.get_current_signals(analyzed)
            
            if signals:
                latest_price = data['Close'].iloc[-1]
                change = data['Daily_Return'].iloc[-1] * 100 if 'Daily_Return' in data.columns else 0
                
                print(f"Price: ${latest_price:.2f} ({change:+.2f}%)")
                print(f"RSI: {signals['RSI']['value']:.1f} - {signals['RSI']['signal']}")
                print(f"Volume: {signals['Volume']['ratio']:.1f}x average")
        else:
            print("❌ No data available")
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    test_system()