"""
Orchestrator - Real-time stock analysis using Yahoo Finance and Gemini AI with LangGraph.
Enhanced with professional user-facing streaming logs.
"""
import asyncio
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, TypedDict
import structlog

from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph

from backend.app.models import (
    TickerInsight, 
    AgentTrace, 
    AgentStep, 
    SourceInfo,
    StanceType,
    ConfidenceLevel
)
from backend.config.settings import get_settings
from backend.tools.yahoo_finance_tool import YahooFinanceTool
from backend.services.gemini_service import GeminiService
from backend.services.ticker_mapper import get_ticker_mapper
from backend.utils.formatters import format_ticker_insight

logger = structlog.get_logger()


class OrchestratorState(TypedDict):
    """State for the orchestrator workflow."""
    query: str
    tickers: List[str]
    unresolved_names: List[str]
    confirmed_tickers: Optional[List[str]]
    max_iterations: int
    timeout_seconds: int
    request_id: str
    log_broadcaster: Any
    
    # Results
    insights: List[TickerInsight]
    errors: List[str]
    
    # Tracking
    start_time: float
    current_ticker: str
    current_ticker_data: Dict[str, Any]


class Orchestrator:
    """
    Orchestrator that uses Yahoo Finance for real-time data and Gemini for analysis.
    Provides professional streaming logs for user-facing progress updates.
    Uses LangGraph for workflow management.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.yahoo_tool = YahooFinanceTool()
        self.gemini_service = GeminiService()
        self.ticker_mapper = get_ticker_mapper()
        self.workflow = self._build_workflow()
    
    def _extract_tickers(self, query: str) -> tuple[List[str], List[str]]:
        """Extract stock tickers from the query using ticker mapper.
        
        Returns:
            Tuple of (resolved_tickers, unresolved_names)
        """
        return self.ticker_mapper.extract_tickers_from_query(query)
    
    def _build_workflow(self) -> CompiledStateGraph:
        """Build the LangGraph workflow for stock analysis."""
        
        async def extract_tickers_node(state: OrchestratorState) -> OrchestratorState:
            """Extract tickers from query or use confirmed tickers."""
            logger.info("Extracting tickers", query=state["query"])
            
            if state.get("confirmed_tickers"):
                state["tickers"] = list(set(state["confirmed_tickers"]))  # Deduplicate
                state["unresolved_names"] = []
                logger.info("Using confirmed tickers", tickers=state["tickers"])
            else:
                tickers, unresolved = self._extract_tickers(state["query"])
                state["tickers"] = list(set(tickers))  # Deduplicate
                state["unresolved_names"] = unresolved
                
                if not tickers and unresolved:
                    error_msg = f"Could not resolve company names: {', '.join(unresolved)}. Please provide valid stock tickers or full company names."
                    state["errors"].append(error_msg)
                    logger.error("Could not resolve tickers", unresolved=unresolved)
                
                if not tickers:
                    error_msg = "No valid stock tickers found in query. Please include stock ticker symbols (e.g., AAPL, MSFT, GOOGL) or company names (e.g., Apple, Microsoft)."
                    state["errors"].append(error_msg)
                    logger.error("No tickers found", query=state["query"])
            
            # Emit log for starting analysis
            if state.get("log_broadcaster"):
                await state["log_broadcaster"].starting_analysis(state["tickers"])
            
            return state
        
        async def analyze_ticker_node(state: OrchestratorState) -> OrchestratorState:
            """Analyze a single ticker - this will be called for each ticker."""
            ticker = state["current_ticker"]
            logger.info(f"Starting analysis for {ticker}")
            
            agent_traces = []
            sources = []
            
            # Step 1: Fetch stock info
            if state.get("log_broadcaster"):
                await state["log_broadcaster"].fetching_company_info(ticker)
            
            stock_info = self.yahoo_tool.get_stock_info(ticker)
            company_name = stock_info.get('company_name', ticker)
            
            if 'error' in stock_info:
                logger.error(f"Failed to fetch stock info for {ticker}", error=stock_info['error'])
                if state.get("log_broadcaster"):
                    await state["log_broadcaster"].error(
                        f"Unable to fetch data for {ticker}. Please verify the ticker symbol.",
                        error_details={"ticker": ticker, "error": stock_info['error']}
                    )
                # Create minimal insight with error
                error_insight = TickerInsight(
                    ticker=ticker,
                    company_name=ticker,
                    stance=StanceType.HOLD,
                    confidence=ConfidenceLevel.LOW,
                    summary=f"Unable to fetch data for {ticker}. Please verify the ticker symbol.",
                    rationale="Data unavailable",
                    key_drivers=["Data unavailable"],
                    risks=["Unable to analyze due to data fetch error"],
                    catalysts=["N/A"],
                    sources=[],
                    agent_traces=[]
                )
                state["insights"].append(error_insight)
                return state
            
            # Step 2: Fetch news (News Agent simulation)
            if state.get("log_broadcaster"):
                await state["log_broadcaster"].fetching_news(ticker, company_name)
            
            news_step_start = time.time()
            news_articles = self.yahoo_tool.get_news(ticker, limit=10)
            news_latency = (time.time() - news_step_start) * 1000
            
            if state.get("log_broadcaster"):
                await state["log_broadcaster"].news_found(ticker, len(news_articles))
            
            # Convert news to sources
            for article in news_articles[:5]:
                sources.append(SourceInfo(
                    url=article['url'],
                    title=article['title'],
                    published_at=article['published_at'],
                    snippet=article['snippet']
                ))
            
            # Summarize news using Gemini
            if state.get("log_broadcaster"):
                await state["log_broadcaster"].analyzing_news_sentiment(ticker)
            
            news_summary = self.gemini_service.summarize_news(ticker, news_articles)
            
            # Create News Agent trace
            news_trace = AgentTrace(
                agent_type="news",
                ticker=ticker,
                steps=[
                    AgentStep(
                        step_number=1,
                        thought=f"I need to gather recent news about {ticker} to understand current market sentiment and developments.",
                        action=f"yahoo_finance_news: {ticker}",
                        observation=f"Found {len(news_articles)} recent news articles. {news_summary['summary']}",
                        sources=sources[:3],
                        latency_ms=news_latency
                    )
                ],
                success=True,
                total_latency_ms=news_latency
            )
            agent_traces.append(news_trace)
            
            # Step 3: Fetch price data (Price Agent simulation)
            if state.get("log_broadcaster"):
                await state["log_broadcaster"].fetching_price_data(ticker, company_name)
            
            price_step_start = time.time()
            price_data = self.yahoo_tool.get_price_history(ticker, period="1mo")
            price_latency = (time.time() - price_step_start) * 1000
            
            # Analyze technical levels using Gemini
            if state.get("log_broadcaster"):
                await state["log_broadcaster"].analyzing_technicals(ticker)
            
            technical_analysis = self.gemini_service.analyze_support_resistance(ticker, price_data)
            
            if state.get("log_broadcaster"):
                await state["log_broadcaster"].price_analysis_complete(
                    ticker, 
                    price_data.get('trend', 'neutral')
                )
            
            # Create Price Agent trace
            price_trace = AgentTrace(
                agent_type="price",
                ticker=ticker,
                steps=[
                    AgentStep(
                        step_number=1,
                        thought=f"I should analyze the recent price movement and technical indicators for {ticker}.",
                        action=f"yahoo_finance_price: {ticker}",
                        observation=f"Current price: ${price_data.get('current_price', 0):.2f}. Trend: {price_data.get('trend', 'neutral')}. {technical_analysis.get('technical_summary', '')}",
                        sources=[],
                        latency_ms=price_latency
                    )
                ],
                success=True,
                total_latency_ms=price_latency
            )
            agent_traces.append(price_trace)
            
            # Step 4: Fetch financial metrics
            if state.get("log_broadcaster"):
                await state["log_broadcaster"].fetching_financials(ticker)
            
            financial_metrics = self.yahoo_tool.get_financial_metrics(ticker)
            
            # Step 5: Generate investment analysis using Gemini (Synthesis Agent)
            if state.get("log_broadcaster"):
                await state["log_broadcaster"].synthesizing_analysis(ticker)
            
            synthesis_start = time.time()
            
            if state.get("log_broadcaster"):
                await state["log_broadcaster"].generating_recommendation(ticker)
            
            investment_analysis = self.gemini_service.generate_investment_analysis(
                ticker=ticker,
                company_name=company_name,
                news_summary=news_summary,
                price_data=price_data,
                financial_metrics=financial_metrics
            )
            synthesis_latency = (time.time() - synthesis_start) * 1000
            
            if state.get("log_broadcaster"):
                await state["log_broadcaster"].recommendation_complete(
                    ticker,
                    investment_analysis['stance'],
                    investment_analysis['confidence']
                )
            
            # Create Synthesis Agent trace
            synthesis_trace = AgentTrace(
                agent_type="synthesis",
                ticker=ticker,
                steps=[
                    AgentStep(
                        step_number=1,
                        thought=f"I need to synthesize all gathered information to provide a comprehensive investment recommendation for {ticker}.",
                        action=f"gemini_analysis: Synthesize news, price, and financial data",
                        observation=f"Generated investment stance: {investment_analysis['stance']} with {investment_analysis['confidence']} confidence.",
                        sources=[],
                        latency_ms=synthesis_latency
                    )
                ],
                success=True,
                total_latency_ms=synthesis_latency
            )
            agent_traces.append(synthesis_trace)
            
            # Map stance string to enum
            stance_map = {
                'buy': StanceType.BUY,
                'sell': StanceType.SELL,
                'hold': StanceType.HOLD
            }
            stance = stance_map.get(investment_analysis['stance'].lower(), StanceType.HOLD)
            
            # Map confidence string to enum
            confidence_map = {
                'high': ConfidenceLevel.HIGH,
                'medium': ConfidenceLevel.MEDIUM,
                'low': ConfidenceLevel.LOW
            }
            confidence = confidence_map.get(investment_analysis['confidence'].lower(), ConfidenceLevel.MEDIUM)
            
            # Create comprehensive summary
            summary = f"{news_summary['summary']} {investment_analysis['confidence_rationale']}"
            
            # Create TickerInsight with all data
            insight = TickerInsight(
                ticker=ticker,
                company_name=company_name,
                current_price=stock_info.get('current_price'),
                market_cap=stock_info.get('market_cap'),
                pe_ratio=stock_info.get('pe_ratio'),
                fifty_two_week_high=stock_info.get('fifty_two_week_high'),
                fifty_two_week_low=stock_info.get('fifty_two_week_low'),
                support_levels=technical_analysis.get('support_levels', []),
                resistance_levels=technical_analysis.get('resistance_levels', []),
                trend=price_data.get('trend'),
                stance=stance,
                confidence=confidence,
                summary=summary,
                rationale=investment_analysis['rationale'],
                key_drivers=investment_analysis['key_drivers'],
                risks=investment_analysis['risks'],
                catalysts=investment_analysis['catalysts'],
                sources=sources,
                agent_traces=agent_traces
            )
            
            logger.info(f"Completed analysis for {ticker}", stance=stance.value, confidence=confidence.value)
            
            # Emit completion log
            if state.get("log_broadcaster"):
                await state["log_broadcaster"].ticker_analysis_complete(ticker, company_name)
            
            # Format insight with 2 decimal places
            formatted_insight = format_ticker_insight(insight.model_dump())
            state["insights"].append(TickerInsight(**formatted_insight))
            
            return state
        
        async def process_all_tickers(state: OrchestratorState) -> OrchestratorState:
            """Process all tickers in parallel."""
            if state.get("errors"):
                # Skip processing if there are errors
                return state
            
            # Clear insights to avoid duplicates
            state["insights"] = []
            
            # Analyze each ticker in parallel
            tasks = []
            for ticker in state["tickers"]:
                # Create a deep copy for each ticker to avoid shared state
                ticker_state = {
                    "query": state["query"],
                    "tickers": state["tickers"],
                    "unresolved_names": state["unresolved_names"],
                    "confirmed_tickers": state.get("confirmed_tickers"),
                    "max_iterations": state["max_iterations"],
                    "timeout_seconds": state["timeout_seconds"],
                    "request_id": state["request_id"],
                    "log_broadcaster": state.get("log_broadcaster"),
                    "insights": [],  # Each ticker gets its own insights list
                    "errors": [],
                    "start_time": state["start_time"],
                    "current_ticker": ticker,
                    "current_ticker_data": {}
                }
                tasks.append(analyze_ticker_node(ticker_state))
            
            # Wait for all analyses to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect insights from all results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    ticker = state["tickers"][i]
                    logger.error(f"Error analyzing ticker {ticker}", error=str(result))
                    if state.get("log_broadcaster"):
                        await state["log_broadcaster"].error(
                            f"Failed to analyze {ticker}: {str(result)}",
                            error_details={"ticker": ticker, "error": str(result)}
                        )
                    state["errors"].append(f"Failed to analyze {ticker}: {str(result)}")
                elif isinstance(result, dict) and "insights" in result:
                    # Merge insights from each ticker's analysis
                    state["insights"].extend(result["insights"])
            
            # Emit final completion message
            if state.get("log_broadcaster") and state["insights"]:
                await state["log_broadcaster"].all_analysis_complete(len(state["insights"]))
            
            return state
        
        # Build the graph
        workflow = StateGraph(OrchestratorState)
        
        # Add nodes
        workflow.add_node("extract_tickers", extract_tickers_node)
        workflow.add_node("process_tickers", process_all_tickers)
        
        # Add edges
        workflow.add_edge("extract_tickers", "process_tickers")
        workflow.add_edge("process_tickers", END)
        
        # Set entry point
        workflow.set_entry_point("extract_tickers")
        
        return workflow.compile()
    
    async def analyze(
        self, 
        query: str, 
        max_iterations: int = 3, 
        timeout_seconds: int = 60,
        request_id: str = "",
        confirmed_tickers: Optional[List[str]] = None,
        log_broadcaster = None
    ) -> List[TickerInsight]:
        """
        Run stock analysis workflow using Yahoo Finance and Gemini AI.
        
        Args:
            query: Natural language query with stock tickers
            max_iterations: Maximum iterations per agent
            timeout_seconds: Timeout for the entire analysis
            request_id: Unique request identifier
            confirmed_tickers: Pre-confirmed tickers to analyze (skips extraction)
            log_broadcaster: LogBroadcaster instance for streaming logs
            
        Returns:
            List of ticker insights
        """
        start_time = time.time()
        
        logger.info("Starting stock analysis", 
                   query=query, 
                   request_id=request_id)
        
        try:
            # Initialize state
            initial_state: OrchestratorState = {
                "query": query,
                "tickers": [],
                "unresolved_names": [],
                "confirmed_tickers": confirmed_tickers,
                "max_iterations": max_iterations,
                "timeout_seconds": timeout_seconds,
                "request_id": request_id,
                "log_broadcaster": log_broadcaster,
                "insights": [],
                "errors": [],
                "start_time": start_time,
                "current_ticker": "",
                "current_ticker_data": {}
            }
            
            # Run the workflow
            final_state = await self.workflow.ainvoke(initial_state)
            
            # Check for errors
            if final_state.get("errors"):
                error_msg = "; ".join(final_state["errors"])
                raise Exception(error_msg)
            
            if not final_state.get("insights"):
                raise Exception("Failed to analyze any tickers. Please try again.")
            
            execution_time = time.time() - start_time
            logger.info("Analysis completed", 
                       request_id=request_id,
                       execution_time=execution_time,
                       insights_count=len(final_state["insights"]))
            
            return final_state["insights"]
            
        except Exception as e:
            logger.error("Analysis failed", 
                        request_id=request_id,
                        error=str(e))
            if log_broadcaster:
                await log_broadcaster.error(
                    f"Analysis failed: {str(e)}",
                    error_details={"error": str(e)}
                )
            raise
