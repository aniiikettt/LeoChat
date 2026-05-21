import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
import sys

from api.chat import router as chat_router
from config import LOG_LEVEL

# Configure Loguru logging output
logger.remove()
logger.add(
    sys.stdout, 
    level=LOG_LEVEL, 
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level:7}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)

# Initialize FastAPI application
app = FastAPI(
    title="MIT AI Systems - Stateful Chatbot Engine",
    description="A decoupled, production-grade stateful chatbot using SQLite session storage and Groq LLM",
    version="1.0.0"
)

# Enable CORS for local development and testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router under the /api prefix
app.include_router(chat_router, prefix="/api")

# Redirect root path to our beautiful web interface
@app.get("/")
async def root_redirect():
    return RedirectResponse(url="/static/index.html")

# Create static directory dynamically if not exists, and mount it
import os
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    logger.info("Starting production ASGI server via Uvicorn...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
