# src/analyzers/sentiment_analyzer.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# We'll use a simpler model first, then upgrade to FinBERT
from textblob import TextBlob
import pandas as pd
from datetime import datetime

class SentimentAnalyzer:
    """Analyze sentiment of financial news"""
    
    def __init__(self):
        self.sentiment_cache = {}
        
    def analyze_text(self, text):
        """
        Simple sentiment analysis using TextBlob
        Returns: score between -1 (negative) and 1 (positive)
        """
        if not text:
            return 0.0
            
        try:
            blob = TextBlob(str(text))
            # Returns polarity: -1 to 1
            return blob.sentiment.polarity
        except:
            return 0.0
    
    def analyze_news_batch(self, articles):
        """Analyze sentiment for multiple articles"""
        results = []
        
        for article in articles:
            # Combine title and description for analysis
            text = f"{article.get('title', '')} {article.get('description', '')}"
            
            sentiment_score = self.analyze_text(text)
            
            # Classify sentiment
            if sentiment_score > 0.1:
                sentiment_label = "positive"
            elif sentiment_score < -0.1:
                sentiment_label = "negative"
            else:
                sentiment_label = "neutral"
            
            results.append({
                'title': article.get('title', ''),
                'published_at': article.get('publishedAt', ''),
                'sentiment_score': sentiment_score,
                'sentiment_label': sentiment_label,
                'source': article.get('source', {}).get('name', 'Unknown')
            })
            
        return results
    
    def calculate_aggregate_sentiment(self, sentiments):
        """Calculate overall sentiment for a stock"""
        if not sentiments:
            return {
                'average_score': 0.0,
                'label': 'neutral',
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'total_articles': 0
            }
        
        scores = [s['sentiment_score'] for s in sentiments]
        labels = [s['sentiment_label'] for s in sentiments]
        
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Determine overall label
        if avg_score > 0.1:
            overall_label = "positive"
        elif avg_score < -0.1:
            overall_label = "negative"
        else:
            overall_label = "neutral"
        
        return {
            'average_score': avg_score,
            'label': overall_label,
            'positive_count': labels.count('positive'),
            'negative_count': labels.count('negative'),
            'neutral_count': labels.count('neutral'),
            'total_articles': len(sentiments),
            'latest_sentiment': sentiments[0]['sentiment_label'] if sentiments else 'neutral'
        }
    
    def generate_sentiment_report(self, stock_sentiments):
        """Generate a report of sentiment analysis"""
        report = []
        
        for symbol, sentiments in stock_sentiments.items():
            agg = self.calculate_aggregate_sentiment(sentiments)
            
            report.append({
                'symbol': symbol,
                'sentiment_score': agg['average_score'],
                'sentiment_label': agg['label'],
                'positive': agg['positive_count'],
                'negative': agg['negative_count'],
                'neutral': agg['neutral_count'],
                'total': agg['total_articles']
            })
        
        return pd.DataFrame(report)

# Test the sentiment analyzer
if __name__ == "__main__":
    analyzer = SentimentAnalyzer()
    
    # Test with sample headlines
    test_headlines = [
        "Tencent stock soars to new heights amid strong earnings",
        "Alibaba faces regulatory challenges in domestic market",
        "HSBC maintains stable dividend despite economic headwinds",
        "China Mobile reports record subscriber growth",
        "AIA insurance sees mixed results in quarterly report"
    ]
    
    print("="*60)
    print(" "*20 + "SENTIMENT ANALYSIS TEST")
    print("="*60)
    
    for headline in test_headlines:
        score = analyzer.analyze_text(headline)
        
        if score > 0.1:
            label = "😊 Positive"
        elif score < -0.1:
            label = "😟 Negative"
        else:
            label = "😐 Neutral"
        
        print(f"\n📰 {headline}")
        print(f"   Sentiment: {label} (Score: {score:.3f})")