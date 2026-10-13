"""Google Earth Engine NDVI time-series module for FieldLens.

Pulls Sentinel-2 SR harmonized imagery for a user-drawn orchard polygon,
applies a simple QA60 cloud mask, computes per-scene NDVI spatial means,
and returns a date-sorted time series.
"""

from datetime import datetime, timedelta
from os import environ

# GEE now requires a Cloud project; set one of these env vars before starting.
_GEE_PROJECT = environ.get("EE_PROJECT") or environ.get("GEE_PROJECT")

# ---------------------------------------------------------------------------
# Lazy GEE initialization: the app must boot even when credentials are missing.
# ---------------------------------------------------------------------------
_ee_ready = False
_ee_error = None

try:
    import ee

    try:
        ee.Initialize(project=_GEE_PROJECT) if _GEE_PROJECT else ee.Initialize()
        _ee_ready = True
    except Exception as exc:  # noqa: BLE001 - surface any init failure
        _ee_error = str(exc)
except ImportError:
    ee = None
    _ee_error = "earthengine-api package not installed"


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
