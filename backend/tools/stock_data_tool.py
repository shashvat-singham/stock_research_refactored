"""
Stock Data Tool - Integrates with Yahoo Finance API for real stock data.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import structlog
import requests

# Assuming a base URL for Yahoo Finance API, this might need to be configured
# or dynamically discovered. For now, we'll use a placeholder.
YAHOO_FINANCE_BASE_URL = "https://query1.finance.yahoo.com/v8/finance/"

from backend.tools.base_tool import BaseTool

logger = structlog.get_logger()


class StockDataTool(BaseTool):
    """Tool for fetching real stock market data and insights."""
    
    def __init__(self):
        super().__init__(
            name="stock_data",
            description="Fetch real-time stock data, charts, and financial insights from Yahoo Finance"
        )

    
    async def execute(self, query: str, ticker: str) -> Dict[str, Any]:
        """
        Execute stock data retrieval for the given ticker.
        
        Args:
            query: Search query (not used directly, but provides context)
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with stock data and sources
        """
        logger.info("Fetching stock data", ticker=ticker, query=query)
        
        try:
            # Fetch both chart data and insights
            chart_data = await self._get_stock_chart(ticker)
            insights_data = await self._get_stock_insights(ticker)
            
            # Combine and analyze the data
            observation = self._create_observation(chart_data, insights_data, ticker)
            sources = self._extract_sources(chart_data, insights_data, ticker)
            
            return {
                "observation": observation,
                "sources": self._format_sources(sources),
                "data": {
                    "chart": chart_data,
                    "insights": insights_data
                }
            }
            
        except Exception as e:
            logger.error("Stock data fetch failed", ticker=ticker, error=str(e))
            return {
                "observation": f"Failed to fetch stock data for {ticker}: {str(e)}",
                "sources": [],
                "data": {}
            }
    
    async def _get_stock_chart(self, ticker: str) -> Dict[str, Any]:
        """Fetch stock chart data."""
        try:
            # Run in thread pool to avoid blocking
            params = {
                "symbol": ticker,
                "region": "US",
                "interval": "1d",
                "range": "3mo",  # 3 months of data
                "includeAdjustedClose": True,
                "events": "div,split"
            }
            response = requests.get(f"{YAHOO_FINANCE_BASE_URL}chart/{ticker}", params=params)
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response.json() or {}
        except Exception as e:
            logger.error("Chart data fetch failed", ticker=ticker, error=str(e))
            return {}
    
    async def _get_stock_insights(self, ticker: str) -> Dict[str, Any]:
        """Fetch stock insights data."""
        try:
            # Run in thread pool to avoid blocking
            params = {
                "symbol": ticker
            }
            response = requests.get(f"{YAHOO_FINANCE_BASE_URL}insights/{ticker}", params=params)
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response.json() or {}
        except Exception as e:
            logger.error("Insights data fetch failed", ticker=ticker, error=str(e))
            return {}
    
    def _create_observation(
        self, 
        chart_data: Dict[str, Any], 
        insights_data: Dict[str, Any], 
        ticker: str
    ) -> str:
        """Create a text observation from the stock data."""
        observations = []
        
        # Basic stock information
        if chart_data and 'chart' in chart_data and 'result' in chart_data['chart']:
            result = chart_data['chart']['result'][0]
            meta = result.get('meta', {})
            
            company_name = meta.get('longName', ticker)
            current_price = meta.get('regularMarketPrice', 0)
            day_change = meta.get('regularMarketChange', 0)
            day_change_pct = meta.get('regularMarketChangePercent', 0)
            volume = meta.get('regularMarketVolume', 0)
            
            observations.append(
                f"{company_name} ({ticker}) is trading at ${current_price:.2f}, "
                f"{'up' if day_change >= 0 else 'down'} ${abs(day_change):.2f} "
                f"({day_change_pct:.2f}%) with volume of {volume:,} shares."
            )
            
            # 52-week range
            week_52_high = meta.get('fiftyTwoWeekHigh', 0)
            week_52_low = meta.get('fiftyTwoWeekLow', 0)
            if week_52_high and week_52_low:
                observations.append(
                    f"52-week range: ${week_52_low:.2f} - ${week_52_high:.2f}. "
                    f"Current price is {((current_price - week_52_low) / (week_52_high - week_52_low) * 100):.1f}% "
                    f"of the 52-week range."
                )
            
            # Recent price trend
            timestamps = result.get('timestamp', [])
            quotes = result.get('indicators', {}).get('quote', [{}])[0]
            
            if timestamps and quotes.get('close'):
                closes = [c for c in quotes['close'] if c is not None]
                if len(closes) >= 20:  # At least 20 trading days
                    recent_trend = self._analyze_price_trend(closes[-20:])
                    observations.append(f"20-day price trend: {recent_trend}")
        
        # Insights data
        if insights_data and 'insights' in insights_data:
            insights = insights_data['insights']
            
            # Technical indicators
            if 'technicalInsights' in insights:
                tech_insights = insights['technicalInsights']
                if 'shortTermOutlook' in tech_insights:
                    short_term = tech_insights['shortTermOutlook']
                    observations.append(f"Short-term technical outlook: {short_term}")
                
                if 'intermediateTermOutlook' in tech_insights:
                    intermediate_term = tech_insights['intermediateTermOutlook']
                    observations.append(f"Intermediate-term technical outlook: {intermediate_term}")
            
            # Company insights
            if 'companyInsights' in insights:
                company_insights = insights['companyInsights']
                if 'innovativeness' in company_insights:
                    innovation = company_insights['innovativeness']
                    observations.append(f"Innovation score: {innovation}")
                
                if 'sustainability' in company_insights:
                    sustainability = company_insights['sustainability']
                    observations.append(f"Sustainability score: {sustainability}")
            
            # Valuation insights
            if 'valuation' in insights:
                valuation = insights['valuation']
                if 'description' in valuation:
                    observations.append(f"Valuation: {valuation['description']}")
        
        if not observations:
            return f"Limited data available for {ticker}. Unable to provide comprehensive analysis."
        
        return " ".join(observations)
    
    def _analyze_price_trend(self, prices: List[float]) -> str:
        """Analyze price trend from a list of closing prices."""
        if len(prices) < 2:
            return "insufficient data"
        
        # Calculate simple moving averages
        sma_5 = sum(prices[-5:]) / 5 if len(prices) >= 5 else prices[-1]
        sma_10 = sum(prices[-10:]) / 10 if len(prices) >= 10 else sum(prices) / len(prices)
        sma_20 = sum(prices) / len(prices)
        
        current_price = prices[-1]
        
        # Determine trend
        if current_price > sma_5 > sma_10 > sma_20:
            return "strong uptrend"
        elif current_price > sma_5 > sma_10:
            return "uptrend"
        elif current_price < sma_5 < sma_10 < sma_20:
            return "strong downtrend"
        elif current_price < sma_5 < sma_10:
            return "downtrend"
        else:
            return "sideways/consolidating"
    
    def _extract_sources(
        self, 
        chart_data: Dict[str, Any], 
        insights_data: Dict[str, Any], 
        ticker: str
    ) -> List[Dict[str, Any]]:
        """Extract source information from the stock data."""
        sources = []
        
        # Yahoo Finance as primary source
        sources.append({
            "url": f"https://finance.yahoo.com/quote/{ticker}",
            "title": f"{ticker} Stock Quote - Yahoo Finance",
            "published_at": datetime.now().isoformat(),
            "snippet": f"Real-time stock data and financial information for {ticker}"
        })
        
        # Add chart data source
        if chart_data:
            sources.append({
                "url": f"https://finance.yahoo.com/quote/{ticker}/chart",
                "title": f"{ticker} Interactive Chart - Yahoo Finance",
                "published_at": datetime.now().isoformat(),
                "snippet": f"Interactive price chart and technical analysis for {ticker}"
            })
        
        # Add insights source
        if insights_data:
            sources.append({
                "url": f"https://finance.yahoo.com/quote/{ticker}/analysis",
                "title": f"{ticker} Analysis & Insights - Yahoo Finance",
                "published_at": datetime.now().isoformat(),
                "snippet": f"Financial analysis and insights for {ticker}"
            })
        
        return sources
