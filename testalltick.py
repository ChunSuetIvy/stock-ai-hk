# test_alltick.py
import requests
import os

def test_alltick():
    api_key = os.getenv('ALLTICK_API_KEY')
    print(f"API Key: {api_key[:8]}...{api_key[-4:] if api_key else 'NOT SET'}")
    
    if not api_key:
        print("❌ ALLTICK_API_KEY not set")
        return
    
    # Test different endpoints
    endpoints = [
        "https://api.alltick.co/v1/historical",
        "https://api.alltick.co/v1/quote", 
        "https://api.alltick.co/v1/eod",
    ]
    
    symbols = ["0700.HK", "0700", "700:HKG"]
    
    for endpoint in endpoints:
        for symbol in symbols:
            print(f"\nTesting {endpoint} with {symbol}:")
            try:
                params = {'symbol': symbol, 'apikey': api_key}
                if 'historical' in endpoint:
                    params['interval'] = '1d'
                    params['outputsize'] = 2
                
                response = requests.get(endpoint, params=params, timeout=10)
                print(f"  Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"  Response keys: {list(data.keys())}")
                    if 'error' in data:
                        print(f"  Error: {data['error']}")
                else:
                    print(f"  Response: {response.text[:100]}...")
            except Exception as e:
                print(f"  Exception: {e}")

if __name__ == "__main__":
    test_alltick()