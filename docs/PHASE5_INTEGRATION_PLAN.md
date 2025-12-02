# Phase 5: AI Optimization Layer - Integration Plan

**Date**: 2025-01-XX  
**Status**: Ready to Start  
**Dependencies**: fks_ai service (Port 8007)

---

## 🎯 Overview

Phase 5 integrates the portfolio service with fks_ai to enhance signals with AI-driven intelligence, bias mitigation, and BTC-centric optimization.

---

## 🔗 fks_ai Service Integration

### Service Details
- **Port**: 8007
- **Base URL**: `http://fks_ai:8007` (Docker) or `http://localhost:8007` (Local)
- **Framework**: FastAPI
- **Status**: ✅ Active with multi-agent system

### Available Endpoints

#### 1. Multi-Agent Analysis
- **Endpoint**: `POST /ai/analyze`
- **Purpose**: Full multi-agent analysis with trading signals
- **Request**:
  ```json
  {
    "symbol": "BTC",
    "market_data": {
      "price": 45000,
      "volume": 1000000,
      "timestamp": "2024-01-01T00:00:00Z"
    }
  }
  ```
- **Response**: Includes analyst insights, debate arguments, final decision, trading signal, confidence score

#### 2. Bull/Bear Debate
- **Endpoint**: `POST /ai/debate`
- **Purpose**: Get bull and bear perspectives on a signal
- **Use Case**: Signal refinement and consensus building

#### 3. Bias Detection
- **Endpoint**: `POST /ai/judge/bias`
- **Purpose**: Analyze systematic bias in signals
- **Use Case**: Advanced bias mitigation (Phase 5.2)

#### 4. Memory Query
- **Endpoint**: `GET /ai/memory/query`
- **Purpose**: Query similar past decisions
- **Use Case**: Learn from historical patterns

#### 5. Agent Status
- **Endpoint**: `GET /ai/agents/status`
- **Purpose**: Health check for all agents
- **Use Case**: Service availability check

---

## 📋 Integration Tasks

### Task 5.1: AI Model Integration

#### Subtask 5.1.1: Create AI Client
**File**: `src/ai/client.py`

```python
import httpx
from typing import Dict, Any, Optional
from loguru import logger

class AIServiceClient:
    """Client for fks_ai service"""
    
    def __init__(self, base_url: str = "http://fks_ai:8007"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.logger = logger.bind(component="AIServiceClient")
    
    async def analyze_symbol(self, symbol: str, market_data: Dict[str, Any]):
        """Get multi-agent analysis for symbol"""
        response = await self.client.post(
            f"{self.base_url}/ai/analyze",
            json={
                "symbol": symbol,
                "market_data": market_data
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def debate_signal(self, signal: Dict[str, Any]):
        """Get bull/bear debate on signal"""
        response = await self.client.post(
            f"{self.base_url}/ai/debate",
            json=signal
        )
        response.raise_for_status()
        return response.json()
    
    async def detect_bias(self, signal: Dict[str, Any]):
        """Detect bias in signal"""
        response = await self.client.post(
            f"{self.base_url}/ai/judge/bias",
            json=signal
        )
        response.raise_for_status()
        return response.json()
```

#### Subtask 5.1.2: Create AI Signal Refiner
**File**: `src/ai/signal_refiner.py`

```python
from .client import AIServiceClient
from ..signals.trading_signal import TradingSignal
from typing import Optional

class AISignalRefiner:
    """Refines signals using AI analysis"""
    
    def __init__(self, ai_client: Optional[AIServiceClient] = None):
        self.ai_client = ai_client or AIServiceClient()
    
    async def refine_signal(self, signal: TradingSignal, market_data: Dict):
        """Refine signal using AI analysis"""
        # Get AI analysis
        analysis = await self.ai_client.analyze_symbol(
            signal.symbol,
            market_data
        )
        
        # Get debate perspectives
        debate = await self.ai_client.debate_signal(signal.to_dict())
        
        # Refine signal based on AI insights
        refined_signal = self._apply_ai_insights(signal, analysis, debate)
        
        return refined_signal
```

#### Subtask 5.1.3: Integrate with Signal Generator
**File**: `src/signals/signal_generator.py` (update)

Add AI enhancement option:

```python
async def generate_ai_enhanced_signals(
    self,
    category: TradeCategory,
    symbols: Optional[List[str]] = None,
    enable_ai: bool = True
) -> List[TradingSignal]:
    """Generate signals with optional AI enhancement"""
    # Generate baseline signals
    signals = self.generate_daily_signals(category, symbols)
    
    if enable_ai:
        # Enhance with AI
        from ..ai.signal_refiner import AISignalRefiner
        refiner = AISignalRefiner()
        
        enhanced_signals = []
        for signal in signals:
            market_data = await self._get_market_data(signal.symbol)
            enhanced_signal = await refiner.refine_signal(signal, market_data)
            enhanced_signals.append(enhanced_signal)
        
        return enhanced_signals
    
    return signals
```

### Task 5.2: Advanced Bias Mitigation

