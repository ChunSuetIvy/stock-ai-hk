# src/ai/predictor.py
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import logging
from typing import Dict, List

class StockPredictor:
    """AI-powered stock price prediction using ML"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.model = LinearRegression()
        self.scaler = StandardScaler()
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract features for ML model"""
        features = pd.DataFrame()
        
        # Price-based features
        features['returns'] = df['Close'].pct_change()
        features['volatility'] = features['returns'].rolling(5).std()
        features['momentum'] = df['Close'].pct_change(5)
        
        # Technical indicators as features
        features['rsi'] = df.get('RSI', 50)
        features['volume_ratio'] = df.get('Volume_Ratio', 1)
        
        # Moving average features
        features['price_to_sma'] = df['Close'] / df['MA_20'] if 'MA_20' in df else 1
        
        # Lag features (past prices affect future)
        for i in range(1, 6):
            features[f'lag_{i}'] = features['returns'].shift(i)
        
        return features.fillna(0)
    
    def predict_trend(self, df: pd.DataFrame, days_ahead: int = 5) -> Dict:
        """Predict stock trend using ML"""
        try:
            if len(df) < 20:
                return self._default_prediction()
            
            # Prepare features
            features = self.prepare_features(df)
            
            # Create training data (use past data to predict next day)
            X = features[:-1].values
            y = (df['Close'].shift(-1) > df['Close'])[:-1].astype(int).values
            
            # Remove NaN rows
            valid_idx = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
            X = X[valid_idx]
            y = y[valid_idx]
            
            if len(X) < 10:
                return self._default_prediction()
            
            # Train model
            X_scaled = self.scaler.fit_transform(X)
            self.model.fit(X_scaled, y)
            
            # Predict next trend
            last_features = features.iloc[-1:].values
            last_scaled = self.scaler.transform(last_features)
            prediction_prob = self.model.predict(last_scaled)[0]
            
            # Calculate price target
            current_price = df['Close'].iloc[-1]
            avg_change = abs(df['Close'].pct_change().mean())
            
            if prediction_prob > 0.5:
                trend = "BULLISH"
                price_target = current_price * (1 + avg_change * days_ahead)
            else:
                trend = "BEARISH"
                price_target = current_price * (1 - avg_change * days_ahead)
            
            # Calculate confidence
            confidence = abs(prediction_prob - 0.5) * 2
            
            return {
                'predicted_trend': trend,
                'confidence': min(confidence, 0.85),
                'price_target': round(price_target, 2),
                'current_price': round(current_price, 2),
                'prediction_horizon': f'{days_ahead} days',
                'reasoning': self._generate_reasoning(trend, features.iloc[-1])
            }
            
        except Exception as e:
            self.logger.error(f"Prediction error: {e}")
            return self._default_prediction()
    
    def _generate_reasoning(self, trend: str, last_features: pd.Series) -> str:
        """Generate human-readable reasoning"""
        reasons = []
        
        if last_features['momentum'] > 0.05:
            reasons.append("strong upward momentum")
        elif last_features['momentum'] < -0.05:
            reasons.append("strong downward momentum")
        
        if last_features['rsi'] > 70:
            reasons.append("overbought RSI conditions")
        elif last_features['rsi'] < 30:
            reasons.append("oversold RSI conditions")
        
        if last_features['volume_ratio'] > 1.5:
            reasons.append("high trading volume")
        
        if not reasons:
            reasons.append("mixed technical signals")
        
        return f"Prediction based on {', '.join(reasons)}. Historical patterns suggest {trend.lower()} movement likely."
    
    def _default_prediction(self) -> Dict:
        """Default prediction when insufficient data"""
        return {
            'predicted_trend': 'NEUTRAL',
            'confidence': 0.5,
            'price_target': 0,
            'current_price': 0,
            'prediction_horizon': '5 days',
            'reasoning': 'Insufficient data for prediction'
        }