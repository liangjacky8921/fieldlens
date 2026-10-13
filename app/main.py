"""FieldLens FastAPI entry point.

Endpoints:
    GET  /health      - liveness + GEE status
    POST /api/ndvi    - NDVI time series for a drawn orchard polygon
    POST /api/report  - NDVI series + bilingual grower advisory report
    GET  /            - single-page mobile frontend (static/index.html)
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.advise import generate_bilingual, generate_report
from app.db import recent_reports, save_report
from app.gee_ndvi import gee_status, get_ndvi_series

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="FieldLens", version="0.2.0")

# Allow the static frontend (and local tooling) to call the API from any origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class NdviRequest(BaseModel):
    geojson: dict
    days: int = 90


class ReportRequest(BaseModel):
    geojson: dict
    crop: str = "pomelo"
    lang: str = "en"  # "en" | "zh" | "both"
    days: int = 90


@app.get("/health")
def health() -> dict:
    """Liveness probe; also reports whether GEE initialized."""
    status = gee_status()
    return {"status": "ok", "gee_ready": status["ready"], "gee_error": status["error"]}


@app.post("/api/ndvi")
def ndvi(req: NdviRequest) -> dict:
    """Return the NDVI time series for the posted GeoJSON polygon."""
    days = max(7, min(req.days, 365))
    return get_ndvi_series(req.geojson, days=days)


@app.post("/api/report")
def report(req: ReportRequest) -> dict:
    """Return NDVI series plus an advisory report.

    lang=both returns EN and ZH reports in a single call so the frontend can
    switch languages instantly without re-querying GEE or the model.
    """
    days = max(7, min(req.days, 365))
    ndvi_data = get_ndvi_series(req.geojson, days=days)
    result = {"ndvi": ndvi_data, "crop": req.crop}

    if ndvi_data.get("error"):
        result["report"] = None
        return result

    if req.lang == "both":
        result["report"] = generate_bilingual(ndvi_data, req.crop)
    else:
        result["report"] = generate_report(ndvi_data, req.crop, req.lang)

    trend = result["report"].get("trend", "stable")
    save_report(req.geojson, req.crop, trend, ndvi_data.get("count", 0))
    return result


@app.get("/api/history")
def history() -> dict:
    """Return the 10 most recent report runs (diagnostics)."""
    return {"items": recent_reports(10)}


@app.get("/", include_in_schema=False)
def index():
    """Serve the landing page (marketing + Aurora hero)."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/app", include_in_schema=False)
def app_page():
    """Serve the field tool page (map + report; no landing animations)."""
    return FileResponse(STATIC_DIR / "app.html")
