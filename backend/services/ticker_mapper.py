"""
Ticker Mapper Service - Maps company names to stock tickers.
Handles fuzzy matching and spelling detection.
"""
import re
from typing import Optional, List, Tuple, Dict
from difflib import get_close_matches
import structlog

logger = structlog.get_logger()


class TickerMapper:
    """
    Maps company names to stock tickers with fuzzy matching support.
    """
    
    # Comprehensive mapping of company names to tickers
    COMPANY_TO_TICKER = {
        # Major Tech Companies
        "apple": "AAPL",
        "apple inc": "AAPL",
        "apple computer": "AAPL",
        "microsoft": "MSFT",
        "microsoft corporation": "MSFT",
        "google": "GOOGL",
        "alphabet": "GOOGL",
        "alphabet inc": "GOOGL",
        "amazon": "AMZN",
        "amazon.com": "AMZN",
        "meta": "META",
        "meta platforms": "META",
        "facebook": "META",
        "nvidia": "NVDA",
        "nvidia corporation": "NVDA",
        "tesla": "TSLA",
        "tesla inc": "TSLA",
        "netflix": "NFLX",
        "netflix inc": "NFLX",
        
        # Semiconductor Companies
        "amd": "AMD",
        "advanced micro devices": "AMD",
        "intel": "INTC",
        "intel corporation": "INTC",
        "tsm": "TSM",
        "taiwan semiconductor": "TSM",
        "tsmc": "TSM",
        "qualcomm": "QCOM",
        "broadcom": "AVGO",
        "micron": "MU",
        "micron technology": "MU",
        
        # Financial Companies
        "jpmorgan": "JPM",
        "jp morgan": "JPM",
        "jpmorgan chase": "JPM",
        "bank of america": "BAC",
        "bofa": "BAC",
        "goldman sachs": "GS",
        "morgan stanley": "MS",
        "wells fargo": "WFC",
        "citigroup": "C",
        "citi": "C",
        
        # Retail & Consumer
        "walmart": "WMT",
        "target": "TGT",
        "costco": "COST",
        "home depot": "HD",
        "nike": "NKE",
        "starbucks": "SBUX",
        "mcdonalds": "MCD",
        "mcdonald's": "MCD",
        "coca cola": "KO",
        "coca-cola": "KO",
        "pepsi": "PEP",
        "pepsico": "PEP",
        
        # Healthcare & Pharma
        "johnson & johnson": "JNJ",
        "johnson and johnson": "JNJ",
        "pfizer": "PFE",
        "moderna": "MRNA",
        "abbvie": "ABBV",
        "merck": "MRK",
        "eli lilly": "LLY",
        "unitedhealth": "UNH",
        "united health": "UNH",
        
        # Energy
        "exxon": "XOM",
        "exxonmobil": "XOM",
        "exxon mobil": "XOM",
        "chevron": "CVX",
        "conocophillips": "COP",
        "shell": "SHEL",
        "bp": "BP",
        
        # Automotive
        "ford": "F",
        "general motors": "GM",
        "gm": "GM",
        "toyota": "TM",
        "honda": "HMC",
        
        # Airlines
        "delta": "DAL",
        "delta airlines": "DAL",
        "united airlines": "UAL",
        "american airlines": "AAL",
        "southwest": "LUV",
        "southwest airlines": "LUV",
        
        # Others
        "disney": "DIS",
        "walt disney": "DIS",
        "boeing": "BA",
        "caterpillar": "CAT",
        "visa": "V",
        "mastercard": "MA",
        "paypal": "PYPL",
        "adobe": "ADBE",
        "salesforce": "CRM",
        "oracle": "ORCL",
        "ibm": "IBM",
        "cisco": "CSCO",
        "verizon": "VZ",
        "at&t": "T",
        "att": "T",
        "comcast": "CMCSA",
        "procter & gamble": "PG",
        "procter and gamble": "PG",
        "pg": "PG",
    }
    
    def __init__(self):
        """Initialize the ticker mapper."""
        # Create reverse mapping for ticker validation
        self.ticker_to_company = {v: k for k, v in self.COMPANY_TO_TICKER.items()}
        
        # Create lowercase company names list for fuzzy matching
        self.company_names = list(self.COMPANY_TO_TICKER.keys())
        
        logger.info("TickerMapper initialized", 
                   companies_count=len(self.COMPANY_TO_TICKER))
    
    def is_ticker(self, text: str) -> bool:
        """
        Check if the text is likely a stock ticker.
        
        Args:
            text: Text to check
            
        Returns:
            True if text appears to be a ticker
        """
        # Tickers are typically 1-5 uppercase letters
        return bool(re.match(r'^[A-Z]{1,5}$', text.strip()))
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize text for matching.
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text
        """
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove common suffixes
        text = re.sub(r'\s+(inc|corp|corporation|company|co|ltd|limited)\b', '', text)
        
        # Remove special characters except spaces and hyphens
        text = re.sub(r'[^\w\s-]', '', text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text
    
    def map_to_ticker(self, text: str) -> Optional[str]:
        """
        Map company name or ticker to ticker symbol.
        
        Args:
            text: Company name or ticker
            
        Returns:
            Ticker symbol if found, None otherwise
        """
        text = text.strip()
        
        # If already a ticker, return as-is
        if self.is_ticker(text):
            logger.debug("Text is already a ticker", text=text)
            return text
        
        # Normalize and try exact match
        normalized = self.normalize_text(text)
        if normalized in self.COMPANY_TO_TICKER:
            ticker = self.COMPANY_TO_TICKER[normalized]
            logger.info("Exact match found", company=text, ticker=ticker)
            return ticker
        
        # Try fuzzy match
        matches = get_close_matches(normalized, self.company_names, n=1, cutoff=0.8)
        if matches:
            ticker = self.COMPANY_TO_TICKER[matches[0]]
            logger.info("Fuzzy match found", 
                       company=text, 
                       matched_to=matches[0], 
                       ticker=ticker)
            return ticker
        
        logger.warning("No ticker mapping found", text=text)
        return None
    
    def find_suggestions(self, text: str, n: int = 3) -> List[Tuple[str, str]]:
        """
        Find suggested company names for misspelled text.
        
        Args:
            text: Potentially misspelled company name
            n: Number of suggestions to return
            
        Returns:
            List of (company_name, ticker) tuples
        """
        normalized = self.normalize_text(text)
        
        # Get close matches with lower cutoff for suggestions
        matches = get_close_matches(normalized, self.company_names, n=n, cutoff=0.6)
        
        suggestions = [(match, self.COMPANY_TO_TICKER[match]) for match in matches]
        
        logger.info("Found suggestions", 
                   text=text, 
                   suggestions_count=len(suggestions))
        
        return suggestions
    
    def extract_tickers_from_query(self, query: str) -> Tuple[List[str], List[str]]:
        """
        Extract tickers and unresolved company names from a query.
        
        Args:
            query: Natural language query
            
        Returns:
            Tuple of (resolved_tickers, unresolved_names)
        """
        # First, extract all existing tickers using regex
        ticker_pattern = r'\b[A-Z]{1,5}\b'
        potential_tickers = re.findall(ticker_pattern, query)
        
        # Filter out common words
        common_words = {
            "THE", "AND", "FOR", "ARE", "BUT", "NOT", "YOU", "ALL", "CAN", "HER", 
            "WAS", "ONE", "OUR", "HAD", "WHAT", "SO", "UP", "OUT", "IF", 
            "ABOUT", "WHO", "GET", "WHICH", "GO", "ME", "WHEN", "MAKE", 
            "LIKE", "TIME", "NO", "JUST", "HIM", "KNOW", "TAKE", "PEOPLE", "INTO", 
            "YEAR", "YOUR", "GOOD", "SOME", "COULD", "THEM", "SEE", "OTHER", "THAN", 
            "THEN", "NOW", "LOOK", "ONLY", "COME", "ITS", "OVER", "THINK", "ALSO", 
            "BACK", "AFTER", "USE", "TWO", "HOW", "WORK", "FIRST", "WELL", 
            "WAY", "EVEN", "NEW", "WANT", "BECAUSE", "ANY", "THESE", "GIVE", "DAY", 
            "MOST", "US", "BEST", "AI", "OR", "TO", "FROM", "AS", "AT", "BY", "IN", "ON",
            "ANALYZE", "COMPARE", "RESEARCH", "MONTH", "MONTHS", "WEEK", "WEEKS", "YEAR", "YEARS",
            "FOR", "WITH", "DURING", "OVER"
        }
        
        resolved_tickers = [t for t in potential_tickers if t not in common_words]
        
        # Now try to find company names in the remaining text
        # Remove already found tickers from query
        remaining_query = query
        for ticker in resolved_tickers:
            remaining_query = remaining_query.replace(ticker, "")
        
        # Split into words and try to match company names
        words = remaining_query.split()
        unresolved_names = []
        
        i = 0
        while i < len(words):
            word = words[i]
            
            # Skip if empty or too short
            if not word or len(word) < 2:
                i += 1
                continue
            
            # Try three-word phrase first (longest match)
            if i + 2 < len(words):
                three_words = f"{word} {words[i+1]} {words[i+2]}"
                ticker = self.map_to_ticker(three_words)
                if ticker and ticker not in resolved_tickers:
                    resolved_tickers.append(ticker)
                    i += 3
                    continue
            
            # Try two-word phrase
            if i + 1 < len(words):
                two_words = f"{word} {words[i+1]}"
                ticker = self.map_to_ticker(two_words)
                if ticker and ticker not in resolved_tickers:
                    resolved_tickers.append(ticker)
                    i += 2
                    continue
            
            # Try single word
            ticker = self.map_to_ticker(word)
            if ticker and ticker not in resolved_tickers:
                resolved_tickers.append(ticker)
                i += 1
                continue
            
            # Could not resolve - add to unresolved if it looks like a company name
            if len(word) > 2 and word[0].isupper() and word.upper() not in common_words:
                unresolved_names.append(word)
            
            i += 1
        
        # Remove duplicates while preserving order
        resolved_tickers = list(dict.fromkeys(resolved_tickers))
        unresolved_names = list(dict.fromkeys(unresolved_names))
        
        logger.info("Extracted tickers from query",
                   query=query,
                   resolved_tickers=resolved_tickers,
                   unresolved_names=unresolved_names)
        
        return resolved_tickers, unresolved_names
    
    def get_company_name(self, ticker: str) -> Optional[str]:
        """
        Get company name for a ticker.
        
        Args:
            ticker: Stock ticker
            
        Returns:
            Company name if found
        """
        return self.ticker_to_company.get(ticker)


# Global instance
_ticker_mapper = None


def get_ticker_mapper() -> TickerMapper:
    """Get the global ticker mapper instance."""
    global _ticker_mapper
    if _ticker_mapper is None:
        _ticker_mapper = TickerMapper()
    return _ticker_mapper