#### Subtask 5.2.1: Integrate AI Bias Detection
**File**: `src/ai/bias_mitigation.py`

```python
from .client import AIServiceClient
from ..risk.bias_detection import BiasDetector

class AIBiasMitigator:
    """Advanced bias mitigation using AI"""
    
    def __init__(self):
        self.ai_client = AIServiceClient()
        self.bias_detector = BiasDetector()
    
    async def detect_and_mitigate(self, signal: TradingSignal):
        """Detect bias using AI and provide mitigation"""
        # Get AI bias analysis
        ai_bias = await self.ai_client.detect_bias(signal.to_dict())
        
        # Combine with rule-based detection
        rule_bias = self.bias_detector.detect_bias(signal)
        
        # Provide mitigation suggestions
        mitigation = self._suggest_mitigation(ai_bias, rule_bias)
        
        return {
            "bias_detected": ai_bias.get("bias_detected", False),
            "bias_type": ai_bias.get("bias_type"),
            "mitigation": mitigation,
            "confidence": ai_bias.get("confidence", 0.0)
        }
```

### Task 5.3: BTC-Centric AI Optimization

#### Subtask 5.3.1: BTC Allocation Optimizer
**File**: `src/ai/btc_optimizer.py`

```python
from .client import AIServiceClient
from typing import Dict, Any

class BTCAIOptimizer:
    """AI-powered BTC allocation optimizer"""
    
    def __init__(self):
        self.ai_client = AIServiceClient()
    
    async def optimize_btc_allocation(
        self,
        portfolio: Portfolio,
        market_state: Dict[str, Any]
    ) -> float:
        """Optimize BTC allocation using AI"""
        # Get BTC analysis from AI
        btc_analysis = await self.ai_client.analyze_symbol(
            "BTC",
            market_state
        )
        
        # Determine optimal allocation based on AI confidence
        ai_confidence = btc_analysis.get("confidence", 0.5)
        
        if ai_confidence > 0.7:
            # Bullish - increase BTC allocation
            target_btc = 0.60
        elif ai_confidence > 0.5:
            # Neutral - maintain current
            target_btc = 0.55
        else:
            # Bearish - maintain minimum
            target_btc = 0.50
        
        return target_btc
```

---

## 🚀 Implementation Steps

### Step 1: Create AI Integration Module
1. Create `src/ai/` directory
2. Create `src/ai/__init__.py`
3. Create `src/ai/client.py` - AI service client
4. Create `src/ai/signal_refiner.py` - Signal refinement
5. Add `httpx` to requirements.txt

### Step 2: Integrate with Signal Generator
1. Update `src/signals/signal_generator.py`
2. Add AI enhancement option
3. Update API endpoints to support AI enhancement

### Step 3: Add Bias Mitigation
1. Create `src/ai/bias_mitigation.py`
2. Integrate with existing bias detection
3. Update guidance module to use AI bias detection

### Step 4: BTC Optimization
1. Create `src/ai/btc_optimizer.py`
2. Integrate with portfolio rebalancer
3. Update API endpoints

### Step 5: Testing
1. Create integration tests
2. Test AI service connectivity
3. Test signal refinement
4. Test bias mitigation
5. Test BTC optimization

---

## 📊 API Endpoints to Add

### Signal Endpoints
- `GET /api/signals/generate?category=swing&ai_enhanced=true` - Generate AI-enhanced signals
- `GET /api/signals/ai-analysis?symbol=BTC` - Get AI analysis for symbol

### Guidance Endpoints
- `GET /api/guidance/ai-recommendations` - Get AI-enhanced recommendations
- `POST /api/guidance/ai-bias-check` - Check bias using AI

### Portfolio Endpoints
- `GET /api/portfolio/btc-optimization` - Get AI-optimized BTC allocation
- `POST /api/portfolio/ai-rebalance` - Rebalance using AI recommendations

---

## 🔧 Dependencies

### New Python Packages
- `httpx` - Async HTTP client for AI service
- `aiohttp` - Alternative async HTTP client (optional)

### Service Dependencies
- **fks_ai**: Must be running on port 8007
- **fks_data**: For market data (already integrated)

---

## 📝 Testing Strategy

### Unit Tests
- Test AI client connectivity
- Test signal refinement logic
- Test bias mitigation
- Test BTC optimization

### Integration Tests
- Test with fks_ai service
- Test end-to-end signal generation
- Test error handling (service unavailable)

### Performance Tests
- Test AI service latency
- Test concurrent requests
- Test caching strategy

---

## 🚦 Next Steps

1. **Create AI Integration Module** (Task 5.1.1)
2. **Create AI Client** (Task 5.1.1)
3. **Integrate with Signal Generator** (Task 5.1.3)
4. **Add Bias Mitigation** (Task 5.2)
5. **Add BTC Optimization** (Task 5.3)
6. **Update API Endpoints** (Step 5)
7. **Testing** (Step 5)

---

**Status**: ✅ **Ready to Start**  
**Next Action**: Create AI integration module and client

