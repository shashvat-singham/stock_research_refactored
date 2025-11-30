"""
Main FastAPI application for the Stock Research Chatbot.
"""
import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from backend.config.settings import get_settings
from backend.app.api import router as api_router
from backend.app.models import AnalysisRequest, AnalysisResponse
from backend.app.websocket import get_connection_manager


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    settings = get_settings()
    logger.info("Starting Stock Research Chatbot API", 
                app_env=settings.app_env, 
                log_level=settings.log_level)
    
    # Initialize any startup tasks here
    yield
    
    logger.info("Shutting down Stock Research Chatbot API")


# Create FastAPI application
app = FastAPI(
    title="Stock Research Chatbot API",
    description="An agentic chatbot for stock research using LangGraph and Gemini 2.5 Flash",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# WebSocket endpoint for streaming logs
@app.websocket("/ws/{request_id}")
async def websocket_endpoint(websocket: WebSocket, request_id: str):
    """
    WebSocket endpoint for streaming real-time analysis logs.
    
    Clients connect to this endpoint with a request_id to receive
    real-time updates about the analysis progress.
    """
    connection_manager = get_connection_manager()
    await connection_manager.connect(websocket, request_id)
    
    try:
        # Keep connection alive and listen for client messages (if needed)
        while True:
            try:
                # Wait for any messages from client (optional)
                data = await websocket.receive_text()
                logger.debug("Received message from client", 
                           request_id=request_id, 
                           data=data)
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error("WebSocket error", 
                           request_id=request_id, 
                           error=str(e))
                break
    
    finally:
        await connection_manager.disconnect(websocket, request_id)
        logger.info("WebSocket connection closed", request_id=request_id)


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "stock-research-chatbot"
    }


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint."""
    return {
        "message": "Stock Research Chatbot API",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "backend.app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.app_env == "development",
        log_level=settings.log_level.lower()
    )
