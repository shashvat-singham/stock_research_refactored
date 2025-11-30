"""
Synthesis Agent - Combines research findings into actionable insights and investment stances.
"""
import asyncio
from datetime import datetime
from typing import Dict, Any, List
import structlog

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from backend.app.models import (
    TickerInsight, 
    AgentTrace, 
    SourceInfo,
    StanceType,
    ConfidenceLevel
)

logger = structlog.get_logger()


class SynthesisAgent:
    """
    Agent responsible for synthesizing research findings from all agents
    into actionable insights and investment recommendations.
    """
    
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
    
    async def synthesize(
        self, 
        ticker: str, 
        agent_results: Dict[str, Dict[str, Any]], 
        query: str
    ) -> TickerInsight:
        """
        Synthesize research findings into a comprehensive ticker insight.
        
        Args:
            ticker: Stock ticker symbol
            agent_results: Results from all research agents
            query: Original user query
            
        Returns:
            TickerInsight with comprehensive analysis and recommendation
        """
        logger.info("Synthesizing insights", ticker=ticker)
        
        try:
            # Extract all findings and sources
            all_findings = self._extract_findings(agent_results)
            all_sources = self._extract_sources(agent_results)
            agent_traces = self._extract_traces(agent_results)
            
            # Generate comprehensive analysis
            analysis = await self._generate_analysis(ticker, all_findings, query)
            
            # Extract structured insights
            summary = analysis.get("summary", "")
            key_drivers = analysis.get("key_drivers", [])
            risks = analysis.get("risks", [])
            catalysts = analysis.get("catalysts", [])
            
            # Generate investment recommendation
            recommendation = await self._generate_recommendation(ticker, analysis, all_findings)
            
            stance = self._parse_stance(recommendation.get("stance", "hold"))
            confidence = self._parse_confidence(recommendation.get("confidence", "medium"))
            rationale = recommendation.get("rationale", "")
            
            # Get company name if available
            company_name = self._extract_company_name(all_findings)
            
            # Create the insight
            insight = TickerInsight(
                ticker=ticker,
                company_name=company_name,
                summary=summary,
                key_drivers=key_drivers,
                risks=risks,
                catalysts=catalysts,
                stance=stance,
                confidence=confidence,
                rationale=rationale,
                sources=all_sources,
                agent_traces=agent_traces,
                analysis_timestamp=datetime.now()
            )
            
            logger.info("Synthesis completed", 
                       ticker=ticker,
                       stance=stance.value,
                       confidence=confidence.value)
            
            return insight
            
        except Exception as e:
            logger.error("Synthesis failed", ticker=ticker, error=str(e))
            
            # Return a basic insight with error information
            return TickerInsight(
                ticker=ticker,
                summary=f"Analysis failed: {str(e)}",
                key_drivers=[],
                risks=[f"Analysis error: {str(e)}"],
                catalysts=[],
                stance=StanceType.HOLD,
                confidence=ConfidenceLevel.LOW,
                rationale="Unable to complete analysis due to technical issues",
                sources=[],
                agent_traces=[],
                analysis_timestamp=datetime.now()
            )
    
    def _extract_findings(self, agent_results: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract all findings from agent results."""
        all_findings = []
        
        for agent_name, result in agent_results.items():
            if "error" in result:
                continue
                
            findings = result.get("findings", [])
            for finding in findings:
                finding["agent"] = agent_name
                all_findings.append(finding)
        
        return all_findings
    
    def _extract_sources(self, agent_results: Dict[str, Dict[str, Any]]) -> List[SourceInfo]:
        """Extract all sources from agent results."""
        all_sources = []
        seen_urls = set()
        
        for agent_name, result in agent_results.items():
            if "error" in result:
                continue
                
            sources = result.get("sources", [])
            for source_data in sources:
                if isinstance(source_data, dict):
                    url = source_data.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        source = SourceInfo(
                            url=url,
                            title=source_data.get("title"),
                            published_at=source_data.get("published_at"),
                            snippet=source_data.get("snippet")
                        )
                        all_sources.append(source)
        
        return all_sources
    
    def _extract_traces(self, agent_results: Dict[str, Dict[str, Any]]) -> List[AgentTrace]:
        """Extract agent execution traces."""
        traces = []
        
        for agent_name, result in agent_results.items():
            trace_data = result.get("trace")
            if trace_data and isinstance(trace_data, AgentTrace):
                traces.append(trace_data)
        
        return traces
    
    async def _generate_analysis(
        self, 
        ticker: str, 
        findings: List[Dict[str, Any]], 
        query: str
    ) -> Dict[str, Any]:
        """Generate comprehensive analysis from all findings."""
        
        # Prepare findings summary
        findings_text = self._format_findings_for_analysis(findings)
        
        analysis_prompt = f"""
        Analyze the following research findings for {ticker} and provide a comprehensive assessment:
        
        Original Query: {query}
        
        Research Findings:
        {findings_text}
        
        Please provide a structured analysis in the following format:
        
        SUMMARY:
        [2-3 sentence executive summary of the key findings]
        
        KEY_DRIVERS:
        - [List 3-5 key growth drivers or positive factors]
        
        RISKS:
        - [List 3-5 key risks or negative factors]
        
        CATALYSTS:
        - [List 2-4 upcoming catalysts or events that could impact the stock]
        
        Focus on the most material and actionable insights. Be specific and cite key findings.
        """
        
        messages = [
            SystemMessage(content=self._get_analysis_system_prompt()),
            HumanMessage(content=analysis_prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return self._parse_analysis_response(response.content)
    
    async def _generate_recommendation(
        self, 
        ticker: str, 
        analysis: Dict[str, Any], 
        findings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate investment recommendation and stance."""
        
        recommendation_prompt = f"""
        Based on the following analysis for {ticker}, provide an investment recommendation:
        
        Summary: {analysis.get('summary', '')}
        Key Drivers: {', '.join(analysis.get('key_drivers', []))}
        Risks: {', '.join(analysis.get('risks', []))}
        Catalysts: {', '.join(analysis.get('catalysts', []))}
        
        Provide your recommendation in the following format:
        
        STANCE: [BUY/HOLD/SELL]
        CONFIDENCE: [HIGH/MEDIUM/LOW]
        RATIONALE: [2-3 sentences explaining the reasoning for your stance and confidence level]
        
        Consider the 3-6 month investment horizon and balance the positive drivers against the risks.
        """
        
        messages = [
            SystemMessage(content=self._get_recommendation_system_prompt()),
            HumanMessage(content=recommendation_prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return self._parse_recommendation_response(response.content)
    
    def _format_findings_for_analysis(self, findings: List[Dict[str, Any]]) -> str:
        """Format findings for analysis prompt."""
        if not findings:
            return "No significant findings available."
        
        formatted = []
        for finding in findings:
            agent = finding.get("agent", "unknown")
            observation = finding.get("observation", "")
            formatted.append(f"[{agent.upper()}] {observation}")
        
        return "\n".join(formatted)
    
    def _get_analysis_system_prompt(self) -> str:
        """Get system prompt for analysis generation."""
        return """
        You are a senior financial analyst with expertise in equity research and investment analysis.
        Your role is to synthesize research findings from multiple sources into clear, actionable insights.
        
        Guidelines:
        - Be objective and balanced in your analysis
        - Focus on material factors that could impact stock performance
        - Prioritize recent and credible information
        - Consider both fundamental and technical factors
        - Be specific and avoid generic statements
        - Cite key findings when making assertions
        """
    
    def _get_recommendation_system_prompt(self) -> str:
        """Get system prompt for recommendation generation."""
        return """
        You are an investment analyst providing stock recommendations for a 3-6 month time horizon.
        
        Guidelines for recommendations:
        - BUY: Strong positive catalysts, limited downside risk, compelling risk/reward
        - HOLD: Balanced outlook, fair valuation, mixed signals
        - SELL: Significant risks, negative catalysts, poor risk/reward
        
        Confidence levels:
        - HIGH: Strong conviction based on multiple confirming factors
        - MEDIUM: Reasonable conviction with some uncertainty
        - LOW: Limited conviction due to conflicting signals or insufficient data
        
        Be conservative and realistic in your assessments.
        """
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parse the structured analysis response."""
        analysis = {
            "summary": "",
            "key_drivers": [],
            "risks": [],
            "catalysts": []
        }
        
        current_section = None
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('SUMMARY:'):
                current_section = 'summary'
                analysis['summary'] = line.replace('SUMMARY:', '').strip()
            elif line.startswith('KEY_DRIVERS:'):
                current_section = 'key_drivers'
            elif line.startswith('RISKS:'):
                current_section = 'risks'
            elif line.startswith('CATALYSTS:'):
                current_section = 'catalysts'
            elif line.startswith('- ') and current_section in ['key_drivers', 'risks', 'catalysts']:
                item = line.replace('- ', '').strip()
                analysis[current_section].append(item)
            elif current_section == 'summary' and not line.startswith(('KEY_DRIVERS:', 'RISKS:', 'CATALYSTS:')):
                analysis['summary'] += ' ' + line
        
        return analysis
    
    def _parse_recommendation_response(self, response: str) -> Dict[str, Any]:
        """Parse the recommendation response."""
        recommendation = {
            "stance": "hold",
            "confidence": "medium",
            "rationale": ""
        }
        
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('STANCE:'):
                stance = line.replace('STANCE:', '').strip().lower()
                recommendation['stance'] = stance
            elif line.startswith('CONFIDENCE:'):
                confidence = line.replace('CONFIDENCE:', '').strip().lower()
                recommendation['confidence'] = confidence
            elif line.startswith('RATIONALE:'):
                rationale = line.replace('RATIONALE:', '').strip()
                recommendation['rationale'] = rationale
        
        return recommendation
    
    def _parse_stance(self, stance_str: str) -> StanceType:
        """Parse stance string to StanceType enum."""
        stance_str = stance_str.lower().strip()
        
        if stance_str in ['buy', 'strong buy']:
            return StanceType.BUY
        elif stance_str in ['sell', 'strong sell']:
            return StanceType.SELL
        else:
            return StanceType.HOLD
    
    def _parse_confidence(self, confidence_str: str) -> ConfidenceLevel:
        """Parse confidence string to ConfidenceLevel enum."""
        confidence_str = confidence_str.lower().strip()
        
        if confidence_str == 'high':
            return ConfidenceLevel.HIGH
        elif confidence_str == 'low':
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.MEDIUM
    
    def _extract_company_name(self, findings: List[Dict[str, Any]]) -> str:
        """Extract company name from findings if available."""
        # Simple extraction - in a real implementation, you'd use more sophisticated methods
        for finding in findings:
            observation = finding.get("observation", "")
            # Look for patterns like "Company Name (TICKER)" or "TICKER Company"
            # This is a simplified approach
            pass
        
        return None
