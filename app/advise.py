"""Grower advisory report generation for FieldLens.

Trend features are computed deterministically in Python (linear-fit slope,
last-step drop, consecutive declines, cloud-point exclusion, gap detection).
Summary and advice come from a local Gemma model via Ollama; if the model is
unavailable, bilingual rule-based templates keep the API fully functional.

Key caveat (D2): the 0.70 high-vigor threshold is a UAV canopy-pixel reference
(R3, MDPI sweet-orange paper). Sentinel-2 10 m plot-mean NDVI naturally runs
lower for sparse/orchard floors. Never downgrade a plot on plot-mean alone if
the trend is stable.
"""

import json
from datetime import datetime

import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma2:2b"
TIMEOUT_SEC = 60

CROPS = {
    "pomelo": {"en": "honey pomelo", "zh": "金柚"},
    "citrus": {"en": "citrus", "zh": "柑橘"},
}

# --- Verified thresholds (from references.js / published sources) ---
VEGETATION_THRESHOLD = 0.25  # R5: NDVI > 0.25 = vegetation (soot-mould paper)
HIGH_VIGOR_UAV = 0.70       # R3: UAV canopy-pixel reference (NOT S2 plot-mean)
ALERT_DROP = 0.10            # Project-defined: sudden drop > 0.10 → field check 7d
ALERT_LOW = 0.55             # Project-defined: NDVI < 0.55 → watch
ALERT_CRITICAL = 0.40        # Project-defined: NDVI < 0.40 → inspect
CONSECUTIVE_DECLINE = 3      # Project-defined: 3 consecutive declining points
GAP_DAYS = 15                # Project-defined: >15-day gap between scenes → flag

# --- Prompt context blocks ---
SENTINEL2_CAVEAT = (
    "0.70 is a canopy-pixel (UAV) reference; do not downgrade a plot "
    "on plot-mean alone if trend is stable."
)
POST_HARVEST = (
    "Meizhou pomelo harvest started Sept 11; October is post-harvest "
    "recovery — a slight NDVI decline is normal and not alarming."
)
TREND_RULES = (
    "Trend rules: sudden drop > 0.10 → field check within 7 days; "
    "continuous slow decline → review water/fertilizer records; "
    "patchy low values vs uniform decline → walk the plot to distinguish."
)
RED_LINES = (
    "Red lines: do NOT diagnose specific pests or diseases; "
    "do NOT prescribe pesticide dosage; refer to local agricultural extension."
)

PROMPTS = {
    "en": (
        "You are an orchard agronomy advisor for Sentinel-2 NDVI monitoring. "
        f"{SENTINEL2_CAVEAT} {POST_HARVEST} {TREND_RULES} {RED_LINES}\n"
        "First line: verdict — one of vigorous / watch / alert.\n"
        "Then one summary sentence.\n"
        "Then up to 3 actions, each with a time window, using 'may/suggest field check' language.\n"
        "Plain English for growers, no jargon, under 200 words."
    ),
    "zh": (
        "你是果园 NDVI 监测的农艺顾问。"
        "0.70 是无人机冠层像元参考值，不能单凭地块均值低于 0.70 就降级——趋势稳定就不算弱。"
        "梅州金柚 9 月 11 日起采收，10 月是采后恢复期，轻微回落正常。"
        "趋势规则：突降超过 0.10 → 7 天内核查；连续缓降 → 查水肥记录；"
        "斑块状低值和整园均匀下降要区分——下地走一圈。"
        "红线：不诊断具体病虫害，不开农药用量，建议咨询当地农技站。\n"
        "第一行给结论（vigorous/watch/alert 对应 旺盛/关注/告警）。\n"
        "然后一句总结，再列最多 3 条行动，每条带时间窗，用'可能/建议实地核查'的措辞。"
        "果农大白话，少用术语，200 字以内。"
    ),
}


# ---------------------------------------------------------------------------
# Deterministic feature computation (pure Python, no numpy)
# ---------------------------------------------------------------------------

