# ============================================================
# FastAPI Application — backend/app_api.py
# Main entry point for the fraud detection REST API
#
# Run with:
#   uvicorn backend.app_api:app --reload --port 8000
# ============================================================

import time
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.routes.auth    import router as auth_router
from backend.routes.predict import router as predict_router
from backend.routes.alerts  import router as alerts_router
from backend.routes.cases   import router as cases_router
from backend.utils.logger   import logger


# ── Lifespan: warm up model on startup ────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Fraud Detection API starting up...")
    # Pre-warm the model so the first /predict call is not slow
    try:
        from backend.routes.predict import _get_bundle
        _get_bundle()
        logger.info("✅ ML model loaded and ready.")
    except Exception as exc:
        logger.warning(f"⚠️  Model pre-warm failed: {exc} — will load on first request.")
    yield
    logger.info("🛑 Fraud Detection API shutting down.")


# ── Application ────────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "Fraud Detection & Monitoring API",
    description = (
        "Enterprise-grade real-time fraud detection REST API.\n\n"
        "Built for Task 4 of the Vinayak IT Internship — Month 3.\n\n"
        "**Auth**: POST `/auth/token` with `username=admin` / `password=secret` to get a JWT bearer token."
    ),
    version     = "1.0.0",
    contact     = {"name": "Fraud System Team", "email": "fraud@example.com"},
    lifespan    = lifespan,
)

# ── CORS (allow Streamlit + any dashboard origin in dev) ──────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],   # Restrict in production
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)


# ── Request timing middleware ──────────────────────────────────────────────────
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    t0       = time.perf_counter()
    response = await call_next(request)
    elapsed  = round((time.perf_counter() - t0) * 1000, 2)
    response.headers["X-Process-Time-Ms"] = str(elapsed)
    if request.url.path not in ("/health", "/docs", "/openapi.json"):
        logger.debug(f"{request.method} {request.url.path} → {response.status_code} ({elapsed}ms)")
    return response


# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "path": str(request.url.path)},
    )


# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(predict_router)
app.include_router(alerts_router)
app.include_router(cases_router)


# ── Root & Health ──────────────────────────────────────────────────────────────
@app.get("/", tags=["System"], summary="API root")
async def root():
    return {
        "service":   "Fraud Detection & Monitoring API",
        "version":   "1.0.0",
        "status":    "operational",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "docs":      "/docs",
    }


@app.get("/health", tags=["System"], summary="System health check")
async def health():
    return {
        "status":    "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "components": {
            "api":      "ok",
            "model":    "ok",
            "database": "ok (in-memory)",
        },
    }


@app.get("/metrics", tags=["System"], summary="System metrics")
async def metrics():
    """Return key operational metrics for monitoring."""
    from backend.routes.alerts import _ALERTS
    from backend.routes.cases  import _CASES
    return {
        "total_alerts":     len(_ALERTS),
        "pending_alerts":   sum(1 for a in _ALERTS if a["status"] == "Pending"),
        "open_cases":       sum(1 for c in _CASES if c["status"] == "Open"),
        "timestamp":        datetime.utcnow().isoformat() + "Z",
    }
