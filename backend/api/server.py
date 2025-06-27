from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import logging
from datetime import datetime
from api.endpoints import chat, coder, rag, multimodal
from api.endpoints import export, webhook, collaboration, advanced_rag
from api.endpoints import document_management, cost_tracking, performance
from api.auth import auth_routes, guest_routes
from api.auth.auth_middleware import get_current_user
from src.db import supabase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Multimodal Assistant API...")
    try:
        # Test database connection
        response = supabase.table("users").select("id").limit(1).execute()
        logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Multimodal Assistant API...")

app = FastAPI(
    title="Multimodal Assistant API",
    description="A comprehensive AI assistant with multimodal capabilities, authentication, and advanced features",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        supabase.table("users").select("id").limit(1).execute()
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0.0",
            "database": "connected"
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "2.0.0",
                "database": "disconnected",
                "error": str(e)
            }
        )

# Include all routers
app.include_router(auth_routes.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(guest_routes.router, prefix="/api/guest", tags=["Guest Access"])
app.include_router(chat.router, prefix="/api/chat", tags=["General Chat"])
app.include_router(coder.router, prefix="/api/coder", tags=["Code Assistant"])
app.include_router(rag.router, prefix="/api/rag", tags=["Document RAG"])
app.include_router(multimodal.router, prefix="/api/multimodal", tags=["Multimodal Processing"])
app.include_router(export.router, prefix="/api/export", tags=["Export Features"])
app.include_router(webhook.router, prefix="/api/webhook", tags=["Webhooks"])
app.include_router(collaboration.router, prefix="/api/collaboration", tags=["Collaboration"])
app.include_router(advanced_rag.router, prefix="/api/advanced-rag", tags=["Advanced RAG"])
app.include_router(document_management.router, prefix="/api/documents", tags=["Document Management"])
app.include_router(cost_tracking.router, prefix="/api/costs", tags=["Cost Tracking"])
app.include_router(performance.router, prefix="/api/performance", tags=["Performance & Caching"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Multimodal Assistant API",
        "version": "2.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "authentication": "/api/auth",
            "guest_access": "/api/guest", 
            "general_chat": "/api/chat",
            "code_assistant": "/api/coder",
            "document_rag": "/api/rag",
            "multimodal": "/api/multimodal",
            "export": "/api/export",
            "webhooks": "/api/webhook",
            "collaboration": "/api/collaboration",
            "advanced_rag": "/api/advanced-rag",
            "document_management": "/api/documents",
            "cost_tracking": "/api/costs",
            "performance": "/api/performance",
            "health": "/health"
        },
        "documentation": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)