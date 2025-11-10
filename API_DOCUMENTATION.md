# Portfolio API Documentation

**Base URL**: `http://localhost:8012`  
**Version**: 0.1.0

---

## Endpoints

### Health & Info

#### `GET /`
Root endpoint
```json
{
  "service": "FKS Portfolio API",
  "version": "0.1.0",
  "status": "running"
}
```

#### `GET /api/health`
Health check
```json
{
  "status": "healthy"
}
```

---

### Asset Prices

#### `GET /api/assets/prices`
Get current prices for assets

**Query Parameters**:
- `symbols` (optional): Comma-separated list of symbols (default: all enabled)

**Response**:
```json
[
  {
    "symbol": "BTC",
    "price_usd": 101862.59,
    "price_btc": 1.0,
    "change_24h": null
  },
  {
    "symbol": "ETH",
    "price_usd": 3415.23,
    "price_btc": 0.0335,
    "change_24h": null
  }
]
```

**Example**:
```bash
curl "http://localhost:8012/api/assets/prices?symbols=BTC,ETH,SPY"
```

---

### Portfolio Value

#### `GET /api/portfolio/value`
Get portfolio value in BTC terms

**Query Parameters**:
- `allocations` (optional): JSON string of allocations

**Response**:
```json
{
  "total_btc": 0.53419407,
  "holdings_btc": {
    "BTC": 0.50000000,
    "ETH": 0.03353537,
    "SPY": 0.00065870
  },
  "btc_allocation": 0.936,
  "timestamp": "2025-01-XXT00:00:00"
}
```

**Example**:
```bash
curl "http://localhost:8012/api/portfolio/value"
```

---

### Correlation Analysis

#### `GET /api/correlation/btc`
Get correlation to BTC for symbols

**Query Parameters**:
- `symbols` (required): Comma-separated list of symbols
- `lookback_days` (optional): Number of days (default: 90)

**Response**:
```json
[
  {
    "symbol": "ETH",
    "correlation_to_btc": 0.823
  },
  {
    "symbol": "SPY",
    "correlation_to_btc": 0.312
  }
]
```

**Example**:
```bash
curl "http://localhost:8012/api/correlation/btc?symbols=ETH,SPY,GLD&lookback_days=90"
```

#### `GET /api/correlation/matrix`
Get full correlation matrix

**Query Parameters**:
- `symbols` (required): Comma-separated list of symbols
- `lookback_days` (optional): Number of days (default: 90)

**Response**:
```json
{
  "matrix": {
    "BTC": {"BTC": 1.0, "ETH": 0.823, "SPY": 0.312},
    "ETH": {"BTC": 0.823, "ETH": 1.0, "SPY": 0.245},
    "SPY": {"BTC": 0.312, "ETH": 0.245, "SPY": 1.0}
  },
  "symbols": ["BTC", "ETH", "SPY"]
}
```

---

### Diversification

#### `GET /api/diversification/score`
Get diversification score

**Query Parameters**:
- `symbols` (required): Comma-separated list of symbols

**Response**:
```json
{
  "score": 0.44,
  "is_diversified": true,
  "suggestions": ["GLD", "USDT", "QQQ"],
  "symbols": ["BTC", "ETH", "SPY"]
}
```

**Example**:
```bash
curl "http://localhost:8012/api/diversification/score?symbols=BTC,ETH,SPY"
```

---

### Rebalancing

#### `GET /api/rebalancing/plan`
Get rebalancing plan

**Query Parameters**:
- `allocations` (required): JSON string of current allocations
- `target_btc_pct` (optional): Target BTC allocation (default: 0.5)

**Response**:
```json
{
  "target_btc_allocation": 0.5,
  "current_btc_allocation": 0.9708,
  "actions": [
    {
      "symbol": "BTC",
      "action": "sell",
      "amount": 0.25,
      "current_amount": 0.5
    },
    {
      "symbol": "ETH",
      "action": "buy",
      "amount": 0.1,
      "current_amount": 0.2
    }
  ]
}
```

**Example**:
```bash
curl "http://localhost:8012/api/rebalancing/plan?allocations={\"BTC\":0.5,\"ETH\":0.2,\"SPY\":0.3}&target_btc_pct=0.5"
```

---

### Asset Configuration

#### `GET /api/assets/enabled`
Get list of enabled assets

**Response**:
```json
{
  "assets": [
    {
      "symbol": "BTC",
      "priority": 1,
      "adapters": ["binance", "coingecko"],
      "collection_interval": "daily",
      "last_collected": "2025-01-XXT00:00:00"
    }
  ]
}
```

---

## Running the API

### Via CLI
```bash
python src/cli.py --api --api-port 8012
```

### Via Python
```python
from src.api.server import app
import uvicorn

uvicorn.run(app, host="0.0.0.0", port=8012)
```

### Via Docker
The API will be available when the portfolio service container starts.

---

## Integration with fks_web

The Django web dashboard can consume these endpoints:

```python
# In Django views
import requests

def portfolio_dashboard(request):
    # Fetch portfolio value
    response = requests.get("http://portfolio:8012/api/portfolio/value")
    portfolio_data = response.json()
    
    # Fetch asset prices
    prices_response = requests.get("http://portfolio:8012/api/assets/prices")
    prices = prices_response.json()
    
    return render(request, "portfolio/dashboard.html", {
        "portfolio": portfolio_data,
        "prices": prices
    })
```

---

## CORS

CORS is enabled for all origins (for development). In production, configure specific origins in `src/api/routes.py`.

---

## Error Handling

All endpoints return standard HTTP status codes:
- `200`: Success
- `500`: Server error (with error detail in response)

---

**API Status**: ✅ Ready for integration with fks_web dashboard

