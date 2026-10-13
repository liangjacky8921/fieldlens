"""Google Earth Engine NDVI time-series module for FieldLens.

Pulls Sentinel-2 SR harmonized imagery for a user-drawn orchard polygon,
applies a simple QA60 cloud mask, computes per-scene NDVI spatial means,
and returns a date-sorted time series.

Auth strategy (order of precedence):
  1. Service account JSON via env vars EE_SERVICE_ACCOUNT_EMAIL + EE_SERVICE_ACCOUNT_KEY
     (key is the full JSON string, base64-optional — Render/Fly/etc pattern).
  2. Local OAuth via `earthengine authenticate` + env EE_PROJECT (dev only).
Falls back cleanly — every public function returns an "error" dict instead of raising.
"""

import json
import base64
from datetime import datetime, timedelta
from os import environ

# GEE Cloud project — required for both auth paths.
_GEE_PROJECT = environ.get("EE_PROJECT") or environ.get("GEE_PROJECT")

# Service account (for Render / cloud deploys, no interactive auth needed).
_SVC_EMAIL = environ.get("EE_SERVICE_ACCOUNT_EMAIL", "")
_SVC_KEY_RAW = environ.get("EE_SERVICE_ACCOUNT_KEY", "")

# ---------------------------------------------------------------------------
# Lazy GEE initialization: the app must boot even when credentials are missing.
# ---------------------------------------------------------------------------
_ee_ready = False
_ee_error = None


def _parse_key(raw: str) -> dict:
    """Accept service account key as raw JSON, or base64-encoded JSON."""
    raw = raw.strip()
    if not raw:
        return {}
    # Try direct JSON first
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict) and "client_email" in obj:
            return obj
    except json.JSONDecodeError:
        pass
    # Try base64
    try:
        decoded = base64.b64decode(raw, validate=True).decode("utf-8")
        obj = json.loads(decoded)
        if isinstance(obj, dict) and "client_email" in obj:
            return obj
    except Exception:  # noqa: BLE001
        pass
    raise ValueError("EE_SERVICE_ACCOUNT_KEY is not valid JSON or base64-JSON")


def _init_gee():
    """Try service account first, then local OAuth. Set _ee_ready / _ee_error."""
    global _ee_ready, _ee_error
    try:
        import ee
    except ImportError:
        _ee_error = "earthengine-api package not installed"
        return

    # --- Path 1: service account (cloud deploy) ---
    if _SVC_EMAIL and _SVC_KEY_RAW:
        try:
            key_data = _parse_key(_SVC_KEY_RAW)
            creds = ee.ServiceAccountCredentials(_SVC_EMAIL, key_data=key_data)
            ee.Initialize(project=_GEE_PROJECT, credentials=creds)
            _ee_ready = True
            return
        except Exception as exc:  # noqa: BLE001
            # Don't give up yet — try OAuth fallback below.
            _ee_error = f"ServiceAccount auth failed: {exc}; trying local OAuth…"

    # --- Path 2: local OAuth (dev machine) ---
    try:
        ee.Initialize(project=_GEE_PROJECT) if _GEE_PROJECT else ee.Initialize()
        _ee_ready = True
    except Exception as exc:  # noqa: BLE001
        _ee_error = str(exc)


_init_gee()


def gee_status() -> dict:
    """Return current GEE availability and an actionable hint."""
    return {
        "ready": _ee_ready,
        "error": _ee_error,
        "hint": None if _ee_ready else (
            "Set env var EE_PROJECT to your Earth Engine Cloud project, "
            "run `earthengine authenticate`, then restart the server."
        ),
    }


def _mask_clouds(image):
    """Mask clouds and cirrus using the QA60 band (bit 10 = clouds, bit 11 = cirrus)."""
    qa = image.select("QA60")
    cloud_bit = 1 << 10
    cirrus_bit = 1 << 11
    mask = qa.bitwiseAnd(cloud_bit).eq(0).And(qa.bitwiseAnd(cirrus_bit).eq(0))
    return image.updateMask(mask)


def get_ndvi_series(geojson: dict, days: int = 90) -> dict:
    """Compute the NDVI time series for a polygon over the past `days` days.

    Args:
        geojson: GeoJSON Polygon dict, e.g. {"type": "Polygon", "coordinates": [...]}.
        days: Look-back window in days (default 90).

    Returns:
        {"dates": [...], "ndvi": [...], "count": n} sorted by date.
        On any failure: same shape with empty lists plus an "error" message,
        so the API layer never raises a 500.
    """
    if not _ee_ready:
        return {
            "dates": [],
            "ndvi": [],
            "count": 0,
            "error": "GEE not authenticated",
            "hint": "Run `earthengine authenticate` and restart the server.",
        }

    if not isinstance(geojson, dict) or geojson.get("type") not in ("Polygon", "MultiPolygon"):
        return {"dates": [], "ndvi": [], "count": 0, "error": "Invalid GeoJSON: expected a Polygon"}

    try:
        region = ee.Geometry(geojson)
        end = datetime.utcnow()
        start = end - timedelta(days=days)

        collection = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(region)
            .filterDate(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 70))
            .map(_mask_clouds)
        )

        def scene_mean(image):
            # NDVI = (NIR - Red) / (NIR + Red); Sentinel-2 SR: B8 = NIR, B4 = Red.
            ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")
            mean = ndvi.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region,
                scale=20,  # meters; coarse enough to stay fast on small plots
                maxPixels=1e8,
            )
            return ee.Feature(
                None,
                {
                    "date": image.date().format("YYYY-MM-dd"),
                    "ndvi": mean.get("NDVI"),
                },
            )

        features = collection.map(scene_mean).filter(ee.Filter.notNull(["ndvi"]))
        features = features.sort("date")
        rows = features.getInfo().get("features", [])

        pairs = [
            (f["properties"]["date"], round(float(f["properties"]["ndvi"]), 4))
            for f in rows
            if f["properties"].get("ndvi") is not None
        ]
        # Sentinel-2 A/B can yield two scenes on the same day; average per date.
        by_date = {}
        for d, v in pairs:
            by_date.setdefault(d, []).append(v)
        pairs = sorted((d, round(sum(vs) / len(vs), 4)) for d, vs in by_date.items())

        if not pairs:
            return {
                "dates": [],
                "ndvi": [],
                "count": 0,
                "error": "No usable Sentinel-2 scenes for this area/time window (clouds or coverage)",
            }

        return {
            "dates": [p[0] for p in pairs],
            "ndvi": [p[1] for p in pairs],
            "count": len(pairs),
        }

    except Exception as exc:  # noqa: BLE001 - degrade gracefully, never 500
        return {
            "dates": [],
            "ndvi": [],
            "count": 0,
            "error": f"GEE query failed: {exc}",
        }
