"""
Test suite for research agents and tools.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from backend.agents.news_agent import NewsAgent
from backend.agents.filings_agent import FilingsAgent
from backend.agents.price_agent import PriceAgent
from backend.agents.synthesis_agent import SynthesisAgent
from backend.tools.web_search_tool import WebSearchTool
from backend.tools.stock_data_tool import StockDataTool
from backend.tools.sec_edgar_tool import SECEdgarTool
from backend.app.models import TickerInsight, StanceType, ConfidenceLevel


class TestAgents:
    """Test cases for research agents."""
    
    def setup_method(self):
        """Set up test agents with mock LLM."""
        self.mock_llm = Mock()
        self.mock_llm.ainvoke = AsyncMock()
        
        self.news_agent = NewsAgent(self.mock_llm)
        self.filings_agent = FilingsAgent(self.mock_llm)
        self.price_agent = PriceAgent(self.mock_llm)
        self.synthesis_agent = SynthesisAgent(self.mock_llm)
    
    def test_agent_initialization(self):
        """Test that agents are properly initialized."""
        assert self.news_agent.agent_type == "news"
        assert self.filings_agent.agent_type == "filings"
        assert self.price_agent.agent_type == "price"
        
        # Check that agents have tools
        assert len(self.news_agent.tools) > 0
        assert len(self.filings_agent.tools) > 0
        assert len(self.price_agent.tools) > 0
    
    def test_agent_system_prompts(self):
        """Test that agents have proper system prompts."""
        news_prompt = self.news_agent._get_system_prompt()
        assert "news" in news_prompt.lower()
        assert "financial" in news_prompt.lower()
        
        filings_prompt = self.filings_agent._get_system_prompt()
        assert "sec" in filings_prompt.lower() or "filing" in filings_prompt.lower()
        
        price_prompt = self.price_agent._get_system_prompt()
        assert "price" in price_prompt.lower() or "technical" in price_prompt.lower()
    
    @pytest.mark.asyncio
    async def test_news_agent_action_selection(self):
        """Test news agent action selection logic."""
        context = {"ticker": "AAPL", "iteration": 1}
        
        # Test earnings-related thought
        earnings_thought = "I need to find recent earnings information"
        action, action_input = await self.news_agent._act(earnings_thought, context)
        assert action == "web_search"
        assert "earnings" in action_input.lower()
        assert "AAPL" in action_input
        
        # Test analyst-related thought
        analyst_thought = "I should look for analyst ratings"
        action, action_input = await self.news_agent._act(analyst_thought, context)
        assert action == "web_search"
        assert "analyst" in action_input.lower()
        assert "AAPL" in action_input
    
    @pytest.mark.asyncio
    async def test_synthesis_agent_stance_parsing(self):
        """Test synthesis agent stance parsing."""
        # Test buy stance
        assert self.synthesis_agent._parse_stance("buy") == StanceType.BUY
        assert self.synthesis_agent._parse_stance("strong buy") == StanceType.BUY
        
        # Test sell stance
        assert self.synthesis_agent._parse_stance("sell") == StanceType.SELL
        assert self.synthesis_agent._parse_stance("strong sell") == StanceType.SELL
        
        # Test hold stance (default)
        assert self.synthesis_agent._parse_stance("hold") == StanceType.HOLD
        assert self.synthesis_agent._parse_stance("unknown") == StanceType.HOLD
    
    @pytest.mark.asyncio
    async def test_synthesis_agent_confidence_parsing(self):
        """Test synthesis agent confidence parsing."""
        assert self.synthesis_agent._parse_confidence("high") == ConfidenceLevel.HIGH
        assert self.synthesis_agent._parse_confidence("low") == ConfidenceLevel.LOW
        assert self.synthesis_agent._parse_confidence("medium") == ConfidenceLevel.MEDIUM
        assert self.synthesis_agent._parse_confidence("unknown") == ConfidenceLevel.MEDIUM
    
    @pytest.mark.asyncio
    async def test_synthesis_agent_analysis_parsing(self):
        """Test synthesis agent analysis response parsing."""
        mock_response = """
        SUMMARY:
        Apple shows strong financial performance with solid growth prospects.
        
        KEY_DRIVERS:
        - iPhone sales growth
        - Services revenue expansion
        - Strong brand loyalty
        
        RISKS:
        - Supply chain disruptions
        - Regulatory challenges
        - Market saturation
        
        CATALYSTS:
        - New product launches
        - Market expansion
        """
        
        analysis = self.synthesis_agent._parse_analysis_response(mock_response)
        
        assert "Apple shows strong" in analysis["summary"]
        assert len(analysis["key_drivers"]) == 3
        assert len(analysis["risks"]) == 3
        assert len(analysis["catalysts"]) == 2
        assert "iPhone sales growth" in analysis["key_drivers"]
        assert "Supply chain disruptions" in analysis["risks"]
    
    @pytest.mark.asyncio
    async def test_synthesis_agent_recommendation_parsing(self):
        """Test synthesis agent recommendation parsing."""
        mock_response = """
        STANCE: BUY
        CONFIDENCE: HIGH
        RATIONALE: Strong fundamentals and positive outlook justify buy recommendation.
        """
        
        recommendation = self.synthesis_agent._parse_recommendation_response(mock_response)
        
        assert recommendation["stance"] == "buy"
        assert recommendation["confidence"] == "high"
        assert "Strong fundamentals" in recommendation["rationale"]


class TestTools:
    """Test cases for research tools."""
    
    def setup_method(self):
        """Set up test tools."""
        self.web_search_tool = WebSearchTool()
        self.stock_data_tool = StockDataTool()
        self.sec_edgar_tool = SECEdgarTool()
    
    def test_tool_initialization(self):
        """Test that tools are properly initialized."""
        assert self.web_search_tool.name == "web_search"
        assert self.stock_data_tool.name == "stock_data"
        assert self.sec_edgar_tool.name == "sec_edgar"
        
        assert "search" in self.web_search_tool.description.lower()
        assert "stock" in self.stock_data_tool.description.lower()
        assert "sec" in self.sec_edgar_tool.description.lower()
    
    @pytest.mark.asyncio
    async def test_web_search_tool_execution(self):
        """Test web search tool execution."""
        result = await self.web_search_tool.execute("AAPL earnings", "AAPL")
        
        assert "observation" in result
        assert "sources" in result
        assert "data" in result
        
        # Check that we get some simulated results
        assert len(result["sources"]) > 0
        assert "AAPL" in result["observation"]
    
    @pytest.mark.asyncio
    async def test_stock_data_tool_price_trend_analysis(self):
        """Test stock data tool price trend analysis."""
        # Test uptrend
        uptrend_prices = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118]
        trend = self.stock_data_tool._analyze_price_trend(uptrend_prices)
        assert "uptrend" in trend.lower()
        
        # Test downtrend
        downtrend_prices = [118, 116, 114, 112, 110, 108, 106, 104, 102, 100]
        trend = self.stock_data_tool._analyze_price_trend(downtrend_prices)
        assert "downtrend" in trend.lower()
        
        # Test insufficient data
        short_prices = [100]
        trend = self.stock_data_tool._analyze_price_trend(short_prices)
        assert "insufficient" in trend.lower()
    
    @pytest.mark.asyncio
    async def test_sec_edgar_tool_execution(self):
        """Test SEC EDGAR tool execution."""
        result = await self.sec_edgar_tool.execute("10-K filings", "AAPL")
        
        assert "observation" in result
        assert "sources" in result
        assert "data" in result
        
        # Check that we get simulated SEC filings
        assert "filings" in result["data"]
        assert len(result["data"]["filings"]) > 0
        assert "SEC" in result["observation"] or "filing" in result["observation"].lower()
    
    def test_tool_source_formatting(self):
        """Test tool source formatting."""
        raw_sources = [
            {
                "url": "https://example.com/article1",
                "title": "Test Article 1",
                "published_at": "2024-10-01",
                "snippet": "Test snippet 1"
            },
            {
                "url": "https://example.com/article2",
                "title": "Test Article 2",
                "snippet": "Test snippet 2"
                # Missing published_at
            }
        ]
        
        formatted = self.web_search_tool._format_sources(raw_sources)
        
        assert len(formatted) == 2
        assert formatted[0]["url"] == "https://example.com/article1"
        assert formatted[0]["title"] == "Test Article 1"
        assert formatted[1]["published_at"] is None  # Should handle missing fields


class TestIntegration:
    """Integration tests for agents and tools working together."""
    
    def setup_method(self):
        """Set up integration test environment."""
        self.mock_llm = Mock()
        self.mock_llm.ainvoke = AsyncMock()
        
        # Mock LLM responses
        self.mock_llm.ainvoke.return_value = Mock(
            content="I need to search for recent news about AAPL earnings."
        )
    
    @pytest.mark.asyncio
    async def test_agent_tool_integration(self):
        """Test that agents can successfully use their tools."""
        news_agent = NewsAgent(self.mock_llm)
        
        # Mock the tool execution
        with patch.object(news_agent.tools[0], 'execute') as mock_execute:
            mock_execute.return_value = {
                "observation": "Found recent earnings news for AAPL",
                "sources": [{"url": "https://example.com", "title": "AAPL Earnings"}],
                "data": {}
            }
            
            # Test the research method
            result = await news_agent.research("AAPL", "Analyze AAPL earnings", max_iterations=1)
            
            assert "trace" in result
            assert result["trace"].success is True
            assert len(result["trace"].steps) > 0
            assert "findings" in result
    
    @pytest.mark.asyncio
    async def test_synthesis_with_mock_data(self):
        """Test synthesis agent with mock agent results."""
        synthesis_agent = SynthesisAgent(self.mock_llm)
        
        # Mock LLM responses for analysis and recommendation
        analysis_response = Mock(content="""
        SUMMARY: Strong performance with good prospects.
        KEY_DRIVERS:
        - Revenue growth
        - Market expansion
        RISKS:
        - Competition
        CATALYSTS:
        - New products
        """)
        
        recommendation_response = Mock(content="""
        STANCE: BUY
        CONFIDENCE: HIGH
        RATIONALE: Strong fundamentals support buy recommendation.
        """)
        
        self.mock_llm.ainvoke.side_effect = [analysis_response, recommendation_response]
        
        # Mock agent results
        agent_results = {
            "news": {
                "findings": [{"observation": "Positive earnings news"}],
                "sources": [{"url": "https://example.com", "title": "News"}],
                "trace": Mock(success=True)
            },
            "price": {
                "findings": [{"observation": "Strong price momentum"}],
                "sources": [{"url": "https://finance.com", "title": "Price Data"}],
                "trace": Mock(success=True)
            }
        }
        
        # Test synthesis
        insight = await synthesis_agent.synthesize("AAPL", agent_results, "Analyze AAPL")
        
        assert insight.ticker == "AAPL"
        assert insight.stance == StanceType.BUY
        assert insight.confidence == ConfidenceLevel.HIGH
        assert "Strong performance" in insight.summary
        assert len(insight.key_drivers) > 0
        assert len(insight.risks) > 0


if __name__ == "__main__":
    pytest.main([__file__])
