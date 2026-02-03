from contextlib import asynccontextmanager
import time
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import structlog
from sqlalchemy import text

from app.config import get_settings
from app.logging_config import configure_logging
from app.database.session import engine, SessionLocal
from app.database.base import Base
from app.routers import auth, documents, users, audit, templates, backup, sync
from app.auth.security import get_password_hash
from app.models.user import User
from sqlalchemy.orm import Session

settings = get_settings()
logger = structlog.get_logger()


def wait_for_db(max_retries: int = 30):
    """Wait for database to be ready."""
    for attempt in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                logger.info("Database connection successful")
                return True
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Database not ready, retrying... ({attempt + 1}/{max_retries})")
                time.sleep(1)
            else:
                logger.error("Failed to connect to database after retries")
                raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting application", app_name=settings.app_name)
    
    # Wait for database to be ready
    wait_for_db()
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Create default admin user if not exists
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.username == settings.admin_username).first()
        if not admin_user:
            admin_user = User(
                username=settings.admin_username,
                email=settings.admin_email,
                hashed_password=get_password_hash(settings.admin_password),
                role="admin",
            )
            db.add(admin_user)
            db.commit()
            logger.info("Default admin user created", username=settings.admin_username)
    finally:
        db.close()
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")


# Configure logging
configure_logging(settings.log_level)

# Rate limiting storage - IP address -> list of (timestamp, endpoint)
rate_limit_store = defaultdict(list)


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Document Management System API",
    version="1.0.0",
    lifespan=lifespan,
)

# Add rate limiting middleware (must be added first)
@app.middleware("http")
async def rate_limit_mw(request: Request, call_next):
    """Rate limiting middleware - 5 requests per minute for /api/auth/login"""
    if request.url.path == "/api/auth/login" and request.method == "POST":
        client_ip = request.client.host if request.client else "unknown"
        now = datetime.utcnow()
        
        # Clean up old entries (older than 1 minute)
        rate_limit_store[client_ip] = [
            ts for ts in rate_limit_store[client_ip]
            if now - ts < timedelta(minutes=1)
        ]
        
        # Check if rate limit exceeded
        if len(rate_limit_store[client_ip]) >= 5:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many login attempts. Please try again later."}
            )
        
        # Add current request timestamp
        rate_limit_store[client_ip].append(now)
    
    return await call_next(request)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(users.router)
app.include_router(audit.router)
app.include_router(templates.router)
app.include_router(backup.router)
app.include_router(sync.router)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main UI page."""
    with open("templates/index.html", "r") as f:
        return HTMLResponse(content=f.read())


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.app_name}
