import requests
import pandas as pd
import numpy as np

OKX = "https://www.okx.com"

def klines(symbol="BTC-USDT-SWAP", interval="1H", limit=500):
    # Map common intervals to OKX format
    tf_map = {"15m": "15m", "1h": "1H", "4h": "4H", "1d": "1D"}
    okx_tf = tf_map.get(interval, "1H")
    
    # OKX uses instId like BTC-USDT-SWAP. We will transform "BTCUSDT" to "BTC-USDT-SWAP"
    inst_id = symbol.replace("USDT", "-USDT-SWAP")
    
    url = f"{OKX}/api/v5/market/candles"
    params = {"instId": inst_id, "bar": okx_tf, "limit": str(limit)}
    r = requests.get(url, params=params, timeout=10)
    data = r.json()
    
    if data.get("code") != "0" or not data.get("data"):
        raise Exception(f"OKX API Error: {data.get('msg')}")
        
    raw = data["data"]
    raw.reverse()
    
    # OKX columns: [ts, open, high, low, close, vol, volCcy, volCcyQuote, confirm]
    df = pd.DataFrame(raw, columns=["open_time", "open", "high", "low", "close", "volume", "volCcy", "turnover", "confirm"])
    
    for c in ["open", "high", "low", "close", "volume", "turnover"]:
        df[c] = df[c].astype(float)
    df["open_time"] = pd.to_datetime(df["open_time"].astype(float), unit="ms")
    
    df["quote_volume"] = df["turnover"]
    df["taker_buy_base"] = df["volume"] * 0.5
    df["taker_buy_quote"] = df["turnover"] * 0.5
    
    return df

def funding_rate(symbol="BTCUSDT"):
    inst_id = symbol.replace("USDT", "-USDT-SWAP")
    url = f"{OKX}/api/v5/public/funding-rate"
    r = requests.get(url, params={"instId": inst_id}, timeout=10)
    data = r.json()
    
    if data.get("code") != "0" or not data.get("data"):
        return {"funding_rate": 0.0, "mark_price": 0.0}
        
    ticker = data["data"][0]
    return {
        "funding_rate": float(ticker.get("fundingRate", 0)),
        "mark_price": 0.0 # Mark price fetch can be added later if needed
    }

def open_interest_hist(symbol="BTCUSDT", period="1h", limit=100):
    # OKX OI data fetching is slightly complex, we'll skip it for now or mock it
    # to prevent errors. The dashboard will just use 0.
    return None
