"""
Conversation Manager - Handles interactive confirmations and conversation state.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import structlog

logger = structlog.get_logger()


class ConversationState(str, Enum):
    """States of a conversation."""
    INITIAL = "initial"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    AWAITING_CLARIFICATION = "awaiting_clarification"
    READY_FOR_ANALYSIS = "ready_for_analysis"
    COMPLETED = "completed"


class Conversation:
    """Represents a conversation session."""
    
    def __init__(self, conversation_id: str):
        """
        Initialize a conversation.
        
        Args:
            conversation_id: Unique conversation identifier
        """
        self.conversation_id = conversation_id
        self.state = ConversationState.INITIAL
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
        
        # Conversation data
        self.original_query: Optional[str] = None
        self.resolved_tickers: List[str] = []
        self.pending_confirmations: List[Dict[str, Any]] = []
        self.user_responses: List[str] = []
        self.final_query: Optional[str] = None
        
    def update(self):
        """Update the last_updated timestamp."""
        self.last_updated = datetime.now()
    
    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """
        Check if conversation has expired.
        
        Args:
            timeout_minutes: Timeout in minutes
            
        Returns:
            True if expired
        """
        return datetime.now() - self.last_updated > timedelta(minutes=timeout_minutes)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to dictionary."""
        return {
            "conversation_id": self.conversation_id,
            "state": self.state.value,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "original_query": self.original_query,
            "resolved_tickers": self.resolved_tickers,
            "pending_confirmations": self.pending_confirmations,
            "user_responses": self.user_responses,
            "final_query": self.final_query
        }


