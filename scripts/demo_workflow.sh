#!/bin/bash
# Demo workflow script for portfolio platform
# Demonstrates end-to-end workflow from data to signals

set -e

PORTFOLIO_URL="${PORTFOLIO_URL:-http://localhost:8012}"

echo "=== Portfolio Platform Demo Workflow ==="
echo ""
echo "Portfolio Service: $PORTFOLIO_URL"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}Step 1: Health Check${NC}"
echo "Checking portfolio service health..."
curl -s "$PORTFOLIO_URL/health" | python3 -m json.tool
echo ""

echo -e "${BLUE}Step 2: Dashboard Overview${NC}"
echo "Fetching portfolio overview..."
curl -s "$PORTFOLIO_URL/api/dashboard/overview" | python3 -m json.tool | head -30
echo ""

echo -e "${BLUE}Step 3: Generate Signals${NC}"
echo "Generating swing trading signals..."
curl -s "$PORTFOLIO_URL/api/signals/generate?category=swing" | python3 -m json.tool | head -50
echo ""

echo -e "${BLUE}Step 4: Performance Metrics${NC}"
echo "Fetching performance metrics (30 days)..."
curl -s "$PORTFOLIO_URL/api/dashboard/performance?days=30" | python3 -m json.tool | head -40
echo ""

echo -e "${BLUE}Step 5: Portfolio Allocation${NC}"
echo "Fetching portfolio allocation..."
curl -s "$PORTFOLIO_URL/api/dashboard/charts/allocation" | python3 -m json.tool
echo ""

echo -e "${GREEN}Demo workflow complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Access web dashboard at http://localhost:8000/portfolio/"
echo "2. View signals at http://localhost:8000/portfolio/signals/"
echo "3. Check performance at http://localhost:8000/portfolio/performance/"

