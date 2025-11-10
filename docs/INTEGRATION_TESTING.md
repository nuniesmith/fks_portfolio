# Portfolio Service - Integration Testing Guide

**Date**: 2025-01-XX  
**Status**: Ready for Testing

---

## 🧪 Testing Overview

This guide covers integration testing for the portfolio service and its integration with fks_web.

---

## 📋 Prerequisites

### Services Required
- **fks_portfolio**: Running on port 8012
- **fks_web**: Running on port 8000 (optional for API tests)
- **fks_data**: Running on port 8003 (optional, for data integration)
- **fks_ai**: Running on port 8007 (optional, for AI-enhanced signals)

### Environment Setup
```bash
# Set environment variables
export PORTFOLIO_URL=http://localhost:8012
export WEB_URL=http://localhost:8000

# Or use .env file
PORTFOLIO_URL=http://localhost:8012
WEB_URL=http://localhost:8000
```

---

## 🚀 Quick Test

### Run Integration Tests
```bash
# Run integration test script
cd repo/portfolio
./scripts/test_integration.sh

# Or run pytest
pytest tests/test_api_integration.py -v
```

### Run Demo Workflow
```bash
# Run demo workflow
./scripts/demo_workflow.sh
```

---

## 📊 Test Categories

### 1. Health Checks

**Test**: Service health and readiness
```bash
# Health check
curl http://localhost:8012/health

# Readiness check
curl http://localhost:8012/ready
```

**Expected**: HTTP 200, status "healthy" or "ready"

---

### 2. Dashboard API Tests

#### Dashboard Overview
```bash
curl http://localhost:8012/api/dashboard/overview
```

**Expected**:
- HTTP 200
- JSON with `assets`, `signals`, `timestamp`
- Asset prices and counts
- Signal summaries

#### Performance Metrics
```bash
curl "http://localhost:8012/api/dashboard/performance?days=30"
```

**Expected**:
- HTTP 200
- JSON with `period_days`, `assets`, `aggregate`
- Performance metrics for each asset
- Aggregate metrics

#### Signal Summary
```bash
curl http://localhost:8012/api/dashboard/signals/summary
```

**Expected**:
- HTTP 200
- JSON with `by_category`, `totals`
- Signal counts by category
- Total signal statistics

#### Charts
```bash
# Allocation chart
curl http://localhost:8012/api/dashboard/charts/allocation

# Performance chart
curl "http://localhost:8012/api/dashboard/charts/performance?days=30"
```

**Expected**:
- HTTP 200
- JSON with chart data
- Proper data format for Chart.js

---

### 3. Signal Generation Tests

#### Generate Signals
```bash
curl "http://localhost:8012/api/signals/generate?category=swing"
```

**Expected**:
- HTTP 200
- JSON with `signals`, `count`, `category`
- Each signal has: symbol, entry_price, take_profit, stop_loss, risk_reward_ratio
- Signals are valid (risk/reward >= 1.0)

#### AI-Enhanced Signals
```bash
curl "http://localhost:8012/api/ai/signals/enhanced?category=swing"
```

**Expected**:
- HTTP 200
- Signals with `ai_enhancements` field
- Enhanced confidence and strength
- AI insights included

---

### 4. Portfolio API Tests

#### Portfolio Value
```bash
curl http://localhost:8012/api/portfolio/value
```

**Expected**:
- HTTP 200
- JSON with `total_btc`, `holdings`
- All values in BTC terms

#### Asset Prices
```bash
curl "http://localhost:8012/api/assets/prices?symbols=BTC,ETH,SPY"
```

**Expected**:
- HTTP 200
- JSON with price data for each symbol
- Current prices and historical data

---

### 5. Web Integration Tests

#### Dashboard Page
```bash
# Access dashboard (requires authentication)
curl -L http://localhost:8000/portfolio/
```

**Expected**:
- HTTP 200 (or redirect to login)
- Dashboard page loads
- Charts render correctly
- Data displays properly

#### Signals Page
```bash
curl -L "http://localhost:8000/portfolio/signals/?category=swing"
```

**Expected**:
- HTTP 200 (or redirect to login)
- Signals page loads
- Signal table displays
- Filters work

#### Performance Page
```bash
curl -L "http://localhost:8000/portfolio/performance/?days=30"
```

**Expected**:
- HTTP 200 (or redirect to login)
- Performance page loads
- Charts render
- Metrics display

---

## 🔍 Manual Testing Checklist

### API Endpoints
- [ ] Health check returns 200
- [ ] Readiness check returns 200
- [ ] Dashboard overview returns data
- [ ] Performance metrics return data
- [ ] Signal summary returns data
- [ ] Charts return valid data
- [ ] Signal generation works
- [ ] AI-enhanced signals work (if fks_ai available)
- [ ] Portfolio value returns BTC values
- [ ] Asset prices return data

### Web Interface
- [ ] Dashboard page loads
- [ ] Charts render correctly
- [ ] Asset prices display
- [ ] Signal summary displays
- [ ] Signals page loads
- [ ] Signal filtering works
- [ ] Performance page loads
- [ ] Performance charts render
- [ ] Navigation works
- [ ] Error handling works (service down)

### Data Flow
- [ ] Data ingestion works
- [ ] Data storage works
- [ ] Data retrieval works
- [ ] BTC conversion works
- [ ] Portfolio optimization works
- [ ] Signal generation works
- [ ] Bias detection works

---

## 🐛 Troubleshooting

### Service Not Responding
```bash
# Check if service is running
curl http://localhost:8012/health

# Check logs
docker logs fks_portfolio

# Check service status
docker ps | grep portfolio
```

### API Errors
```bash
# Check API response
curl -v http://localhost:8012/api/dashboard/overview

# Check error logs
tail -f repo/portfolio/data/logs/*.log
```

### Web Integration Issues
```bash
# Check web service
curl http://localhost:8000/health

# Check portfolio service from web
curl http://fks_portfolio:8012/health

# Check Django logs
docker logs fks_web
```

---

## 📊 Performance Testing

### Response Time Targets
- Health check: < 100ms
- Dashboard overview: < 500ms
- Signal generation: < 5s
- Performance metrics: < 1s
- Chart data: < 500ms

### Load Testing
```bash
# Simple load test
for i in {1..10}; do
    curl -s http://localhost:8012/api/dashboard/overview > /dev/null
done
```

---

## ✅ Success Criteria

### API Tests
- All health checks pass
- All dashboard endpoints return data
- Signal generation works
- Error handling works
- Response times within targets

### Web Integration
- All pages load
- Charts render
- Data displays correctly
- Navigation works
- Error handling works

### End-to-End
- Data ingestion → Storage → Retrieval works
- Signal generation → Display works
- Portfolio optimization → Display works
- BTC conversion → Display works

---

## 🚀 Next Steps

1. **Run Integration Tests**: Execute test scripts
2. **Manual Testing**: Test web interface manually
3. **Performance Testing**: Check response times
4. **Load Testing**: Test under load
5. **Documentation**: Document any issues found

---

**Status**: Ready for Testing  
**Next**: Execute integration tests and document results

