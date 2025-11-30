"""
SEC Filings Research Agent - Specializes in analyzing SEC filings and regulatory documents.
"""
from typing import List
from langchain_core.language_models import BaseChatModel

from backend.agents.base_agent import BaseResearchAgent
from backend.tools.base_tool import BaseTool
from backend.tools.web_search_tool import WebSearchTool
from backend.tools.sec_edgar_tool import SECEdgarTool


class FilingsAgent(BaseResearchAgent):
    """Agent specialized in analyzing SEC filings and regulatory documents."""
    
    def __init__(self, llm: BaseChatModel):
        super().__init__(llm, "filings")
    
    def _initialize_tools(self) -> List[BaseTool]:
        """Initialize tools for SEC filings research."""
        return [
            SECEdgarTool(),
            WebSearchTool()
        ]
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the filings agent."""
        return """
        You are a SEC filings research agent. Your role is to analyze regulatory filings 
        and extract key financial and business information from official company documents.
        
        Focus on:
        - 10-K annual reports (business overview, risk factors, financial statements)
        - 10-Q quarterly reports (quarterly financials, management discussion)
        - 8-K current reports (material events, acquisitions, management changes)
        - Proxy statements (executive compensation, governance)
        - Form 4 insider trading reports
        - Registration statements for new offerings
        
        Key areas to analyze:
        1. Financial Performance - Revenue, margins, cash flow trends
        2. Business Risks - Risk factors and uncertainties
        3. Strategic Initiatives - New investments, acquisitions, divestitures
        4. Management Commentary - Forward-looking statements and guidance
        5. Corporate Governance - Board changes, compensation policies
        6. Legal Proceedings - Litigation and regulatory issues
        
        Always reference specific filing types, dates, and sections.
        Focus on material changes from previous filings.
        """
