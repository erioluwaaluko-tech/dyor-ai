import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY  = os.getenv("BIRDEYE_API_KEY")
BASE_URL = "https://public-api.birdeye.so"

HEADERS = {
    "accept":    "application/json",
    "x-chain":   "solana",
    "X-API-KEY": API_KEY
}

def _get(url, params=None):
    time.sleep(1.1)
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        return response.json().get("data", {})
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] {url} → {e}")
        return {}

def get_token_overview(address):
    return _get(f"{BASE_URL}/defi/token_overview", {"address": address})

def get_token_ohlcv(address, timeframe="1H", limit=24):
    result = _get(f"{BASE_URL}/defi/ohlcv", {
        "address": address, "type": timeframe, "limit": limit
    })
    if result:
        return result
    return _get(f"{BASE_URL}/defi/ohlcv/base_quote", {
        "base_address": address, "type": timeframe, "limit": limit
    }) or {}

def get_trending_tokens(limit=20):
    data = _get(f"{BASE_URL}/defi/token_trending", {
        "sort_by": "rank", "sort_type": "asc", "offset": 0, "limit": limit
    })
    return data.get("tokens", [])

def get_similar_tokens(min_liq, max_liq, limit=3):
    data = _get(f"{BASE_URL}/defi/tokenlist", {
        "sort_by": "v24hUSD", "sort_type": "desc",
        "offset": 50, "limit": limit,
        "min_liquidity": min_liq * 0.5,
        "max_liquidity": max_liq * 1.5
    })
    return data.get("tokens", [])

def get_wallet_portfolio(wallet_address):
    """Fetch wallet portfolio using available free tier endpoint."""
    # Try v1 wallet endpoint
    data = _get(f"{BASE_URL}/v1/wallet/token_list", {
        "wallet": wallet_address
    })
    items = data.get("items", []) if data else []
    if items:
        return items

    # Fallback — try wallet portfolio endpoint
    data2 = _get(f"{BASE_URL}/v1/wallet/token_list_v2", {
        "wallet": wallet_address,
        "limit": 20
    })
    items2 = data2.get("items", []) if data2 else []
    if items2:
        return items2

    # Second fallback
    data3 = _get(f"{BASE_URL}/defi/multi_price", {
        "list_address": wallet_address
    })
    return data3.get("items", []) if data3 else []

def get_multi_token_overview(addresses: list):
    """Fetch overview for multiple tokens — one call each."""
    results = []
    for addr in addresses:
        overview = get_token_overview(addr)
        if overview:
            results.append({"address": addr, "overview": overview})
    return results

def get_full_token_report(address):
    """Master function — all data for one token report."""
    print(f"[INFO] Fetching overview...")
    overview = get_token_overview(address)
    print(f"[INFO] Fetching OHLCV...")
    ohlcv = get_token_ohlcv(address)
    print(f"[INFO] Fetching trending...")
    trending = get_trending_tokens(20)
    trending_status = any(t.get("address") == address for t in trending)
    liquidity = overview.get("liquidity", 0) or 0
    print(f"[INFO] Fetching comparables...")
    comparables = get_similar_tokens(liquidity * 0.3, liquidity * 3, limit=3)
    return {
        "address":      address,
        "overview":     overview,
        "ohlcv":        ohlcv,
        "is_trending":  trending_status,
        "comparables":  comparables
    }