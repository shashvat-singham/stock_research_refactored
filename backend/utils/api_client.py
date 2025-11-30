"""
API Client wrapper that works both in Manus environment and locally.
"""
import os
import sys
import requests
from typing import Dict, Any

# Try to import Manus API client if available
try:
    sys.path.append('/opt/.manus/.sandbox-runtime')
    from data_api import ApiClient as ManusApiClient
    MANUS_AVAILABLE = True
except ImportError:
    MANUS_AVAILABLE = False


class ApiClient:
    """
    Unified API client that works in both Manus and local environments.
    Falls back to direct HTTP requests when Manus API is not available.
    """
    
    def __init__(self):
        if MANUS_AVAILABLE:
            self.client = ManusApiClient()
            self.use_manus = True
        else:
            self.use_manus = False
    
    def call_api(self, endpoint: str, query: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Call an API endpoint.
        
        Args:
            endpoint: API endpoint (e.g., 'YahooFinance/get_stock_chart')
            query: Query parameters
            
        Returns:
            API response as dictionary
        """
        if self.use_manus:
            # Use Manus API client
            return self.client.call_api(endpoint, query=query)
        else:
            # Fallback to direct Yahoo Finance API calls
            return self._call_yahoo_finance_direct(endpoint, query)
    
    def _call_yahoo_finance_direct(self, endpoint: str, query: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Direct Yahoo Finance API calls for local development.
        
        Args:
            endpoint: API endpoint
            query: Query parameters
            
        Returns:
            API response
        """
        if query is None:
            query = {}
        
        # Map Manus endpoints to Yahoo Finance API endpoints
        if endpoint == 'YahooFinance/get_stock_chart':
            return self._get_stock_chart(query)
        elif endpoint == 'YahooFinance/get_stock_insights':
            return self._get_stock_insights(query)
        elif endpoint == 'YahooFinance/get_news':
            return self._get_news(query)
        else:
            raise NotImplementedError(f"Endpoint {endpoint} not implemented for local mode")
    
    def _get_stock_chart(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Get stock chart data from Yahoo Finance."""
        symbol = query.get('symbol', '')
        interval = query.get('interval', '1d')
        range_param = query.get('range', '1mo')
        
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        params = {
            'interval': interval,
            'range': range_param,
            'includeAdjustedClose': str(query.get('includeAdjustedClose', True)).lower()
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {'error': str(e)}
    
    def _get_stock_insights(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Get stock insights from Yahoo Finance."""
        symbol = query.get('symbol', '')
        
        url = f"https://query1.finance.yahoo.com/ws/insights/v2/finance/insights"
        params = {'symbol': symbol}
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {'error': str(e)}
    
    def _get_news(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Get news from Yahoo Finance."""
        # This endpoint is not publicly available, return empty news
        return {'news': []}

