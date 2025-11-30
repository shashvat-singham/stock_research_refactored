"""
Pydantic models for API requests and responses.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

from pydantic import BaseModel, Field


class StanceType(str, Enum):
    """Investment stance types."""
    HOLD = "hold"
    BUY = "buy"
    SELL = "sell"


class ConfidenceLevel(str, Enum):
    """Confidence levels for analysis."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SourceInfo(BaseModel):
    """Information about a data source."""
    url: str = Field(..., description="Source URL")
    title: Optional[str] = Field(None, description="Source title")
    published_at: Optional[datetime] = Field(None, description="Publication date")
    fetched_at: datetime = Field(default_factory=datetime.now, description="Fetch timestamp")
    snippet: Optional[str] = Field(None, description="Relevant snippet from source")


class AgentStep(BaseModel):
    """A single step in an agent's ReAct loop."""
    step_number: int = Field(..., description="Step number in the sequence")
    thought: str = Field(..., description="Agent's reasoning")
    action: str = Field(..., description="Action taken")
    observation: str = Field(..., description="Result of the action")
    sources: List[SourceInfo] = Field(default_factory=list, description="Sources used in this step")
    timestamp: datetime = Field(default_factory=datetime.now, description="Step timestamp")
    latency_ms: Optional[float] = Field(None, description="Step execution time in milliseconds")


class AgentTrace(BaseModel):
    """Complete trace of an agent's execution."""
    agent_type: str = Field(..., description="Type of agent (news, filings, etc.)")
    ticker: str = Field(..., description="Stock ticker being analyzed")
    steps: List[AgentStep] = Field(default_factory=list, description="Sequence of agent steps")
    total_latency_ms: Optional[float] = Field(None, description="Total execution time")
    success: bool = Field(True, description="Whether the agent completed successfully")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class TickerInsight(BaseModel):
    """Research insights for a single ticker."""
    ticker: str = Field(..., description="Stock ticker symbol")
    company_name: Optional[str] = Field(None, description="Company name")
    
    # Price and market data
    current_price: Optional[float] = Field(None, description="Current stock price")
    market_cap: Optional[float] = Field(None, description="Market capitalization")
    pe_ratio: Optional[float] = Field(None, description="P/E ratio")
    fifty_two_week_high: Optional[float] = Field(None, description="52-week high")
    fifty_two_week_low: Optional[float] = Field(None, description="52-week low")
    
    # Technical analysis
    support_levels: List[float] = Field(default_factory=list, description="Support price levels")
    resistance_levels: List[float] = Field(default_factory=list, description="Resistance price levels")
    trend: Optional[str] = Field(None, description="Current price trend")
    
    # Analysis results
    summary: str = Field(..., description="Executive summary of findings")
    key_drivers: List[str] = Field(default_factory=list, description="Key growth drivers")
    risks: List[str] = Field(default_factory=list, description="Key risks")
    catalysts: List[str] = Field(default_factory=list, description="Upcoming catalysts")
    
    # Investment recommendation
    stance: StanceType = Field(..., description="Investment stance")
    confidence: ConfidenceLevel = Field(..., description="Confidence level")
    rationale: str = Field(..., description="Reasoning for the stance")
    
    # Supporting data
    sources: List[SourceInfo] = Field(default_factory=list, description="All sources used")
    agent_traces: List[AgentTrace] = Field(default_factory=list, description="Agent execution traces")
    
    # Metadata
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="Analysis completion time")


class AnalysisRequest(BaseModel):
    """Request model for stock analysis."""
    query: str = Field(..., description="Natural language query with tickers and analysis request")
    max_iterations: Optional[int] = Field(3, description="Maximum iterations per agent")
    timeout_seconds: Optional[int] = Field(30, description="Timeout for the entire analysis")
    request_id: Optional[str] = Field(None, description="Request ID for WebSocket streaming")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for follow-up interactions")
    confirmation_response: Optional[str] = Field(None, description="User's response to a confirmation prompt")


class CorrectionSuggestion(BaseModel):
    """Suggestion for correcting a misspelled company name."""
    original_input: str = Field(..., description="The original user input")
    corrected_name: str = Field(..., description="The corrected company name")
    ticker: str = Field(..., description="The stock ticker symbol")
    confidence: str = Field(..., description="Confidence level (high, medium, low)")
    explanation: str = Field(..., description="Explanation of the correction")


class ConfirmationPrompt(BaseModel):
    """Prompt for user confirmation of a correction."""
    type: str = Field(..., description="Type of prompt (confirmation, selection, clarification)")
    message: str = Field(..., description="Message to display to the user")
    suggestion: Optional[CorrectionSuggestion] = Field(None, description="Correction suggestion")
    conversation_id: str = Field(..., description="Conversation ID for follow-up")


class AnalysisResponse(BaseModel):
    """Response model for stock analysis."""
    request_id: str = Field(..., description="Unique request identifier")
    query: str = Field(..., description="Original query")
    
    # Results
    insights: List[TickerInsight] = Field(default_factory=list, description="Insights per ticker")
    cross_ticker_analysis: Optional[str] = Field(None, description="Cross-ticker comparison")
    
    # Execution metadata
    total_latency_ms: float = Field(..., description="Total analysis time")
    tickers_analyzed: List[str] = Field(default_factory=list, description="List of analyzed tickers")
    agents_used: List[str] = Field(default_factory=list, description="Types of agents used")
    
    # Status
    success: bool = Field(True, description="Whether analysis completed successfully")
    warnings: List[str] = Field(default_factory=list, description="Any warnings during analysis")
    errors: List[str] = Field(default_factory=list, description="Any errors during analysis")
    
    # Confirmation flow
    needs_confirmation: bool = Field(False, description="Whether user confirmation is needed")
    confirmation_prompt: Optional[ConfirmationPrompt] = Field(None, description="Confirmation prompt if needed")
    
    # Timestamps
    started_at: datetime = Field(..., description="Analysis start time")
    completed_at: datetime = Field(..., description="Analysis completion time")


class AnalysisStatus(BaseModel):
    """Status model for ongoing analysis."""
    request_id: str = Field(..., description="Request identifier")
    status: str = Field(..., description="Current status")
    progress: float = Field(..., description="Progress percentage (0-100)")
    current_step: Optional[str] = Field(None, description="Current processing step")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")

