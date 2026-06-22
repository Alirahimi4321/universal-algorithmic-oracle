"""FastAPI web API interface for the Universal Algorithmic Oracle.

Exposes the oracle as a REST API with endpoints for querying, listing systems,
and health checks.
"""
import time
import logging
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ..runtime.executor import OraclePipeline

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Universal Algorithmic Oracle API",
    description="REST API for the evolved symbolic oracle system",
    version="0.1.0",
)

_pipeline: Optional[OraclePipeline] = None


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="The question to ask the oracle")
    engine: str = Field(default="ga", description="Evolution engine to use (ga, gp, nsga)")
    generations: int = Field(default=50, ge=1, le=1000, description="Number of evolutionary generations")
    timestamp: Optional[float] = Field(default=None, description="Optional timestamp override")


class AskResponse(BaseModel):
    answer: str
    symbolic_answer: dict
    numeric_signature: list[float]
    oracle_confidence: float
    dominant_systems: list[str]
    evolved_structure: dict
    explanation_trace: list[str]
    lineage_id: str
    generation: int
    fitness: dict
    disclaimer: dict
    confidence_model: dict
    system_contributions: list[dict]
    fusion_info: dict
    output_hash: str


class SystemInfo(BaseModel):
    id: str
    name: str


class HealthResponse(BaseModel):
    status: str
    version: str
    available_engines: list[str]
    system_count: int
    uptime: float


def get_pipeline() -> OraclePipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = OraclePipeline()
    return _pipeline


@app.on_event("startup")
async def startup():
    global _pipeline
    _pipeline = OraclePipeline()
    logger.info("Oracle API started, loaded %d symbolic systems", len(_pipeline.get_available_systems()))


@app.post("/ask", response_model=AskResponse)
async def ask_oracle(request: AskRequest):
    """Submit a question and receive an oracle reading."""
    pipeline = get_pipeline()
    try:
        result = pipeline.ask(
            question=request.question,
            timestamp=request.timestamp,
            generations=request.generations,
            engine=request.engine,
        )
        return AskResponse(**result.to_dict())
    except Exception as e:
        logger.exception("Oracle ask failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/systems")
async def list_systems():
    """List all available symbolic systems."""
    pipeline = get_pipeline()
    systems = pipeline.get_available_systems()
    return {
        "systems": systems,
        "count": len(systems),
    }


@app.get("/engines")
async def list_engines():
    """List all available evolution engines."""
    pipeline = get_pipeline()
    engines = pipeline.get_available_engines()
    return {
        "engines": engines,
        "count": len(engines),
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    pipeline = get_pipeline()
    return HealthResponse(
        status="ok",
        version="0.1.0",
        available_engines=pipeline.get_available_engines(),
        system_count=len(pipeline.get_available_systems()),
        uptime=time.time() - app.state.start_time if hasattr(app.state, "start_time") else 0.0,
    )


@app.on_event("startup")
async def record_start_time():
    app.state.start_time = time.time()


def run_server(host: str = "127.0.0.1", port: int = 8000):
    """Start the API server."""
    import uvicorn
    logger.info("Starting Oracle API on %s:%d", host, port)
    uvicorn.run(app, host=host, port=port)
