from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load .env from current dir or parent dir
for env_path in [Path(".env"), Path("../.env"), Path(__file__).parent.parent / ".env"]:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        break

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

from routers import transactions, budgets, ai_advisor, dashboard, goals, aica_router, auth

app = FastAPI(
    title="FinanceAI API",
    description="AI-Powered Personal Finance Assistant",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler — prevents raw 500s leaking stack traces to client
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error", "error": str(exc)})

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["Transactions"])
app.include_router(budgets.router, prefix="/api/budgets", tags=["Budgets"])
app.include_router(ai_advisor.router, prefix="/api/ai", tags=["AI Advisor"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(goals.router, prefix="/api/goals", tags=["Goals"])
app.include_router(aica_router.router, prefix="/api/ai-ca", tags=["AI CA"])


@app.get("/", tags=["Health"])
def root():
    return {"message": "FinanceAI API is running", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
def health():
    groq_key_set = bool(os.environ.get("GROQ_API_KEY", ""))
    return {
        "status": "healthy",
        "groq_api_key_configured": groq_key_set,
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
