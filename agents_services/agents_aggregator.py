"""
Unified Agents Aggregator
Combines all agent services into a single FastAPI application for easier deployment.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import importlib
import sys
import os
import logging

if sys.platform.startswith("win"):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agents_aggregator")

# Add current and parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Unified Agents Aggregator...")
    yield
    logger.info("Shutting down Unified Agents Aggregator...")

app = FastAPI(
    title="Heureka Unified Agents API",
    description="Aggregation of all Heureka agent services for deployment",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mapping of path to module name
services_map = {
    "matching": "matching_agent_service",
    "bias": "bias_agent_service",
    "skill": "skill_agent_service",
    "ats": "ats_service",
    "github": "github_service",
    "leetcode": "leetcode_service",
    "linkedin": "linkedin_service",
    "passport": "passport_service",
    "job_description": "conditional_test_service",
    "codeforces": "codeforce_service",
}

try:
    from a2wsgi import WSGIMiddleware
except ImportError:
    import anyio.from_thread
    from fastapi.middleware.wsgi import WSGIMiddleware

for path, module_name in services_map.items():
    try:
        logger.info(f"Loading agent: {module_name}...")
        module = importlib.import_module(module_name)
        if hasattr(module, "app"):
            sub_app = module.app
            
            # Detect if it's a Flask app (WSGI) or FastAPI app (ASGI)
            if hasattr(sub_app, "wsgi_app"): # True for Flask
                logger.info(f"Detected Flask app for {module_name}, wrapping in WSGIMiddleware")
                app.mount(f"/{path}", WSGIMiddleware(sub_app))
            else:
                app.mount(f"/{path}", sub_app)
                
            logger.info(f"Successfully mounted {module_name} at /{path}")
        else:
            logger.warning(f"Module {module_name} has no 'app' attribute")
    except Exception as e:
        logger.error(f"Error mounting {module_name}: {e}")

@app.get("/")
async def root():
    return {
        "message": "Heureka Unified Agents API is running",
        "mounted_services": list(services_map.keys()),
        "status": "healthy"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "unified-agents"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