def compute_features(ndvi_data: dict) -> dict:
    """Compute deterministic trend features from the NDVI series.

    Returns dict with:
        trend: rising / stable / declining / volatile
        verdict: vigorous / watch / alert
        slope: linear-fit slope per sample index
        last_drop: last-step change (positive = drop magnitude)
        consecutive_decline: count of consecutive declining points at the tail
        has_gap: whether any gap between scenes exceeds GAP_DAYS
        cloud_points: indices of suspected cloud-contaminated points (NDVI < 0.25)
        cleaned_ndvi: values with cloud points excluded
        gap_note: str — empty or gap explanation
    """
    dates = ndvi_data.get("dates", [])
    ndvi = ndvi_data.get("ndvi", [])

    if not ndvi or len(ndvi) < 3:
        return {
            "trend": "stable",
            "verdict": "watch",
            "slope": 0.0,
            "last_drop": 0.0,
            "consecutive_decline": 0,
            "has_gap": True,
            "cloud_points": list(range(len(ndvi))),
            "cleaned_ndvi": [],
            "gap_note": "Insufficient valid observations in this period.",
        }

    # Cloud-contaminated point detection: NDVI < vegetation threshold in a
    # mature orchard is almost certainly cloud shadow or bare-soil contamination.
    cloud_points = [i for i, v in enumerate(ndvi) if v < VEGETATION_THRESHOLD]

    # Cleaned series for trend computation (exclude cloud points)
    cleaned = [(i, v) for i, v in enumerate(ndvi) if i not in cloud_points]
    if len(cleaned) < 3:
        # Too few clean points — fall back to all points, note cloud contamination
        cleaned = list(enumerate(ndvi))

    clean_values = [v for _, v in cleaned]
    n = len(clean_values)

    # Least-squares linear fit
    xs = list(range(n))
    x_mean = sum(xs) / n
    y_mean = sum(clean_values) / n
    denom = sum((x - x_mean) ** 2 for x in xs) or 1.0
    slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, clean_values)) / denom
    intercept = y_mean - slope * x_mean

    residuals = [y - (intercept + slope * x) for x, y in zip(xs, clean_values)]
    volatility = (sum(r * r for r in residuals) / n) ** 0.5

    # Trend classification
    if volatility > 0.08:
        trend = "volatile"
    elif slope > 0.005:
        trend = "rising"
    elif slope < -0.005:
        trend = "declining"
    else:
        trend = "stable"

    # Last-step drop (on original series, not cleaned)
    last_drop = (ndvi[-2] - ndvi[-1]) if len(ndvi) >= 2 else 0.0
    if last_drop < 0:
        last_drop = 0.0  # it's a rise, not a drop

    # Consecutive declining points at the tail
    consec = 0
    for i in range(len(ndvi) - 1, 0, -1):
        if ndvi[i] < ndvi[i - 1]:
            consec += 1
        else:
            break
    consecutive_decline = consec

    # Gap detection: check if any gap between consecutive dates > GAP_DAYS
    has_gap = False
    if len(dates) >= 2:
        for i in range(1, len(dates)):
            try:
                d1 = datetime.strptime(str(dates[i - 1])[:10], "%Y-%m-%d")
                d2 = datetime.strptime(str(dates[i])[:10], "%Y-%m-%d")
                if (d2 - d1).days > GAP_DAYS:
                    has_gap = True
                    break
            except (ValueError, TypeError):
                continue

    gap_note = ""
    if has_gap:
        gap_note = "Gaps in the observation window — some periods lack valid satellite data."
    if cloud_points:
        cloud_note = f"{len(cloud_points)} scene(s) excluded as cloud-contaminated."
        gap_note = (gap_note + " " + cloud_note).strip() if gap_note else cloud_note

    # Verdict: vigorous / watch / alert
    if last_drop > ALERT_DROP or (consecutive_decline >= CONSECUTIVE_DECLINE and trend == "declining"):
        verdict = "alert"
    elif trend in ("declining", "volatile") or consecutive_decline >= 2 or ndvi[-1] < ALERT_LOW:
        verdict = "watch"
    else:
        verdict = "vigorous"

    return {
        "trend": trend,
        "verdict": verdict,
        "slope": round(slope, 6),
        "last_drop": round(last_drop, 4),
        "consecutive_decline": consecutive_decline,
        "has_gap": has_gap,
        "cloud_points": cloud_points,
        "cleaned_ndvi": clean_values,
        "gap_note": gap_note,
    }


