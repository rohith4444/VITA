from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from chat_api.routes import session_routes, message_routes, file_routes, agent_routes, auth_routes
from chat_api.config import settings
from chat_api.database import Base, engine, memory_manager, get_memory_manager
from core.logging.logger import setup_logger

# Initialize logger
logger = setup_logger(__name__)
logger.info("Starting Chat API application")

# Create database tables
Base.metadata.create_all(bind=engine)
logger.info("Database tables created")

# Initialize memory manager
memory_manager = get_memory_manager()
logger.info("Memory manager initialized")

# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info(f"CORS configured with origins: {settings.CORS_ORIGINS}")

# Include routers
app.include_router(auth_routes.router, prefix=settings.API_PREFIX)
app.include_router(session_routes.router, prefix=settings.API_PREFIX)
app.include_router(message_routes.router, prefix=settings.API_PREFIX)
app.include_router(file_routes.router, prefix=settings.API_PREFIX)
app.include_router(agent_routes.router, prefix=settings.API_PREFIX)
logger.info("API routes registered")

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors.
    """
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handle HTTP exceptions.
    """
    logger.warning(f"HTTP exception: {exc.detail} (status code: {exc.status_code})")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle general exceptions.
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# API root
@app.get("/")
async def root():
    """
    Root endpoint.
    """
    return {
        "message": f"Welcome to the {settings.API_TITLE}",
        "docs": "/docs",
        "version": settings.API_VERSION
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)