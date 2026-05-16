from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pathlib import Path
from app.fetcher import get_full_token_report, get_wallet_portfolio, get_multi_token_overview, get_token_overview
from app.scorer import score_token
from app.lifecycle import classify_lifecycle
import anthropic
import os
import time

app = FastAPI(title="DYOR.ai", description="AI-Powered Token Intelligence", version="2.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def build_chart_from_overview(overview: dict) -> list:
    now = int(time.time())
    points = [
        {"offset": 86400, "key": "history24hPrice"},
        {"offset": 28800, "key": "history8hPrice"},
        {"offset": 14400, "key": "history4hPrice"},
        {"offset": 7200,  "key": "history2hPrice"},
        {"offset": 3600,  "key": "history1hPrice"},
        {"offset": 0,     "key": "price"},
    ]
    chart = []
    for p in points:
        val = overview.get(p["key"], 0) or 0
        if val:
            chart.append({"time": now - p["offset"], "open": val, "high": val, "low": val, "close": val, "volume": 0})
    return chart if len(chart) >= 2 else []

def enrich_token(address: str, overview: dict, ohlcv: dict, is_trending: bool, comparables: list) -> dict:
    score_result     = score_token(overview)
    lifecycle_result = classify_lifecycle(overview, ohlcv)

    items = []
    if isinstance(ohlcv, dict):
        items = ohlcv.get("items", []) or []
    elif isinstance(ohlcv, list):
        items = ohlcv

    chart_data = [
        {"time": c.get("unixTime", 0), "open": c.get("o", 0), "high": c.get("h", 0),
         "low": c.get("l", 0), "close": c.get("c", 0), "volume": c.get("v", 0)}
        for c in items if c.get("unixTime")
    ]
    if not chart_data:
        chart_data = build_chart_from_overview(overview)

    formatted_flags = [{"icon": f[0], "title": f[1], "detail": f[2]} for f in score_result["flags"]]
    formatted_comparables = [
        {"address": t.get("address",""), "symbol": t.get("symbol","?"),
         "name": t.get("name","?"), "liquidity": t.get("liquidity",0),
         "holders": t.get("holder",0)}
        for t in comparables
    ]

    return {
        "address":           address,
        "symbol":            overview.get("symbol", "?"),
        "name":              overview.get("name", "?"),
        "logo":              overview.get("logoURI", ""),
        "price":             overview.get("price", 0),
        "price_change_24h":  overview.get("priceChange24hPercent", 0) or overview.get("v24hChangePercent", 0) or 0,
        "market_cap":        overview.get("marketCap", 0) or overview.get("mc", 0) or 0,
        "liquidity":         overview.get("liquidity", 0),
        "volume_24h":        overview.get("v24hUSD", 0),
        "holders":           overview.get("holder", 0),
        "unique_wallets_24h": overview.get("uniqueWallet24h", 0),
        "trades_24h":        overview.get("trade24h", 0),
        "is_trending":       is_trending,
        "risk_score":        score_result["score"],
        "risk_label":        score_result["risk_label"],
        "risk_color":        score_result["risk_color"],
        "verdict":           score_result["verdict"],
        "verdict_color":     score_result["verdict_color"],
        "flags":             formatted_flags,
        "lifecycle":         lifecycle_result,
        "chart_data":        chart_data,
        "comparables":       formatted_comparables,
        "scanned_at":        time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

def generate_ai_narrative(token_data: dict) -> str:
    """Generate rule-based narrative when AI is unavailable."""
    stage = token_data['lifecycle']['stage']
    score = token_data['risk_score']
    symbol = token_data['symbol']
    change = token_data['price_change_24h']
    holders = token_data['holders']
    liquidity = token_data['liquidity']

    # Sentence 1 — current state
    stage_desc = {
        "EARLY": f"{symbol} is a newly launched token with only {holders} holders and limited market activity.",
        "GROWING": f"{symbol} is in a growth phase with organic volume building and {holders} holders.",
        "PEAKING": f"{symbol} has made a significant move with {change:.0f}% gain in 24 hours — momentum is at its peak.",
        "DISTRIBUTION": f"{symbol} shows signs of distribution — price is elevated but volume is fading.",
        "DECLINING": f"{symbol} is in a declining phase with both price and volume trending downward.",
        "CONSOLIDATING": f"{symbol} is consolidating with relatively stable price and volume across 24 hours.",
    }.get(stage, f"{symbol} shows mixed market signals across the last 24 hours.")

    # Sentence 2 — key risk
    if score >= 70:
        risk_desc = f"Multiple serious red flags were detected including extremely low liquidity of ${liquidity:,.0f} — this token exhibits characteristics consistent with a scam."
    elif score >= 40:
        risk_desc = f"Some concerning signals were detected — traders should research thoroughly before committing capital."
    else:
        risk_desc = f"No major risk signals were detected — liquidity of ${liquidity:,.0f} and {holders} holders suggest legitimate market activity."

    # Sentence 3 — recommendation
    if score >= 70:
        rec = "Avoid this token entirely unless you have verified its legitimacy through independent research."
    elif score >= 40:
        rec = "Proceed with caution — only invest amounts you are fully prepared to lose."
    else:
        rec = "Standard investment caution applies — always verify the project before investing."

    return f"{stage_desc} {risk_desc} {rec}"

@app.get("/")
def root():
    html_path = Path(__file__).parent.parent / "dashboard.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
    return {"status": "online", "message": "DYOR.ai is running"}

@app.get("/api/analyze/{address}")
def analyze_token(address: str):
    """Full token intelligence report with AI narrative."""
    try:
        report   = get_full_token_report(address)
        overview = report["overview"]
        ohlcv    = report["ohlcv"]
        result   = enrich_token(address, overview, ohlcv, report["is_trending"], report["comparables"])
        result["ai_narrative"] = generate_ai_narrative(result)
        return result
    except Exception as e:
        return {"error": str(e), "address": address}

@app.get("/api/watchlist")
def scan_watchlist(addresses: str):
    """Scan multiple token addresses for watchlist feature."""
    try:
        addr_list = [a.strip() for a in addresses.split(",") if a.strip()][:5]
        results = []
        for addr in addr_list:
            overview = get_token_overview(addr)
            if not overview:
                continue
            score_result = score_token(overview)
            lifecycle_result = classify_lifecycle(overview, {})
            results.append({
                "address": addr,
                "symbol": overview.get("symbol", "?"),
                "name": overview.get("name", "?"),
                "logo": overview.get("logoURI", ""),
                "price": overview.get("price", 0),
                "price_change_24h": overview.get("priceChange24hPercent", 0) or 0,
                "liquidity": overview.get("liquidity", 0),
                "market_cap": overview.get("marketCap", 0) or overview.get("mc", 0) or 0,
                "volume_24h": overview.get("v24hUSD", 0),
                "holders": overview.get("holder", 0),
                "risk_score": score_result["score"],
                "risk_label": score_result["risk_label"],
                "risk_color": score_result["risk_color"],
                "lifecycle": lifecycle_result["stage"],
                "lifecycle_color": lifecycle_result["color"],
                "scanned_at": time.strftime("%H:%M:%S", time.gmtime()),
            })
        return {"tokens": results, "count": len(results)}
    except Exception as e:
        return {"error": str(e)}
    
@app.get("/api/compare")
def compare_tokens(a: str, b: str, c: str = None):
    """Compare 2-3 tokens side by side."""
    try:
        addresses = [addr for addr in [a, b, c] if addr]
        results = []
        for addr in addresses:
            overview = get_token_overview(addr)
            if overview:
                score_result     = score_token(overview)
                lifecycle_result = classify_lifecycle(overview, {})
                results.append({
                    "address":    addr,
                    "symbol":     overview.get("symbol", "?"),
                    "name":       overview.get("name", "?"),
                    "logo":       overview.get("logoURI", ""),
                    "price":      overview.get("price", 0),
                    "price_change_24h": overview.get("priceChange24hPercent", 0) or 0,
                    "market_cap": overview.get("marketCap", 0) or overview.get("mc", 0) or 0,
                    "liquidity":  overview.get("liquidity", 0),
                    "volume_24h": overview.get("v24hUSD", 0),
                    "holders":    overview.get("holder", 0),
                    "risk_score": score_result["score"],
                    "risk_label": score_result["risk_label"],
                    "risk_color": score_result["risk_color"],
                    "verdict":    score_result["verdict"],
                    "lifecycle":  lifecycle_result["stage"],
                    "lifecycle_color": lifecycle_result["color"],
                })
        return {"tokens": results, "count": len(results)}
    except Exception as e:
        return {"error": str(e)}

@app.get("/status")
def status():
    return {"status": "online", "message": "DYOR.ai — AI-Powered Token Intelligence"}