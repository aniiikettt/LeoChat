# Default system instructions
DEFAULT_SYSTEM_PROMPT = (
    "You are a highly capable AI Assistant built from scratch using a custom, "
    "decoupled three-tier architecture. Provide accurate, clear, and helpful answers. "
    "Keep response length reasonable and aligned with the user's request details."
)

def build_messages(system_prompt: str, history: list[dict], user_message: str) -> list[dict]:
    """
    Constructs the list of messages for the LLM API call.
    Combines:
    1. System Prompt (sets persona/boundaries)
    2. History (sliding window context of past turns)
    3. User Message (the current query)
    """
    messages = []
    
    # 1. System Prompt
    messages.append({
        "role": "system",
        "content": system_prompt or DEFAULT_SYSTEM_PROMPT
    })
    
    # 2. Historical Context (already pruned by memory manager)
    for msg in history:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
        
    # 3. Current User Message
    messages.append({
        "role": "user",
        "content": user_message
    })
    
    return messages
