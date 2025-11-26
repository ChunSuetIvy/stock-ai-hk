# src/visualizer.py
import pandas as pd
import json

class SimpleVisualizer:
    """Create simple text-based visualizations"""
    
    @staticmethod
    def price_chart(df, days=20):
        """Simple ASCII price chart"""
        recent = df.tail(days)
        prices = recent['Close'].values
        
        # Normalize to 0-20 scale for display
        min_price = prices.min()
        max_price = prices.max()
        range_price = max_price - min_price
        
        if range_price == 0:
            return "Price unchanged"
        
        print(f"\n📊 Price Chart (Last {days} days)")
        print(f"High: ${max_price:.2f} | Low: ${min_price:.2f}")
        print("-" * 50)
        
        for i, price in enumerate(prices):
            height = int(((price - min_price) / range_price) * 20)
            bar = "█" * height
            print(f"Day {i+1:2d}: {bar} ${price:.2f}")
    
    @staticmethod
    def summary_dashboard(stock_data):
        """Create a summary dashboard"""
        print("\n" + "="*60)
        print(" "*20 + "📊 STOCK DASHBOARD")
        print("="*60)
        
        for symbol, data in stock_data.items():
            latest = data.iloc[-1]
            prev = data.iloc[-2]
            
            change = latest['Close'] - prev['Close']
            change_pct = (change / prev['Close']) * 100
            
            # Determine trend emoji
            if change_pct > 2:
                trend = "🚀"
            elif change_pct > 0:
                trend = "📈"
            elif change_pct < -2:
                trend = "💥"
            else:
                trend = "📉"
            
            print(f"\n{symbol} {trend}")
            print(f"Price: ${latest['Close']:.2f} ({change_pct:+.2f}%)")
            print(f"Volume: {latest['Volume']:,.0f}")
            if 'RSI' in data.columns:
                rsi_val = latest['RSI']
                if pd.notna(rsi_val):
                    print(f"RSI: {rsi_val:.1f}")
            print("-"*30)

# Test it
if __name__ == "__main__":
    import sys
    sys.path.append('..')
    from src.collectors.data_fetcher import HKStockDataFetcher
    from src.analyzers.indicators import TechnicalIndicators
    
    fetcher = HKStockDataFetcher()
    analyzer = TechnicalIndicators()
    visualizer = SimpleVisualizer()
    
    # Get all stock data
    all_data = fetcher.fetch_all_stocks()
    
    # Analyze all stocks
    analyzed_data = {}
    for symbol, df in all_data.items():
        analyzed_data[symbol] = analyzer.analyze_stock(df)
    
    # Show dashboard
    visualizer.summary_dashboard(analyzed_data)
    
    # Show price chart for Tencent
    visualizer.price_chart(analyzed_data['0700.HK'])