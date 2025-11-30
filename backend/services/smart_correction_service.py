"""
Smart Correction Service - Uses Gemini AI to detect and correct misspelled company names.
Supports multiple misspellings in a single query.
"""
import google.generativeai as genai
import json
import os
from typing import Optional, Dict, Any, List
import structlog
from dotenv import load_dotenv

load_dotenv()

logger = structlog.get_logger()


class SmartCorrectionService:
    """
    Service for detecting and correcting misspelled company names using Gemini AI.
    Handles multiple misspellings in a single query.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Smart Correction service.
        
        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found, smart correction will not work")
            raise ValueError("GEMINI_API_KEY is required for smart correction")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        logger.info("SmartCorrectionService initialized")
    
    def detect_and_correct_multiple(self, user_input: str) -> Dict[str, Any]:
        """
        Detect if the user input contains misspelled company names and suggest corrections.
        Handles MULTIPLE misspellings in a single query.
        
        Args:
            user_input: The user's input text (e.g., "analyze metae Apple and TSLAA")
            
        Returns:
            Dictionary containing:
            - has_misspellings: bool - Whether any misspellings were detected
            - original_input: str - The original user input
            - corrections: List[Dict] - List of corrections, each with:
                - original: str - The misspelled text
                - corrected_name: str - The corrected company name
                - ticker: str - The stock ticker symbol
                - confidence: str - Confidence level (high, medium, low)
                - explanation: str - Brief explanation
        """
        prompt = f"""You are a financial assistant that helps users identify company names and stock tickers.

USER INPUT: "{user_input}"

TASK:
Analyze the ENTIRE user input and identify ALL misspelled or ambiguous company names/tickers. Return corrections for EVERY misspelling found, not just the first one.

RULES:
1. Look for ALL company names or tickers that might be misspelled
2. Consider common typos, missing letters, extra letters, or phonetic similarities
3. Only suggest corrections for well-known publicly traded companies
4. If a word is correctly spelled or is a valid ticker, do NOT include it in corrections
5. Return ALL corrections in a single response

EXAMPLES:
Input: "analyze metae Apple and TSLAA"
Output: Should detect TWO misspellings:
  - "metae" → Meta Platforms Inc. (META)
  - "TSLAA" → Tesla Inc. (TSLA)
  - "Apple" is correct, so not included

Input: "compare microsft gogle and amazn"
Output: Should detect THREE misspellings:
  - "microsft" → Microsoft Corporation (MSFT)
  - "gogle" → Alphabet Inc. (GOOGL)
  - "amazn" → Amazon.com Inc. (AMZN)

Input: "analyze AAPL MSFT and GOOGL"
Output: No misspellings (all valid tickers)

Respond in JSON format:
{{
    "has_misspellings": true or false,
    "original_input": "the exact user input",
    "corrections": [
        {{
            "original": "misspelled text",
            "corrected_name": "Full Company Name",
            "ticker": "TICKER",
            "confidence": "high, medium, or low",
            "explanation": "Brief explanation"
        }}
    ]
}}

If no misspellings found, return empty corrections array.
Respond with ONLY the JSON, no additional text."""

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Extract JSON from response
            if '```json' in result_text:
                result_text = result_text.split('```json')[1].split('```')[0].strip()
            elif '```' in result_text:
                result_text = result_text.split('```')[1].split('```')[0].strip()
            
            result = json.loads(result_text)
            
            logger.info("Smart correction analysis completed",
                       user_input=user_input,
                       has_misspellings=result.get('has_misspellings'),
                       corrections_count=len(result.get('corrections', [])))
            
            return result
            
        except Exception as e:
            logger.error("Error in smart correction", 
                        user_input=user_input,
                        error=str(e))
            
            # Return a safe fallback
            return {
                "has_misspellings": False,
                "original_input": user_input,
                "corrections": []
            }
    
    def detect_and_correct(self, user_input: str) -> Dict[str, Any]:
        """
        Legacy method for backward compatibility.
        Detects the FIRST misspelling only.
        
        Args:
            user_input: The user's input text
            
        Returns:
            Dictionary with single correction (legacy format)
        """
        result = self.detect_and_correct_multiple(user_input)
        
        if result.get('has_misspellings') and result.get('corrections'):
            # Return first correction in legacy format
            first_correction = result['corrections'][0]
            return {
                "is_misspelled": True,
                "original_input": result['original_input'],
                "corrected_name": first_correction['corrected_name'],
                "ticker": first_correction['ticker'],
                "confidence": first_correction['confidence'],
                "explanation": first_correction['explanation']
            }
        else:
            return {
                "is_misspelled": False,
                "original_input": result['original_input'],
                "corrected_name": None,
                "ticker": None,
                "confidence": "high",
                "explanation": "No misspellings detected"
            }
    
    def generate_confirmation_message(self, correction_result: Dict[str, Any]) -> str:
        """
        Generate a user-friendly confirmation message based on correction result.
        
        Args:
            correction_result: Result from detect_and_correct()
            
        Returns:
            Confirmation message string
        """
        if not correction_result.get('is_misspelled'):
            return None
        
        corrected_name = correction_result.get('corrected_name')
        ticker = correction_result.get('ticker')
        confidence = correction_result.get('confidence', 'medium')
        
        if corrected_name and ticker:
            if confidence == 'high':
                return f"Did you mean **{corrected_name}** ({ticker})?"
            elif confidence == 'medium':
                return f"Did you mean **{corrected_name}** ({ticker})? (I'm moderately confident about this)"
            else:
                return f"Did you possibly mean **{corrected_name}** ({ticker})? (I'm not very confident about this)"
        
        return None
    
    def generate_multiple_corrections_message(self, corrections: List[Dict[str, Any]]) -> str:
        """
        Generate a user-friendly message for multiple corrections.
        
        Args:
            corrections: List of correction dictionaries
            
        Returns:
            Formatted message string
        """
        if not corrections:
            return None
        
        if len(corrections) == 1:
            correction = corrections[0]
            return f"Did you mean **{correction['corrected_name']}** ({correction['ticker']})?"
        
        # Multiple corrections
        corrections_list = []
        for i, correction in enumerate(corrections, 1):
            corrections_list.append(
                f"{i}. '{correction['original']}' → **{correction['corrected_name']}** ({correction['ticker']})"
            )
        
        message = "I found multiple potential misspellings:\n\n" + "\n".join(corrections_list)
        message += "\n\nDid you mean these corrections?"
        
        return message


# Global instance
_smart_correction_service = None


def get_smart_correction_service() -> SmartCorrectionService:
    """Get the global smart correction service instance."""
    global _smart_correction_service
    if _smart_correction_service is None:
        try:
            _smart_correction_service = SmartCorrectionService()
        except ValueError as e:
            logger.error("Failed to initialize SmartCorrectionService", error=str(e))
            # Return None if initialization fails
            return None
    return _smart_correction_service

