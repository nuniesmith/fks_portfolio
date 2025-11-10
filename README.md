# FKS Portfolio Platform
## AI-Optimized Portfolio Management with BTC as Core Backing

**Status**: Phase 1 - Foundation (Complete)  
**Version**: 0.1.0  
**Location**: `repo/portfolio/`  
**Port**: 8012

---

## 🎯 Overview

AI-optimized portfolio management system with BTC as the core backing asset (50-60% allocation). The platform generates trading signals, manages risk using CVaR, and provides emotion-free, data-driven investment decisions.

---

## 📁 Directory Structure

```
repo/portfolio/
├── src/
│   ├── optimization/      # Mean-variance optimization
│   ├── risk/              # CVaR, bias detection, risk metrics
│   ├── data/              # Data fetchers (Yahoo Finance, etc.)
│   ├── signals/            # Signal generation (Phase 3+)
│   ├── portfolio/          # Asset classes, portfolio management
│   ├── backtesting/        # Backtesting framework
│   └── cli.py              # Command-line interface
├── tests/                  # Unit tests
├── data/                   # Data storage
│   └── historical/         # Historical price data
├── notebooks/              # Jupyter notebooks for analysis
├── Dockerfile              # Docker container definition
├── docker-compose.yml      # Docker Compose configuration
├── entrypoint.sh           # Container entrypoint
├── requirements.txt        # Python dependencies
├── pytest.ini             # Pytest configuration
├── ruff.toml              # Linting configuration
├── LICENSE                # MIT License
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd repo/portfolio
pip install -r requirements.txt
```

**Note**: TA-Lib requires system libraries. On Ubuntu/Debian:
```bash
sudo apt-get install ta-lib
```

### 2. Set Up Environment

```bash
cp .env.example .env
# Edit .env with your API keys (optional for Phase 1)
```

### 3. Test Data Fetching

```bash
python -m src.data.fetchers
```

### 4. Run Portfolio Optimization

```bash
python -m src.cli --optimize
```

---

## 📋 Phase 1 Tasks

- [x] Task 1.1: Repo and Environment Preparation
- [x] Task 1.2: Define Portfolio Structure
- [x] Task 1.3: Initial Risk Framework
- [x] Task 1.4: Backtesting Framework

**Status**: ✅ Phase 1 Complete - See `PHASE1_COMPLETE.md` for details

---

## 🔧 Development

### Running Tests

```bash
pytest tests/
```

### Code Style

Follow PEP 8. Use `ruff` for linting (if configured).

---

## 📚 Documentation

See `todo/tasks/active/` for detailed phase plans:
- `00-PORTFOLIO-PLATFORM-MASTER-PLAN.md` - Overall plan
- `01-PHASE-1-FOUNDATION.md` - Phase 1 details

---

## 🔗 Integration with FKS Services

- **fks_data**: Historical data storage and retrieval
- **fks_ai**: AI-enhanced signal generation (Phase 5)
- **fks_web**: Web dashboard (Phase 4)
- **fks_execution**: Trade execution (future)

---

**Next Steps**: Complete Task 1.2 - Portfolio Structure Implementation

