import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="EZYerrScanner Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "https://ez-yerr-scanner.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routers.analyze import router as analyze_router
app.include_router(analyze_router, prefix="/api")

@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "detail": "Internal server error"}
    )

@app.on_event("startup")
async def on_startup():
    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    print(f"EZYerrScanner ready. Model: {model} (via Groq)")
