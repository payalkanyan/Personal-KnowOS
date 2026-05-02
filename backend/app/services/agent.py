import operator
from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from app.core.config import settings
from app.services.agent_tools import search_personal_knowledge, search_live_web

# Define the state of the agent
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

# Define the tools
tools = [search_personal_knowledge, search_live_web]
tool_node = ToolNode(tools)

# Initialize the LLM (Gemini 2.5 Flash is excellent for this)
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.1
)
# Bind tools to the LLM so it knows they exist
bound_llm = llm.bind_tools(tools)

def should_continue(state: AgentState) -> str:
    """Determine if the agent should continue to tool execution or end."""
    messages = state["messages"]
    last_message = messages[-1]
    
    # If the LLM returned tool calls, we must execute them
    if last_message.tool_calls:
        return "continue"
    # Otherwise, it has produced a final answer
    return "end"

def call_model(state: AgentState):
    """Call the LLM with the current conversation history."""
    messages = state["messages"]
    response = bound_llm.invoke(messages)
    return {"messages": [response]}

# Build the LangGraph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("agent", call_model)
workflow.add_node("action", tool_node)

# Set the entrypoint
workflow.set_entry_point("agent")

# Add conditional edges from agent
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "action",
        "end": END
    }
)

# Loop back from tools to agent
workflow.add_edge("action", "agent")

# Compile the graph
agent_executor = workflow.compile()
