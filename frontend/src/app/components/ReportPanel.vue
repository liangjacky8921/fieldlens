<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Chart, CategoryScale, Filler, Legend, LineController, LineElement, LinearScale, PointElement, Tooltip } from 'chart.js'
import { i18n, useT } from '../../i18n'

const props = defineProps<{ geojson: object | null }>()

const t = useT()

// Tree-shaken Chart.js: line chart only
Chart.register(LineController, LineElement, PointElement, LinearScale, CategoryScale, Tooltip, Filler)
Chart.defaults.color = '#a7b8ad'
Chart.defaults.borderColor = 'rgba(232, 239, 233, 0.08)'

// API base: empty (same-origin) by default; VITE_API_BASE_URL set at build time for cross-deploy
const API_BASE = (import.meta as any).env?.VITE_API_BASE_URL || ''

const crop = ref('pomelo')
const loading = ref(false)
const statusMsg = ref('')
const statusKind = ref<'info' | 'error'>('info')
const lastReport = ref<any>(null)
const isDemo = ref(false)
const canvasRef = ref<HTMLCanvasElement | null>(null)
let chart: Chart | null = null

// ---------------------------------------------------------------------------
// Demo data — shown when backend is unreachable (e.g. Vercel-only deployment).
// This keeps /app visually functional for hackathon demos.
// ---------------------------------------------------------------------------
const DEMO = {
  ndvi: {
    dates: ['2026-09-17', '2026-09-24', '2026-09-27', '2026-10-07', '2026-10-12'],
    ndvi: [0.412, 0.528, 0.487, 0.613, 0.554],
    count: 5,
  },
  report: {
    trend: 'stable',
    en: {
      summary: 'Canopy vigor is stable across the past 30 days of Sentinel-2 scenes. NDVI stays in the healthy range with no upward or downward drift.',
      advice: [
        'Maintain routine irrigation and fertilization — no urgent action needed.',
        'Do a regular pest and disease walk-through every 1–2 weeks.',
        'Watch the next few satellite passes for any sign of decline after rain.',
      ],
      source: 'demo',
      trend: 'stable',
    },
    zh: {
      summary: '过去 30 天 Sentinel-2 影像显示果树长势平稳，NDVI 保持在健康区间，未见明显上升或下降趋势。',
      advice: [
        '按常规水肥管理即可，暂无紧急事项。',
        '每 1–2 周例行巡查一次病虫害。',
        '关注雨后后续卫星影像，警惕由稳转弱。',
      ],
      source: 'demo',
      trend: 'stable',
    },
  },
}

const rep = computed(() => {
  const r = lastReport.value?.report
  if (!r) return null
  return r.en && r.zh ? r[i18n.lang] : r
})

const trendKey = computed(() => lastReport.value?.report?.trend ?? rep.value?.trend ?? 'stable')

watch([rep, trendKey, () => lastReport.value?.ndvi], renderChart, { deep: false })