class ConversationManager:
    """
    Manages conversation sessions for interactive confirmations.
    """
    
    def __init__(self):
        """Initialize the conversation manager."""
        self.conversations: Dict[str, Conversation] = {}
        logger.info("ConversationManager initialized")
    
    def create_conversation(self, conversation_id: str) -> Conversation:
        """
        Create a new conversation.
        
        Args:
            conversation_id: Unique conversation identifier
            
        Returns:
            New conversation instance
        """
        conversation = Conversation(conversation_id)
        self.conversations[conversation_id] = conversation
        
        logger.info("Created conversation", conversation_id=conversation_id)
        return conversation
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Get an existing conversation.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Conversation if found, None otherwise
        """
        conversation = self.conversations.get(conversation_id)
        
        if conversation and conversation.is_expired():
            logger.warning("Conversation expired", conversation_id=conversation_id)
            self.delete_conversation(conversation_id)
            return None
        
        return conversation
    
    def delete_conversation(self, conversation_id: str):
        """
        Delete a conversation.
        
        Args:
            conversation_id: Conversation identifier
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            logger.info("Deleted conversation", conversation_id=conversation_id)
    
    def cleanup_expired_conversations(self, timeout_minutes: int = 30):
        """
        Clean up expired conversations.
        
        Args:
            timeout_minutes: Timeout in minutes
        """
        expired_ids = [
            conv_id for conv_id, conv in self.conversations.items()
            if conv.is_expired(timeout_minutes)
        ]
        
        for conv_id in expired_ids:
            self.delete_conversation(conv_id)
        
        if expired_ids:
            logger.info("Cleaned up expired conversations", 
                       count=len(expired_ids))
    
    def create_confirmation_prompt(
        self, 
        conversation: Conversation,
        suggestions: List[tuple]
    ) -> Dict[str, Any]:
        """
        Create a confirmation prompt for ambiguous company names.
        
        Args:
            conversation: Conversation instance
            suggestions: List of (company_name, ticker) suggestions
            
        Returns:
            Confirmation prompt data
        """
        conversation.state = ConversationState.AWAITING_CONFIRMATION
        conversation.pending_confirmations = [
            {"company": company, "ticker": ticker}
            for company, ticker in suggestions
        ]
        conversation.update()
        
        if len(suggestions) == 1:
            company, ticker = suggestions[0]
            prompt = {
                "type": "confirmation",
                "message": f"Did you mean {company.title()} ({ticker})?",
                "options": ["Yes", "No"],
                "suggestions": conversation.pending_confirmations
            }
        else:
            prompt = {
                "type": "selection",
                "message": "I found multiple matches. Which company did you mean?",
                "options": [
                    f"{company.title()} ({ticker})"
                    for company, ticker in suggestions
                ] + ["None of these"],
                "suggestions": conversation.pending_confirmations
            }
        
        logger.info("Created confirmation prompt",
                   conversation_id=conversation.conversation_id,
                   suggestions_count=len(suggestions))
        
        return prompt
    
    def create_clarification_prompt(
        self,
        conversation: Conversation,
        unresolved_names: List[str]
    ) -> Dict[str, Any]:
        """
        Create a clarification prompt for unresolved company names.
        
        Args:
            conversation: Conversation instance
            unresolved_names: List of unresolved company names
            
        Returns:
            Clarification prompt data
        """
        conversation.state = ConversationState.AWAITING_CLARIFICATION
        conversation.update()
        
        if len(unresolved_names) == 1:
            message = (
                f"I couldn't recognize '{unresolved_names[0]}'. "
                "Could you please provide the stock ticker or full company name? "
                "For example: 'AAPL' or 'Apple Inc.'"
            )
        else:
            names_str = "', '".join(unresolved_names)
            message = (
                f"I couldn't recognize these companies: '{names_str}'. "
                "Could you please provide their stock tickers or full company names? "
                "For example: 'AAPL for Apple, MSFT for Microsoft'"
            )
        
        prompt = {
            "type": "clarification",
            "message": message,
            "unresolved_names": unresolved_names
        }
        
        logger.info("Created clarification prompt",
                   conversation_id=conversation.conversation_id,
                   unresolved_count=len(unresolved_names))
        
        return prompt
    
    def process_confirmation_response(
        self,
        conversation: Conversation,
        response: str
    ) -> Dict[str, Any]:
        """
        Process user response to confirmation prompt.
        
        Args:
            conversation: Conversation instance
            response: User response
            
        Returns:
            Processing result
        """
        conversation.user_responses.append(response)
        conversation.update()
        
        response_lower = response.lower().strip()
        
        # Handle "Yes" response - confirm ALL tickers at once
        if response_lower in ["yes", "y", "yeah", "yep", "sure", "correct"]:
            # All tickers are already in confirmed_tickers from the initial detection
            conversation.state = ConversationState.READY_FOR_ANALYSIS
            
            tickers = getattr(conversation, 'confirmed_tickers', [])
            
            logger.info("User confirmed all suggestions",
                       conversation_id=conversation.conversation_id,
                       tickers=tickers)
            
            return {
                "status": "confirmed",
                "ticker": ", ".join(tickers) if tickers else "unknown",
                "message": f"Great! I'll analyze {', '.join(tickers)}."
            }
        
        # Handle "No" response
        elif response_lower in ["no", "n", "nope", "incorrect"]:
            conversation.state = ConversationState.AWAITING_CLARIFICATION
            conversation.pending_confirmations = []
            
            logger.info("User rejected suggestion",
                       conversation_id=conversation.conversation_id)
            
            return {
                "status": "rejected",
                "message": (
                    "Got it. Which company or ticker would you like to analyze, "
                    "and for how long? For example, 'Apple for 1 month'."
                )
            }
        
        # Handle selection from multiple options
        else:
            # Try to extract ticker from response
            for confirmation in conversation.pending_confirmations:
                ticker = confirmation["ticker"]
                company = confirmation["company"]
                
                if ticker in response.upper() or company in response.lower():
                    conversation.resolved_tickers.append(ticker)
                    conversation.pending_confirmations = []
                    conversation.state = ConversationState.READY_FOR_ANALYSIS
                    
                    logger.info("User selected option",
                               conversation_id=conversation.conversation_id,
                               ticker=ticker)
                    
                    return {
                        "status": "confirmed",
                        "ticker": ticker,
                        "message": f"Perfect! I'll analyze {ticker}."
                    }
            
            # Could not parse response
            logger.warning("Could not parse confirmation response",
                          conversation_id=conversation.conversation_id,
                          response=response)
            
            return {
                "status": "unclear",
                "message": (
                    "I didn't quite understand. Please respond with 'Yes', 'No', "
                    "or select one of the options provided."
                )
            }
    
    def process_clarification_response(
        self,
        conversation: Conversation,
        response: str
    ) -> Dict[str, Any]:
        """
        Process user response to clarification prompt.
        
        Args:
            conversation: Conversation instance
            response: User response with tickers or company names
            
        Returns:
            Processing result
        """
        from backend.services.ticker_mapper import get_ticker_mapper
        
        conversation.user_responses.append(response)
        conversation.update()
        
        ticker_mapper = get_ticker_mapper()
        
        # Extract tickers from response
        resolved, unresolved = ticker_mapper.extract_tickers_from_query(response)
        
        if resolved:
            conversation.resolved_tickers.extend(resolved)
            conversation.state = ConversationState.READY_FOR_ANALYSIS
            
            logger.info("Resolved tickers from clarification",
                       conversation_id=conversation.conversation_id,
                       tickers=resolved)
            
            return {
                "status": "resolved",
                "tickers": resolved,
                "message": f"Perfect! I'll analyze {', '.join(resolved)}."
            }
        
        else:
            logger.warning("Could not resolve tickers from clarification",
                          conversation_id=conversation.conversation_id,
                          response=response)
            
            return {
                "status": "still_unclear",
                "message": (
                    "I still couldn't identify the company. "
                    "Please provide a valid stock ticker (e.g., 'AAPL') "
                    "or a well-known company name (e.g., 'Apple Inc.')."
                )
            }


# Global instance
_conversation_manager = None


def get_conversation_manager() -> ConversationManager:
    """Get the global conversation manager instance."""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
    return _conversation_manager

