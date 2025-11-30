"""
SEC EDGAR Tool - Searches and retrieves SEC filings and regulatory documents.
"""
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, Any, List
import structlog

from backend.tools.base_tool import BaseTool

logger = structlog.get_logger()


class SECEdgarTool(BaseTool):
    """Tool for searching SEC EDGAR database for regulatory filings."""
    
    def __init__(self):
        super().__init__(
            name="sec_edgar",
            description="Search SEC EDGAR database for regulatory filings like 10-K, 10-Q, 8-K reports"
        )
        self.base_url = "https://www.sec.gov/Archives/edgar"
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an HTTP session with proper headers for SEC.gov."""
        if self.session is None or self.session.closed:
            headers = {
                'User-Agent': 'Stock Research Chatbot (research@example.com)',
                'Accept': 'application/json, text/html',
                'Host': 'www.sec.gov'
            }
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=15),
                headers=headers
            )
        return self.session
    
    async def execute(self, query: str, ticker: str) -> Dict[str, Any]:
        """
        Execute SEC EDGAR search for the given ticker.
        
        Args:
            query: Search query (used to determine filing types)
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with SEC filing information and sources
        """
        logger.info("Searching SEC EDGAR", ticker=ticker, query=query)
        
        try:
            # For demo purposes, we'll simulate SEC EDGAR results
            # In a real implementation, you would:
            # 1. Use the SEC EDGAR API or RSS feeds
            # 2. Parse XBRL data for structured information
            # 3. Extract text from filing documents
            
            filings = await self._simulate_edgar_search(ticker, query)
            
            observation = self._create_observation(filings, ticker)
            sources = self._extract_sources(filings, ticker)
            
            return {
                "observation": observation,
                "sources": self._format_sources(sources),
                "data": {"filings": filings}
            }
            
        except Exception as e:
            logger.error("SEC EDGAR search failed", ticker=ticker, error=str(e))
            return {
                "observation": f"SEC EDGAR search failed for {ticker}: {str(e)}",
                "sources": [],
                "data": {}
            }
    
    async def _simulate_edgar_search(self, ticker: str, query: str) -> List[Dict[str, Any]]:
        """
        Simulate SEC EDGAR search results.
        In a real implementation, this would query the actual SEC EDGAR database.
        """
        # Simulate realistic SEC filings
        filings = [
            {
                "form_type": "10-Q",
                "filing_date": "2024-10-01",
                "period_end": "2024-09-30",
                "document_url": f"https://www.sec.gov/Archives/edgar/data/example/{ticker}-10Q-Q3-2024.htm",
                "description": f"{ticker} Quarterly Report (Form 10-Q) for Q3 2024",
                "key_highlights": [
                    "Revenue increased 15% year-over-year",
                    "Operating margin improved to 22%",
                    "Strong cash flow generation of $2.1B"
                ]
            },
            {
                "form_type": "8-K",
                "filing_date": "2024-09-15",
                "period_end": "2024-09-15",
                "document_url": f"https://www.sec.gov/Archives/edgar/data/example/{ticker}-8K-Sept-2024.htm",
                "description": f"{ticker} Current Report (Form 8-K) - Management Changes",
                "key_highlights": [
                    "Appointment of new Chief Technology Officer",
                    "Strategic partnership announcement",
                    "Updated forward guidance for Q4"
                ]
            },
            {
                "form_type": "10-K",
                "filing_date": "2024-03-15",
                "period_end": "2023-12-31",
                "document_url": f"https://www.sec.gov/Archives/edgar/data/example/{ticker}-10K-2023.htm",
                "description": f"{ticker} Annual Report (Form 10-K) for fiscal year 2023",
                "key_highlights": [
                    "Record annual revenue of $45.2B",
                    "Expanded international operations",
                    "Increased R&D investment by 25%"
                ]
            },
            {
                "form_type": "DEF 14A",
                "filing_date": "2024-04-01",
                "period_end": "2024-04-01",
                "document_url": f"https://www.sec.gov/Archives/edgar/data/example/{ticker}-DEF14A-2024.htm",
                "description": f"{ticker} Proxy Statement (DEF 14A) for 2024 Annual Meeting",
                "key_highlights": [
                    "Executive compensation details",
                    "Board of directors election",
                    "Shareholder proposals on sustainability"
                ]
            }
        ]
        
        # Add some delay to simulate network request
        await asyncio.sleep(0.3)
        
        return filings
    
    def _create_observation(self, filings: List[Dict[str, Any]], ticker: str) -> str:
        """Create a text observation from SEC filings."""
        if not filings:
            return f"No recent SEC filings found for {ticker}."
        
        observations = []
        observations.append(f"Found {len(filings)} recent SEC filings for {ticker}:")
        
        for filing in filings:
            form_type = filing.get("form_type", "Unknown")
            filing_date = filing.get("filing_date", "Unknown")
            description = filing.get("description", "")
            
            observations.append(f"- {form_type} filed on {filing_date}: {description}")
            
            # Add key highlights if available
            highlights = filing.get("key_highlights", [])
            if highlights:
                for highlight in highlights[:2]:  # Limit to top 2 highlights
                    observations.append(f"  • {highlight}")
        
        return "\n".join(observations)
    
    def _extract_sources(self, filings: List[Dict[str, Any]], ticker: str) -> List[Dict[str, Any]]:
        """Extract source information from SEC filings."""
        sources = []
        
        for filing in filings:
            source = {
                "url": filing.get("document_url", f"https://www.sec.gov/edgar/search/#/q={ticker}"),
                "title": filing.get("description", f"{ticker} SEC Filing"),
                "published_at": filing.get("filing_date"),
                "snippet": f"{filing.get('form_type', 'SEC Filing')} - {', '.join(filing.get('key_highlights', [])[:2])}"
            }
            sources.append(source)
        
        return sources
    
    async def close(self):
        """Close the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