function renderChart() {
  const ndvi = lastReport.value?.ndvi
  if (!canvasRef.value || !ndvi?.dates?.length) return
  chart?.destroy()
  chart = new Chart(canvasRef.value, {
    type: 'line',
    data: {
      labels: ndvi.dates,
      datasets: [
        {
          label: 'NDVI',
          data: ndvi.ndvi,
          borderColor: '#d4a44e',
          backgroundColor: 'rgba(212, 164, 78, 0.16)',
          fill: true,
          tension: 0.3,
          pointRadius: 3,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: { y: { suggestedMin: 0, suggestedMax: 1 } },
      plugins: { legend: { display: false } },
    },
  })
}

async function generate() {
  if (!props.geojson) {
    statusMsg.value = t('needPolygon')
    statusKind.value = 'error'
    return
  }

  loading.value = true
  statusMsg.value = t('generating')
  statusKind.value = 'info'
  lastReport.value = null
  isDemo.value = false

  try {
    // AbortController: 15s timeout so Render cold-start (sleeping free tier)
    // doesn't hang the UI forever — falls back to demo data gracefully.
    const ctrl = new AbortController()
    const tid = setTimeout(() => ctrl.abort(), 15000)

    const resp = await fetch(`${API_BASE}/api/report`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      signal: ctrl.signal,
      // lang=both: one call returns EN + ZH so the toggle is instant
      body: JSON.stringify({ geojson: props.geojson, crop: crop.value, lang: 'both' }),
    })
    clearTimeout(tid)

    if (!resp.ok) {
      // Backend unreachable or non-200 → gracefully fall back to demo data
      throw new Error(`HTTP ${resp.status}`)
    }

    const data = await resp.json()
    if (data.ndvi && data.ndvi.error) {
      statusMsg.value = /GEE/i.test(data.ndvi.error) ? t('errGee') : t('noData')
      statusKind.value = 'error'
      return
    }
    if (!data.report) {
      statusMsg.value = t('errGeneric')
      statusKind.value = 'error'
      return
    }

    lastReport.value = data
    statusMsg.value = ''
  } catch {
    // Demo mode: show sample data so the UI isn't dead during hackathon demos.
    lastReport.value = DEMO
    isDemo.value = true
    statusMsg.value = ''
    statusKind.value = 'info'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="panel">
    <p class="hint">{{ t('drawHint') }}</p>

    <div class="controls">
      <select v-model="crop" class="crop">
        <option value="pomelo">{{ t('cropPomelo') }}</option>
        <option value="citrus">{{ t('cropCitrus') }}</option>
      </select>
      <button class="btn btn--primary gen" type="button" :disabled="loading" @click="generate">
        {{ loading ? t('generating') : t('generate') }}
      </button>
    </div>

    <p class="status" :class="{ error: statusKind === 'error' }">
      <span v-if="loading" class="spinner" aria-hidden="true"></span>{{ statusMsg }}
      <span v-if="isDemo" class="demo-badge">DEMO · 示例数据</span>
    </p>

    <article v-if="rep" class="card">
      <div class="card-head">
        <h2>{{ t('trendTitle') }}</h2>
        <span class="badge" :class="trendKey">{{ t('trend')[trendKey] || trendKey }}</span>
      </div>
      <p class="summary">{{ rep.summary }}</p>
      <h2 class="advice-title">{{ t('adviceTitle') }}</h2>
      <ul class="advice">
        <li v-for="(a, i) in rep.advice || []" :key="i">{{ a }}</li>
      </ul>
    </article>

    <article v-if="lastReport?.ndvi?.dates?.length" class="card">
      <h2>{{ t('chartTitle') }}</h2>
      <div class="chart-wrap"><canvas ref="canvasRef"></canvas></div>
    </article>

    <p v-if="lastReport" class="data-note">{{ t('dataNote') }}</p>
  </div>
</template>

<style scoped>
.panel {
  max-width: 760px;
  margin: 0 auto;
  padding: 18px clamp(16px, 4vw, 32px) 40px;
}

.hint {
  font-size: 13px;
  color: var(--ink-2);
  margin-bottom: 10px;
}

.controls {
  display: flex;
  gap: 10px;
  margin-bottom: 8px;
}

.crop {
  flex: 1;
  padding: 12px;
  border-radius: 8px;
  font-size: 15px;
  border: 1px solid var(--line-strong);
  background: var(--bg-raised);
  color: var(--ink);
}

.gen { flex: 1; }

.gen:disabled {
  background: #3a4a41;
  color: var(--ink-3);
  cursor: not-allowed;
}

.status {
  font-size: 13px;
  min-height: 20px;
  margin: 6px 0 4px;
  color: var(--amber-bright);
}

.status.error { color: #e08b7d; }

.spinner {
  display: inline-block;
  width: 13px;
  height: 13px;
  border: 2px solid var(--amber-deep);
  border-top-color: var(--amber-bright);
  border-radius: 50%;
  vertical-align: -2px;
  margin-right: 6px;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.card {
  background: var(--bg-raised);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 16px;
  margin-top: 14px;
}

.card h2 {
  font-size: 15px;
  color: var(--ink);
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
}

.badge {
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 12.5px;
  font-weight: 600;
  color: #100e0a;
}

.badge.rising { background: var(--amber-bright); }
.badge.stable { background: var(--blue); }
.badge.declining { background: var(--red); }
.badge.volatile { background: #a39472; }

.summary {
  margin-top: 6px;
  font-size: 14.5px;
  line-height: 1.7;
  color: var(--ink);
}

.advice-title { margin-top: 16px; }

.advice {
  margin-top: 8px;
  padding-left: 20px;
  font-size: 14px;
  line-height: 1.75;
  color: var(--ink-2);
}

.chart-wrap {
  position: relative;
  height: 220px;
  margin-top: 10px;
}

.data-note {
  margin-top: 14px;
  font-size: 11.5px;
  color: var(--ink-3);
}

.demo-badge {
  display: inline-block;
  margin-left: 8px;
  padding: 1px 8px;
  border-radius: 3px;
  background: var(--amber-deep);
  color: var(--amber-bright);
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: 0.1em;
  vertical-align: middle;
}

@media (max-width: 600px) {
  .panel { padding: 14px clamp(12px, 4vw, 20px) 32px; }
  .controls { flex-direction: column; }
  .crop, .gen { width: 100%; flex: none; }
  .card { padding: 14px; }
  .chart-wrap { height: 200px; }
  .summary { font-size: 14px; line-height: 1.65; }
  .advice { font-size: 13.5px; }
  .card-head h2 { font-size: 14px; }
  .hint { font-size: 12.5px; }
}
</style>
