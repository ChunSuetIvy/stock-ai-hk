# src/api/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
import numpy as np

# Fix import paths
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Now imports should work
from analysis_pipeline import StockAnalysisPipeline
from collectors.data_fetcher import HKStockDataFetcher
from database import StockDatabase

# Add the new imports
from ai.predictor import StockPredictor
from backtesting.backtest_engine import BacktestEngine

import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
import json

app = FastAPI(
    title="HK Stock AI Analysis API",
    description="AI-powered stock analysis for Hong Kong market",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://stock-ai-hk-6wox.vercel.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
pipeline = StockAnalysisPipeline()
fetcher = HKStockDataFetcher()
db = StockDatabase()
predictor = StockPredictor()
backtest_engine = BacktestEngine()

@app.get("/")
def read_root():
    """Welcome endpoint"""
    return {
        "message": "HK Stock AI Analysis API",
        "version": "1.0.0",
        "endpoints": [
            "/stocks - List all tracked stocks",
            "/analysis/{symbol} - Get analysis for a specific stock",
            "/analysis/all - Analyze all stocks",
            "/market/summary - Get market overview",
            "/prediction/{symbol} - Get AI prediction",
            "/backtest/{symbol} - Run backtesting"
        ]
    }

@app.get("/stocks")
def get_stocks():
    """Get list of tracked stocks"""
    return {
        "stocks": [
            {"symbol": symbol, "name": name}
            for symbol, name in fetcher.stocks.items()
        ]
    }

@app.get("/analysis/{symbol}")
def analyze_stock(symbol: str):
    """Get complete analysis for a specific stock"""
    if symbol not in fetcher.stocks:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
    
    try:
        result = pipeline.analyze_single_stock(symbol)
        if result:
            result['name'] = fetcher.stocks[symbol]
            return result
        else:
            raise HTTPException(status_code=500, detail="Analysis failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analysis/all")
async def analyze_all_stocks():
    """Analyze all tracked stocks"""
    try:
        print("Starting analysis for all stocks...")
        results = pipeline.analyze_all_stocks()
        response = {
            "timestamp": datetime.now().isoformat(),
            "count": len(results) if results else 0,
            "results": results if results else []
        }
        print(f"Analysis complete. Returning {len(results) if results else 0} results")
        return response
    except Exception as e:
        print(f"Error in analyze_all_stocks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/market/summary")
def get_market_summary():
    """Get market overview and recommendations"""
    try:
        if not pipeline.analysis_results:
            pipeline.analyze_all_stocks()
        
        results = list(pipeline.analysis_results.values())
        
        if not results:
            return {"error": "No analysis data available"}
        
        bullish = sum(1 for r in results if 'BULLISH' in r.get('recommendation', ''))
        bearish = sum(1 for r in results if 'BEARISH' in r.get('recommendation', ''))
        neutral = sum(1 for r in results if 'NEUTRAL' in r.get('recommendation', ''))
        
        avg_sentiment = sum(r.get('sentiment_score', 0) for r in results) / len(results)
        
        sorted_by_change = sorted(results, key=lambda x: x.get('price_change', 0))
        
        return {
            "timestamp": datetime.now().isoformat(),
            "market_mood": "Positive" if avg_sentiment > 0.1 else "Negative" if avg_sentiment < -0.1 else "Neutral",
            "average_sentiment": round(avg_sentiment, 3),
            "recommendations": {
                "bullish": bullish,
                "bearish": bearish,
                "neutral": neutral
            },
            "best_performer": {
                "symbol": sorted_by_change[-1]['symbol'],
                "change": round(sorted_by_change[-1]['price_change'], 2)
            },
            "worst_performer": {
                "symbol": sorted_by_change[0]['symbol'],
                "change": round(sorted_by_change[0]['price_change'], 2)
            },
            "total_stocks": len(results)
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/stock/{symbol}/history")
def get_stock_history(symbol: str, days: int = 30):
    """Get historical data for a stock"""
    if symbol not in fetcher.stocks:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
    
    try:
        # Fetch historical data
        data = fetcher.fetch_stock_data(symbol, period=f"{days}d")
        
        if data.empty:
            return {"error": "No data available"}
        
        # Convert to list of dicts for JSON response
        history = []
        for date, row in data.iterrows():
            # Clean up NaN and Infinity values
            open_price = float(row['Open']) if pd.notna(row['Open']) and np.isfinite(row['Open']) else 0
            high_price = float(row['High']) if pd.notna(row['High']) and np.isfinite(row['High']) else 0
            low_price = float(row['Low']) if pd.notna(row['Low']) and np.isfinite(row['Low']) else 0
            close_price = float(row['Close']) if pd.notna(row['Close']) and np.isfinite(row['Close']) else 0
            volume = int(row['Volume']) if pd.notna(row['Volume']) and np.isfinite(row['Volume']) else 0
            
            # Handle SMA - it might be NaN for early dates
            sma_value = None
            if 'MA_20' in row and pd.notna(row['MA_20']) and np.isfinite(row['MA_20']):
                sma_value = round(float(row['MA_20']), 2)
            elif 'MA_5' in row and pd.notna(row['MA_5']) and np.isfinite(row['MA_5']):
                sma_value = round(float(row['MA_5']), 2)
            
            # Only add valid data points
            if close_price > 0:  # Skip invalid data
                history.append({
                    "date": date.strftime('%Y-%m-%d'),
                    "open": round(open_price, 2),
                    "high": round(high_price, 2),
                    "low": round(low_price, 2),
                    "close": round(close_price, 2),
                    "volume": volume,
                    "sma_20": sma_value
                })
        
        return {
            "symbol": symbol,
            "name": fetcher.stocks[symbol],
            "period": f"{days} days",
            "data": history
        }
        
    except Exception as e:
        print(f"Error in get_stock_history for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/prediction/{symbol}")
def get_prediction(symbol: str):
    """Get AI price prediction for a stock"""
    if symbol not in fetcher.stocks:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
    
    try:
        df = fetcher.fetch_stock_data(symbol, period="3mo")
        
        if df.empty:
            return {"error": "Insufficient data for prediction"}
        
        prediction = predictor.predict_trend(df, days_ahead=5)
        prediction['symbol'] = symbol
        prediction['name'] = fetcher.stocks[symbol]
        
        return prediction
    except Exception as e:
        return {"error": str(e)}

@app.get("/backtest/{symbol}")
def run_backtest(symbol: str):
    """Run backtest on a stock"""
    if symbol not in fetcher.stocks:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
    
    try:
        df = fetcher.fetch_stock_data(symbol, period="3mo")
        
        if df.empty:
            return {"error": "Insufficient data for backtesting"}
        
        signals = backtest_engine.generate_signals_from_analysis(df)
        results = backtest_engine.backtest_strategy(df, signals)
        results['symbol'] = symbol
        results['name'] = fetcher.stocks[symbol]
        
        return results
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting API server at http://localhost:8000")
    print("📚 API documentation at http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)