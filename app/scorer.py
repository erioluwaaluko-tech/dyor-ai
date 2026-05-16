def score_token(overview: dict) -> dict:
    score = 0
    flags = []

    liquidity = overview.get("liquidity", 0) or 0
    if liquidity < 1000:
        score += 25
        flags.append(("🚨", "Extremely low liquidity", f"${liquidity:,.0f} — easy to manipulate"))
    elif liquidity < 10000:
        score += 12
        flags.append(("⚠️", "Low liquidity", f"${liquidity:,.0f} — moderate risk"))

    volume_24h = overview.get("v24hUSD", 0) or 0
    market_cap = overview.get("marketCap", 0) or overview.get("mc", 0) or 0
    if market_cap and volume_24h:
        ratio = volume_24h / market_cap
        if ratio > 10:
            score += 25
            flags.append(("🚨", "Extreme volume anomaly", f"Volume is {ratio:.1f}x market cap"))
        elif ratio > 5:
            score += 15
            flags.append(("⚠️", "High volume anomaly", f"Volume is {ratio:.1f}x market cap"))
        elif ratio > 2:
            score += 8
            flags.append(("⚠️", "Elevated volume", f"Volume is {ratio:.1f}x market cap"))

    price_change = overview.get("priceChange24hPercent", 0) or overview.get("v24hChangePercent", 0) or 0
    if price_change > 500:
        score += 20
        flags.append(("🚨", "Extreme price spike", f"+{price_change:.0f}% in 24h"))
    elif price_change > 200:
        score += 12
        flags.append(("⚠️", "Major price spike", f"+{price_change:.0f}% in 24h"))
    elif price_change < -60:
        score += 15
        flags.append(("🚨", "Sharp price drop", f"{price_change:.0f}% in 24h"))

    holders = overview.get("holder", 0) or 0
    if holders < 50:
        score += 20
        flags.append(("🚨", "Dangerously few holders", f"Only {holders} wallets"))
    elif holders < 200:
        score += 10
        flags.append(("⚠️", "Low holder count", f"Only {holders} holders"))

    trades_24h = overview.get("trade24h", 0) or 0
    if volume_24h > 100000 and trades_24h < 20:
        score += 15
        flags.append(("🚨", "Wash trading detected", f"${volume_24h:,.0f} across only {trades_24h} trades"))

    unique_wallets = overview.get("uniqueWallet24h", 0) or 0
    if unique_wallets < 10 and volume_24h > 10000:
        score += 10
        flags.append(("⚠️", "Coordinated activity", f"Only {unique_wallets} unique wallets"))

    if market_cap == 0 and volume_24h > 0:
        score += 5
        flags.append(("⚠️", "No market cap data", "Token supply data incomplete"))

    score = min(score, 100)

    if score >= 70:
        risk_label, risk_color = "HIGH RISK", "red"
        verdict = "AVOID — Multiple serious red flags. High probability of scam or pump-and-dump."
        verdict_color = "red"
    elif score >= 40:
        risk_label, risk_color = "MEDIUM RISK", "yellow"
        verdict = "CAUTION — Concerning signals detected. Research thoroughly before investing."
        verdict_color = "yellow"
    else:
        risk_label, risk_color = "LOW RISK", "green"
        verdict = "LOOKS SAFE — No major red flags. Standard investment risks still apply."
        verdict_color = "green"

    return {
        "score": score, "risk_label": risk_label,
        "risk_color": risk_color, "verdict": verdict,
        "verdict_color": verdict_color,
        "flags": flags if flags else [("✅", "No red flags", "No major risk signals detected")]
    }