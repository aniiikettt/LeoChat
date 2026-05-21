import httpx
from loguru import logger
from config import GROQ_API_KEY, GROQ_API_URL, LLM_MODEL

class LLMClient:
    def __init__(self, api_key: str = GROQ_API_KEY, api_url: str = GROQ_API_URL, model: str = LLM_MODEL):
        self.api_key = api_key
        self.api_url = api_url
        self.model = model

    async def generate_response(self, messages: list[dict]) -> tuple[str, dict]:
        """
        Sends the compiled messages to the Groq API asynchronously.
        Returns:
            A tuple of (response_text, usage_metadata)
        """
        if not self.api_key:
            logger.error("Groq API Key is missing. Please set GROQ_API_KEY in your .env file.")
            raise ValueError("Groq API Key is not configured. Add it to your .env file.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1024
        }

        logger.debug(f"Sending request to Groq API using model '{self.model}' with {len(messages)} messages.")
        
        # Using HTTPX async client for non-blocking I/O
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(self.api_url, headers=headers, json=payload)
                
                # Check for HTTP errors (e.g., 401 Unauthorized, 429 Rate Limit, 500 Server Error)
                if response.status_code != 200:
                    logger.error(f"Groq API returned error {response.status_code}: {response.text}")
                    if response.status_code == 429:
                        raise RuntimeError("Groq API rate limit exceeded. Please wait a moment.")
                    elif response.status_code == 401:
                        raise RuntimeError("Unauthorized access. Check your GROQ_API_KEY.")
                    else:
                        raise RuntimeError(f"Groq API error: {response.text}")

                response_data = response.json()
                
                # Parse response content
                choices = response_data.get("choices", [])
                if not choices:
                    raise RuntimeError("Invalid response structure from Groq API (no choices).")
                
                assistant_content = choices[0].get("message", {}).get("content", "")
                
                # Parse token usage metrics for cost tracking & logging
                usage = response_data.get("usage", {})
                usage_metadata = {
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                    "model": self.model
                }
                
                logger.info(
                    f"LLM Response received. Prompt Tokens: {usage_metadata['prompt_tokens']} | "
                    f"Completion Tokens: {usage_metadata['completion_tokens']} | "
                    f"Total Tokens: {usage_metadata['total_tokens']}"
                )
                
                return assistant_content, usage_metadata

            except httpx.RequestError as exc:
                logger.error(f"HTTP Request failed while connecting to Groq: {exc}")
                raise RuntimeError(f"Failed to connect to LLM provider: {exc}")
            except Exception as e:
                logger.error(f"Unexpected error in generate_response: {e}")
                raise
