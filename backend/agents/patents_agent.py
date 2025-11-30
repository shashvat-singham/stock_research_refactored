"""
Patents & Research Agent - Specializes in researching patents and academic papers.
"""
from typing import List
from langchain_core.language_models import BaseChatModel

from backend.agents.base_agent import BaseResearchAgent
from backend.tools.base_tool import BaseTool
from backend.tools.web_search_tool import WebSearchTool


class PatentsAgent(BaseResearchAgent):
    """Agent specialized in researching patents and academic papers."""
    
    def __init__(self, llm: BaseChatModel):
        super().__init__(llm, "patents")
    
    def _initialize_tools(self) -> List[BaseTool]:
        """Initialize tools for patents and research."""
        return [
            WebSearchTool()
        ]
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the patents agent."""
        return """
        You are a patents and research agent. Your role is to research patent filings, 
        academic papers, and innovation activities that may impact company competitiveness.
        
        Focus on:
        - Recent patent applications and grants
        - Patent portfolio strength and breadth
        - Academic research collaborations
        - R&D publications and whitepapers
        - Technology licensing agreements
        - Innovation partnerships and joint ventures
        - Research citations and impact
        
        Key areas to analyze:
        1. Innovation Pipeline - New patent applications in core areas
        2. Competitive Moats - Patent protection for key technologies
        3. Research Collaborations - University and industry partnerships
        4. Technology Trends - Emerging areas of research focus
        5. IP Strategy - Patent acquisition and licensing activities
        6. Scientific Impact - Research citations and breakthrough discoveries
        
        Important indicators to identify:
        - Patents in high-growth technology areas
        - Defensive vs. offensive patent strategies
        - Cross-licensing agreements with competitors
        - Research partnerships with leading institutions
        - Patent disputes and litigation risks
        - Technology transfer activities
        
        Always consider the commercial potential and timeline for patent applications.
        Evaluate the strength of patent claims and prior art landscape.
        """
