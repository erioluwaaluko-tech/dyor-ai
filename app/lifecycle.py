def classify_lifecycle(overview: dict, ohlcv: dict) -> dict:
    price_change = overview.get("priceChange24hPercent", 0) or overview.get("v24hChangePercent", 0) or 0
    volume_24h   = overview.get("v24hUSD", 0) or 0
    market_cap   = overview.get("marketCap", 0) or overview.get("mc", 0) or 0
    holders      = overview.get("holder", 0) or 0
    unique_wallets = overview.get("uniqueWallet24h", 0) or 0

    items = []
    if isinstance(ohlcv, dict):
        items = ohlcv.get("items", []) or []
    elif isinstance(ohlcv, list):
        items = ohlcv

    volume_trend = "flat"
    price_trend  = "flat"

    if len(items) >= 6:
        mid = len(items) // 2
        early_vol = sum(c.get("v", 0) or 0 for c in items[:mid])
        late_vol  = sum(c.get("v", 0) or 0 for c in items[mid:])
        if late_vol > early_vol * 1.5:
            volume_trend = "rising"
        elif late_vol < early_vol * 0.6:
            volume_trend = "falling"

        first_close = items[0].get("c",  0) or 0
        last_close  = items[-1].get("c", 0) or 0
        if first_close and last_close:
            price_move = ((last_close - first_close) / first_close) * 100
            if price_move > 20:   price_trend = "rising"
            elif price_move < -20: price_trend = "falling"

    vol_mcap_ratio = (volume_24h / market_cap) if market_cap else 0

    if holders < 100 and volume_24h < 50000:
        stage, color = "EARLY", "cyan"
        explanation = "Brand new token with very few holders and minimal volume. Highest risk but also highest potential if legitimate. Treat with extreme caution."
    elif volume_trend == "rising" and price_trend == "rising" and price_change < 200:
        stage, color = "GROWING", "green"
        explanation = "Organic momentum building — volume and price rising together. This is typically the best entry window before the big move happens."
    elif price_change > 200 or vol_mcap_ratio > 5:
        stage, color = "PEAKING", "yellow"
        explanation = "This token has already made a major move. Buyers at this stage are often buying from early holders who are selling. Proceed with extreme caution."
    elif price_change > 50 and volume_trend == "falling":
        stage, color = "DISTRIBUTION", "orange"
        explanation = "Price is elevated but volume is fading. Early buyers are selling into retail demand. Classic pre-dump setup — high risk."
    elif price_trend == "falling" and volume_trend == "falling":
        stage, color = "DECLINING", "red"
        explanation = "Both price and volume are falling. Market interest is fading. High risk of continued downside without a strong catalyst."
    else:
        stage, color = "CONSOLIDATING", "gray"
        explanation = "No clear directional trend. Price and volume are relatively stable. Watch for a volume spike as an early breakout signal."

    return {
        "stage": stage, "color": color, "explanation": explanation,
        "signals": {
            "price_change_24h": price_change,
            "volume_trend":     volume_trend,
            "price_trend":      price_trend,
            "vol_mcap_ratio":   round(vol_mcap_ratio, 2),
            "holders":          holders,
            "unique_wallets":   unique_wallets,
        }
    }