"""
Base Tool class for agent tools.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List
import structlog

logger = structlog.get_logger()


class BaseTool(ABC):
    """Base class for all agent tools."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def execute(self, query: str, ticker: str) -> Dict[str, Any]:
        """
        Execute the tool with the given query and ticker.
        
        Args:
            query: Search query or input
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary containing:
            - observation: Text description of what was found
            - sources: List of source information
            - data: Any structured data (optional)
        """
        pass
    
    def _format_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format sources into a consistent structure."""
        formatted_sources = []
        
        for source in sources:
            formatted_source = {
                "url": source.get("url", ""),
                "title": source.get("title", ""),
                "published_at": source.get("published_at"),
                "snippet": source.get("snippet", "")
            }
            formatted_sources.append(formatted_source)
        
        return formatted_sources
