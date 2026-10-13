"""Grower advisory report generation for FieldLens.

Trend is computed with a deterministic linear fit; summary/advice come from a
local open-source model (Gemma via Ollama). If the model call fails for any
reason, bilingual rule-based templates keep the API fully functional.
"""

import json

import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma2:2b"
TIMEOUT_SEC = 60

CROPS = {
    "pomelo": {"en": "honey pomelo", "zh": "金柚"},
    "citrus": {"en": "citrus", "zh": "柑橘"},
}

PROMPTS = {
    "en": (
        "You are an orchard agronomy advisor. Based on the NDVI time series, "
        "assess the vigor trend and give up to 3 concrete suggestions "
        "(irrigation, fertilization, pest/disease scouting). "
        "Plain English for growers, no jargon, under 200 words."
    ),
    "zh": (
        "你是一位果园农艺顾问。请根据下面的 NDVI 长势时间序列，判断长势趋势，"
        "并给出最多 3 条具体建议（灌溉、施肥、病虫害巡查）。"
        "用果农能听懂的大白话，少用术语，200 字以内。"
    ),
}

# Rule-based fallback templates (bilingual), keyed by trend.
FALLBACK = {
    "rising": {
        "en": {
            "summary": "Canopy vigor is improving over the period. NDVI is trending upward, which usually means healthy leaf growth.",
            "advice": [
                "Keep the current irrigation schedule; do not overwater during vigorous growth.",
                "Scout for pests and diseases while the canopy is dense, especially after rain.",
                "Plan the next fertilization round according to your fruit development stage.",
            ],
        },
        "zh": {
            "summary": "本时段果树长势向好，NDVI 呈上升趋势，通常说明叶片生长健康。",
            "advice": [
                "保持现有灌溉节奏，旺长期避免浇水过量。",
                "树冠茂密期加强雨后病虫害巡查。",
                "按果实发育阶段安排下一轮施肥。",
            ],
        },
    },
    "stable": {
        "en": {
            "summary": "Canopy vigor is stable. NDVI shows no clear upward or downward trend over the period.",
            "advice": [
                "Maintain routine irrigation and fertilization; no urgent action needed.",
                "Do a regular pest and disease walk-through every one to two weeks.",
                "Watch the next few satellite passes for any sign of decline.",
            ],
        },
        "zh": {
            "summary": "果树长势平稳，本时段 NDVI 没有明显上升或下降。",
            "advice": [
                "按常规水肥管理即可，暂无紧急事项。",
                "每 1–2 周例行巡查一次病虫害。",
                "留意后续卫星影像，警惕由稳转弱。",
            ],
        },
    },
    "declining": {
        "en": {
            "summary": "Canopy vigor is declining. NDVI is trending downward, which can signal water stress, nutrient shortage, or pest/disease pressure.",
            "advice": [
                "Check soil moisture soon; increase irrigation if the topsoil is dry.",
                "Inspect leaves for yellowing, spots, or curling to rule out pests and disease.",
                "Consider a balanced fertilizer application if watering and scouting show no other cause.",
            ],
        },
        "zh": {
            "summary": "果树长势走弱，NDVI 呈下降趋势，可能是缺水、缺肥或病虫害引起。",
            "advice": [
                "尽快检查土壤墒情，表层干了就及时补水。",
                "查看叶片有无发黄、斑点、卷叶，排查病虫害。",
                "若水肥和病虫害都无异常，可考虑补施平衡肥。",
            ],
        },
    },
    "volatile": {
        "en": {
            "summary": "NDVI is fluctuating without a clear trend. This often comes from cloud interference or uneven canopy conditions across the plot.",
            "advice": [
                "Walk the plot and compare weaker spots with stronger ones side by side.",
                "Check irrigation coverage for dry corners or poorly drained low spots.",
                "Re-check the next clear-sky satellite pass before making big input changes.",
            ],
        },
        "zh": {
            "summary": "NDVI 波动较大、趋势不明，常见于云层干扰或地块内长势不均。",
            "advice": [
                "下地对比长势弱和长势好的区域，找出差异原因。",
                "检查灌溉是否覆盖到边角，低洼处是否积水。",
                "等下一次晴朗影像确认后再调整水肥投入。",
            ],
        },
    },
}


