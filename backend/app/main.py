import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.analyze import router as analyze_router
from app.services.classifier import warmup

logger = logging.getLogger("uvicorn")

_state: dict[str, str] = {"device": "unknown"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the model once at startup so the first request isn't slow during demo.
    logger.info("Loading RoBERTa injection classifier...")
    device = warmup()
    _state["device"] = device
    logger.info("Classifier ready on device=%s", device)
    yield


app = FastAPI(
    title="Singkap AI",
    description="LLM Prompt Injection Defense Middleware",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "device": _state["device"]}
