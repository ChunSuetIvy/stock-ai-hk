# src/analyzers/analysis_orchestrator.py
from typing import Dict, List
import pandas as pd
import logging
from .technical_analyzer import EnhancedTechnicalAnalyzer
from .sentiment_engine import EnhancedSentimentEngine
from .risk_assessor import RiskAssessor

class AnalysisOrchestrator:
    """Main orchestrator that combines all analysis components"""
    
    def __init__(self):
        self.technical_analyzer = EnhancedTechnicalAnalyzer()
        self.sentiment_engine = EnhancedSentimentEngine()
        self.risk_assessor = RiskAssessor()
        self.logger = logging.getLogger(__name__)
    
    def analyze_stock(self, symbol: str, price_data: pd.DataFrame, news_data: List[Dict] = None) -> Dict:
        """Complete stock analysis combining all components"""
        try:
            if price_data.empty:
                return self._create_error_response(symbol, "No price data available")
            
            # Technical Analysis
            technical_analysis = self.technical_analyzer.calculate_technical_score(price_data)
            technical_insights = self.technical_analyzer.generate_technical_insights(technical_analysis, symbol)
            
            # Sentiment Analysis
            sentiment_analysis = self.sentiment_engine.calculate_sentiment_score(news_data or [])
            sentiment_insights = self.sentiment_engine.generate_sentiment_insights(sentiment_analysis, symbol)
            
            # Risk Assessment
            risk_analysis = self.risk_assessor.calculate_risk_score(
                price_data['Close'], 
                technical_analysis['technical_score'],
                sentiment_analysis['sentiment_score']
            )
            
            # Generate overall recommendation
            overall_recommendation = self._generate_overall_recommendation(
                technical_analysis, sentiment_analysis, risk_analysis
            )
            
            # Calculate price change
            price_change = self._calculate_price_change(price_data)
            
            return {
                'symbol': symbol,
                'current_price': round(price_data['Close'].iloc[-1], 2),
                'price_change': price_change,
                'technical_analysis': technical_analysis,
                'technical_insights': technical_insights,
                'sentiment_analysis': sentiment_analysis,
                'sentiment_insights': sentiment_insights,
                'risk_analysis': risk_analysis,
                'overall_recommendation': overall_recommendation,
                'analysis_timestamp': pd.Timestamp.now().isoformat(),
                'confidence_score': self._calculate_confidence(technical_analysis, sentiment_analysis)
            }
            
        except Exception as e:
            self.logger.error(f"Stock analysis error for {symbol}: {e}")
            return self._create_error_response(symbol, str(e))
    
    def _calculate_price_change(self, price_data: pd.DataFrame, periods: int = 1) -> float:
        """Calculate percentage price change"""
        if len(price_data) < periods + 1:
            return 0.0
        current = price_data['Close'].iloc[-1]
        previous = price_data['Close'].iloc[-(periods + 1)]
        return round(((current - previous) / previous) * 100, 2)
    
    def _calculate_confidence(self, technical: Dict, sentiment: Dict) -> float:
        """Calculate overall analysis confidence"""
        tech_confidence = technical.get('confidence', 0)
        sentiment_confidence = sentiment.get('confidence', 0)
        
        # Weight technical analysis more heavily
        overall_confidence = (tech_confidence * 0.7) + (sentiment_confidence * 0.3)
        return round(overall_confidence, 2)
    
    def _generate_overall_recommendation(self, technical: Dict, sentiment: Dict, risk: Dict) -> str:
        """Generate overall investment recommendation"""
        tech_signal = technical.get('signal', 'NEUTRAL')
        sentiment_signal = sentiment.get('signal', 'NEUTRAL')
        risk_level = risk.get('risk_level', 'MODERATE')
        
        # Simple decision matrix
        if tech_signal == 'BULLISH' and sentiment_signal == 'POSITIVE' and risk_level == 'LOW':
            return "STRONG BUY - Excellent technicals, positive sentiment, low risk"
        elif tech_signal == 'BULLISH' and sentiment_signal != 'NEGATIVE' and risk_level in ['LOW', 'MODERATE']:
            return "BUY - Positive outlook with acceptable risk"
        elif tech_signal == 'BEARISH' and sentiment_signal == 'NEGATIVE':
            return "SELL - Negative technicals and sentiment"
        elif risk_level == 'HIGH' or risk_level == 'VERY HIGH':
            return "HOLD - High risk, wait for better entry point"
        elif tech_signal == 'NEUTRAL' and sentiment_signal == 'NEUTRAL':
            return "HOLD - Neutral signals, monitor for changes"
        else:
            return "HOLD - Mixed signals, further monitoring recommended"
    
    def _create_error_response(self, symbol: str, error: str) -> Dict:
        """Create error response with default values"""
        return {
            'symbol': symbol,
            'error': error,
            'technical_analysis': {'technical_score': 50, 'signal': 'NEUTRAL', 'confidence': 0},
            'sentiment_analysis': {'sentiment_score': 0, 'signal': 'NEUTRAL', 'confidence': 0},
            'risk_analysis': {'risk_score': 50, 'risk_level': 'MODERATE'},
            'overall_recommendation': 'Analysis unavailable',
            'technical_insights': ['Technical analysis temporarily unavailable'],
            'sentiment_insights': ['Sentiment analysis temporarily unavailable']
        }