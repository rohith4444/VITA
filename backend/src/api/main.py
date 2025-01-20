from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.utils.logger import setup_logger
from src.api.middleware.logging import log_request_middleware
from src.api.routers import python_router, mechatronic_router, supervisor_router

# Initialize logger
logger = setup_logger("API")

# Create FastAPI instance
app = FastAPI(
    title="Multi-Agent System API",
    description="API for interacting with specialized AI agents",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add logging middleware
app.middleware("http")(log_request_middleware)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "service": "Multi-Agent API"}

# Include routers
app.include_router(
    python_router.router,
    prefix="/api/v1/python",
    tags=["Python Agent"]
)

app.include_router(
    mechatronic_router.router,
    prefix="/api/v1/mechatronic",
    tags=["Mechatronic Agent"]
)

app.include_router(
    supervisor_router.router,
    prefix="/api/v1/supervisor",
    tags=["Supervising Agent"]
)

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting API server")
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)