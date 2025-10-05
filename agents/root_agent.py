"""
Root Agent - Orchestrates specialized sub-agents
"""

from google.adk.agents.llm_agent import Agent
from google.adk.tools import agent_tool
from agents.kpi_agent import create_kpi_agent
from agents.metrics_agent import create_metrics_agent
from agents.trace_agent import create_trace_agent
from agents.failover_agent import create_failover_agent
from agents.deployment_agent import create_deployment_agent
from config.prompts import ROOT_AGENT_PROMPT

def create_root_agent() -> Agent:
    """
    Create and configure the root orchestration agent.
    
    Returns:
        Agent: Configured root agent with all sub-agents
    """
    
    # Create specialized sub-agents
    kpi_agent = create_kpi_agent()
    metrics_agent = create_metrics_agent()
    trace_agent = create_trace_agent()
    failover_agent = create_failover_agent()
    deployment_agent = create_deployment_agent()
    
    # Create root agent with sub-agents as tools
    root_agent = Agent(
        name="root_agent",
        model="gemini-2.0-flash-exp",
        description="Root agent responsible for orchestrating specialized SRE agents",
        instruction=ROOT_AGENT_PROMPT,
        tools=[
            agent_tool.AgentTool(agent=kpi_agent),
            agent_tool.AgentTool(agent=metrics_agent),
            agent_tool.AgentTool(agent=trace_agent),
            agent_tool.AgentTool(agent=failover_agent),
            agent_tool.AgentTool(agent=deployment_agent),
        ]
    )
    
    return root_agent
