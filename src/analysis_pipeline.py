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
        """Complete analysis for one stock with robust error handling"""
        print(f"\n🔍 Analyzing {symbol}...")
        results = {
            'symbol': symbol,
            'name': self.fetcher.stocks.get(symbol, symbol),
            'timestamp': datetime.now().isoformat(),
            'has_real_data': False,
            'data_source': 'unknown'
            }
        try:
            # 1. Fetch price data
            price_data = self.fetcher.fetch_stock_data(symbol, period="1mo")
            if price_data.empty:
                print(f"  ⚠️ No price data available")
                # Set default values to prevent crashes
                results.update({
                    'price': 0,
                    'price_change': 0,
                    'rsi': 50,
                    'rsi_signal': 'NEUTRAL',
                    'volume_unusual': False,
                    'news_count': 0,
                    'sentiment_score': 0,
                    'sentiment_label': 'neutral',
                    'positive_news': 0,
                    'negative_news': 0,
                    'combined_score': 0,
                    'recommendation': 'NO DATA',
                    'has_real_data': False,
                    'data_source': 'none'
                })
                return results
            # Track data source
            results['data_source'] = price_data.attrs.get('data_source', 'unknown')
            results['has_real_data'] = price_data.attrs.get('data_source') != 'fallback'
            
            # 2. Technical analysis
            analyzed_data = self.technical_analyzer.analyze_stock(price_data)
            signals = self.technical_analyzer.get_current_signals(analyzed_data)
            
            results['price'] = float(price_data['Close'].iloc[-1])
            
            # Calculate price change safely
            if len(price_data) > 1 and 'Daily_Return' in price_data:
                results['price_change'] = float(price_data['Daily_Return'].iloc[-1] * 100)
            else:
                results['price_change'] = 0.0
            
            results['rsi'] = float(signals.get('RSI', {}).get('value', 50)) if signals else 50.0
            results['rsi_signal'] = signals.get('RSI', {}).get('signal', 'NEUTRAL') if signals else 'NEUTRAL'
            results['volume_unusual'] = signals.get('Volume', {}).get('unusual', False) if signals else False
            # 3. News collection
            try:
                news = self.news_collector.search_company_news(symbol, days_back=7)
                results['news_count'] = len(news)
            except Exception as e:
                print(f"  ⚠️ News collection failed: {e}")
                results['news_count'] = 0
                news = []
            # 4. Sentiment analysis
            if news and len(news) > 0:
                try:
                    sentiments = self.sentiment_analyzer.analyze_news_batch(news)
                    agg_sentiment = self.sentiment_analyzer.calculate_aggregate_sentiment(sentiments)
                    
                    results['sentiment_score'] = float(agg_sentiment.get('average_score', 0))
                    results['sentiment_label'] = agg_sentiment.get('label', 'neutral')
                    results['positive_news'] = agg_sentiment.get('positive_count', 0)
                    results['negative_news'] = agg_sentiment.get('negative_count', 0)
                except Exception as e:
                    print(f"  ⚠️ Sentiment analysis failed: {e}")
                    results['sentiment_score'] = 0.0
                    results['sentiment_label'] = 'neutral'
                    results['positive_news'] = 0
                    results['negative_news'] = 0
            else:
                results['sentiment_score'] = 0.0
                results['sentiment_label'] = 'neutral'
                results['positive_news'] = 0
                results['negative_news'] = 0
                
            # 5. Calculate combined score
            technical_score = (results['rsi'] - 50) / 50  # Normalize RSI to -1 to 1
            sentiment_score = results['sentiment_score']
            
            results['combined_score'] = float((technical_score * 0.6) + (sentiment_score * 0.4))
            
            # 6. Generate recommendation
            if results['combined_score'] > 0.3:
                results['recommendation'] = "BULLISH 🚀"
            elif results['combined_score'] < -0.3:
                results['recommendation'] = "BEARISH 📉"
            else:
                results['recommendation'] = "NEUTRAL ➡️"
            # Add data source indicator to recommendation if fallback
            if not results['has_real_data']:
                results['recommendation'] += " (SIMULATED DATA)"
            
            print(f"  ✅ Analysis complete for {symbol} (Source: {results['data_source']})")
        except Exception as e:
            print(f"  ❌ Analysis failed for {symbol}: {str(e)}")
            # Ensure all required fields are present even on error
            required_fields = {
                'price': 0, 'price_change': 0, 'rsi': 50, 'rsi_signal': 'NEUTRAL',
                'news_count': 0, 'sentiment_score': 0, 'sentiment_label': 'neutral',
                'positive_news': 0, 'negative_news': 0, 'combined_score': 0,
                'recommendation': 'ERROR', 'has_real_data': False, 'data_source': 'error'
            }
            for field, default in required_fields.items():
                if field not in results:
                    results[field] = default
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