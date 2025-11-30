"""
Base Research Agent - Implements the ReAct (Reason-Act-Observe) pattern.
"""
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional
import structlog

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from backend.app.models import AgentStep, AgentTrace, SourceInfo
from backend.tools.base_tool import BaseTool

logger = structlog.get_logger()


class BaseResearchAgent(ABC):
    """
    Base class for all research agents implementing the ReAct pattern.
    
    Each agent follows the Reason-Act-Observe loop:
    1. Reason: Think about what to do next
    2. Act: Use a tool to gather information
    3. Observe: Process the results and decide whether to continue
    """
    
    def __init__(self, llm: BaseChatModel, agent_type: str):
        self.llm = llm
        self.agent_type = agent_type
        self.tools = self._initialize_tools()
        
    @abstractmethod
    def _initialize_tools(self) -> List[BaseTool]:
        """Initialize the tools available to this agent."""
        pass
    
    @abstractmethod
    def _get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        pass
    
    async def research(
        self, 
        ticker: str, 
        query: str, 
        max_iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Run the research process for a given ticker.
        
        Args:
            ticker: Stock ticker symbol
            query: Original user query
            max_iterations: Maximum number of ReAct iterations
            
        Returns:
            Dictionary containing research results and execution trace
        """
        start_time = time.time()
        
        logger.info("Starting research", 
                   agent_type=self.agent_type,
                   ticker=ticker,
                   max_iterations=max_iterations)
        
        # Initialize trace
        trace = AgentTrace(
            agent_type=self.agent_type,
            ticker=ticker,
            steps=[],
            success=False
        )
        
        # Initialize context
        context = {
            "ticker": ticker,
            "query": query,
            "findings": [],
            "sources": [],
            "iteration": 0
        }
        
        try:
            # Run ReAct loop
            for iteration in range(max_iterations):
                context["iteration"] = iteration + 1
                
                logger.info("Starting ReAct iteration", 
                           agent_type=self.agent_type,
                           ticker=ticker,
                           iteration=iteration + 1)
                
                step_start_time = time.time()
                
                # REASON: Think about what to do next
                thought = await self._reason(context, trace.steps)
                
                # Check if agent thinks it's done
                if self._is_done(thought):
                    logger.info("Agent decided to stop", 
                               agent_type=self.agent_type,
                               ticker=ticker,
                               iteration=iteration + 1)
                    break
                
                # ACT: Choose and execute a tool
                action, action_input = await self._act(thought, context)
                
                # Execute the action
                observation, sources = await self._execute_action(action, action_input, ticker)
                
                # Update context with new findings
                context["findings"].append({
                    "thought": thought,
                    "action": action,
                    "observation": observation,
                    "sources": sources
                })
                context["sources"].extend(sources)
                
                # Record the step
                step_latency = (time.time() - step_start_time) * 1000
                step = AgentStep(
                    step_number=iteration + 1,
                    thought=thought,
                    action=f"{action}: {action_input}",
                    observation=observation,
                    sources=sources,
                    latency_ms=step_latency
                )
                trace.steps.append(step)
                
                logger.info("Completed ReAct step", 
                           agent_type=self.agent_type,
                           ticker=ticker,
                           iteration=iteration + 1,
                           latency_ms=step_latency)
            
            # Mark as successful
            trace.success = True
            
            # Calculate total latency
            total_latency = (time.time() - start_time) * 1000
            trace.total_latency_ms = total_latency
            
            logger.info("Research completed", 
                       agent_type=self.agent_type,
                       ticker=ticker,
                       total_latency_ms=total_latency,
                       steps_count=len(trace.steps))
            
            return {
                "trace": trace,
                "findings": context["findings"],
                "sources": context["sources"],
                "summary": await self._summarize_findings(context)
            }
            
        except Exception as e:
            logger.error("Research failed", 
                        agent_type=self.agent_type,
                        ticker=ticker,
                        error=str(e))
            
            trace.success = False
            trace.error_message = str(e)
            trace.total_latency_ms = (time.time() - start_time) * 1000
            
            return {
                "trace": trace,
                "error": str(e),
                "findings": context.get("findings", []),
                "sources": context.get("sources", [])
            }
    
    async def _reason(self, context: Dict[str, Any], previous_steps: List[AgentStep]) -> str:
        """
        Reason about what to do next based on the current context.
        
        Args:
            context: Current research context
            previous_steps: Previous steps taken
            
        Returns:
            Thought about what to do next
        """
        # Build the reasoning prompt
        system_prompt = self._get_system_prompt()
        
        # Create context summary
        context_summary = f"""
        Ticker: {context['ticker']}
        Original Query: {context['query']}
        Current Iteration: {context['iteration']}
        
        Previous Findings:
        {self._format_findings(context['findings'])}
        
        Available Tools:
        {self._format_tools()}
        """
        
        if previous_steps:
            context_summary += f"\n\nPrevious Steps:\n{self._format_previous_steps(previous_steps)}"
        
        reasoning_prompt = f"""
        {context_summary}
        
        Think step by step about what you should do next to gather relevant information about {context['ticker']} 
        related to the query: "{context['query']}"
        
        If you have gathered sufficient information, respond with "DONE: [brief summary]"
        Otherwise, explain what specific information you need to gather next and which tool would be best to use.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=reasoning_prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content.strip()
    
    async def _act(self, thought: str, context: Dict[str, Any]) -> tuple[str, str]:
        """
        Choose an action based on the reasoning.
        
        Args:
            thought: The agent's reasoning
            context: Current research context
            
        Returns:
            Tuple of (action_name, action_input)
        """
        # Simple action selection based on keywords in the thought
        # In a more sophisticated implementation, you'd use the LLM to parse the thought
        
        thought_lower = thought.lower()
        ticker = context['ticker']
        
        # Default to web search if no specific tool is mentioned
        action = "web_search"
        action_input = f"{ticker} stock analysis news"
        
        # Check for specific tool mentions
        for tool in self.tools:
            if tool.name.lower() in thought_lower:
                action = tool.name
                action_input = f"{ticker}"
                break
        
        # Customize action input based on the thought
        if "news" in thought_lower or "recent" in thought_lower:
            action_input = f"{ticker} recent news earnings"
        elif "filing" in thought_lower or "sec" in thought_lower:
            action_input = f"{ticker} SEC filings 10-K 10-Q"
        elif "earnings" in thought_lower or "transcript" in thought_lower:
            action_input = f"{ticker} earnings call transcript"
        elif "insider" in thought_lower or "ownership" in thought_lower:
            action_input = f"{ticker} insider trading ownership"
        elif "patent" in thought_lower or "research" in thought_lower:
            action_input = f"{ticker} patents research papers"
        elif "price" in thought_lower or "technical" in thought_lower:
            action_input = f"{ticker} stock price technical analysis"
        
        return action, action_input
    
    async def _execute_action(
        self, 
        action: str, 
        action_input: str, 
        ticker: str
    ) -> tuple[str, List[SourceInfo]]:
        """
        Execute the chosen action using the appropriate tool.
        
        Args:
            action: Name of the action/tool to use
            action_input: Input for the action
            ticker: Stock ticker
            
        Returns:
            Tuple of (observation, sources)
        """
        # Find the tool
        tool = None
        for t in self.tools:
            if t.name == action:
                tool = t
                break
        
        if not tool:
            # Fallback to first available tool
            tool = self.tools[0] if self.tools else None
            
        if not tool:
            return "No tools available", []
        
        try:
            # Execute the tool
            result = await tool.execute(action_input, ticker)
            
            # Extract observation and sources
            if isinstance(result, dict):
                observation = result.get("observation", str(result))
                sources_data = result.get("sources", [])
                
                # Convert sources to SourceInfo objects
                sources = []
                for source_data in sources_data:
                    if isinstance(source_data, dict):
                        source = SourceInfo(
                            url=source_data.get("url", ""),
                            title=source_data.get("title"),
                            published_at=source_data.get("published_at"),
                            snippet=source_data.get("snippet")
                        )
                        sources.append(source)
                
                return observation, sources
            else:
                return str(result), []
                
        except Exception as e:
            logger.error("Tool execution failed", 
                        tool=action, 
                        ticker=ticker, 
                        error=str(e))
            return f"Tool execution failed: {str(e)}", []
    
    def _is_done(self, thought: str) -> bool:
        """Check if the agent thinks it's done."""
        return thought.upper().startswith("DONE:")
    
    async def _summarize_findings(self, context: Dict[str, Any]) -> str:
        """Summarize the research findings."""
        if not context["findings"]:
            return "No significant findings."
        
        findings_text = "\n".join([
            f"- {finding['observation']}" 
            for finding in context["findings"]
        ])
        
        summary_prompt = f"""
        Summarize the following research findings for {context['ticker']}:
        
        {findings_text}
        
        Provide a concise summary highlighting the most important insights.
        """
        
        messages = [
            SystemMessage(content="You are a financial research analyst. Provide clear, concise summaries."),
            HumanMessage(content=summary_prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content.strip()
    
    def _format_findings(self, findings: List[Dict[str, Any]]) -> str:
        """Format findings for display."""
        if not findings:
            return "None yet."
        
        formatted = []
        for i, finding in enumerate(findings, 1):
            formatted.append(f"{i}. {finding['observation']}")
        
        return "\n".join(formatted)
    
    def _format_tools(self) -> str:
        """Format available tools for display."""
        if not self.tools:
            return "No tools available."
        
        formatted = []
        for tool in self.tools:
            formatted.append(f"- {tool.name}: {tool.description}")
        
        return "\n".join(formatted)
    
    def _format_previous_steps(self, steps: List[AgentStep]) -> str:
        """Format previous steps for display."""
        if not steps:
            return "None."
        
        formatted = []
        for step in steps:
            formatted.append(f"Step {step.step_number}: {step.thought} -> {step.action} -> {step.observation[:100]}...")
        
        return "\n".join(formatted)
