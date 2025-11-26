# src/collectors/news_collector.py
import requests
from datetime import datetime, timedelta
import time
import json
import os
import sys
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class NewsCollector:
    """Collect news for Hong Kong stocks"""
    
    def __init__(self, api_key=None):
        # Get free API key from https://newsapi.org
        self.api_key = api_key or os.getenv('NEWS_API_KEY')
        self.base_url = "https://newsapi.org/v2/everything"
        if not self.api_key:
            print("⚠️ No NEWS_API_KEY found in .env file")
            print("📝 To get a free API key:")
            print("   1. Go to https://newsapi.org")
            print("   2. Click 'Get API Key'")
            print("   3. Sign up (it's free)")
            print("   4. Copy your API key")
            print("   5. Add it to .env file")
        # Company name mappings for better search
        self.company_names = {
            "0700.HK": ["Tencent", "騰訊"],
            "9988.HK": ["Alibaba", "阿里巴巴", "BABA"],
            "0005.HK": ["HSBC", "匯豐"],
            "0941.HK": ["China Mobile", "中國移動"],
            "1299.HK": ["AIA", "友邦保險"]
        }
        
        # Store collected news
        self.news_cache = {}
        
    def search_company_news(self, symbol, days_back=7):
        """Search news for a specific company"""
        if not self.api_key:
            print("⚠️ No API key set. Get one from https://newsapi.org")
            return []
            
        company_names = self.company_names.get(symbol, [symbol])
        all_articles = []
        
        for name in company_names:
            params = {
                'q': f'"{name}" stock OR shares',
                'from': (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d'),
                'sortBy': 'publishedAt',
                'language': 'en',
                'apiKey': self.api_key,
                'pageSize': 10
            }
            
            try:
                response = requests.get(self.base_url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    articles = data.get('articles', [])
                    all_articles.extend(articles)
                    print(f"  Found {len(articles)} articles for {name}")
                    time.sleep(0.5)  # Rate limiting
                elif response.status_code == 426:
                    print("⚠️ API limit reached. Using mock data for demo.")
                    return self.get_mock_news(symbol)
                else:
                    print(f"  API Error {response.status_code}: {response.text}")
            except Exception as e:
                print(f"  Error fetching news: {str(e)}")
                
        # Remove duplicates by title
        unique_articles = {}
        for article in all_articles:
            title = article.get('title', '')
            if title and title not in unique_articles:
                unique_articles[title] = article
                
        return list(unique_articles.values())
    
    def get_mock_news(self, symbol):
        """Return mock news for testing when API is not available"""
        mock_templates = {
            "0700.HK": [
                {
                    "title": "Tencent Gaming Revenue Shows Strong Growth",
                    "description": "Tencent's gaming division reports 15% increase in Q3 revenue",
                    "publishedAt": datetime.now().isoformat(),
                    "sentiment": "positive"
                },
                {
                    "title": "Regulatory Concerns Impact Tencent Stock",
                    "description": "New regulations may affect Tencent's fintech operations",
                    "publishedAt": (datetime.now() - timedelta(days=1)).isoformat(),
                    "sentiment": "negative"
                }
            ],
            "9988.HK": [
                {
                    "title": "Alibaba Cloud Expansion Accelerates",
                    "description": "Alibaba announces new data centers in Southeast Asia",
                    "publishedAt": datetime.now().isoformat(),
                    "sentiment": "positive"
                }
            ]
        }
        return mock_templates.get(symbol, [])
    
    def process_articles(self, articles):
        """Process and structure articles for analysis"""
        processed = []
        for article in articles:
            processed.append({
                'title': article.get('title', ''),
                'description': article.get('description', ''),
                'content': article.get('content', ''),
                'published_at': article.get('publishedAt', ''),
                'source': article.get('source', {}).get('name', 'Unknown'),
                'url': article.get('url', ''),
                'sentiment_score': None  # Will be filled by sentiment analyzer
            })
        return processed
    
    def collect_all_news(self):
        """Collect news for all tracked stocks"""
        all_news = {}
        
        for symbol in self.company_names.keys():
            print(f"\n📰 Collecting news for {symbol}...")
            articles = self.search_company_news(symbol)
            processed = self.process_articles(articles)
            all_news[symbol] = processed
            
            # Cache the results
            self.news_cache[symbol] = {
                'collected_at': datetime.now().isoformat(),
                'articles': processed
            }
            
        return all_news
    
    def save_news(self, filepath='data/processed/news_data.json'):
        """Save collected news to file"""
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.news_cache, f, ensure_ascii=False, indent=2)
        print(f"💾 Saved news data to {filepath}")
        
    def load_news(self, filepath='data/processed/news_data.json'):
        """Load previously collected news"""
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                self.news_cache = json.load(f)
            print(f"📂 Loaded news data from {filepath}")
            return self.news_cache
        return {}

# Test the news collector
if __name__ == "__main__":
    # You can get a free API key from https://newsapi.org
    # For testing, we'll use mock data if no API key is provided
    
    collector = NewsCollector()  # Will use mock data without API key
    
    print("="*60)
    print(" "*20 + "NEWS COLLECTION TEST")
    print("="*60)
    
    # Test single stock
    print("\n📰 Testing news collection for Tencent (0700.HK):")
    news = collector.search_company_news("0700.HK", days_back=7)
    
    if news:
        for i, article in enumerate(news[:3], 1):  # Show first 3
            print(f"\n{i}. {article.get('title', 'No title')}")
            print(f"   Source: {article.get('source', {}).get('name', 'Unknown')}")
            if 'sentiment' in article:  # For mock data
                print(f"   Sentiment: {article.get('sentiment', 'neutral')}")
    else:
        print("   No news found (this is normal without API key)")
    
    # Collect all news
    print("\n" + "="*60)
    print("📰 Collecting news for all stocks...")
    all_news = collector.collect_all_news()
    
    # Save to file
    collector.save_news('data/processed/news_data.json')
    
    # Summary
    print("\n📊 News Collection Summary:")
    for symbol, articles in all_news.items():
        print(f"  {symbol}: {len(articles)} articles")