# ---------------------------------------------------------------------------
# Rule-based fallback templates (bilingual), keyed by verdict
# ---------------------------------------------------------------------------

FALLBACK = {
    "vigorous": {
        "en": {
            "verdict": "vigorous",
            "summary": "Canopy vigor is healthy and stable. NDVI shows no concerning decline over the period.",
            "advice": [
                "Maintain current irrigation and fertilization; no urgent action needed this week.",
                "Do a routine pest and disease walk-through within the next 1–2 weeks.",
                "Watch the next satellite pass (5 days) for any sign of decline.",
            ],
        },
        "zh": {
            "verdict": "vigorous",
            "summary": "果树长势健康平稳，本时段 NDVI 没有明显下降。",
            "advice": [
                "本周按常规水肥管理即可，暂无紧急事项。",
                "1–2 周内例行巡查一次病虫害。",
                "留意下一次卫星影像（5 天后），警惕由稳转弱。",
            ],
        },
    },
    "watch": {
        "en": {
            "verdict": "watch",
            "summary": "Canopy vigor shows some signs of stress. NDVI is declining or fluctuating — worth a closer look.",
            "advice": [
                "Check soil moisture within 7 days; increase irrigation if topsoil is dry.",
                "Inspect leaves for yellowing, spots, or curling — rule out water stress first.",
                "Review recent water/fertilizer records for missed applications.",
            ],
        },
        "zh": {
            "verdict": "watch",
            "summary": "长势有些走弱迹象，NDVI 在下降或波动——值得留意。",
            "advice": [
                "7 天内检查土壤墒情，表层干了就及时补水。",
                "查看叶片有无发黄、斑点、卷叶，先排查是否缺水。",
                "翻一下最近的水肥记录，有没有漏施。",
            ],
        },
    },
    "alert": {
        "en": {
            "verdict": "alert",
            "summary": "Canopy vigor dropped sharply. NDVI shows a sudden decline — immediate field check recommended.",
            "advice": [
                "Walk the plot within 7 days; compare weak spots with healthy areas side by side.",
                "Check irrigation system coverage — dry corners or blocked emitters may be the cause.",
                "If water and nutrition check out, consult the local agricultural extension for diagnosis.",
            ],
        },
        "zh": {
            "verdict": "alert",
            "summary": "长势明显走弱，NDVI 突降——建议尽快下地查看。",
            "advice": [
                "7 天内下地走一圈，对比长势弱和好的地方。",
                "检查灌溉有没有死角——边角干、滴头堵都可能导致局部差。",
                "水肥查不出问题，就找当地农技站帮忙看看。",
            ],
        },
    },
}


# ---------------------------------------------------------------------------
# Ollama Gemma integration
# ---------------------------------------------------------------------------

def _ollama_generate(prompt: str) -> str:
    """Call the local Ollama generate API; raise on any failure."""
    resp = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3},
        },
        timeout=TIMEOUT_SEC,
    )
    resp.raise_for_status()
    payload = json.loads(resp.content.decode("utf-8"))
    return payload.get("response", "").strip()


def _build_prompt(ndvi_data: dict, crop: str, lang: str, features: dict) -> str:
    """Build a rich prompt with Python-computed features and all context."""
    series = ", ".join(
        f"{d}: {v:.3f}" for d, v in zip(ndvi_data.get("dates", []), ndvi_data.get("ndvi", []))
    )
    crop_name = CROPS.get(crop, CROPS["pomelo"])[lang]

    # Feature summary line (so the model doesn't recompute)
    feat_line = (
        f"trend={features['trend']}, verdict={features['verdict']}, "
        f"slope={features['slope']}, last_drop={features['last_drop']}, "
        f"consecutive_decline={features['consecutive_decline']}, "
        f"has_gap={features['has_gap']}"
    )

    if lang == "zh":
        return (
            f"{PROMPTS['zh']}\n\n"
            f"作物：{crop_name}。\n"
            f"Python 计算的特征：{feat_line}。\n"
            f"NDVI 时间序列（日期: 数值）：{series}\n"
            f"缺口说明：{features['gap_note'] or '无'}\n\n"
            "第一行给结论，然后一句总结，再列建议。"
        )
    return (
        f"{PROMPTS['en']}\n\n"
        f"Crop: {crop_name}.\n"
        f"Python-computed features: {feat_line}.\n"
        f"NDVI time series (date: value): {series}\n"
        f"Gap note: {features['gap_note'] or 'none'}\n\n"
        "First line: verdict. Then summary. Then actions."
    )


