from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
#from langchain.tools.render import format_tool_to_openai_tool
from langchain_core.utils.function_calling import convert_to_openai_tool
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing import TypedDict, Annotated, List
import operator
from . import tools
from langchain_tavily import TavilySearch
from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.tools import Tool
#from langchain_core.schema import ToolMessage  # or wherever you import it

load_dotenv()
args_schema = {
  "type": "object",
  "properties": {
    "pickup":      {"type": "string", "description": "Pickup location"},
    "destination": {"type": "string", "description": "Dropoff location"},
    "time":        {"type": "string", "description": "Pickup time, e.g. '15:30'"}
  },
  "required": ["pickup", "destination", "time"]
}

args_schema_create_ticket = {
  "type": "object",
  "properties": {
    "description": {"type": "string", "description": "Ticket Description"},
    "summary": {"type": "string", "description": "Ticket Summary"},
  },
  "required": ["description", "summary"]
}

# 1. Define the tools
searchtool = TavilySearch(max_results=2)
book_cab_tool = Tool.from_function(func=tools.book_cab, name="book_cab", description="Books a cab by specifying pickup, destination and time.",args_schema=args_schema)
create_ticket_tool = Tool.from_function(func=tools.create_ticket, name="create_ticket", description="Used for creating a ticket",args_schema=args_schema_create_ticket)

tool_executor = ToolNode([searchtool, book_cab_tool, create_ticket_tool])
#llm = ChatGroq(model="llama3-8b-8192")
llm = ChatGroq(temperature=0, model="llama-3.3-70b-versatile")

llm_with_tools = llm.bind(tools=[convert_to_openai_tool(t) for t in [searchtool,tools.book_cab, tools.create_ticket]])

# 2. Define the agent's state
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    # This will hold the details for the modal form if needed
    action_request: dict

# 3. Define the nodes of the graph

def should_continue(state: AgentState):
    """Decides the next step: call a tool, ask for info, or end."""
    last_message = state["messages"][-1]
    # If the LLM made a tool call
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        # Check if we have all arguments for the tool
        tool_call = last_message.tool_calls[0]
        tool_name = tool_call['name']
        all_args_present = all(arg in tool_call['args'] for arg in tool_executor.tools_by_name[tool_name].args)

        if all_args_present:
            return "call_tool"
        else:
            # Not all arguments are present, request them from the user
            return "request_info"
    # Otherwise, the conversation is over
    return END

def call_model(state: AgentState):
    """The primary node that calls the LLM."""
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
# Append the new AI response to the message list
    messages.append(response)
# Find the latest ToolMessage (if any)
    tool_message = None
    for msg in reversed(messages):
        if msg.type == "tool":  # or isinstance(msg, ToolMessage)
            tool_message = msg
        break

    return {
    "messages": [response, tool_message] if tool_message else [response]
    }
   # return {"messages": [response]}

# def call_tool(state: AgentState):
#     """Node that executes a tool and returns the result."""
#     last_message = state["messages"][-1]
#     tool_call = last_message.tool_calls[0]
#     action = {"tool": tool_call['name'], "tool_input": tool_call['args']}
    
#     response = tool_executor.invoke(action)
#     tool_message = ToolMessage(content=str(response), tool_call_id=tool_call['id'])
    
#     return {"messages": [tool_message]}

def call_tool(state: AgentState):
    last = state["messages"][-1]
    tool_call = last.tool_calls[0]
    name = tool_call["name"]
    args = tool_call["args"]

    # look up the actual python function behind that tool name
    tool_fn = tool_executor.tools_by_name[name].func
    result = tool_fn(**args)

    msg = ToolMessage(
      content=str(result),
      tool_call_id=tool_call["id"]
    )
    return {"messages": [msg]}

def request_info(state: AgentState):
    """Node that prepares a request for more information from the user."""
    last_message = state["messages"][-1]
    tool_call = last_message.tool_calls[0]
    tool_name = tool_call['name']
    # Get the required arguments for the tool from its signature
    required_args = list(tool_call['args'].keys())
    
    # Prepare the action request for the frontend
    action_request = {
        "action_required": True,
        "tool_name": tool_name,
        "required_fields": required_args,
    }
    return {"action_request": action_request}


# 4. Wire up the graph
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("action", call_tool)
workflow.add_node("request_info", request_info)

workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "call_tool": "action",
        "request_info": "request_info",
        END: END,
    },
)

workflow.add_edge("action", "agent")
workflow.add_edge("request_info", END) # Stop here and wait for frontend

# Compile the graph
app = workflow.compile()