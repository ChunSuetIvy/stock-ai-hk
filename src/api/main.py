# src/api/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import sys
import os

# Add the parent directories to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)
sys.path.append(parent_dir)
sys.path.append(grandparent_dir)

# Now import with correct paths
from analysis_pipeline import StockAnalysisPipeline
from collectors.data_fetcher import HKStockDataFetcher
from database import StockDatabase

import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
import json

app = FastAPI(
    title="HK Stock AI Analysis API",
    description="AI-powered stock analysis for Hong Kong market",
    version="1.0.0"
)

# FIXED CORS - Add your Vercel domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://stock-ai-hk-6wox.vercel.app",  # Your Vercel domain
        "http://localhost:3000",  # Local development
        "http://127.0.0.1:3000",  # Local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
pipeline = StockAnalysisPipeline()
fetcher = HKStockDataFetcher()
db = StockDatabase()

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
            "/market/summary - Get market overview"
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
    # Validate symbol
    if symbol not in fetcher.stocks:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
    
    try:
        # Run analysis
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
        
        # The function returns a list but we need to format it properly
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
        # Run analysis if not done recently
        if not pipeline.analysis_results:
            pipeline.analyze_all_stocks()
        
        # Calculate market statistics
        results = list(pipeline.analysis_results.values())
        
        if not results:
            return {"error": "No analysis data available"}
        
        # Count recommendations
        bullish = sum(1 for r in results if 'BULLISH' in r.get('recommendation', ''))
        bearish = sum(1 for r in results if 'BEARISH' in r.get('recommendation', ''))
        neutral = sum(1 for r in results if 'NEUTRAL' in r.get('recommendation', ''))
        
        # Average sentiment
        avg_sentiment = sum(r.get('sentiment_score', 0) for r in results) / len(results)
        
        # Best and worst performers
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
            history.append({
                "date": date.strftime('%Y-%m-%d'),
                "open": round(row['Open'], 2),
                "high": round(row['High'], 2),
                "low": round(row['Low'], 2),
                "close": round(row['Close'], 2),
                "volume": int(row['Volume']),
                "sma_20": round(row['MA_5'], 2) if 'MA_5' in row else None
            })
        
        return {
            "symbol": symbol,
            "name": fetcher.stocks[symbol],
            "period": f"{days} days",
            "data": history
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting API server at http://localhost:8000")
    print("📚 API documentation at http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)