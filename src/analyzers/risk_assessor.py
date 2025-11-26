# src/analyzers/risk_assessor.py
import pandas as pd
import numpy as np
from typing import Dict
import logging

class RiskAssessor:
    """Risk assessment and scoring engine"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_volatility(self, prices: pd.Series, window: int = 30) -> float:
        """Calculate historical volatility"""
        try:
            returns = prices.pct_change().dropna()
            if len(returns) < 2:
                return 0.0
            volatility = returns.rolling(window=min(window, len(returns))).std().iloc[-1]
            annualized_vol = volatility * np.sqrt(252)  # Annualize
            return round(annualized_vol, 4)
        except Exception as e:
            self.logger.error(f"Volatility calculation error: {e}")
            return 0.0
    
    def calculate_support_resistance(self, prices: pd.Series, window: int = 20) -> Dict:
        """Identify key support and resistance levels"""
        try:
            if len(prices) < window:
                window = len(prices)
                
            support = prices.rolling(window=window).min().iloc[-1]
            resistance = prices.rolling(window=window).max().iloc[-1]
            current_price = prices.iloc[-1]
            
            # Distance to support/resistance as percentage
            dist_to_support = ((current_price - support) / current_price) * 100
            dist_to_resistance = ((resistance - current_price) / current_price) * 100
            
            return {
                'support_level': round(support, 2),
                'resistance_level': round(resistance, 2),
                'dist_to_support_pct': round(dist_to_support, 2),
                'dist_to_resistance_pct': round(dist_to_resistance, 2),
                'position': 'near_support' if dist_to_support < 5 else 'near_resistance' if dist_to_resistance < 5 else 'mid_range'
            }
        except Exception as e:
            self.logger.error(f"Support/resistance calculation error: {e}")
            return {'support_level': 0, 'resistance_level': 0, 'position': 'unknown'}
    
    def calculate_risk_score(self, prices: pd.Series, technical_score: float, sentiment_score: float) -> Dict:
        """Calculate comprehensive risk score (0-100, lower is safer)"""
        try:
            volatility = self.calculate_volatility(prices)
            sr_levels = self.calculate_support_resistance(prices)
            
            # Volatility component (0-40 points)
            vol_score = min(40, volatility * 1000)  # Scale volatility
            
            # Technical score component (0-30 points)
            tech_risk = 30 - (technical_score * 0.3)  # Invert technical score
            
            # Sentiment component (0-20 points)
            sentiment_risk = 10 - (sentiment_score * 50)  # Negative sentiment increases risk
            sentiment_risk = max(0, min(20, sentiment_risk))
            
            # Support/resistance component (0-10 points)
            sr_risk = 0
            if sr_levels['position'] == 'near_support':
                sr_risk = 3  # Lower risk near support
            elif sr_levels['position'] == 'near_resistance':
                sr_risk = 8  # Higher risk near resistance
            else:
                sr_risk = 5  # Medium risk in middle
            
            total_risk_score = vol_score + tech_risk + sentiment_risk + sr_risk
            total_risk_score = max(0, min(100, total_risk_score))
            
            # Risk level categorization
            if total_risk_score < 25:
                risk_level = "LOW"
                recommendation = "Low risk - Suitable for conservative investors"
            elif total_risk_score < 50:
                risk_level = "MODERATE"
                recommendation = "Moderate risk - Balanced risk-reward profile"
            elif total_risk_score < 75:
                risk_level = "HIGH"
                recommendation = "Elevated risk - Monitor closely"
            else:
                risk_level = "VERY HIGH"
                recommendation = "High risk - Exercise caution"
            
            return {
                'risk_score': round(total_risk_score, 1),
                'risk_level': risk_level,
                'volatility_risk': round(vol_score, 1),
                'technical_risk': round(tech_risk, 1),
                'sentiment_risk': round(sentiment_risk, 1),
                'support_resistance_risk': sr_risk,
                'recommendation': recommendation,
                'volatility': volatility
            }
            
        except Exception as e:
            self.logger.error(f"Risk score calculation error: {e}")
            return {
                'risk_score': 50, 
                'risk_level': 'MODERATE', 
                'recommendation': 'Further analysis needed'
            }