def _parse_model_output(text: str) -> dict:
    """Split model output into verdict, summary sentence, and advice lines."""
    lines = [ln.strip(" -*•\t") for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    if not lines:
        return {"verdict": "", "summary": "", "advice": []}

    # First line might be the verdict
    verdict = ""
    summary_idx = 0
    first_lower = lines[0].lower()
    if first_lower.startswith(("vigorous", "watch", "alert")):
        verdict = first_lower.split()[0]
        summary_idx = 1
    elif "vigorous" in first_lower:
        verdict = "vigorous"
        summary_idx = 1
    elif "alert" in first_lower:
        verdict = "alert"
        summary_idx = 1
    elif "watch" in first_lower:
        verdict = "watch"
        summary_idx = 1

    remaining = lines[summary_idx:]
    if not remaining:
        return {"verdict": verdict, "summary": lines[0], "advice": []}

    summary = remaining[0]
    advice = [ln for ln in remaining[1:] if len(ln) > 3][:3]
    return {"verdict": verdict, "summary": summary, "advice": advice}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_report(ndvi_data: dict, crop: str = "pomelo", lang: str = "en") -> dict:
    """Generate one advisory report in the requested language.

    Returns {"verdict", "summary", "advice", "trend", "source", "gap_note"}.
    Never raises: model failure falls back to bilingual rule templates.
    """
    if lang not in ("en", "zh"):
        lang = "en"
    if crop not in CROPS:
        crop = "pomelo"

    features = compute_features(ndvi_data)
    gap_note = features["gap_note"]

    # Try the local Gemma model first
    if features["cleaned_ndvi"]:
        try:
            text = _ollama_generate(_build_prompt(ndvi_data, crop, lang, features))
            parsed = _parse_model_output(text)
            if parsed["summary"]:
                # Use Python-computed verdict if model didn't provide one
                verdict = parsed["verdict"] or features["verdict"]
                return {
                    "verdict": verdict,
                    "summary": parsed["summary"],
                    "advice": parsed["advice"],
                    "trend": features["trend"],
                    "source": "model",
                    "gap_note": gap_note,
                }
        except Exception:  # noqa: BLE001 - any Ollama failure → fallback
            pass

    # Fallback: bilingual rule templates keyed by verdict
    fb = FALLBACK[features["verdict"]][lang]
    return {
        "verdict": fb["verdict"],
        "summary": fb["summary"],
        "advice": fb["advice"],
        "trend": features["trend"],
        "source": "fallback",
        "gap_note": gap_note,
    }


def generate_bilingual(ndvi_data: dict, crop: str = "pomelo") -> dict:
    """Generate both EN and ZH reports in one call (features computed once)."""
    features = compute_features(ndvi_data)
    gap_note = features["gap_note"]
    trend = features["trend"]
    verdict = features["verdict"]

    reports = {}
    for lang in ("en", "zh"):
        if features["cleaned_ndvi"]:
            try:
                text = _ollama_generate(_build_prompt(ndvi_data, crop, lang, features))
                parsed = _parse_model_output(text)
                if parsed["summary"]:
                    v = parsed["verdict"] or verdict
                    reports[lang] = {
                        "verdict": v,
                        "summary": parsed["summary"],
                        "advice": parsed["advice"],
                        "trend": trend,
                        "source": "model",
                        "gap_note": gap_note,
                    }
                    continue
            except Exception:  # noqa: BLE001
                pass

        fb = FALLBACK[verdict][lang]
        reports[lang] = {
            "verdict": fb["verdict"],
            "summary": fb["summary"],
            "advice": fb["advice"],
            "trend": trend,
            "source": "fallback",
            "gap_note": gap_note,
        }

    return {"trend": trend, "verdict": verdict, "en": reports["en"], "zh": reports["zh"]}


# Backward compatibility: old code may import compute_trend
def compute_trend(ndvi: list) -> str:
    """Backward-compat shim — use compute_features() for full features."""
    return compute_features({"ndvi": ndvi, "dates": []})["trend"]
