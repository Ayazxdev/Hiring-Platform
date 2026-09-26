"""
Main FastAPI Application for Fair Hiring System
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from root directory BEFORE other imports
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import routers
from app.routers import pipeline, candidate, job, application, auth, candidate_public, company, passport
from app.database import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting Fair Hiring Backend...")
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise
    
    # Initialize Zynd Orchestrator if enabled
    if os.getenv('USE_ZYND', '0') == '1':
        try:
            from app.zynd_orchestrator import get_orchestrator
            orch = get_orchestrator()
            logger.info(f"Zynd Orchestrator initialized on port {os.getenv('ORCH_ZYND_PORT', '5100')}")
            logger.info(f"Orchestrator Agent ID: {orch.agent.agent_id}")
        except Exception as e:
            logger.warning(f"Failed to initialize Zynd Orchestrator: {str(e)}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Fair Hiring Backend...")
    await close_db()
    logger.info("Database connections closed")


# Create FastAPI app
app = FastAPI(
    title="Fair Hiring System API",
    description="Backend API for Fair Hiring Platform - AI-powered skill verification and bias-free recruitment",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
_env = os.getenv("ENV", "development")
if _env == "production":
    _allowed_origins = os.getenv("CORS_ORIGINS", "").split(",")
    allow_origins = _allowed_origins
else:
    # Allow all origins in development to support network IPs during demos
    allow_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
        headers={"Access-Control-Allow-Origin": "*"}
    )



# Include routers
app.include_router(auth.router)
app.include_router(candidate_public.router)
app.include_router(company.router)
app.include_router(pipeline.router)
app.include_router(candidate.router)
app.include_router(job.router)
app.include_router(application.router)
app.include_router(passport.router)

# Mount Unified Agents Aggregator so all agent services run in-process
try:
    import sys
    from pathlib import Path
    _root_dir = Path(__file__).resolve().parent.parent.parent
    _agents_dir = _root_dir / "agents_services"
    for _p in [str(_root_dir), str(_agents_dir)]:
        if _p not in sys.path:
            sys.path.insert(0, _p)
    from agents_services.agents_aggregator import app as agents_app
    app.mount("/agents", agents_app)
    logger.info("Unified Agents Aggregator mounted at /agents")
except Exception as e:
    logger.warning(f"Could not mount agents_aggregator: {e}")



# Health check endpoint
@app.get("/health")
@app.head("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {
        "status": "healthy",
        "service": "fair-hiring-backend",
        "version": "2.0.0"
    }


# Root endpoint
@app.get("/")
@app.head("/")
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "name": "Fair Hiring System API",
        "version": "2.0.0",
        "description": "AI-powered skill verification and bias-free recruitment platform",
        "documentation": "/docs",
        "health": "/health"
    }


# Global exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    """
    Handle HTTP exceptions.
    """
    logger.error(f"HTTP error: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """
    Handle validation errors.
    """
    logger.error(f"Validation error: {str(exc)}")
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "Validation error",
            "details": exc.errors(),
            "status_code": 422
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """
    Handle general exceptions.
    """
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "status_code": 500
        }
    )


if __name__ == "__main__":
    import uvicorn
    import os
    
    # Make port configurable via environment variable
    port = int(os.getenv("PORT", os.getenv("BACKEND_PORT", "8012")))
    env = os.getenv("ENV", "development")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=(env != "production"),
        log_level="info"
    )