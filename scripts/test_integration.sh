#!/bin/bash
# Integration test script for portfolio service
# Tests API endpoints and web integration

set -e

PORTFOLIO_URL="${PORTFOLIO_URL:-http://localhost:8012}"
WEB_URL="${WEB_URL:-http://localhost:8000}"

echo "=== Portfolio Service Integration Tests ==="
echo ""
echo "Portfolio Service: $PORTFOLIO_URL"
echo "Web Service: $WEB_URL"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Test function
test_endpoint() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "Testing $name... "
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" --max-time 10)
    
    if [ "$response" == "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL (HTTP $response)${NC}"
        ((FAILED++))
        return 1
    fi
}

# Test health endpoints
echo "=== Health Checks ==="
test_endpoint "Health Check" "$PORTFOLIO_URL/health"
test_endpoint "Readiness Check" "$PORTFOLIO_URL/ready"

echo ""
echo "=== Dashboard API Endpoints ==="
test_endpoint "Dashboard Overview" "$PORTFOLIO_URL/api/dashboard/overview"
test_endpoint "Dashboard Performance" "$PORTFOLIO_URL/api/dashboard/performance?days=30"
test_endpoint "Signal Summary" "$PORTFOLIO_URL/api/dashboard/signals/summary"
test_endpoint "Allocation Chart" "$PORTFOLIO_URL/api/dashboard/charts/allocation"
test_endpoint "Performance Chart" "$PORTFOLIO_URL/api/dashboard/charts/performance?days=30"

echo ""
echo "=== Signal API Endpoints ==="
test_endpoint "Generate Signals" "$PORTFOLIO_URL/api/signals/generate?category=swing"
test_endpoint "Signal Summary" "$PORTFOLIO_URL/api/signals/summary?category=swing"

echo ""
echo "=== Portfolio API Endpoints ==="
test_endpoint "Portfolio Value" "$PORTFOLIO_URL/api/portfolio/value"
test_endpoint "Asset Prices" "$PORTFOLIO_URL/api/assets/prices?symbols=BTC,ETH"

echo ""
echo "=== AI API Endpoints ==="
test_endpoint "AI Health" "$PORTFOLIO_URL/api/ai/health"

echo ""
echo "=== Test Results ==="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi

