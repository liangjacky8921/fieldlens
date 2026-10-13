# FieldLens

Satellite vigor monitoring for high-value orchards (Meizhou pomelo / citrus).
Draw a field boundary on the map → Sentinel-2 NDVI time series (Google Earth Engine)
→ local open-source LLM (Gemma via Ollama) grower advisory in English and Chinese.

- `/` — landing page: dark material design, one signature Aurora visual, animated copy
- `/app` — field tool: Leaflet map + NDVI chart + bilingual report (no landing animations)

## Stack

- Python 3.10+ · FastAPI · earthengine-api · requests
- Ollama running `gemma2:2b` locally (bilingual EN/ZH report generation, with rule-based fallback)
- Vue 3 + Vite multi-page frontend (`frontend/`), built into `static/`:
  - landing: vue-bits components (source-installed) + Lenis smooth scroll + VueUse
  - tool: Leaflet + leaflet-draw + Chart.js (npm, offline-capable)

## Local setup

```bash
# 1. Google Earth Engine (one-time)
#    GEE now requires a Cloud project (e.g. seventh-acrobat-494312-s0).
#    - Run `earthengine authenticate` (opens a browser)
#    - Set the project:  set EE_PROJECT=<your-project-id>   (Windows)
#                        export EE_PROJECT=<your-project-id> (Linux/macOS)
#    Or just run start.bat on Windows, which sets it for you.

# 2. Local LLM (one-time, ~1.6 GB download)
ollama pull gemma2:2b

# 3. Backend deps
pip install -r requirements.txt

# 4. Run
uvicorn app.main:app --reload
# open http://127.0.0.1:8000/        (landing)
#      http://127.0.0.1:8000/app     (field tool)
```

### Rebuilding the frontend (only needed after editing `frontend/`)

```bash
cd frontend
npm install
npm run build     # outputs to ../static (landing index.html + app.html + assets/)
```

## API

- `GET  /health` — liveness + GEE auth status
- `POST /api/ndvi` — body `{"geojson": <Polygon>, "days": 90}` → `{"dates": [...], "ndvi": [...], "count": n}`
- `POST /api/report` — body `{"geojson": <Polygon>, "crop": "pomelo"|"citrus", "lang": "en"|"zh"|"both"}`
  → NDVI series + advisory report (`trend` / `summary` / `advice[]`); `lang=both` returns EN+ZH in one call

If GEE is not authenticated, `/api/ndvi` and `/api/report` return a structured
`{"error": "GEE not authenticated", "hint": "..."}` instead of crashing.
If Ollama is down, reports fall back to bilingual rule-based templates.

## Frontend dependencies record

Rule: install only what the current stage needs; every dependency records reason,
version, and bundle-size impact. Components from vue-bits are installed as reviewed
source files (`frontend/src/vuebits/`), not as an npm package — no `npx jsrepo`
script was executed; registry JSON was downloaded and audited manually.

| Dependency | Version | License | Reason | Bundle impact (build output) |
|---|---|---|---|---|
| vue | ^3.5 | MIT | App framework for the Vue 3 rewrite of the tool page | shared `i18n` chunk ~71 KB raw / 29 KB gzip |
| vite + @vitejs/plugin-vue | ^7 / ^6 | MIT | Build tooling (dev only, not shipped) | — |
| ogl | ^1.0.11 | MIT | WebGL renderer required by vue-bits Aurora + Line Waves backgrounds | inside landing `main` chunk, 214 KB raw / 77 KB gzip total |
| gsap | ^3.13.0 | MIT (all plugins free since 3.13) | vue-bits Split Text entrance animation (per-word/char) | included in landing chunk above |
| lenis | ^1.3.26 | MIT | Smooth scrolling on the landing page only (tool page never loads it); honors prefers-reduced-motion | ~5 KB gzip |
| @vueuse/core | ^14 | MIT | usePreferredReducedMotion (skip WebGL when user opts out), useScroll (nav state) | tree-shaken, <2 KB gzip |
| leaflet + leaflet-draw | ^1.9.4 / ^1.0.4 | BSD-2 / MIT | Field boundary drawing (migrated from CDN to npm so demos work offline) | tool chunk 374 KB raw / 113 KB gzip |
| chart.js | ^4.4.3 | MIT | NDVI line chart, registered line-only (tree-shaken) | included in tool chunk |

TresJS evaluated and **not** installed: no business case for 3D, and meaningless 3D
is explicitly out of scope for this project.

vue-bits licensing note: MIT + Commons Clause — use as part of an application is
explicitly permitted; only reselling/redistributing the components themselves is
restricted. Copyright headers are kept in each component file.
