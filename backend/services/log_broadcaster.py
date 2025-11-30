"""
Log broadcaster service for streaming real-time logs via WebSocket.
Enhanced with professional, user-facing messages.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
import asyncio
import structlog

logger = structlog.get_logger()


class LogEventType(str, Enum):
    """Types of log events that can be broadcast."""
    AGENT_START = "agent_start"
    AGENT_PROGRESS = "agent_progress"
    AGENT_COMPLETE = "agent_complete"
    TOOL_CALL = "tool_call"
    SEARCH_QUERY = "search_query"
    DATA_FETCH = "data_fetch"
    ANALYSIS = "analysis"
    ERROR = "error"
    INFO = "info"
    THINKING = "thinking"
    SUCCESS = "success"
    WARNING = "warning"


class LogBroadcaster:
    """
    Service for broadcasting log events to WebSocket clients.
    Provides professional, user-facing messages for real-time updates.
    """
    
    def __init__(self, request_id: str, connection_manager=None):
        """
        Initialize the log broadcaster.
        
        Args:
            request_id: The request ID to broadcast logs for
            connection_manager: The WebSocket connection manager instance
        """
        self.request_id = request_id
        self.connection_manager = connection_manager
        self._enabled = connection_manager is not None
    
    async def emit(
        self,
        event_type: LogEventType,
        message: str,
        agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        delay: float = 0.0
    ):
        """
        Emit a log event to all connected clients.
        
        Args:
            event_type: The type of log event
            message: Human-readable message
            agent: The agent name (if applicable)
            details: Additional details about the event
            delay: Optional delay after emitting (for readability)
        """
        if not self._enabled:
            return
        
        log_event = {
            "type": event_type.value,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "message": message,
        }
        
        if agent:
            log_event["agent"] = agent
        
        if details:
            log_event["details"] = details
        
        try:
            await self.connection_manager.broadcast(self.request_id, log_event)
            logger.debug("Log event emitted", 
                        request_id=self.request_id,
                        event_type=event_type.value)
        except Exception as e:
            logger.error("Failed to emit log event", 
                        request_id=self.request_id,
                        error=str(e))
        
        if delay > 0:
            await asyncio.sleep(delay)
    
    # ========== User-Facing Progress Messages ==========
    
    async def query_received(self, query: str):
        """User submitted a query."""
        await self.emit(
            LogEventType.INFO,
            f"📝 Analyzing your query: \"{query}\"",
            details={"query": query},
            delay=0.5
        )
    
    async def extracting_tickers(self):
        """Extracting company names and tickers from query."""
        await self.emit(
            LogEventType.THINKING,
            "🔍 Identifying companies and stock tickers from your query...",
            delay=0.8
        )
    
    async def tickers_found(self, tickers: list, company_names: dict = None):
        """Successfully identified tickers."""
        if company_names:
            ticker_list = ", ".join([f"{company_names.get(t, t)} ({t})" for t in tickers])
        else:
            ticker_list = ", ".join(tickers)
        
        await self.emit(
            LogEventType.SUCCESS,
            f"✅ Found {len(tickers)} stock(s): {ticker_list}",
            details={"tickers": tickers, "company_names": company_names},
            delay=0.6
        )
    
    async def checking_typos(self):
        """Checking for potential typos in company names."""
        await self.emit(
            LogEventType.THINKING,
            "🤖 Checking for potential typos in company names...",
            agent="smart_correction",
            delay=1.0
        )
    
    async def typos_detected(self, corrections_count: int):
        """Detected potential typos."""
        await self.emit(
            LogEventType.WARNING,
            f"⚠️  Detected {corrections_count} potential typo(s) - requesting confirmation",
            details={"corrections_count": corrections_count},
            delay=0.5
        )
    
    async def starting_analysis(self, tickers: list):
        """Starting comprehensive analysis."""
        ticker_str = ", ".join(tickers)
        await self.emit(
            LogEventType.INFO,
            f"🚀 Starting comprehensive analysis for {len(tickers)} stock(s): {ticker_str}",
            details={"tickers": tickers},
            delay=0.8
        )
    
    async def fetching_company_info(self, ticker: str, company_name: str = None):
        """Fetching basic company information."""
        display_name = company_name or ticker
        await self.emit(
            LogEventType.DATA_FETCH,
            f"📊 Gathering company information for {display_name}...",
            details={"ticker": ticker, "company_name": company_name},
            delay=0.6
        )
    
    async def fetching_news(self, ticker: str, company_name: str = None):
        """Fetching latest news articles."""
        display_name = company_name or ticker
        await self.emit(
            LogEventType.AGENT_START,
            f"📰 Searching for latest news about {display_name}...",
            agent="news",
            details={"ticker": ticker},
            delay=0.7
        )
    
    async def news_found(self, ticker: str, count: int):
        """Found news articles."""
        await self.emit(
            LogEventType.AGENT_COMPLETE,
            f"✓ Found {count} recent news article(s) for {ticker}",
            agent="news",
            details={"ticker": ticker, "articles_count": count},
            delay=0.5
        )
    
    async def analyzing_news_sentiment(self, ticker: str):
        """Analyzing news sentiment."""
        await self.emit(
            LogEventType.THINKING,
            f"🧠 Analyzing news sentiment and market perception for {ticker}...",
            agent="news",
            delay=1.0
        )
    
    async def fetching_price_data(self, ticker: str, company_name: str = None):
        """Fetching price history and technical data."""
        display_name = company_name or ticker
        await self.emit(
            LogEventType.AGENT_START,
            f"📈 Analyzing price trends and technical indicators for {display_name}...",
            agent="price",
            details={"ticker": ticker},
            delay=0.7
        )
    
    async def analyzing_technicals(self, ticker: str):
        """Analyzing technical indicators."""
        await self.emit(
            LogEventType.THINKING,
            f"📊 Calculating support/resistance levels and trend analysis for {ticker}...",
            agent="price",
            delay=1.0
        )
    
    async def price_analysis_complete(self, ticker: str, trend: str):
        """Price analysis completed."""
        trend_emoji = {"bullish": "📈", "bearish": "📉", "neutral": "➡️"}.get(trend.lower(), "➡️")
        await self.emit(
            LogEventType.AGENT_COMPLETE,
            f"✓ Price analysis complete - Trend: {trend_emoji} {trend.capitalize()}",
            agent="price",
            details={"ticker": ticker, "trend": trend},
            delay=0.5
        )
    
    async def fetching_financials(self, ticker: str):
        """Fetching financial metrics."""
        await self.emit(
            LogEventType.DATA_FETCH,
            f"💰 Gathering financial metrics and valuation data for {ticker}...",
            details={"ticker": ticker, "data_type": "financials"},
            delay=0.6
        )
    
    async def synthesizing_analysis(self, ticker: str):
        """Synthesizing all data into investment recommendation."""
        await self.emit(
            LogEventType.AGENT_START,
            f"🔬 Synthesizing all data to generate investment recommendation for {ticker}...",
            agent="synthesis",
            details={"ticker": ticker},
            delay=0.8
        )
    
    async def generating_recommendation(self, ticker: str):
        """Generating final recommendation."""
        await self.emit(
            LogEventType.THINKING,
            f"💡 Evaluating investment opportunities, risks, and catalysts for {ticker}...",
            agent="synthesis",
            delay=1.2
        )
    
    async def recommendation_complete(self, ticker: str, stance: str, confidence: str):
        """Investment recommendation generated."""
        stance_emoji = {"buy": "🟢", "sell": "🔴", "hold": "🟡"}.get(stance.lower(), "🟡")
        await self.emit(
            LogEventType.AGENT_COMPLETE,
            f"✓ Recommendation generated: {stance_emoji} {stance.upper()} ({confidence} confidence)",
            agent="synthesis",
            details={"ticker": ticker, "stance": stance, "confidence": confidence},
            delay=0.6
        )
    
    async def ticker_analysis_complete(self, ticker: str, company_name: str = None):
        """Completed analysis for a ticker."""
        display_name = company_name or ticker
        await self.emit(
            LogEventType.SUCCESS,
            f"✅ Completed comprehensive analysis for {display_name}",
            details={"ticker": ticker, "company_name": company_name},
            delay=0.5
        )
    
    async def all_analysis_complete(self, tickers_count: int):
        """All tickers analyzed successfully."""
        await self.emit(
            LogEventType.SUCCESS,
            f"🎉 Analysis complete! Generated investment insights for {tickers_count} stock(s)",
            details={"tickers_count": tickers_count},
            delay=0.5
        )
    
    # ========== Error and Warning Messages ==========
    
    async def error(self, message: str, error_details: Optional[Dict[str, Any]] = None):
        """Emit an error event."""
        await self.emit(
            LogEventType.ERROR,
            f"❌ {message}",
            details=error_details,
            delay=0.5
        )
    
    async def warning(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Emit a warning event."""
        await self.emit(
            LogEventType.WARNING,
            f"⚠️  {message}",
            details=details,
            delay=0.5
        )
    
    # ========== Legacy Methods (for backward compatibility) ==========
    
    async def agent_start(self, agent: str, ticker: str, message: str, delay: float = 0.7):
        """Emit an agent start event."""
        await self.emit(
            LogEventType.AGENT_START,
            message,
            agent=agent,
            details={"ticker": ticker},
            delay=delay
        )
    
    async def agent_progress(self, agent: str, ticker: str, message: str, progress: int, delay: float = 0.6):
        """Emit an agent progress event."""
        await self.emit(
            LogEventType.AGENT_PROGRESS,
            message,
            agent=agent,
            details={"ticker": ticker, "progress": progress},
            delay=delay
        )
    
    async def agent_complete(self, agent: str, ticker: str, message: str, delay: float = 0.5):
        """Emit an agent complete event."""
        await self.emit(
            LogEventType.AGENT_COMPLETE,
            message,
            agent=agent,
            details={"ticker": ticker},
            delay=delay
        )
    
    async def tool_call(self, tool: str, message: str, details: Optional[Dict[str, Any]] = None):
        """Emit a tool call event."""
        await self.emit(
            LogEventType.TOOL_CALL,
            message,
            details={**(details or {}), "tool": tool}
        )
    
    async def search_query(self, query: str, source: str):
        """Emit a search query event."""
        await self.emit(
            LogEventType.SEARCH_QUERY,
            f"🔎 Searching: {query}",
            details={"query": query, "source": source},
            delay=0.5
        )
    
    async def data_fetch(self, ticker: str, data_type: str, message: str, delay: float = 0.6):
        """Emit a data fetch event."""
        await self.emit(
            LogEventType.DATA_FETCH,
            message,
            details={"ticker": ticker, "data_type": data_type},
            delay=delay
        )
    
    async def analysis(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Emit an analysis event."""
        await self.emit(
            LogEventType.ANALYSIS,
            message,
            details=details,
            delay=0.5
        )
    
    async def info(self, message: str, details: Optional[Dict[str, Any]] = None, delay: float = 0.5):
        """Emit an info event."""
        await self.emit(
            LogEventType.INFO,
            message,
            details=details,
            delay=delay
        )
    
    async def thinking(self, message: str, agent: Optional[str] = None, delay: float = 1.0):
        """Emit a thinking event (like Perplexity's 'Thinking...' status)."""
        await self.emit(
            LogEventType.THINKING,
            message,
            agent=agent,
            delay=delay
        )


def create_log_broadcaster(request_id: str, connection_manager=None) -> LogBroadcaster:
    """
    Factory function to create a LogBroadcaster instance.
    
    Args:
        request_id: The request ID to broadcast logs for
        connection_manager: The WebSocket connection manager instance
    
    Returns:
        A configured LogBroadcaster instance
    """
    return LogBroadcaster(request_id, connection_manager)
