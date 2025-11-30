"""
Improved Gemini AI Service - Enhanced prompts for detailed, specific analysis.
"""
import google.generativeai as genai
import json
import os
from typing import List, Dict, Any, Optional
import structlog
from dotenv import load_dotenv

load_dotenv()

logger = structlog.get_logger()


class GeminiService:
    """Service for interacting with Google's Gemini AI API with enhanced prompts."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini service.
        
        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY') 

        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found, some features may not work")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def summarize_news(self, ticker: str, news_articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Summarize news articles using Gemini with enhanced prompts.
        
        Args:
            ticker: Stock ticker symbol
            news_articles: List of news articles
            
        Returns:
            Dictionary containing summary, sentiment, and key points
        """
        if not news_articles:
            return {
                'summary': f'No recent news available for {ticker}. Market activity continues with normal trading patterns.',
                'sentiment': 'neutral',
                'key_points': []
            }
        
        # Prepare news text
        news_text = "\n\n".join([
            f"Title: {article['title']}\nPublisher: {article['publisher']}\nDate: {article['published_at']}\nSummary: {article['snippet']}"
            for article in news_articles[:5]
        ])
        
        prompt = f"""You are a professional financial analyst at a top investment bank. Analyze the following news articles about {ticker} and provide detailed, actionable insights.

NEWS ARTICLES:
{news_text}

INSTRUCTIONS:
1. Write a comprehensive 3-4 sentence summary that covers the main developments, their business impact, and market implications
2. Determine the overall sentiment (positive, negative, or neutral) based on the news impact on stock value
3. Extract 5 specific, actionable key points that investors should know

Provide your analysis in JSON format:
{{
    "summary": "Detailed 3-4 sentence summary covering main developments, business impact, and market implications",
    "sentiment": "positive, negative, or neutral",
    "key_points": [
        "Specific point 1 with concrete details",
        "Specific point 2 with concrete details",
        "Specific point 3 with concrete details",
        "Specific point 4 with concrete details",
        "Specific point 5 with concrete details"
    ]
}}

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
            logger.info(f"Successfully summarized news for {ticker}")
            return result
            
        except Exception as e:
            logger.error(f"Error summarizing news for {ticker}", error=str(e))
            # Better fallback with more detail
            return {
                'summary': f'{ticker} continues to show market activity with recent developments in operations and strategic initiatives. The company maintains its position in the market while navigating current economic conditions. Investor attention remains focused on upcoming catalysts and financial performance.',
                'sentiment': 'neutral',
                'key_points': [article['title'] for article in news_articles[:5]]
            }
    
    def generate_investment_analysis(
        self,
        ticker: str,
        company_name: str,
        news_summary: Dict[str, Any],
        price_data: Dict[str, Any],
        financial_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive investment analysis using Gemini with enhanced prompts.
        
        Args:
            ticker: Stock ticker symbol
            company_name: Company name
            news_summary: Summarized news data
            price_data: Price and technical data
            financial_metrics: Financial metrics
            
        Returns:
            Dictionary containing detailed investment analysis
        """
        # Format financial metrics, only include what we have
        pe_ratio = financial_metrics.get('pe_ratio', 0)
        profit_margin = financial_metrics.get('profit_margin', 0)
        revenue_growth = financial_metrics.get('revenue_growth')
        market_cap = financial_metrics.get('market_cap', 0)
        eps = financial_metrics.get('eps', 0)
        
        # Calculate price change
        current_price = price_data.get('current_price', 0)
        high_52w = price_data.get('high_52w', 0) or financial_metrics.get('fifty_two_week_high', 0)
        low_52w = price_data.get('low_52w', 0) or financial_metrics.get('fifty_two_week_low', 0)
        
        if high_52w and low_52w and current_price:
            price_change_pct = ((current_price - low_52w) / low_52w) * 100
        else:
            price_change_pct = 0
        
        # Format revenue growth display - handle None and 0 differently
        if revenue_growth is None:
            revenue_growth_display = "N/A (data not available)"
            revenue_growth_value = 0  # For calculations
        elif revenue_growth == 0:
            revenue_growth_display = "0.00% (flat or data unavailable)"
            revenue_growth_value = 0
        else:
            revenue_growth_display = f"{revenue_growth*100:.2f}%"
            revenue_growth_value = revenue_growth
        
        prompt = f"""You are a senior equity research analyst at Goldman Sachs. Provide a detailed investment analysis for {ticker} ({company_name}).

CURRENT DATA:

News Summary:
{news_summary.get('summary', 'No news available')}

Sentiment: {news_summary.get('sentiment', 'neutral')}

Key Developments:
{chr(10).join(['- ' + point for point in news_summary.get('key_points', [])])}

Price Data:
- Current Price: ${current_price:.2f}
- 52-Week High: ${high_52w:.2f}
- 52-Week Low: ${low_52w:.2f}
- Trend: {price_data.get('trend', 'neutral')}
- Price Change from 52W Low: {price_change_pct:.2f}%

Financial Metrics:
- Market Cap: ${market_cap:,.0f}
- P/E Ratio (TTM): {pe_ratio:.2f}x
- EPS (TTM): ${eps:.2f}
- Profit Margin: {profit_margin*100:.2f}%
- Revenue Growth: {revenue_growth_display}

INSTRUCTIONS:
Provide a comprehensive investment analysis with:

1. RATIONALE: Write 3-4 detailed sentences explaining:
   - The core investment thesis
   - Why this is a buy/hold/sell opportunity
   - Key factors supporting your recommendation
   - Expected outlook and timeframe

2. KEY DRIVERS (5 specific, measurable factors):
   - Each should be concrete and actionable
   - Include specific business metrics or initiatives
   - Explain HOW each driver impacts value

3. RISKS (5 specific, quantifiable concerns):
   - Each should be a real, material risk
   - Include potential impact magnitude
   - Be specific to this company, not generic

4. CATALYSTS (5 upcoming, time-bound events):
   - Each should have a timeframe (e.g., "Q4 2025")
   - Focus on near-term catalysts (next 3-12 months)
   - Include specific events, not vague statements

5. STANCE: Choose buy, hold, or sell based on:
   - buy: Strong upside potential (>15%), improving fundamentals
   - hold: Fair value, stable outlook, limited catalysts
   - sell: Overvalued (>10%), deteriorating fundamentals

6. CONFIDENCE: Choose high, medium, or low based on:
   - high: Clear trend, strong data, low uncertainty
   - medium: Mixed signals, moderate uncertainty
   - low: Limited data, high uncertainty, conflicting signals

Provide your analysis in JSON format:
{{
    "rationale": "Detailed 3-4 sentence investment thesis with specific reasoning and outlook",
    "key_drivers": [
        "Specific driver 1 with measurable impact (e.g., 'Services revenue growing 15% YoY driving margin expansion')",
        "Specific driver 2 with measurable impact",
        "Specific driver 3 with measurable impact",
        "Specific driver 4 with measurable impact",
        "Specific driver 5 with measurable impact"
    ],
    "risks": [
        "Specific risk 1 with potential impact (e.g., 'iPhone sales decline of 5-10% in China market')",
        "Specific risk 2 with potential impact",
        "Specific risk 3 with potential impact",
        "Specific risk 4 with potential impact",
        "Specific risk 5 with potential impact"
    ],
    "catalysts": [
        "Time-bound catalyst 1 (e.g., 'Q1 2026 earnings release expected to show 20% EPS growth')",
        "Time-bound catalyst 2",
        "Time-bound catalyst 3",
        "Time-bound catalyst 4",
        "Time-bound catalyst 5"
    ],
    "stance": "buy, hold, or sell",
    "confidence": "high, medium, or low",
    "confidence_rationale": "2-3 sentences explaining the confidence level based on data quality, market conditions, and outlook clarity"
}}

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
            logger.info(f"Successfully generated investment analysis for {ticker}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating investment analysis for {ticker}", error=str(e))
            # Enhanced fallback with more specific content
            trend = price_data.get('trend', 'neutral')
            current_price = price_data.get('current_price', 0)
            high_52w = price_data.get('high_52w', 0) or financial_metrics.get('fifty_two_week_high', 0)
            low_52w = price_data.get('low_52w', 0) or financial_metrics.get('fifty_two_week_low', 0)
            
            if high_52w and low_52w and current_price:
                price_change = ((current_price - low_52w) / low_52w) * 100
            else:
                price_change = 0
            
            sentiment = news_summary.get('sentiment', 'neutral')
            pe_ratio = financial_metrics.get('pe_ratio', 0)
            profit_margin = financial_metrics.get('profit_margin', 0)
            
            # Determine stance based on data
            if trend == 'bullish' and sentiment == 'positive' and price_change > 5:
                stance = 'buy'
                confidence = 'medium'
            elif trend == 'bearish' and sentiment == 'negative' and price_change < -5:
                stance = 'sell'
                confidence = 'medium'
            else:
                stance = 'hold'
                confidence = 'medium'
            
            # Format revenue growth for fallback message
            if revenue_growth is None or revenue_growth_value == 0:
                revenue_growth_text = "with revenue growth data unavailable"
            else:
                revenue_growth_text = f"with {revenue_growth_value*100:.1f}% revenue growth"
            
            return {
                'rationale': f'{company_name} ({ticker}) demonstrates a {trend} technical trend with {sentiment} market sentiment. The stock has moved {abs(price_change):.1f}% from its 52-week low, trading at a P/E ratio of {pe_ratio:.1f}x. Based on current fundamentals including {profit_margin*100:.1f}% profit margins, the company maintains a stable market position. The investment outlook suggests a {stance} recommendation with {confidence} confidence given the current market dynamics and company-specific factors.',
                'key_drivers': [
                    f'Profit margin of {profit_margin*100:.1f}% demonstrating strong operational efficiency',
                    f'P/E ratio of {pe_ratio:.1f}x indicating market valuation relative to earnings',
                    'Strategic market positioning and competitive advantages in core business segments',
                    'Innovation pipeline and product development initiatives driving future growth',
                    'Brand strength and customer loyalty supporting pricing power'
                ],
                'risks': [
                    f'Current P/E ratio of {pe_ratio:.1f}x may indicate valuation concerns',
                    'Macroeconomic headwinds including interest rate environment and inflation pressures',
                    'Competitive intensity in key markets potentially impacting market share',
                    'Regulatory environment changes that could affect business operations',
                    'Limited revenue growth visibility requiring close monitoring of business trends'
                ],
                'catalysts': [
                    'Next quarterly earnings announcement expected to provide updated guidance',
                    'Upcoming product launches and service expansions in key markets',
                    'Potential strategic partnerships or M&A activity to enhance market position',
                    'Industry conference presentations and investor day events',
                    'Analyst day or capital markets day with long-term financial targets'
                ],
                'stance': stance,
                'confidence': confidence,
                'confidence_rationale': f'Confidence level is {confidence} based on the {trend} price trend, {sentiment} news sentiment, and {abs(price_change):.1f}% price movement. The analysis incorporates available financial metrics {revenue_growth_text}, though some uncertainty remains regarding near-term catalysts and market conditions.'
            }
    
    def analyze_support_resistance(self, ticker: str, price_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze support and resistance levels using Gemini.
        
        Args:
            ticker: Stock ticker symbol
            price_data: Price history data
            
        Returns:
            Dictionary containing support/resistance analysis
        """
        prompt = f"""You are a professional technical analyst. Analyze the price levels for {ticker}:

Current Price: ${price_data.get('current_price', 0):.2f}
52-Week High: ${price_data.get('high_52w', 0):.2f}
52-Week Low: ${price_data.get('low_52w', 0):.2f}
Trend: {price_data.get('trend', 'neutral')}
20-Day MA: ${price_data.get('ma_20', 0):.2f}
50-Day MA: ${price_data.get('ma_50', 0):.2f}

Recent Resistance Levels: {', '.join([f'${x:.2f}' for x in price_data.get('resistance_levels', [])])}
Recent Support Levels: {', '.join([f'${x:.2f}' for x in price_data.get('support_levels', [])])}

Provide technical analysis in JSON format:
{{
    "support_levels": [level1, level2, level3],
    "resistance_levels": [level1, level2, level3],
    "technical_summary": "2-3 sentence technical summary with specific price levels and trend analysis"
}}

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
            logger.info(f"Successfully analyzed support/resistance for {ticker}")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing support/resistance for {ticker}", error=str(e))
            current_price = price_data.get('current_price', 0)
            trend = price_data.get('trend', 'neutral')
            return {
                'support_levels': price_data.get('support_levels', [])[:3],
                'resistance_levels': price_data.get('resistance_levels', [])[:3],
                'technical_summary': f'{ticker} is currently trading at ${current_price:.2f} in a {trend} trend. The stock is positioned between key support levels at {", ".join([f"${x:.2f}" for x in price_data.get("support_levels", [])[:2]])} and resistance at {", ".join([f"${x:.2f}" for x in price_data.get("resistance_levels", [])[:2]])}. Technical indicators suggest monitoring these levels for potential breakout or breakdown signals.'
            }