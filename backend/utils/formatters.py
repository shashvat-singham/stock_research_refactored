"""
Formatting utilities for consistent data presentation.
"""
from typing import Any, Optional, Dict, List
from decimal import Decimal, ROUND_HALF_UP


def format_decimal(value: Any, decimal_places: int = 2) -> Optional[float]:
    """
    Format a numeric value to a specific number of decimal places.
    
    Args:
        value: Numeric value to format
        decimal_places: Number of decimal places (default: 2)
        
    Returns:
        Formatted float value or None if value is None/invalid
    """
    if value is None:
        return None
    
    try:
        # Convert to Decimal for precise rounding
        decimal_value = Decimal(str(value))
        
        # Create quantizer for desired decimal places
        quantizer = Decimal('0.1') ** decimal_places
        
        # Round and convert back to float
        rounded = float(decimal_value.quantize(quantizer, rounding=ROUND_HALF_UP))
        
        return rounded
    
    except (ValueError, TypeError, ArithmeticError):
        return None


def format_price(price: Any) -> Optional[float]:
    """
    Format a price value to 2 decimal places.
    
    Args:
        price: Price value
        
    Returns:
        Formatted price or None
    """
    return format_decimal(price, 2)


def format_percentage(value: Any) -> Optional[float]:
    """
    Format a percentage value to 2 decimal places.
    
    Args:
        value: Percentage value
        
    Returns:
        Formatted percentage or None
    """
    return format_decimal(value, 2)


def format_ratio(ratio: Any) -> Optional[float]:
    """
    Format a ratio value to 2 decimal places.
    
    Args:
        ratio: Ratio value (e.g., P/E ratio)
        
    Returns:
        Formatted ratio or None
    """
    return format_decimal(ratio, 2)


def format_market_cap(market_cap: Any) -> Optional[float]:
    """
    Format market cap to 2 decimal places (in billions).
    
    Args:
        market_cap: Market cap value
        
    Returns:
        Formatted market cap or None
    """
    return format_decimal(market_cap, 2)


def format_financial_dict(data: Dict[str, Any], keys_to_format: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Format all numeric values in a dictionary to 2 decimal places.
    
    Args:
        data: Dictionary with financial data
        keys_to_format: Specific keys to format (if None, formats all numeric values)
        
    Returns:
        Dictionary with formatted values
    """
    formatted_data = data.copy()
    
    # Common financial keys that should be formatted
    default_keys = [
        'price', 'current_price', 'open_price', 'close_price', 'high', 'low',
        'pe_ratio', 'pb_ratio', 'ps_ratio', 'peg_ratio',
        'market_cap', 'enterprise_value', 'revenue', 'net_income',
        'eps', 'dividend_yield', 'beta',
        'fifty_two_week_high', 'fifty_two_week_low',
        'change', 'change_percent', 'volume'
    ]
    
    keys = keys_to_format if keys_to_format is not None else default_keys
    
    for key in keys:
        if key in formatted_data and isinstance(formatted_data[key], (int, float, Decimal)):
            formatted_data[key] = format_decimal(formatted_data[key])
    
    return formatted_data


def format_ticker_insight(insight: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format all numeric fields in a ticker insight to 2 decimal places.
    
    Args:
        insight: Ticker insight dictionary
        
    Returns:
        Formatted ticker insight
    """
    formatted = insight.copy()
    
    # Format price and market data
    if 'current_price' in formatted:
        formatted['current_price'] = format_price(formatted['current_price'])
    
    if 'market_cap' in formatted:
        formatted['market_cap'] = format_market_cap(formatted['market_cap'])
    
    if 'pe_ratio' in formatted:
        formatted['pe_ratio'] = format_ratio(formatted['pe_ratio'])
    
    if 'fifty_two_week_high' in formatted:
        formatted['fifty_two_week_high'] = format_price(formatted['fifty_two_week_high'])
    
    if 'fifty_two_week_low' in formatted:
        formatted['fifty_two_week_low'] = format_price(formatted['fifty_two_week_low'])
    
    # Format support and resistance levels
    if 'support_levels' in formatted and isinstance(formatted['support_levels'], list):
        formatted['support_levels'] = [
            format_price(level) for level in formatted['support_levels']
            if level is not None
        ]
    
    if 'resistance_levels' in formatted and isinstance(formatted['resistance_levels'], list):
        formatted['resistance_levels'] = [
            format_price(level) for level in formatted['resistance_levels']
            if level is not None
        ]
    
    return formatted


def format_analysis_response(**kwargs) -> Dict[str, Any]:
    """
    Format all numeric fields in an analysis response to 2 decimal places.
    
    Args:
        **kwargs: Analysis response fields (request_id, query, insights, started_at, total_latency_ms, etc.)
        
    Returns:
        Formatted analysis response as a dictionary
    """
    from backend.app.models import AnalysisResponse
    from datetime import datetime
    
    # Format total latency
    total_latency_ms = kwargs.get('total_latency_ms', 0)
    if total_latency_ms:
        total_latency_ms = format_decimal(total_latency_ms, 2)
    
    # Format insights
    insights = kwargs.get('insights', [])
    if isinstance(insights, list):
        formatted_insights = [
            format_ticker_insight(insight) if hasattr(insight, 'ticker') else insight
            for insight in insights
        ]
    else:
        formatted_insights = []
    
    # Extract tickers and agents from insights
    tickers_analyzed = [insight.ticker if hasattr(insight, 'ticker') else insight.get('ticker', '') for insight in insights]
    agents_used = list(set(
        trace.agent_type if hasattr(trace, 'agent_type') else trace.get('agent_type', '')
        for insight in insights
        for trace in (insight.agent_traces if hasattr(insight, 'agent_traces') else insight.get('agent_traces', []))
    ))
    
    # Create the response model
    return AnalysisResponse(
        request_id=kwargs.get('request_id', ''),
        query=kwargs.get('query', ''),
        insights=formatted_insights,
        cross_ticker_analysis=kwargs.get('cross_ticker_analysis'),
        total_latency_ms=total_latency_ms,
        tickers_analyzed=tickers_analyzed,
        agents_used=agents_used,
        success=kwargs.get('success', True),
        warnings=kwargs.get('warnings', []),
        errors=kwargs.get('errors', []),
        needs_confirmation=kwargs.get('needs_confirmation', False),
        confirmation_prompt=kwargs.get('confirmation_prompt'),
        started_at=kwargs.get('started_at', datetime.now()),
        completed_at=kwargs.get('completed_at', datetime.now())
    )


def format_json_response(data: Any) -> Any:
    """
    Recursively format all numeric values in a JSON-serializable structure.
    
    Args:
        data: Data structure to format
        
    Returns:
        Formatted data structure
    """
    if isinstance(data, dict):
        return {key: format_json_response(value) for key, value in data.items()}
    
    elif isinstance(data, list):
        return [format_json_response(item) for item in data]
    
    elif isinstance(data, (int, float, Decimal)):
        # Only format floats and Decimals, keep integers as-is
        if isinstance(data, int):
            return data
        return format_decimal(data, 2)
    
    else:
        return data

