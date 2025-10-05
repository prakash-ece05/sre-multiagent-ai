"""
Root Agent and Sub-Agents Configuration
Complete agent setup for SRE Multi-Agent AI System
"""

from google.adk.sessions import InMemorySessionsService
from google.adk.runners import Runner
from google.adk.agents.llm_agent import Agent
from google.genai import types as genai_types  # For formatting messages for ADK
from google.adk.tools.tool_context import ToolContext  # For accessing session state in tools
from google.adk.tools import agent_tool
from dotenv import load_dotenv

# Import tools
from tools.failover_tools import failover_service, get_service_backends
from tools.trace_tools import fetch_traceid_by_service
from tools.kpi_tools import get_business_kpis, get_performance_kpis, get_resource_utilization, compare_with_baseline
from tools.metrics_tools import (
    get_success_rate_for_service,
    get_p95_latency_for_service,
    get_p90_latency_for_service,
    get_volume_for_service
)
from tools.deployment_tools import (
    get_recent_deployments,
    get_deployment_details,
    check_deployment_status
)

# Load environment variables
load_dotenv()  # Fixed: proper capitalization

# Root agent prompt
ROOT_PROMPT = """
You are a SRE Conversational AI Agent.
Please follow these steps to accomplish the task at hand.

<Greetings>
1. Greet the user in a cheerful way. Use your tools to best answer the user's questions.
2. Route questions to the appropriate specialized agents based on the query type.
3. Provide clear, actionable responses with relevant metrics and insights.
</Greetings>
"""

# Create specialized sub-agents

deployment_agent = Agent(
    name="deployment_agent",
    model="gemini-2.0-flash-exp",
    description="Agent to answer questions regarding service deployments",
    instruction=(
        "You are the deployment agent responsible for tracking and analyzing service deployments. "
        "Provide deployment history, correlate deployments with incidents, and identify potential deployment-related issues."
    ),
    tools=[
        get_recent_deployments,
        get_deployment_details,
        check_deployment_status
    ]
)

kpi_agent = Agent(
    name="kpi_agent",
    model="gemini-2.0-flash-exp",
    description="Agent to answer KPI related questions for applications and services",
    instruction=(
        "You are the KPI agent responsible for analyzing business and performance KPIs. "
        "When the user requests KPI data, fetch metrics including volume, success rate, latency, and failure rate. "
        "Format results clearly showing current performance and comparison with baselines. "
        "Highlight any degradations or improvements."
    ),
    tools=[
        get_business_kpis,
        get_performance_kpis,
        get_resource_utilization,
        compare_with_baseline
    ]
)

failover_agent = Agent(
    name="failover_agent",
    model="gemini-2.0-flash-exp",
    description="Agent responsible for managing routing and failover for services",
    instruction=(
        "You are the failover agent. When a user requests to update routing, interpret the input flexibly. "
        "If the input format is not strictly followed, attempt to parse it intelligently. "
        "ALWAYS check backend health before executing failover. "
        "ALWAYS verify that weights sum to 100%. "
        "Provide clear confirmation of configuration changes and emphasize safety checks."
    ),
    tools=[
        failover_service,
        get_service_backends
    ]
)

metrics_agent = Agent(
    name="metrics_agent",
    model="gemini-2.0-flash-exp",
    description="Agent to analyze VALE metrics (Volume, Availability, Latency, Errors)",
    instruction=(
        "You are the metrics agent responsible for analyzing performance metrics. "
        "If the user asks for metric details, provide consolidated results across all backends. "
        "If a specific backend is requested, provide only that backend's metrics. "
        "Highlight any concerning trends or anomalies in the data."
    ),
    tools=[
        get_success_rate_for_service,
        get_p95_latency_for_service,
        get_p90_latency_for_service,
        get_volume_for_service
    ]
)

trace_agent = Agent(
    name="trace_agent",
    model="gemini-2.0-flash-exp",
    description="Agent responsible for gathering and analyzing distributed traces",
    instruction=(
        "You are the trace agent, responsible for gathering traces for specific services. "
        "Help users identify slow traces, error traces, and latency hotspots. "
        "Provide trace IDs for further investigation and summarize key findings."
    ),
    tools=[fetch_traceid_by_service]
)

# Create root agent with all sub-agents
root_agent = Agent(
    name="root_agent",
    model="gemini-2.0-flash-exp",
    description="Root agent responsible for orchestrating specialized SRE agents",
    instruction=ROOT_PROMPT,  # Fixed: lowercase 'instruction'
    tools=[
        agent_tool.AgentTool(agent=deployment_agent),
        agent_tool.AgentTool(agent=kpi_agent),
        agent_tool.AgentTool(agent=metrics_agent),
        agent_tool.AgentTool(agent=trace_agent),
        agent_tool.AgentTool(agent=failover_agent),
    ]
)

def create_root_agent() -> Agent:
    """
    Factory function to create and return the root agent.
    
    Returns:
        Agent: Configured root agent with all sub-agents
    """
    return root_agent
