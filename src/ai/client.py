"""
AI Service Client
Client for communicating with fks_ai service
"""
import os
from typing import Dict, Any, Optional
from datetime import datetime
import httpx
from loguru import logger


class AIServiceClient:
    """Client for fks_ai service"""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize AI service client
        
        Args:
            base_url: Base URL for fks_ai service (default: from env or http://fks_ai:8007)
        """
        self.base_url = base_url or os.getenv(
            "FKS_AI_BASE_URL",
            "http://fks_ai:8007"
        )
        self.timeout = 30.0
        self.logger = logger.bind(component="AIServiceClient")
        
        # Create async client
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            base_url=self.base_url
        )
    
    async def analyze_symbol(
        self,
        symbol: str,
        market_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get multi-agent analysis for symbol
        
        Args:
            symbol: Asset symbol (e.g., "BTC")
            market_data: Optional market data dict
        
        Returns:
            Analysis response with insights, debate, decision, signal
        """
        try:
            if market_data is None:
                market_data = {}
            
            response = await self.client.post(
                "/ai/analyze",
                json={
                    "symbol": symbol.upper(),
                    "market_data": market_data
                },
                timeout=60.0  # AI analysis can take longer
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self.logger.warning(f"AI analyze service unavailable: {e}, using fallback")
            # Return fallback response
            return {
                "confidence": 0.5,
                "final_decision": "HOLD",
                "summary": "AI service unavailable, using baseline signal",
                "bull_consensus": 0.5,
                "bear_consensus": 0.5
            }
        except Exception as e:
            self.logger.warning(f"Unexpected error in analyze_symbol: {e}, using fallback")
            return {
                "confidence": 0.5,
                "final_decision": "HOLD",
                "summary": f"Error: {e}",
                "bull_consensus": 0.5,
                "bear_consensus": 0.5
            }
    
    async def debate_signal(
        self,
        signal: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get bull/bear debate on signal
        
        Args:
            signal: Signal dictionary
        
        Returns:
            Debate response with bull and bear perspectives
        """
        try:
            # Prepare debate request
            debate_request = {
                "symbol": signal.get("symbol", ""),
                "market_data": {
                    "price": signal.get("entry_price", 0),
                    "volume": 0,
                    "timestamp": signal.get("timestamp", datetime.now().isoformat())
                }
            }
            
            response = await self.client.post(
                "/ai/debate",
                json=debate_request
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self.logger.warning(f"AI debate service unavailable: {e}, using fallback")
            # Return fallback response
            return {
                "debate_output": {
                    "bull": "AI service unavailable",
                    "bear": "AI service unavailable"
                },
                "bull_consensus": 0.5,
                "bear_consensus": 0.5,
                "summary": "AI debate service unavailable"
            }
        except Exception as e:
            self.logger.warning(f"Unexpected error in debate_signal: {e}, using fallback")
            return {
                "debate_output": {
                    "bull": "Error",
                    "bear": "Error"
                },
                "bull_consensus": 0.5,
                "bear_consensus": 0.5,
                "summary": f"Error: {e}"
            }
    
    async def detect_bias(
        self,
        signal: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Detect bias in signal using AI
        
        Args:
            signal: Signal dictionary
        
        Returns:
            Bias detection response
        """
        try:
            response = await self.client.post(
                "/ai/judge/bias",
                json=signal
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self.logger.error(f"Error calling AI bias detection: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in detect_bias: {e}")
            raise
    
    async def query_memory(
        self,
        query: str,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Query similar past decisions from memory
        
        Args:
            query: Query string
            limit: Maximum number of results
        
        Returns:
            Memory query response
        """
        try:
            response = await self.client.get(
                "/ai/memory/query",
                params={"query": query, "limit": limit}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self.logger.error(f"Error calling AI memory query: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in query_memory: {e}")
            raise
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """
        Get status of all AI agents
        
        Returns:
            Agent status response
        """
        try:
            response = await self.client.get("/ai/agents/status")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            self.logger.error(f"Error calling AI agent status: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in get_agent_status: {e}")
            raise
    
    async def health_check(self) -> bool:
        """
        Check if AI service is healthy
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = await self.client.get("/health")
            response.raise_for_status()
            data = response.json()
            return data.get("status") == "healthy"
        except Exception as e:
            self.logger.warning(f"AI service health check failed: {e}")
            return False
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

