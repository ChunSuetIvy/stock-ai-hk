# src/analysis_pipeline.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collectors.data_fetcher import HKStockDataFetcher
from collectors.news_collector import NewsCollector
from analyzers.sentiment_analyzer import SentimentAnalyzer
from analyzers.indicators import TechnicalIndicators
from analyzers.analysis_orchestrator import AnalysisOrchestrator  # NEW - Make sure this import works
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
        self.analysis_orchestrator = AnalysisOrchestrator()  # NEW - Initialize the orchestrator
        self.database = StockDatabase()
        
        self.analysis_results = {}
        
    def analyze_single_stock(self, symbol):
        """Complete analysis for one stock using the new AI engine"""
        print(f"\n🔍 Analyzing {symbol}...")
        
        # Initialize results with basic structure
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
                return self._create_default_results(results)
            
            # Track data source
            results['data_source'] = 'yfinance' if not self.fetcher.is_railway else 'simulated'
            results['has_real_data'] = not self.fetcher.is_railway
            
            # 2. Fetch news data
            try:
                news = self.news_collector.search_company_news(symbol, days_back=7)
                results['news_count'] = len(news)
            except Exception as e:
                print(f"  ⚠️ News collection failed: {e}")
                results['news_count'] = 0
                news = []
            
            # 3. USE NEW ANALYSIS ORCHESTRATOR FOR COMPREHENSIVE ANALYSIS
            print(f"  🤖 Using AI analysis engine for {symbol}")
            analysis_result = self.analysis_orchestrator.analyze_stock(symbol, price_data, news)
            
            # 4. MAP NEW ANALYSIS RESULTS TO EXISTING FRONTEND STRUCTURE
            results.update(self._map_analysis_to_frontend_format(analysis_result, price_data))
            
            print(f"  ✅ AI analysis complete for {symbol}")
            print(f"     Technical Score: {results.get('technical_score', 'N/A')}")
            print(f"     Risk Level: {results.get('risk_level', 'N/A')}")
            
        except Exception as e:
            print(f"  ❌ Analysis failed for {symbol}: {str(e)}")
            results.update(self._create_error_results())
            
        return results
    
    def _map_analysis_to_frontend_format(self, analysis_result, price_data):
        """Map the new analysis format to the existing frontend expected format"""
        try:
            technical = analysis_result.get('technical_analysis', {})
            sentiment = analysis_result.get('sentiment_analysis', {})
            risk = analysis_result.get('risk_analysis', {})
            
            # Calculate price change (daily)
            price_change = 0.0
            if len(price_data) > 1:
                current_price = price_data['Close'].iloc[-1]
                prev_price = price_data['Close'].iloc[-2]
                price_change = ((current_price - prev_price) / prev_price) * 100
            
            # Map to existing frontend structure
            mapped_results = {
                'price': analysis_result.get('current_price', 0),
                'price_change': round(price_change, 2),
                'rsi': technical.get('rsi', 50),
                'rsi_signal': technical.get('rsi_signal', 'NEUTRAL'),
                'volume_unusual': technical.get('volume', {}).get('unusual', False),
                'news_count': sentiment.get('news_count', 0),
                'sentiment_score': sentiment.get('sentiment_score', 0),
                'sentiment_label': sentiment.get('signal', 'neutral').lower(),
                'positive_news': sentiment.get('positive_count', 0),
                'negative_news': sentiment.get('negative_count', 0),
                
                'has_real_data': not self.fetcher.is_railway,  # Add this!
                
                # NEW FIELDS FOR ENHANCED ANALYSIS
                'technical_score': technical.get('technical_score', 50),
                'technical_signal': technical.get('signal', 'NEUTRAL'),
                'risk_score': risk.get('risk_score', 50),
                'risk_level': risk.get('risk_level', 'MODERATE'),
                'technical_insights': analysis_result.get('technical_insights', []),
                'sentiment_insights': analysis_result.get('sentiment_insights', []),
                'ai_recommendation': analysis_result.get('overall_recommendation', 'Analysis unavailable'),
                'confidence_score': analysis_result.get('confidence_score', 0),
                
                # Backward compatibility - calculate combined_score for existing frontend
                'combined_score': self._calculate_legacy_combined_score(technical, sentiment)
            }
            
            # Generate legacy recommendation for existing frontend
            mapped_results['recommendation'] = self._generate_legacy_recommendation(
                mapped_results['combined_score'], 
                mapped_results['has_real_data']
            )
            
            return mapped_results
            
        except Exception as e:
            print(f"  ⚠️ Error mapping analysis results: {e}")
            return self._create_error_results()
    
    def _calculate_legacy_combined_score(self, technical, sentiment):
        """Calculate the legacy combined score for backward compatibility"""
        try:
            # Normalize technical score (0-100) to -1 to 1
            tech_score_normalized = (technical.get('technical_score', 50) - 50) / 50
            sentiment_score = sentiment.get('sentiment_score', 0)
            
            # Same weighting as before
            combined_score = (tech_score_normalized * 0.6) + (sentiment_score * 0.4)
            return float(combined_score)
        except:
            return 0.0
    
    def _generate_legacy_recommendation(self, combined_score, has_real_data):
        """Generate legacy recommendation format for existing frontend"""
        if combined_score > 0.3:
            recommendation = "BULLISH 🚀"
        elif combined_score < -0.3:
            recommendation = "BEARISH 📉"
        else:
            recommendation = "NEUTRAL ➡️"
            
        # Add data source indicator if fallback
        if not has_real_data:
            recommendation += " (SIMULATED DATA)"
            
        return recommendation
    
    def _create_default_results(self, base_results):
        """Create default results when no data is available"""
        default_results = {
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
            'technical_score': 50,
            'technical_signal': 'NEUTRAL',
            'risk_score': 50,
            'risk_level': 'MODERATE',
            'technical_insights': ['No technical data available'],
            'sentiment_insights': ['No sentiment data available'],
            'ai_recommendation': 'No data available for analysis',
            'confidence_score': 0,
            'recommendation': 'NO DATA',
            'has_real_data': False,
            'data_source': 'none'
        }
        base_results.update(default_results)
        return base_results
    
    def _create_error_results(self):
        """Create error results when analysis fails"""
        return {
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
            'technical_score': 50,
            'technical_signal': 'NEUTRAL',
            'risk_score': 50,
            'risk_level': 'MODERATE',
            'technical_insights': ['Technical analysis temporarily unavailable'],
            'sentiment_insights': ['Sentiment analysis temporarily unavailable'],
            'ai_recommendation': 'Analysis error occurred',
            'confidence_score': 0,
            'recommendation': 'ERROR',
            'has_real_data': False,
            'data_source': 'error'
        }
    
    def analyze_all_stocks(self):
        """Analyze all tracked stocks"""
        print("="*60)
        print(" "*15 + "🤖 ENHANCED AI STOCK ANALYSIS")
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
        """Generate enhanced analysis report"""
        if not self.analysis_results:
            print("No analysis results available")
            return
        
        print("\n" + "="*60)
        print(" "*20 + "📊 ENHANCED AI ANALYSIS REPORT")
        print("="*60)
        
        # Convert to DataFrame for easy analysis
        df = pd.DataFrame(self.analysis_results.values())
        
        # Sort by technical score (new primary metric)
        df_sorted = df.sort_values('technical_score', ascending=False)
        
        print("\n🏆 STOCK RANKINGS (by Technical Score)")
        print("-"*50)
        
        for idx, row in df_sorted.iterrows():
            emoji = "🥇" if idx == df_sorted.index[0] else "🥈" if idx == df_sorted.index[1] else "🥉" if idx == df_sorted.index[2] else "  "
            
            print(f"{emoji} {row['name']} ({row['symbol']})")
            print(f"   Price: ${row['price']:.2f} ({row['price_change']:+.2f}%)")
            print(f"   Technical Score: {row['technical_score']:.1f}/100 ({row['technical_signal']})")
            print(f"   RSI: {row['rsi']:.1f} | Risk: {row['risk_level']} ({row['risk_score']:.1f})")
            print(f"   Sentiment: {row['sentiment_label']} ({row['sentiment_score']:+.3f})")
            print(f"   News: {row['positive_news']}↑ {row['negative_news']}↓ from {row['news_count']} articles")
            print(f"   🤖 AI Recommendation: {row['ai_recommendation']}")
            
            # Show top insight if available
            if row.get('technical_insights') and len(row['technical_insights']) > 0:
                print(f"   💡 {row['technical_insights'][0]}")
            print()
        
        return df

# Run the enhanced pipeline
if __name__ == "__main__":
    pipeline = StockAnalysisPipeline()
    
    # Analyze all stocks with new AI engine
    results = pipeline.analyze_all_stocks()
    
    # Generate enhanced report
    report_df = pipeline.generate_report()
    
    # Save report
    if report_df is not None:
        os.makedirs('data/processed', exist_ok=True)
        report_df.to_csv('data/processed/analysis_report.csv', index=False)
        print("\n💾 Enhanced report saved to: data/processed/analysis_report.csv")