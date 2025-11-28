# src/backtesting/backtest_engine.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
import logging

class BacktestEngine:
    """Backtest trading strategies on historical data"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.initial_capital = 100000  # Starting with $100k
    
    def backtest_strategy(self, df: pd.DataFrame, strategy_signals: pd.Series) -> Dict:
        """
        Backtest a trading strategy
        strategy_signals: Series with 'BUY', 'SELL', 'HOLD' signals
        """
        try:
            if df.empty or len(strategy_signals) != len(df):
                return self._default_results()
            
            capital = self.initial_capital
            shares = 0
            trades = []
            portfolio_values = []
            
            for i in range(len(df)):
                price = df['Close'].iloc[i]
                signal = strategy_signals.iloc[i]
                date = df.index[i]
                
                # Execute trades based on signals
                if signal == 'BUY' and capital > price:
                    # Buy as many shares as possible
                    shares_to_buy = int(capital / price)
                    if shares_to_buy > 0:
                        cost = shares_to_buy * price
                        shares += shares_to_buy
                        capital -= cost
                        trades.append({
                            'date': date,
                            'action': 'BUY',
                            'shares': shares_to_buy,
                            'price': price,
                            'value': cost
                        })
                
                elif signal == 'SELL' and shares > 0:
                    # Sell all shares
                    revenue = shares * price
                    capital += revenue
                    trades.append({
                        'date': date,
                        'action': 'SELL',
                        'shares': shares,
                        'price': price,
                        'value': revenue
                    })
                    shares = 0
                
                # Calculate portfolio value
                portfolio_value = capital + (shares * price)
                portfolio_values.append(portfolio_value)
            
            # Calculate metrics
            final_value = portfolio_values[-1]
            total_return = ((final_value - self.initial_capital) / self.initial_capital) * 100
            
            # Buy and hold comparison
            buy_hold_shares = int(self.initial_capital / df['Close'].iloc[0])
            buy_hold_value = buy_hold_shares * df['Close'].iloc[-1]
            buy_hold_return = ((buy_hold_value - self.initial_capital) / self.initial_capital) * 100
            
            # Calculate Sharpe ratio
            returns = pd.Series(portfolio_values).pct_change().dropna()
            sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
            
            # Win rate
            winning_trades = sum(1 for t in trades if t['action'] == 'SELL' and t['value'] > self.initial_capital/len([x for x in trades if x['action'] == 'BUY']))
            win_rate = (winning_trades / max(len([t for t in trades if t['action'] == 'SELL']), 1)) * 100
            
            return {
                'initial_capital': self.initial_capital,
                'final_value': round(final_value, 2),
                'total_return': round(total_return, 2),
                'buy_hold_return': round(buy_hold_return, 2),
                'sharpe_ratio': round(sharpe_ratio, 2),
                'total_trades': len(trades),
                'win_rate': round(win_rate, 2),
                'portfolio_values': portfolio_values,
                'trades': trades,
                'outperformed_buy_hold': total_return > buy_hold_return
            }
            
        except Exception as e:
            self.logger.error(f"Backtest error: {e}")
            return self._default_results()
    
    def generate_signals_from_analysis(self, df: pd.DataFrame) -> pd.Series:
        """Generate trading signals from technical analysis"""
        signals = pd.Series(index=df.index, data='HOLD')
        
        if 'RSI' not in df or 'MA_20' not in df:
            return signals
        
        for i in range(1, len(df)):
            rsi = df['RSI'].iloc[i]
            price = df['Close'].iloc[i]
            sma = df['MA_20'].iloc[i]
            
            # Simple strategy: Buy oversold, Sell overbought
            if rsi < 30 and price < sma:
                signals.iloc[i] = 'BUY'
            elif rsi > 70 and price > sma:
                signals.iloc[i] = 'SELL'
            else:
                signals.iloc[i] = 'HOLD'
        
        return signals
    
    def _default_results(self) -> Dict:
        """Default results when backtest fails"""
        return {
            'initial_capital': self.initial_capital,
            'final_value': self.initial_capital,
            'total_return': 0,
            'buy_hold_return': 0,
            'sharpe_ratio': 0,
            'total_trades': 0,
            'win_rate': 0,
            'portfolio_values': [],
            'trades': [],
            'outperformed_buy_hold': False
        }