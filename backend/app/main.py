import uuid
from dotenv import load_dotenv
load_dotenv() # Load env vars from .env file

from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage

from .agent import graph

app = FastAPI(title="Cootradecun Chatbot API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None

class ChatResponse(BaseModel):
    messages: List[Dict[str, Any]]
    thread_id: str

# In-memory storage for simple persisting of non-checkpointer state if needed.
# For LangGraph checkpointer, we typically need a checkpointer (like MemorySaver/Sqlite).
# For this basic implementation, we will rely on LangGraph's checkpointer if we configured one,
# OR we will just keeping state in memory if we passed a checkpointer.
# Wait, in agent.py I did `builder.compile()`. I didn't pass a checkpointer.
# For a real chatbot, we NEED a checkpointer to remember conversation history.
# I will modify agent.py to use MemorySaver in the next step or patch it here.
# Actually, I'll update this file to use a global checkpointer or pass it to compile.

# Let's fix agent.py compilation in a separate step or here.
# For now, let's assume we re-compile it with a checkpointer or I make a singleton.

from langgraph.checkpoint.memory import MemorySaver
checkpointer = MemorySaver()
# Re-compiling the graph here to ensure we have memory
from .agent import builder
graph_with_memory = builder.compile(checkpointer=checkpointer)

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    thread_id = request.thread_id or str(uuid.uuid4())
    
    config = {"configurable": {"thread_id": thread_id}}
    
    inputs = {
        "messages": [HumanMessage(content=request.message)]
    }
    
    # We want to stream the output or get the final state.
    # invoke() returns the final state.
    try:
        final_state = graph_with_memory.invoke(inputs, config=config)
        
        # Extract the last message if it's an AI message
        # We need to return the conversation delta or the full history.
        # Let's return the last AI message.
        
        messages = final_state.get("messages", [])
        last_message = messages[-1] if messages else None
        
        response_messages = []
        if isinstance(last_message, AIMessage):
             response_messages.append({"role": "assistant", "content": last_message.content})
        else:
             # If the last message wasn't AI (unlikely unless error), send something generic
             response_messages.append({"role": "assistant", "content": "Lo siento, hubo un error procesando tu solicitud."})

        return ChatResponse(
            messages=response_messages,
            thread_id=thread_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok"}
