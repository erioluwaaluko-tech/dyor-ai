# 🤖 DYOR.ai — AI-Powered Token Intelligence Platform

> Stop guessing. Actually DYOR.

**Live:** https://dyor-ai.onrender.com

---

## What It Does

DYOR.ai is the first AI-powered token intelligence platform for Solana. Paste any token address and get a complete intelligence report in seconds — no wallet connection, no sign-up, no fees.

Every report includes:
- 🔴 **Risk Score** (0–100) across 6 on-chain signals
- 🤖 **AI Narrative** — plain-English analysis powered by Claude
- 📈 **Lifecycle Stage** — Early / Growing / Peaking / Distribution / Declining
- 📊 **24h Price Chart** from Birdeye OHLCV data
- 🔍 **Multi-Token Comparison** — analyze up to 3 tokens side by side
- 📋 **Token Watchlist** — monitor up to 5 tokens with auto-refresh
- 💡 **Market Health** — price, volume, liquidity, holders, trades

---

## Risk Scoring — 6 Signals

| Signal | Max Points | What It Detects |
|--------|-----------|-----------------|
| Liquidity depth | 25 pts | Low liquidity = easy price manipulation |
| Volume / Market Cap ratio | 25 pts | Extreme ratio = coordinated pump signal |
| 24h price spike | 20 pts | 200%+ move = possible pump in progress |
| Holder count | 20 pts | Under 50 holders = concentrated dump risk |
| Wash trading signal | 15 pts | High volume + very few trades = fake activity |
| Unique wallet activity | 10 pts | Few wallets driving high volume = coordinated buying |

**Risk Labels:** 🟢 LOW RISK (0–39) · 🟡 MEDIUM RISK (40–69) · 🔴 HIGH RISK (70–100)

---

## Lifecycle Stages

| Stage | What It Means |
|-------|--------------|
| Early | New token, few holders. Highest risk and potential. |
| Growing | Organic momentum building. Usually the best entry window. |
| Peaking | Already pumped significantly. Late entry risk. |
| Distribution | Price stalling, whales selling to retail. Classic dump setup. |
| Declining | Both price and volume falling. High downside risk. |

---

## Tech Stack

- **Backend:** Python 3.13, FastAPI, Uvicorn
- **Data:** Birdeye Data API — `/defi/token_overview`, `/defi/ohlcv`, `/defi/token_trending`, `/defi/tokenlist`
- **AI:** Anthropic Claude API — `claude-sonnet-4-20250514`
- **Frontend:** Vanilla HTML/CSS/JS, Chart.js
- **Deployment:** Render

---

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Serves the DYOR.ai dashboard |
| `GET /api/analyze/{address}` | Full intelligence report for any Solana token |
| `GET /api/watchlist?addresses=a,b,c` | Scan multiple tokens for watchlist |
| `GET /api/compare?a=x&b=y&c=z` | Compare 2-3 tokens side by side |
| `GET /status` | Server health check |

---

## Run Locally

```bash
git clone https://github.com/erioluwaaluko-tech/dyor-ai.git
cd dyor-ai
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env`:
BIRDEYE_API_KEY=your_birdeye_key
ANTHROPIC_API_KEY=your_anthropic_key

Start server:
```bash
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000` in your browser.

---

## Built For

[Birdeye Data BIP Competition](https://bds.birdeye.so) — Sprint 4 (May 9–16, 2026)

Built by [@erioluwaaluko-tech](https://github.com/erioluwaaluko-tech)