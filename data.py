import requests
import pandas as pd
import numpy as np

BYBIT = "https://api.bybit.com"

def klines(symbol="BTCUSDT", interval="1h", limit=500):
    # Bybit interval mapping
    tf_map = {"15m": "15", "1h": "60", "4h": "240", "1d": "D"}
    bybit_tf = tf_map.get(interval, "60")
    
    url = f"{BYBIT}/v5/market/kline"
    params = {
        "category": "linear",
        "symbol": symbol,
        "interval": bybit_tf,
        "limit": limit
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    
    if data.get("retCode") != 0:
        raise Exception(f"Bybit API Error: {data.get('retMsg')}")
        
    # Bybit returns data newest first, so we reverse it
    raw = data["result"]["list"]
    raw.reverse()
    
    # Create DataFrame
    df = pd.DataFrame(raw, columns=["open_time", "open", "high", "low", "close", "volume", "turnover"])
    
    # Convert to appropriate types
    for c in ["open", "high", "low", "close", "volume", "turnover"]:
        df[c] = df[c].astype(float)
    df["open_time"] = pd.to_datetime(df["open_time"].astype(float), unit="ms")
    
    # Dummy columns to match old logic (scoring.py checks for these)
    df["quote_volume"] = df["turnover"]
    df["taker_buy_base"] = df["volume"] * 0.5 # Bybit klines dont provide taker buy natively here
    df["taker_buy_quote"] = df["turnover"] * 0.5
    
    return df

def funding_rate(symbol="BTCUSDT"):
    url = f"{BYBIT}/v5/market/tickers"
    params = {"category": "linear", "symbol": symbol}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    
    if data.get("retCode") != 0 or len(data["result"]["list"]) == 0:
        return {"funding_rate": 0.0, "mark_price": 0.0}
        
    ticker = data["result"]["list"][0]
    return {
        "funding_rate": float(ticker.get("fundingRate", 0)),
        "mark_price": float(ticker.get("markPrice", 0))
    }

def open_interest_hist(symbol="BTCUSDT", period="1h", limit=100):
    tf_map = {"15m": "15min", "1h": "1h", "4h": "4h", "1d": "1d"}
    bybit_tf = tf_map.get(period, "1h")
    
    url = f"{BYBIT}/v5/market/open-interest"
    params = {
        "category": "linear",
        "symbol": symbol,
        "intervalTime": bybit_tf,
        "limit": limit
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    
    if data.get("retCode") != 0 or len(data["result"]["list"]) == 0:
        return None
        
    raw = data["result"]["list"]
    raw.reverse() # newest first to oldest
    
    df = pd.DataFrame(raw)
    df["sumOpenInterest"] = df["openInterest"].astype(float)
    return df
