"""
Web Search Tool for gathering information from the web.
"""
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, Any, List
from urllib.parse import quote_plus
import structlog

from backend.tools.base_tool import BaseTool

logger = structlog.get_logger()


class WebSearchTool(BaseTool):
    """Tool for searching the web and extracting relevant information."""
    
    def __init__(self):
        super().__init__(
            name="web_search",
            description="Search the web for recent information about stocks, companies, and financial topics"
        )
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an HTTP session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10),
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            )
        return self.session
    
    async def execute(self, query: str, ticker: str) -> Dict[str, Any]:
        """
        Execute web search for the given query and ticker.
        
        Args:
            query: Search query
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with search results and sources
        """
        logger.info("Executing web search", query=query, ticker=ticker)
        
        try:
            # For demo purposes, we'll simulate web search results
            # In a real implementation, you would integrate with search APIs like:
            # - Google Custom Search API
            # - Bing Search API
            # - DuckDuckGo API
            # - Or scrape search results (respecting robots.txt)
            
            search_results = await self._simulate_search(query, ticker)
            
            # Extract key information
            observation = self._create_observation(search_results, ticker)
            sources = self._extract_sources(search_results)
            
            return {
                "observation": observation,
                "sources": self._format_sources(sources),
                "data": search_results
            }
            
        except Exception as e:
            logger.error("Web search failed", query=query, ticker=ticker, error=str(e))
            return {
                "observation": f"Web search failed: {str(e)}",
                "sources": [],
                "data": {}
            }
    
    async def _simulate_search(self, query: str, ticker: str) -> List[Dict[str, Any]]:
        """
        Simulate web search results.
        In a real implementation, this would call actual search APIs.
        """
        # Simulate some realistic search results
        results = [
            {
                "title": f"{ticker} Reports Strong Q3 Earnings, Beats Expectations",
                "url": f"https://finance.yahoo.com/{ticker.lower()}-earnings-q3-2024",
                "snippet": f"{ticker} reported quarterly earnings that exceeded analyst expectations, driven by strong revenue growth and improved margins. The company raised its full-year guidance.",
                "published_at": "2024-10-08T10:30:00Z",
                "source": "Yahoo Finance"
            },
            {
                "title": f"Analyst Upgrades {ticker} to Buy Rating",
                "url": f"https://www.marketwatch.com/{ticker.lower()}-analyst-upgrade",
                "snippet": f"Leading investment firm upgrades {ticker} to Buy rating with a price target of $150, citing strong fundamentals and market position.",
                "published_at": "2024-10-07T14:15:00Z",
                "source": "MarketWatch"
            },
            {
                "title": f"{ticker} Announces New Product Launch",
                "url": f"https://www.reuters.com/{ticker.lower()}-product-launch",
                "snippet": f"{ticker} unveiled its latest product innovation, expected to drive significant revenue growth in the coming quarters.",
                "published_at": "2024-10-06T09:00:00Z",
                "source": "Reuters"
            },
            {
                "title": f"Insider Trading Activity at {ticker}",
                "url": f"https://www.sec.gov/edgar/{ticker.lower()}-insider-trading",
                "snippet": f"Recent SEC filings show increased insider buying activity at {ticker}, with executives purchasing shares in the open market.",
                "published_at": "2024-10-05T16:45:00Z",
                "source": "SEC EDGAR"
            }
        ]
        
        # Add some delay to simulate network request
        await asyncio.sleep(0.5)
        
        return results
    
    def _create_observation(self, search_results: List[Dict[str, Any]], ticker: str) -> str:
        """Create a text observation from search results."""
        if not search_results:
            return f"No recent web search results found for {ticker}."
        
        observations = []
        observations.append(f"Found {len(search_results)} recent articles about {ticker}:")
        
        for i, result in enumerate(search_results[:3], 1):  # Limit to top 3 results
            observations.append(f"{i}. {result['title']} - {result['snippet'][:100]}...")
        
        return "\n".join(observations)
    
    def _extract_sources(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract source information from search results."""
        sources = []
        
        for result in search_results:
            source = {
                "url": result.get("url", ""),
                "title": result.get("title", ""),
                "published_at": result.get("published_at"),
                "snippet": result.get("snippet", "")
            }
            sources.append(source)
        
        return sources
    
    async def close(self):
        """Close the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
