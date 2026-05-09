from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv
import os

load_dotenv()

from contact import router as contact_router
from medium import router as medium_router
from analytics import router as analytics_router

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Kartik Kale — Portfolio API", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(contact_router,   prefix="/api/contact",   tags=["Contact"])
app.include_router(medium_router,    prefix="/api/medium",    tags=["Medium"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])

@app.get("/api/health")
def health():
    return {"status": "ok"}
