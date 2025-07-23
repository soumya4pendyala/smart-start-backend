from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict

from src.agent import app as langgraph_app
from langchain_core.messages import HumanMessage
from fastapi.middleware.cors import CORSMiddleware

# Use a dictionary to store conversation states by session_id
conversations = {}

api = FastAPI()

# Allow requests from your React app's origin
api.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    sessionId: str
    tool_values: Optional[Dict] = None

@api.post("/chat")
def chat(request: ChatRequest):
    session_id = request.sessionId
    
    # Get the conversation history for this session
    current_state = conversations.get(session_id, {"messages": [], "action_request": None})

    # If the user submitted form data, use it to fulfill the last tool call
    if request.tool_values and current_state.get("action_request"):
        last_action_request = current_state["action_request"]
        tool_name = last_action_request['tool_name']
        
        # We need to find the last AI message with the incomplete tool call
        last_ai_message_idx = -1
        for i, msg in reversed(list(enumerate(current_state["messages"]))):
            if hasattr(msg, "tool_calls"):
                last_ai_message_idx = i
                break
        
        # Update the tool call with the new values from the form
        if last_ai_message_idx != -1:
            tool_call = current_state["messages"][last_ai_message_idx].tool_calls[0]
            tool_call['args'] = request.tool_values
            
            # Now, we can run the graph from the `action` state
            inputs = {"messages": [HumanMessage(content=request.message)], "action_request": None}
            current_state["messages"].append(HumanMessage(content=request.message))
            
            final_state = langgraph_app.invoke(inputs)
            conversations[session_id] = final_state # Update session state
            
            # The last message should be the result from the tool
            return {"response": final_state["messages"][-1].content}

    # Normal message processing
    inputs = {"messages": [HumanMessage(content=request.message)], "action_request": None}


    final_state = langgraph_app.invoke(inputs, config={"recursion_limit": 5})
    
    # Save the updated state
    conversations[session_id] = final_state

    # Check if the agent is requesting more information
    if final_state.get("action_request") and final_state["action_request"]["action_required"]:
        return final_state["action_request"]
    else:
        # Return the latest message from the bot
        return {"response": final_state["messages"][-1].content}