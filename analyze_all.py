# analyze_all.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.collectors.data_fetcher import HKStockDataFetcher
from src.collectors.news_collector import NewsCollector
from src.database import StockDatabase
from src.analyzers.indicators import TechnicalIndicators
from datetime import datetime

def run_complete_analysis():
    """Run complete analysis pipeline"""
    print("="*60)
    print(" "*15 + "🤖 STOCK AI COMPLETE ANALYSIS")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize all components
    fetcher = HKStockDataFetcher()
    news_collector = NewsCollector()
    db = StockDatabase()
    analyzer = TechnicalIndicators()
    
    # Analysis results
    results = {}
    
    for symbol, name in fetcher.stocks.items():
        print(f"\n{'='*50}")
        print(f"📊 Analyzing {name} ({symbol})")
        print('='*50)
        
        # 1. Get price data
        price_data = fetcher.fetch_stock_data(symbol, period="1mo")
        
        if not price_data.empty:
            # 2. Calculate indicators
            analyzed_data = analyzer.analyze_stock(price_data)
            signals = analyzer.get_current_signals(analyzed_data)
            
            # 3. Get news (will use mock data without API key)
            news = news_collector.search_company_news(symbol, days_back=7)
            
            # 4. Store results
            latest_price = price_data['Close'].iloc[-1]
            prev_price = price_data['Close'].iloc[-2]
            change_pct = ((latest_price - prev_price) / prev_price) * 100
            
            results[symbol] = {
                'name': name,
                'price': latest_price,
                'change': change_pct,
                'rsi': signals['RSI']['value'] if signals else 50,
                'rsi_signal': signals['RSI']['signal'] if signals else 'Unknown',
                'volume_ratio': signals['Volume']['ratio'] if signals else 1.0,
                'news_count': len(news),
                'price_vs_sma': signals['Price_vs_SMA']['distance'] if signals else 0
            }
            
            # 5. Print summary
            print(f"\n💰 Price: ${latest_price:.2f} ({change_pct:+.2f}%)")
            print(f"📈 RSI: {results[symbol]['rsi']:.1f} ({results[symbol]['rsi_signal']})")
            print(f"📊 Price vs 20-day avg: {results[symbol]['price_vs_sma']:+.1f}%")
            print(f"📰 News articles: {results[symbol]['news_count']}")
            
            # 6. Save to database
            db.save_price_data(symbol, analyzed_data)
            
    # Final Summary
    print(f"\n{'='*60}")
    print(" "*20 + "📊 MARKET SUMMARY")
    print('='*60)
    
    # Find best and worst performers
    if results:
        best = max(results.items(), key=lambda x: x[1]['change'])
        worst = min(results.items(), key=lambda x: x[1]['change'])
        
        print(f"\n🚀 Best Performer: {best[1]['name']} ({best[0]})")
        print(f"   Change: {best[1]['change']:+.2f}%")
        
        print(f"\n📉 Worst Performer: {worst[1]['name']} ({worst[0]})")
        print(f"   Change: {worst[1]['change']:+.2f}%")
        
        # RSI extremes
        overbought = [s for s, d in results.items() if d['rsi'] > 70]
        oversold = [s for s, d in results.items() if d['rsi'] < 30]
        
        if overbought:
            print(f"\n⚠️ Overbought (RSI > 70): {', '.join(overbought)}")
        if oversold:
            print(f"\n💡 Oversold (RSI < 30): {', '.join(oversold)}")
        
        if not overbought and not oversold:
            print("\n✅ All stocks in neutral RSI range (30-70)")
    
    print("\n" + "="*60)
    print("Analysis complete! Data saved to data/processed/")
    print("="*60)

if __name__ == "__main__":
    run_complete_analysis()