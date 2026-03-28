import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="OptiScan AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    from routers.analyze import router as analyze_router
    app.include_router(analyze_router, prefix="/api")
except ImportError:
    pass

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
    print(f"OptiScan AI ready. Model: {model} (via Groq)")
