# src/analysis_pipeline.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collectors.data_fetcher import HKStockDataFetcher
from collectors.news_collector import NewsCollector
from analyzers.sentiment_analyzer import SentimentAnalyzer
from analyzers.indicators import TechnicalIndicators
from database import StockDatabase
import pandas as pd
from datetime import datetime

class StockAnalysisPipeline:
    """Complete analysis pipeline combining all components"""
    
    def __init__(self):
        self.fetcher = HKStockDataFetcher()
        self.news_collector = NewsCollector()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.technical_analyzer = TechnicalIndicators()
        self.database = StockDatabase()
        
        self.analysis_results = {}
        
    def analyze_single_stock(self, symbol):
        """Complete analysis for one stock"""
        print(f"\n🔍 Analyzing {symbol}...")
        
        results = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat()
        }
        
        # 1. Fetch price data
        price_data = self.fetcher.fetch_stock_data(symbol, period="1mo")
        
        if price_data.empty:
            print(f"  ❌ No price data available")
            return None
            
        # 2. Technical analysis
        analyzed_data = self.technical_analyzer.analyze_stock(price_data)
        signals = self.technical_analyzer.get_current_signals(analyzed_data)
        
        results['price'] = price_data['Close'].iloc[-1]
        results['price_change'] = price_data['Daily_Return'].iloc[-1] * 100 if 'Daily_Return' in price_data else 0
        results['rsi'] = signals['RSI']['value'] if signals else 50
        results['rsi_signal'] = signals['RSI']['signal'] if signals else 'Unknown'
        results['volume_unusual'] = signals['Volume']['unusual'] if signals else False
        
        # 3. News collection
        news = self.news_collector.search_company_news(symbol, days_back=7)
        results['news_count'] = len(news)
        
        # 4. Sentiment analysis
        if news:
            sentiments = self.sentiment_analyzer.analyze_news_batch(news)
            agg_sentiment = self.sentiment_analyzer.calculate_aggregate_sentiment(sentiments)
            
            results['sentiment_score'] = agg_sentiment['average_score']
            results['sentiment_label'] = agg_sentiment['label']
            results['positive_news'] = agg_sentiment['positive_count']
            results['negative_news'] = agg_sentiment['negative_count']
        else:
            results['sentiment_score'] = 0
            results['sentiment_label'] = 'neutral'
            results['positive_news'] = 0
            results['negative_news'] = 0
        
        # 5. Calculate combined score (Technical + Sentiment)
        technical_score = (results['rsi'] - 50) / 50  # Normalize RSI to -1 to 1
        sentiment_score = results['sentiment_score']
        
        # Weighted combination: 60% technical, 40% sentiment
        results['combined_score'] = (technical_score * 0.6) + (sentiment_score * 0.4)
        
        # 6. Generate recommendation
        if results['combined_score'] > 0.3:
            results['recommendation'] = "BULLISH 🚀"
        elif results['combined_score'] < -0.3:
            results['recommendation'] = "BEARISH 📉"
        else:
            results['recommendation'] = "NEUTRAL ➡️"
        
        # 7. Save to database
        self.database.save_price_data(symbol, analyzed_data)
        
        return results
    
    def analyze_all_stocks(self):
        """Analyze all tracked stocks"""
        print("="*60)
        print(" "*15 + "🤖 COMPREHENSIVE STOCK ANALYSIS")
        print("="*60)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        all_results = []
        
        for symbol, name in self.fetcher.stocks.items():
            result = self.analyze_single_stock(symbol)
            if result:
                result['name'] = name
                all_results.append(result)
                self.analysis_results[symbol] = result
        
        return all_results
    
    def generate_report(self):
        """Generate analysis report"""
        if not self.analysis_results:
            print("No analysis results available")
            return
        
        print("\n" + "="*60)
        print(" "*20 + "📊 ANALYSIS REPORT")
        print("="*60)
        
        # Convert to DataFrame for easy analysis
        df = pd.DataFrame(self.analysis_results.values())
        
        # Sort by combined score
        df_sorted = df.sort_values('combined_score', ascending=False)
        
        print("\n🏆 STOCK RANKINGS (by Combined Score)")
        print("-"*50)
        
        for idx, row in df_sorted.iterrows():
            emoji = "🥇" if idx == df_sorted.index[0] else "🥈" if idx == df_sorted.index[1] else "🥉" if idx == df_sorted.index[2] else "  "
            
            print(f"{emoji} {row['name']} ({row['symbol']})")
            print(f"   Price: ${row['price']:.2f} ({row['price_change']:+.2f}%)")
            print(f"   Technical: RSI {row['rsi']:.1f} ({row['rsi_signal']})")
            print(f"   Sentiment: {row['sentiment_label']} ({row['sentiment_score']:+.3f})")
            print(f"   News: {row['positive_news']}↑ {row['negative_news']}↓ from {row['news_count']} articles")
            print(f"   📍 {row['recommendation']}")
            print()
        
        # Market Overview
        print("\n📈 MARKET OVERVIEW")
        print("-"*50)
        
        bullish = len(df[df['recommendation'].str.contains('BULLISH')])
        bearish = len(df[df['recommendation'].str.contains('BEARISH')])
        neutral = len(df[df['recommendation'].str.contains('NEUTRAL')])
        
        print(f"Bullish Stocks: {bullish}")
        print(f"Bearish Stocks: {bearish}")
        print(f"Neutral Stocks: {neutral}")
        
        avg_sentiment = df['sentiment_score'].mean()
        if avg_sentiment > 0.1:
            market_mood = "😊 Positive"
        elif avg_sentiment < -0.1:
            market_mood = "😟 Negative"
        else:
            market_mood = "😐 Neutral"
        
        print(f"\nOverall Market Sentiment: {market_mood} ({avg_sentiment:+.3f})")
        
        return df

# Run the complete pipeline
if __name__ == "__main__":
    pipeline = StockAnalysisPipeline()
    
    # Analyze all stocks
    results = pipeline.analyze_all_stocks()
    
    # Generate report
    report_df = pipeline.generate_report()
    
    # Save report
    if report_df is not None:
        report_df.to_csv('data/processed/analysis_report.csv', index=False)
        print("\n💾 Report saved to: data/processed/analysis_report.csv")