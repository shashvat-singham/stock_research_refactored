"""
News Research Agent - Specializes in gathering recent news and press releases.
"""
from typing import List
from langchain_core.language_models import BaseChatModel

from backend.agents.base_agent import BaseResearchAgent
from backend.tools.base_tool import BaseTool
from backend.tools.web_search_tool import WebSearchTool


class NewsAgent(BaseResearchAgent):
    """Agent specialized in gathering recent news and press releases about stocks."""
    
    def __init__(self, llm: BaseChatModel):
        super().__init__(llm, "news")
    
    def _initialize_tools(self) -> List[BaseTool]:
        """Initialize tools for news research."""
        return [
            WebSearchTool()
        ]
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the news agent."""
        return """
        You are a financial news research agent. Your role is to gather and analyze recent news, 
        press releases, and market developments related to specific stock tickers.
        
        Focus on:
        - Recent earnings announcements and guidance updates
        - Product launches and business developments
        - Management changes and strategic initiatives
        - Analyst ratings and price target changes
        - Market sentiment and investor reactions
        - Regulatory news and compliance issues
        - Partnership announcements and acquisitions
        - Industry trends affecting the company
        
        When researching, prioritize:
        1. Recency - Focus on news from the last 30 days
        2. Relevance - Ensure news directly impacts the company's business
        3. Credibility - Prefer established financial news sources
        4. Market Impact - Consider how news might affect stock price
        
        Always cite your sources with URLs and publication dates.
        Be objective and factual in your analysis.
        Look for both positive and negative developments to provide balanced coverage.
        """
    
    async def _act(self, thought: str, context: dict) -> tuple[str, str]:
        """
        Enhanced action selection for news research.
        """
        thought_lower = thought.lower()
        ticker = context['ticker']
        
        # Customize search queries based on the thought
        if "earnings" in thought_lower or "financial" in thought_lower:
            action_input = f"{ticker} earnings results financial performance Q3 2024"
        elif "analyst" in thought_lower or "rating" in thought_lower:
            action_input = f"{ticker} analyst rating upgrade downgrade price target"
        elif "product" in thought_lower or "launch" in thought_lower:
            action_input = f"{ticker} product launch new announcement innovation"
        elif "management" in thought_lower or "executive" in thought_lower:
            action_input = f"{ticker} management changes CEO executive leadership"
        elif "partnership" in thought_lower or "acquisition" in thought_lower:
            action_input = f"{ticker} partnership acquisition merger deal announcement"
        elif "regulatory" in thought_lower or "compliance" in thought_lower:
            action_input = f"{ticker} regulatory approval FDA SEC compliance news"
        else:
            # Default comprehensive news search
            action_input = f"{ticker} stock news recent developments 2024"
        
        return "web_search", action_input
