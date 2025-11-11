# Portfolio Service - Architecture Documentation

**Date**: 2025-01-XX  
**Version**: 0.1.0

---

## 🏗️ Architecture Overview

The portfolio service is a FastAPI-based microservice that provides AI-optimized portfolio management with BTC as the core backing asset.

---

## 📦 Service Structure

```
repo/portfolio/
├── src/
│   ├── api/              # API routes and server
│   ├── data/             # Data collection and management
│   ├── portfolio/        # Portfolio management
│   ├── optimization/     # Portfolio optimization
│   ├── risk/             # Risk management
│   ├── signals/          # Signal generation
│   ├── guidance/         # User guidance
│   ├── ai/               # AI integration
│   ├── dashboard/        # Dashboard data providers
│   └── backtesting/      # Backtesting framework
├── tests/                # Unit and integration tests
├── data/                 # Data storage
├── scripts/              # Utility scripts
└── docs/                 # Documentation
```

---

## 🔄 Data Flow

### 1. Data Collection
```
Data Sources → Adapters → Data Manager → Storage → Cache
```

**Sources**:
- Yahoo Finance
- CoinGecko
- Polygon
- Alpha Vantage
- Binance
- CoinMarketCap

**Flow**:
1. Adapters fetch data from sources
2. Data Manager selects appropriate adapter
3. Data is cached and stored in SQLite
4. Background collector periodically updates data

### 2. Signal Generation
```
Market Data → Signal Engine → Signal Generator → Bias Detection → AI Enhancement → Signals
```

**Flow**:
1. Signal Engine analyzes market data
2. Technical indicators calculated
3. Signals generated with entry/TP/SL
4. Bias detection filters signals
5. AI enhancement (optional) refines signals
6. Valid signals returned

### 3. Portfolio Optimization
```
Asset Data → Optimization Engine → Constraints → BTC Conversion → Portfolio
```

**Flow**:
1. Asset data collected
2. Mean-variance optimization
3. BTC constraints applied (50-60%)
4. Portfolio allocation calculated
5. Values converted to BTC terms

---

## 🔗 Service Integration

### fks_data Integration
- **Purpose**: Historical data storage
- **Status**: Ready for integration
- **API**: Can query fks_data for historical data
- **Fallback**: Local adapters if fks_data unavailable

### fks_ai Integration
- **Purpose**: AI-enhanced signal generation
- **Status**: Integrated (Phase 5)
- **API**: `http://fks_ai:8007`
- **Features**: Signal refinement, bias detection, BTC optimization

### fks_web Integration
- **Purpose**: Web dashboard
- **Status**: Integrated (Phase 6)
- **API**: Portfolio API consumed by Django views
- **Features**: Dashboard, signals, performance views

### fks_execution Integration
- **Purpose**: Trade execution
- **Status**: Future integration
- **API**: Signals can trigger execution
- **Features**: Manual execution workflow ready

---

## 📊 API Architecture

### REST API Endpoints
- **Base URL**: `http://fks_portfolio:8012`
- **Framework**: FastAPI
- **Total Endpoints**: 37

### Endpoint Categories
1. **Portfolio** (13 endpoints): Asset management, portfolio value, optimization
2. **Signals** (3 endpoints): Signal generation, summary, categories
3. **Guidance** (5 endpoints): Decision support, workflow, tracking
4. **AI** (7 endpoints): AI analysis, bias detection, BTC optimization
5. **Dashboard** (9 endpoints): Overview, performance, charts

### API Design
- RESTful design
- JSON request/response
- Error handling with proper HTTP status codes
- CORS enabled for web integration
- Health checks for monitoring

---

## 💾 Data Storage

### SQLite Database
- **Location**: `data/historical/portfolio.db`
- **Tables**: `prices`, `assets`, `signals`, `decisions`
- **Purpose**: Historical data storage
- **Backup**: Regular backups recommended

### File Cache
- **Location**: `data/cache/`
- **Purpose**: API response caching
- **TTL**: 300 seconds (5 minutes)
- **Format**: Pickle files

### Configuration
- **Location**: `data/config/assets.json`
- **Purpose**: Asset configuration
- **Format**: JSON
- **Content**: Enabled assets, priorities, adapters

---

## 🔒 Security

### API Keys
- Stored in environment variables
- Never committed to git
- Rotated regularly
- Access controlled

### Data Protection
- Sensitive data encrypted
- Secure database connections
- Access control
- Regular backups

### Network Security
- HTTPS in production
- CORS configured
- Firewall rules
- Service isolation

---

## 📈 Performance

### Optimization
- Data caching (5 minute TTL)
- Async API endpoints
- Efficient database queries
- Background data collection

### Scalability
- Stateless API design
- Horizontal scaling possible
- Database optimization
- Caching strategies

### Monitoring
- Health checks
- Readiness checks
- Performance metrics
- Error logging

---

## 🧪 Testing

### Unit Tests
- Test individual components
- Mock external dependencies
- Test error handling
- Test edge cases

### Integration Tests
- Test API endpoints
- Test service integration
- Test data flow
- Test error scenarios

### End-to-End Tests
- Test full workflow
- Test web integration
- Test data accuracy
- Test performance

---

## 🚀 Deployment

### Docker
- Containerized service
- Docker Compose configuration
- Health checks
- Volume mounts

### Kubernetes
- Service deployment
- Health probes
- Resource limits
- Auto-scaling

### Environment Variables
- Port configuration
- API keys
- Service URLs
- Log levels

---

## 📚 Dependencies

### Core Dependencies
- FastAPI: API framework
- Uvicorn: ASGI server
- Pydantic: Data validation
- Pandas: Data manipulation
- NumPy: Numerical computing

### Portfolio Dependencies
- PyPortfolioOpt: Portfolio optimization
- TA-Lib: Technical analysis
- SciPy: Scientific computing

### Data Dependencies
- yfinance: Yahoo Finance
- requests: HTTP client
- httpx: Async HTTP client

### AI Dependencies
- httpx: AI service client
- (fks_ai service): AI analysis

---

## 🔄 Future Enhancements

### Planned Features
- PostgreSQL migration
- Redis caching
- WebSocket support
- Real-time updates
- Advanced backtesting
- Multi-user support

### Integration Plans
- fks_execution: Trade execution
- fks_analyze: Performance analysis
- fks_app: Strategy signals
- fks_ninja: NinjaTrader integration
- fks_meta: MetaTrader integration

---

## 📊 Metrics and Monitoring

### Key Metrics
- API response times
- Error rates
- Request counts
- Service availability
- Data collection status
- Signal generation rate

### Monitoring Tools
- Health checks
- Readiness checks
- Logging
- Performance metrics
- Error tracking

---

## 🎯 Success Criteria

### Functional
- All API endpoints working
- Data collection operational
- Signal generation functional
- Portfolio optimization working
- Web integration complete

### Performance
- API response times < 1s
- Signal generation < 5s
- Data collection efficient
- Caching effective

### Reliability
- Service availability > 99%
- Error handling robust
- Graceful degradation
- Health checks working

---

**Status**: Architecture Complete  
**Next**: Continue with testing and deployment

