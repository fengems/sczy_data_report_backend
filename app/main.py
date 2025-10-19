"""
FastAPI main application
"""

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config.settings import settings
from app.utils.logger import setup_logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle management"""
    # Execute on startup
    setup_logger()
    yield
    # Execute on shutdown
    pass


def create_app() -> FastAPI:
    """Create FastAPI application instance"""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="ERP data crawling and processing system",
        debug=settings.debug,
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Production environment should restrict specific domains
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    register_routes(app)

    # Add exception handlers
    register_exception_handlers(app)

    return app


def register_routes(app: FastAPI) -> None:
    """Register API routes"""
    from app.api import crawler, health

    app.include_router(health.router, prefix="/api/v1", tags=["Health Check"])
    app.include_router(
        crawler.router, prefix="/api/v1/crawler", tags=["Crawler Management"]
    )

    @app.get("/", tags=["Root"])
    async def root() -> Dict[str, Any]:
        return {
            "message": f"Welcome to {settings.app_name}",
            "version": settings.app_version,
            "docs": "/docs",
            "redoc": "/redoc",
        }


def register_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers"""

    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Global exception handler"""
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": str(exc) if settings.debug else "Internal server error",
                "type": type(exc).__name__,
            },
        )


app = create_app()
