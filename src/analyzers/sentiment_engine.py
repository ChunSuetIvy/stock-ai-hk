# src/analyzers/sentiment_engine.py
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime, timedelta
import logging
from .sentiment_analyzer import SentimentAnalyzer
a
class EnhancedSentimentEngine:
    """Enhanced sentiment analysis with scoring and trends"""
    
    def __init__(self):
        self.base_analyzer = SentimentAnalyzer()
        self.logger = logging.getLogger(__name__)
    
    def calculate_sentiment_score(self, news_data: List[Dict]) -> Dict:
        """Calculate comprehensive sentiment score"""
        if not news_data:
            return {
                'sentiment_score': 0.0,
                'sentiment_trend': 'neutral',
                'news_count': 0,
                'confidence': 0.0,
                'signal': 'NEUTRAL'
            }
        
        try:
            # Use base analyzer for individual article sentiment
            analyzed_articles = self.base_analyzer.analyze_news_batch(news_data)
            agg_sentiment = self.base_analyzer.calculate_aggregate_sentiment(analyzed_articles)
            
            # Calculate trend (compare recent vs older news)
            recent_news = analyzed_articles[:min(3, len(analyzed_articles))]
            older_news = analyzed_articles[3:6] if len(analyzed_articles) > 3 else recent_news
            
            recent_avg = sum([n['sentiment_score'] for n in recent_news]) / len(recent_news) if recent_news else 0
            older_avg = sum([n['sentiment_score'] for n in older_news]) / len(older_news) if older_news else recent_avg
            
            trend = 'improving' if recent_avg > older_avg else 'deteriorating' if recent_avg < older_avg else 'stable'
            
            # Calculate confidence based on volume and consistency
            scores = [article['sentiment_score'] for article in analyzed_articles]
            score_std = np.std(scores) if len(scores) > 1 else 0
            confidence = max(0, 1 - score_std) * min(1, len(news_data) / 10)
            
            # Determine signal
            avg_score = agg_sentiment['average_score']
            if avg_score > 0.2:
                signal = "POSITIVE"
            elif avg_score < -0.2:
                signal = "NEGATIVE"
            else:
                signal = "NEUTRAL"
            
            return {
                'sentiment_score': round(avg_score, 3),
                'sentiment_trend': trend,
                'news_count': len(news_data),
                'confidence': round(confidence, 2),
                'signal': signal,
                'positive_count': agg_sentiment['positive_count'],
                'negative_count': agg_sentiment['negative_count'],
                'neutral_count': agg_sentiment['neutral_count'],
                'latest_sentiment': agg_sentiment['latest_sentiment']
            }
            
        except Exception as e:
            self.logger.error(f"Sentiment calculation error: {e}")
            return {
                'sentiment_score': 0.0, 
                'sentiment_trend': 'neutral', 
                'news_count': 0, 
                'confidence': 0.0,
                'signal': 'NEUTRAL'
            }
    
    def generate_sentiment_insights(self, sentiment_data: Dict, stock_symbol: str) -> List[str]:
        """Generate human-readable sentiment insights"""
        insights = []
        
        score = sentiment_data.get('sentiment_score', 0)
        trend = sentiment_data.get('sentiment_trend', 'neutral')
        news_count = sentiment_data.get('news_count', 0)
        signal = sentiment_data.get('signal', 'NEUTRAL')
        
        if news_count == 0:
            insights.append("📰 No recent news coverage available")
            return insights
        
        # Score-based insights
        if signal == "POSITIVE":
            insights.append("😊 Strong positive sentiment in recent news")
        elif signal == "NEGATIVE":
            insights.append("😟 Strong negative sentiment in recent news")
        else:
            insights.append("😐 Neutral news sentiment overall")
        
        # Trend-based insights
        if trend == 'improving':
            insights.append("📈 Sentiment showing recent improvement")
        elif trend == 'deteriorating':
            insights.append("📉 Sentiment showing recent decline")
        
        # Volume-based insights
        if news_count > 15:
            insights.append("🔥 High media coverage indicates strong market interest")
        elif news_count < 3:
            insights.append("ℹ️ Limited news coverage may affect sentiment reliability")
        
        # Breakdown insights
        pos = sentiment_data.get('positive_count', 0)
        neg = sentiment_data.get('negative_count', 0)
        neu = sentiment_data.get('neutral_count', 0)
        
        if pos > neg and pos > neu:
            insights.append(f"✅ Majority positive news ({pos} positive articles)")
        elif neg > pos and neg > neu:
            insights.append(f"❌ Majority negative news ({neg} negative articles)")
        
        return insights