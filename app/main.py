"""
DecisionDeck Main Application Entry Point
Mounts routes, static frontend assets, and initializes database schema.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import engine, Base
import app.models  # Ensure all models are registered with Base.metadata
from app.routes.auth import router as auth_router
from app.routes.decisions import router as decisions_router

# Determine base paths
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on application startup
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="DecisionDeck API",
    description="Transparent decision-support application with weighted scoring and hard constraints.",
    version="1.0.0",
    lifespan=lifespan
)

# Include API Routers
app.include_router(auth_router)
app.include_router(decisions_router)

# Serve static assets (CSS, JS, images)
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint to verify backend server status."""
    return {"status": "ok", "app": "DecisionDeck", "version": "1.0.0"}


# HTML Page Routes
@app.get("/", tags=["Frontend"])
def serve_index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/login.html", tags=["Frontend"])
@app.get("/login", tags=["Frontend"])
def serve_login():
    return FileResponse(FRONTEND_DIR / "login.html")


@app.get("/register.html", tags=["Frontend"])
@app.get("/register", tags=["Frontend"])
def serve_register():
    return FileResponse(FRONTEND_DIR / "register.html")


@app.get("/dashboard.html", tags=["Frontend"])
@app.get("/dashboard", tags=["Frontend"])
def serve_dashboard():
    return FileResponse(FRONTEND_DIR / "dashboard.html")


@app.get("/decision.html", tags=["Frontend"])
@app.get("/decision", tags=["Frontend"])
def serve_decision():
    return FileResponse(FRONTEND_DIR / "decision.html")