def compute_trend(ndvi: list) -> str:
    """Classify the series as rising / stable / declining / volatile.

    Uses a least-squares slope on the sample index plus residual volatility.
    Pure Python (no numpy) so it works even in minimal environments.
    """
    n = len(ndvi)
    if n < 3:
        return "stable"

    xs = list(range(n))
    x_mean = sum(xs) / n
    y_mean = sum(ndvi) / n
    denom = sum((x - x_mean) ** 2 for x in xs) or 1.0
    slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ndvi)) / denom
    intercept = y_mean - slope * x_mean

    residuals = [y - (intercept + slope * x) for x, y in zip(xs, ndvi)]
    volatility = (sum(r * r for r in residuals) / n) ** 0.5

    if volatility > 0.08:
        return "volatile"
    if slope > 0.005:
        return "rising"
    if slope < -0.005:
        return "declining"
    return "stable"


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
    # Ollama may send a misleading charset header — decode raw bytes as UTF-8.
    payload = json.loads(resp.content.decode("utf-8"))
    return payload.get("response", "").strip()


def _build_prompt(ndvi_data: dict, crop: str, lang: str, trend: str) -> str:
    series = ", ".join(
        f"{d}: {v:.3f}" for d, v in zip(ndvi_data.get("dates", []), ndvi_data.get("ndvi", []))
    )
    crop_name = CROPS.get(crop, CROPS["pomelo"])[lang]
    if lang == "zh":
        return (
            f"{PROMPTS['zh']}\n\n"
            f"作物：{crop_name}。检测到的趋势：{trend}。\n"
            f"NDVI 时间序列（日期: 数值）：{series}\n\n"
            "请先给一句总体长势总结，再列出建议，每条建议单独一行。"
        )
    return (
        f"{PROMPTS['en']}\n\n"
        f"Crop: {crop_name}. Detected trend: {trend}.\n"
        f"NDVI time series (date: value): {series}\n\n"
        "Start with one summary sentence, then list each suggestion on its own line."
    )


def _parse_model_output(text: str) -> dict:
    """Split model output into a summary sentence and advice bullet lines."""
    lines = [ln.strip(" -*•\t") for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    if not lines:
        return {"summary": "", "advice": []}
    summary, advice = lines[0], [ln for ln in lines[1:] if len(ln) > 3][:3]
    return {"summary": summary, "advice": advice}


def generate_report(ndvi_data: dict, crop: str = "pomelo", lang: str = "en") -> dict:
    """Generate one advisory report in the requested language.

    Returns {"summary": str, "advice": [str], "trend": str, "source": "model"|"fallback"}.
    Never raises: model failure falls back to bilingual rule templates.
    """
    if lang not in ("en", "zh"):
        lang = "en"
    if crop not in CROPS:
        crop = "pomelo"

    ndvi_values = ndvi_data.get("ndvi", []) or []
    trend = compute_trend(ndvi_values)

    if ndvi_values:
        try:
            text = _ollama_generate(_build_prompt(ndvi_data, crop, lang, trend))
            parsed = _parse_model_output(text)
            if parsed["summary"]:
                return {**parsed, "trend": trend, "source": "model"}
        except Exception:  # noqa: BLE001 - any Ollama failure -> fallback
            pass

    fallback = FALLBACK[trend][lang]
    return {**fallback, "trend": trend, "source": "fallback"}


def generate_bilingual(ndvi_data: dict, crop: str = "pomelo") -> dict:
    """Generate both EN and ZH reports in one call (trend computed once)."""
    trend = compute_trend(ndvi_data.get("ndvi", []) or [])
    return {
        "trend": trend,
        "en": generate_report(ndvi_data, crop, "en"),
        "zh": generate_report(ndvi_data, crop, "zh"),
    }
