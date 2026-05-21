import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from loguru import logger

from db.session_store import SessionStore
from core.memory import MemoryManager
from core.llm import LLMClient
from core.prompt import build_messages
from core.rag import chunk_text, SimpleRetrievalEngine

router = APIRouter()

# Instantiate core orchestrators (Decoupled Dependency Injection baseline)
# In production, you might inject these via FastAPI Depends or containers
store = SessionStore()
memory_manager = MemoryManager(store)
llm_client = LLMClient()

# Request/Response schemas
class ChatRequest(BaseModel):
    message: str = Field(..., description="The user's message input to the chatbot")
    session_id: Optional[str] = Field(default=None, description="Unique session ID. If empty, a new session will be generated.")
    system_prompt: Optional[str] = Field(default=None, description="Optional custom system instructions to override the default prompt.")

class ChatResponse(BaseModel):
    response: str
    session_id: str
    usage: dict = Field(..., description="Token usage details for monitoring and budgeting.")

class ClearSessionResponse(BaseModel):
    session_id: str
    status: str

class KnowledgeRequest(BaseModel):
    session_id: str
    content: str

class KnowledgeResponse(BaseModel):
    session_id: str
    status: str

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chat gateway endpoint.
    Handles stateless-to-stateful memory translation, prompt compilation (RAG),
    calls LLM, updates history, and returns token metrics.
    """
    # 1. Ensure we have a valid session ID
    session_id = request.session_id
    if not session_id or session_id.strip() == "":
        session_id = str(uuid.uuid4())
        logger.info(f"Generated new session ID: {session_id}")

    try:
        # 2. RAG Retrieval Stage (if session-specific document context exists)
        knowledge_text = store.get_knowledge(session_id)
        context_str = ""
        
        if knowledge_text and knowledge_text.strip():
            # Slice the document text into overlapping segments
            chunks = chunk_text(knowledge_text, chunk_size=400, overlap=80)
            
            if chunks:
                # Index and calculate TF-IDF relevance manually
                engine = SimpleRetrievalEngine(chunks)
                matches = engine.retrieve(request.message, top_k=2)
                
                # Filter to match list with positive similarity scores
                relevant_chunks = [match[0] for match in matches if match[1] > 0.0]
                if relevant_chunks:
                    context_str = "\n---\n".join(relevant_chunks)
                    logger.info(f"RAG: Retrieved {len(relevant_chunks)} relevant chunks from index.")

        # 3. Augment system prompt instructions with retrieved context
        system_prompt = request.system_prompt
        if context_str:
            base_instructions = system_prompt or "You are a helpful assistant."
            system_prompt = (
                f"{base_instructions}\n\n"
                "USE THE FOLLOWING CONTEXT TO ANSWER THE USER'S QUESTION.\n"
                "If the answer cannot be found in the context, answer using your general knowledge, "
                "but explicitly state that the answer was not found in the provided documents.\n"
                f"--- CONTEXT DOCUMENTATION ---\n{context_str}\n---------------------------"
            )

        # 4. Retrieve history (Sliding Window applied inside MemoryManager)
        history = memory_manager.get_context(session_id)
        
        # 5. Assemble final prompt list (System Instructions + Sliding Window History + Query)
        compiled_messages = build_messages(
            system_prompt=system_prompt,
            history=history,
            user_message=request.message
        )
        
        # 6. Save current user message to Persistent Store
        memory_manager.save_user_message(session_id, request.message)

        # 7. Call LLM (async, non-blocking call to Groq)
        assistant_response, usage_data = await llm_client.generate_response(compiled_messages)

        # 8. Save LLM assistant's response to Persistent Store
        memory_manager.save_assistant_message(session_id, assistant_response)

        return ChatResponse(
            response=assistant_response,
            session_id=session_id,
            usage=usage_data
        )

    except ValueError as val_err:
        # Configuration error (e.g. missing API key)
        raise HTTPException(status_code=500, detail=str(val_err))
    except RuntimeError as run_err:
        # LLM service error or rate-limiting
        raise HTTPException(status_code=503, detail=str(run_err))
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail="An unexpected system error occurred.")

@router.post("/knowledge", response_model=KnowledgeResponse)
async def update_knowledge_endpoint(request: KnowledgeRequest):
    """Saves or updates the session-scoped knowledge base context."""
    if not request.session_id or request.session_id.strip() == "":
        raise HTTPException(status_code=400, detail="A valid session_id is required.")
        
    try:
        store.save_knowledge(request.session_id, request.content)
        return KnowledgeResponse(session_id=request.session_id, status="updated")
    except Exception as e:
        logger.error(f"Error saving knowledge for session {request.session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to save knowledge context.")

@router.post("/session/clear", response_model=ClearSessionResponse)
async def clear_session_endpoint(session_id: str):
    """Clears history for the given session to reset conversation context."""
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id parameter is required.")
        
    try:
        memory_manager.clear_session(session_id)
        return ClearSessionResponse(session_id=session_id, status="cleared")
    except Exception as e:
        logger.error(f"Error clearing session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear session history.")

