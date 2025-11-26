# src/analyzers/technical_analyzer.py
import pandas as pd
import numpy as np
import logging
from typing import Dict, List
from .indicators import TechnicalIndicators

class EnhancedTechnicalAnalyzer:
    """Enhanced technical analysis with scoring and insights"""
    
    def __init__(self):
        self.base_analyzer = TechnicalIndicators()
        self.logger = logging.getLogger(__name__)
    
    def calculate_macd(self, prices: pd.Series) -> Dict:
        """Calculate MACD indicator"""
        try:
            exp1 = prices.ewm(span=12).mean()
            exp2 = prices.ewm(span=26).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9).mean()
            histogram = macd - signal
            
            return {
                'macd': round(macd.iloc[-1], 4),
                'signal': round(signal.iloc[-1], 4),
                'histogram': round(histogram.iloc[-1], 4),
                'trend': 'bullish' if macd.iloc[-1] > signal.iloc[-1] else 'bearish'
            }
        except Exception as e:
            self.logger.error(f"MACD calculation error: {e}")
            return {'macd': 0, 'signal': 0, 'histogram': 0, 'trend': 'neutral'}
    
    def calculate_bollinger_bands(self, prices: pd.Series, window: int = 20) -> Dict:
        """Calculate Bollinger Bands"""
        try:
            sma = prices.rolling(window=window).mean()
            std = prices.rolling(window=window).std()
            upper_band = sma + (std * 2)
            lower_band = sma - (std * 2)
            
            current_price = prices.iloc[-1]
            position = (current_price - lower_band.iloc[-1]) / (upper_band.iloc[-1] - lower_band.iloc[-1])
            
            return {
                'upper_band': round(upper_band.iloc[-1], 2),
                'lower_band': round(lower_band.iloc[-1], 2),
                'sma': round(sma.iloc[-1], 2),
                'position': round(position, 2),
                'signal': 'overbought' if position > 0.8 else 'oversold' if position < 0.2 else 'neutral'
            }
        except Exception as e:
            self.logger.error(f"Bollinger Bands calculation error: {e}")
            return {'upper_band': 0, 'lower_band': 0, 'sma': 0, 'position': 0.5, 'signal': 'neutral'}
    
    def calculate_technical_score(self, df: pd.DataFrame) -> Dict:
        """Calculate comprehensive technical score (0-100)"""
        try:
            if df.empty:
                return {'technical_score': 50, 'signal': 'NEUTRAL', 'confidence': 0}
            
            prices = df['Close']
            signals = self.base_analyzer.get_current_signals(df)
            
            if not signals:
                return {'technical_score': 50, 'signal': 'NEUTRAL', 'confidence': 0}
            
            # RSI scoring (30-70 ideal)
            rsi = signals['RSI']['value']
            rsi_score = 100 - abs(50 - rsi) * 2
            
            # Price vs SMA scoring
            sma_score = 80 if signals['Price_vs_SMA']['above'] else 20
            sma_distance = abs(signals['Price_vs_SMA']['distance'])
            if sma_distance < 2:  # Very close to SMA
                sma_score = 50
            
            # Volume scoring
            volume_score = 30 if signals['Volume']['unusual'] else 70
            
            # Additional indicators
            macd_data = self.calculate_macd(prices)
            bb_data = self.calculate_bollinger_bands(prices)
            
            # MACD scoring
            macd_score = 50 + (macd_data['histogram'] * 1000)
            
            # Bollinger Bands scoring
            bb_score = 50 if bb_data['signal'] == 'neutral' else (
                30 if bb_data['signal'] == 'overbought' else 70
            )
            
            # Composite score (weighted)
            technical_score = (
                rsi_score * 0.25 +
                sma_score * 0.20 +
                volume_score * 0.15 +
                macd_score * 0.20 +
                bb_score * 0.20
            )
            
            technical_score = max(0, min(100, technical_score))
            
            # Determine signal
            if technical_score > 70:
                signal = "BULLISH"
            elif technical_score < 30:
                signal = "BEARISH"
            else:
                signal = "NEUTRAL"
            
            return {
                'technical_score': round(technical_score, 1),
                'signal': signal,
                'rsi': rsi,
                'rsi_signal': signals['RSI']['signal'],
                'price_vs_sma': {
                    'above': signals['Price_vs_SMA']['above'],
                    'distance_pct': signals['Price_vs_SMA']['distance']
                },
                'volume': {
                    'unusual': signals['Volume']['unusual'],
                    'ratio': signals['Volume']['ratio']
                },
                'macd': macd_data,
                'bollinger_bands': bb_data,
                'confidence': min(1.0, abs(technical_score - 50) / 50)  # Distance from neutral
            }
            
        except Exception as e:
            self.logger.error(f"Technical score calculation error: {e}")
            return {'technical_score': 50, 'signal': 'NEUTRAL', 'confidence': 0}
    
    def generate_technical_insights(self, analysis: Dict, symbol: str) -> List[str]:
        """Generate human-readable technical insights"""
        insights = []
        
        score = analysis['technical_score']
        rsi = analysis['rsi']
        rsi_signal = analysis['rsi_signal']
        price_vs_sma = analysis['price_vs_sma']
        volume = analysis['volume']
        macd = analysis['macd']
        bb = analysis['bollinger_bands']
        
        # Score-based insights
        if score > 80:
            insights.append("🚀 Strong bullish technical signals")
        elif score > 60:
            insights.append("📈 Moderately bullish technical outlook")
        elif score < 20:
            insights.append("🔻 Strong bearish technical signals")
        elif score < 40:
            insights.append("📉 Moderately bearish technical outlook")
        else:
            insights.append("➡️ Mixed or neutral technical signals")
        
        # RSI insights
        if rsi_signal == 'Overbought':
            insights.append("⚡ RSI indicates overbought conditions")
        elif rsi_signal == 'Oversold':
            insights.append("💎 RSI indicates oversold conditions")
        
        # Price vs SMA insights
        if price_vs_sma['above']:
            insights.append(f"📊 Trading above 20-day SMA by {price_vs_sma['distance_pct']:.2f}%")
        else:
            insights.append(f"📊 Trading below 20-day SMA by {abs(price_vs_sma['distance_pct']):.2f}%")
        
        # Volume insights
        if volume['unusual']:
            insights.append(f"🔥 Unusual volume detected ({volume['ratio']:.1f}x average)")
        
        # MACD insights
        if macd['trend'] == 'bullish':
            insights.append("📈 MACD shows bullish momentum")
        elif macd['trend'] == 'bearish':
            insights.append("📉 MACD shows bearish momentum")
        
        # Bollinger Bands insights
        if bb['signal'] == 'overbought':
            insights.append("🎯 Price near upper Bollinger Band (potential resistance)")
        elif bb['signal'] == 'oversold':
            insights.append("🎯 Price near lower Bollinger Band (potential support)")
        
        return insights