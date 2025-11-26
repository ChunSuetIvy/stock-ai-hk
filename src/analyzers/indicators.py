# src/analyzers/indicators.py
import pandas as pd
import numpy as np
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TechnicalIndicators:
    """Calculate technical indicators for stocks"""
    
    @staticmethod
    def sma(prices, window=20):
        """Simple Moving Average"""
        return prices.rolling(window=window).mean()
    
    @staticmethod
    def rsi(prices, periods=14):
        """
        Relative Strength Index
        RSI > 70: Overbought (price might fall)
        RSI < 30: Oversold (price might rise)
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
        
        # Avoid division by zero
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def volume_analysis(volume, window=20):
        """Analyze volume patterns"""
        avg_volume = volume.rolling(window=window).mean()
        volume_ratio = volume / avg_volume
        
        # Detect unusual volume (>2x average)
        unusual_volume = volume_ratio > 2
        
        return {
            'avg_volume': avg_volume,
            'volume_ratio': volume_ratio,
            'unusual_days': unusual_volume
        }
    
    def analyze_stock(self, df):
        """Run all indicators on a stock dataframe"""
        close_prices = df['Close']
        volume = df['Volume']
        
        # Calculate indicators
        df['SMA_20'] = self.sma(close_prices, 20)
        df['RSI'] = self.rsi(close_prices)
        
        # Volume
        vol_analysis = self.volume_analysis(volume)
        df['Volume_Ratio'] = vol_analysis['volume_ratio']
        df['Unusual_Volume'] = vol_analysis['unusual_days']
        
        # Trading signals
        df['RSI_Signal'] = 'Hold'
        df.loc[df['RSI'] > 70, 'RSI_Signal'] = 'Overbought'
        df.loc[df['RSI'] < 30, 'RSI_Signal'] = 'Oversold'
        
        return df
    
    def get_current_signals(self, df):
        """Get current trading signals for a stock"""
        if df.empty or len(df) < 20:  # Need at least 20 days for indicators
            return None
            
        latest = df.iloc[-1]
        
        signals = {
            'RSI': {
                'value': latest['RSI'] if pd.notna(latest['RSI']) else 50,
                'signal': latest.get('RSI_Signal', 'Hold')
            },
            'Price_vs_SMA': {
                'above': latest['Close'] > latest['SMA_20'] if pd.notna(latest['SMA_20']) else False,
                'distance': ((latest['Close'] / latest['SMA_20']) - 1) * 100 if pd.notna(latest['SMA_20']) else 0
            },
            'Volume': {
                'unusual': bool(latest.get('Unusual_Volume', False)),
                'ratio': latest.get('Volume_Ratio', 1.0)
            }
        }
            
        return signals

# Test the indicators
if __name__ == "__main__":
    from collectors.data_fetcher import HKStockDataFetcher
    
    fetcher = HKStockDataFetcher()
    analyzer = TechnicalIndicators()
    
    # Analyze Tencent
    print("📈 Analyzing Tencent (0700.HK)")
    print("="*50)
    
    df = fetcher.fetch_stock_data("0700.HK", period="3mo")  # Need more data for indicators
    
    if not df.empty:
        df_analyzed = analyzer.analyze_stock(df)
        
        # Get current signals
        signals = analyzer.get_current_signals(df_analyzed)
        
        if signals:
            print("\n🎯 Current Signals:")
            print(f"RSI: {signals['RSI']['value']:.2f} - {signals['RSI']['signal']}")
            print(f"Price vs SMA20: {'Above' if signals['Price_vs_SMA']['above'] else 'Below'} by {signals['Price_vs_SMA']['distance']:.2f}%")
            print(f"Volume: {'🔴 UNUSUAL' if signals['Volume']['unusual'] else '🟢 Normal'} (Ratio: {signals['Volume']['ratio']:.2f}x)")
            
            # Show last 5 days with indicators
            print("\n📊 Last 5 Days with Indicators:")
            print(df_analyzed[['Close', 'SMA_20', 'RSI', 'Volume_Ratio', 'RSI_Signal']].tail())
    else:
        print("❌ Could not fetch data")