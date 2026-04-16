"""
SmartAgent Backend — FastAPI Main Entry Point
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Routers
from routers.connect import router as connect_router
from routers.analyze import router as analyze_router
from routers.actions import router as actions_router

app = FastAPI(
    title="SmartAgent API",
    description="AI-powered Smartsheet data quality agent",
    version="2.0.0"
)

# CORS — allow all origins in dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers under /api
app.include_router(connect_router, prefix="/api")
app.include_router(analyze_router, prefix="/api")
app.include_router(actions_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "service": "SmartAgent API",
        "version": "2.0.0",
        "mode": "mock_wiremock" if os.getenv("USE_MOCK_SERVER", "true").lower() == "true" else "live",
        "endpoints": {
            "connect": "GET /api/analyze/connect",
            "analyze": "POST /api/analyze/start",
            "execute": "POST /api/actions/execute",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
