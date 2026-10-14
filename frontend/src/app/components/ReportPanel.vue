<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Chart, CategoryScale, Filler, Legend, LineController, LineElement, LinearScale, PointElement, Tooltip } from 'chart.js'
import { i18n, useT } from '../../i18n'
import { SAMPLE_NDVI } from '../../data/references'
import { generateDemoReport } from '../../data/analyze'

const props = defineProps<{ geojson: object | null }>()
const emit = defineEmits<{ (e: 'report', data: any): void }>()

const t = useT()

Chart.register(LineController, LineElement, PointElement, LinearScale, CategoryScale, Tooltip, Filler)
Chart.defaults.color = '#a7b8ad'
Chart.defaults.borderColor = 'rgba(232, 239, 233, 0.08)'

const API_BASE = (import.meta as any).env?.VITE_API_BASE_URL || ''

const crop = ref('pomelo')
const loading = ref(false)
const loadingStep = ref(0)
const statusMsg = ref('')
const statusKind = ref<'info' | 'error'>('info')
const lastReport = ref<any>(null)
const isDemo = ref(false)
const canvasRef = ref<HTMLCanvasElement | null>(null)
let chart: Chart | null = null
let stepTimer: ReturnType<typeof setInterval> | null = null

const rep = computed(() => {
  const r = lastReport.value?.report
  if (!r) return null
  return r.en && r.zh ? r[i18n.lang] : r
})

const trendKey = computed(() => lastReport.value?.report?.trend ?? rep.value?.trend ?? 'stable')
const verdictKey = computed(() => rep.value?.verdict ?? 'watch')
const gapNote = computed(() => rep.value?.gap_note ?? '')
const engineKey = computed(() => rep.value?.source ?? (isDemo.value ? 'sample' : 'fallback'))

// --- KPI summary row computed values ---
const ndviValues = computed(() => lastReport.value?.ndvi?.ndvi ?? [])
const latestNdvi = computed(() => {
  const arr = ndviValues.value
  return arr.length ? arr[arr.length - 1] : null
})
const ndviMean = computed(() => {
  const arr = ndviValues.value
  if (!arr.length) return null
  return arr.reduce((a: number, b: number) => a + b, 0) / arr.length
})
const ndviRange = computed(() => {
  const arr = ndviValues.value
  if (!arr.length) return null
  return Math.max(...arr) - Math.min(...arr)
})
const validPasses = computed(() => ndviValues.value.length)
const latestHealthClass = computed(() => {
  const v = latestNdvi.value
  if (v === null) return 'mid'
  if (v >= 0.6) return 'good'
  if (v >= 0.4) return 'mid'
  return 'low'
})

watch([rep, trendKey, () => lastReport.value?.ndvi], renderChart, { deep: false })

// Loading step animation: cycle through messages every 4s
watch(loading, (isLoading) => {
  if (isLoading) {
    loadingStep.value = 0
    stepTimer = setInterval(() => {
      loadingStep.value = (loadingStep.value + 1) % 2
    }, 4000)
  } else {
    if (stepTimer) { clearInterval(stepTimer); stepTimer = null }
  }
})

const loadingText = computed(() => {
  if (loadingStep.value === 0) return t('loadStep1')
  return t('loadStep2')
})

// --- Anomaly detection for chart ---
function detectAnomalies(values: number[]): boolean[] {
  return values.map((v, i) => {
    if (v < 0.35) return true
    // Sudden dip: much lower than both neighbors
    if (i > 0 && i < values.length - 1) {
      const avg = (values[i - 1] + values[i + 1]) / 2
      if (v < avg - 0.15) return true
    }
    return false
  })
}

function renderChart() {
  const ndvi = lastReport.value?.ndvi
  if (!canvasRef.value || !ndvi?.dates?.length) return
  chart?.destroy()

  const values: number[] = ndvi.ndvi
  const anomalies = detectAnomalies(values)

  // Health baseline dataset: flat line at 0.65
  const baselineData = values.map(() => 0.65)

  // Per-point styling: anomalies get amber border + larger radius
  const pointBg = values.map((v) => v >= 0.65 ? '#7fa388' : v >= 0.4 ? '#d4a44e' : '#c26856')
  const pointBorder = anomalies.map((a) => a ? '#e8b73a' : 'rgba(212, 164, 78, 0.3)')
  const pointRadius = anomalies.map((a) => a ? 6 : 3)
  const pointHoverRadius = anomalies.map(() => 8)

  chart = new Chart(canvasRef.value, {
    type: 'line',
    data: {
      labels: ndvi.dates,
      datasets: [
        {
          label: 'NDVI',
          data: values,
          borderColor: '#d4a44e',
          backgroundColor: 'rgba(212, 164, 78, 0.16)',
          fill: true,
          tension: 0.3,
          pointRadius,
          pointHoverRadius,
          pointBackgroundColor: pointBg,
          pointBorderColor: pointBorder,
          pointBorderWidth: 2,
        },
        {
          label: t('healthBaseline'),
          data: baselineData,
          borderColor: 'rgba(232, 183, 58, 0.4)',
          borderDash: [6, 4],
          borderWidth: 1.5,
          fill: false,
          pointRadius: 0,
          pointHoverRadius: 0,
          tension: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { suggestedMin: 0, suggestedMax: 1, ticks: { font: { size: 11 } } },
        x: { ticks: { font: { size: 10 }, maxRotation: 45 } },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(16, 14, 10, 0.92)',
          borderColor: 'rgba(212, 164, 78, 0.35)',
          borderWidth: 1,
          titleColor: '#e8b73a',
          bodyColor: '#f0ebe2',
          titleFont: { size: 13, weight: 600 },
          bodyFont: { size: 12 },
          padding: 12,
          cornerRadius: 8,
          displayColors: false,
          filter: (item: any) => item.datasetIndex === 0,
          callbacks: {
            label: (ctx: any) => {
              const val = ctx.parsed.y
              const level = val >= 0.65 ? t('healthLevelVigorous') : val >= 0.4 ? t('healthLevelWatch') : t('healthLevelAlert')
              return `NDVI ${val.toFixed(2)} · ${level}`
            },
            afterLabel: (ctx: any) => {
              if (anomalies[ctx.dataIndex]) return t('cloudArtifact')
              return ''
            },
          },
        },
      },
    },
  })
}

function loadDemo() {
  isDemo.value = true
  const report = generateDemoReport(SAMPLE_NDVI, 'pomelo')
  lastReport.value = { ndvi: SAMPLE_NDVI, report, crop: 'pomelo' }
  statusMsg.value = ''
  statusKind.value = 'info'
  emit('report', lastReport.value)
}

function clearAll() {
  isDemo.value = false
  lastReport.value = null
  statusMsg.value = ''
  statusKind.value = 'info'
  emit('report', null)
}

// Render free-tier cold start takes 30-60s; GEE query ~2-5s.
// 120s covers both with margin; auto-retry once on failure.
async function callReport(geojson: object, crop: string): Promise<Response> {
  const ctrl = new AbortController()
  const tid = setTimeout(() => ctrl.abort(), 120000)
  try {
    const resp = await fetch(`${API_BASE}/api/report`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      signal: ctrl.signal,
      body: JSON.stringify({ geojson, crop, lang: 'both' }),
    })
    clearTimeout(tid)
    return resp
  } catch (err) {
    clearTimeout(tid)
    throw err
  }
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
    let resp = await callReport(props.geojson, crop.value)

    // Auto-retry once on network failure (Render cold-start may drop first request)
    if (!resp.ok && resp.status >= 500) {
      statusMsg.value = t('retrying')
      resp = await callReport(props.geojson, crop.value)
    }

    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)

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
    emit('report', data)
  } catch {
    statusMsg.value = t('errNetwork')
    statusKind.value = 'error'
  } finally {
    loading.value = false
  }
}

defineExpose({ loadDemo, clearAll })
</script>

<template>
  <div class="panel">
    <p class="hint">{{ t('drawHint') }}</p>

    <!-- Crop select + generate -->
    <div class="controls-gen">
      <select v-model="crop" class="crop">
        <option value="pomelo">{{ t('cropPomelo') }}</option>
        <option value="citrus">{{ t('cropCitrus') }}</option>
      </select>
      <button class="btn btn--primary gen" type="button" :disabled="loading" @click="generate">
        {{ loading ? t('generating') : t('generate') }}
      </button>
    </div>

    <!-- Status / loading step -->
    <p class="status" :class="{ error: statusKind === 'error' }">
      <span v-if="loading" class="spinner" aria-hidden="true"></span>
      <span v-if="loading" class="loading-text">{{ loadingText }}</span>
      <template v-else>{{ statusMsg }}</template>
      <span v-if="isDemo" class="demo-badge">{{ t('sampleBadge') }}</span>
    </p>

    <!-- Loading skeleton with breathing animation -->
    <div v-if="loading" class="loading-skeleton">
      <div class="breath-line"></div>
      <div class="breath-line short"></div>
      <div class="breath-line mid"></div>
    </div>

    <!-- Empty state: 3-step guide -->
    <div v-if="!lastReport && !loading" class="empty-state">
      <div class="steps">
        <div class="step"><span class="step-num">1</span><span>{{ t('emptyStep1') }}</span></div>
        <div class="step-arrow" aria-hidden="true">→</div>
        <div class="step"><span class="step-num">2</span><span>{{ t('emptyStep2') }}</span></div>
        <div class="step-arrow" aria-hidden="true">→</div>
        <div class="step"><span class="step-num">3</span><span>{{ t('emptyStep3') }}</span></div>
      </div>
    </div>

    <!-- KPI summary row -->
    <div v-if="rep && latestNdvi !== null" class="kpi-row">
      <div class="kpi-card">
        <p class="kpi-label">{{ t('kpiLatestNdvi') }}</p>
        <p class="kpi-value">
          <span class="health-dot" :class="latestHealthClass"></span>
          {{ latestNdvi!.toFixed(2) }}
        </p>
      </div>
      <div class="kpi-card">
        <p class="kpi-label">{{ t('kpiMean') }}</p>
        <p class="kpi-value">{{ ndviMean!.toFixed(2) }} <span class="kpi-sub">±{{ ndviRange!.toFixed(2) }}</span></p>
      </div>
      <div class="kpi-card">
        <p class="kpi-label">{{ t('kpiPasses') }}</p>
        <p class="kpi-value">{{ validPasses }} <span class="kpi-sub">{{ t('kpiScenes') }}</span></p>
        <p class="kpi-sat">{{ t('kpiSatellite') }}</p>
      </div>
    </div>

    <!-- Report card -->
    <article v-if="rep" class="card">
      <!-- Verdict: first, large, unmissable -->
      <div class="verdict-bar" :class="verdictKey">
        <span class="verdict-label">{{ t('verdict')[verdictKey] || verdictKey }}</span>
        <span class="engine-tag" :class="engineKey">{{ t('engine')[engineKey] || engineKey }}</span>
      </div>

      <p v-if="rep?.season_note" class="season-note">{{ rep.season_note }}</p>

      <div class="card-head">
        <h2>{{ t('trendTitle') }}</h2>
        <span class="badge badge--sub" :class="trendKey">{{ t('trend')[trendKey] || trendKey }}</span>
      </div>
      <p v-if="gapNote" class="gap-note">{{ gapNote }}</p>
      <p class="summary">{{ rep.summary }}</p>
      <h2 class="advice-title">{{ t('adviceTitle') }}</h2>
      <ul class="advice">
        <li v-for="(a, i) in rep.advice || []" :key="i">{{ a }}</li>
      </ul>
    </article>

    <!-- NDVI chart -->
    <article v-if="lastReport?.ndvi?.dates?.length" class="card">
      <h2>{{ t('chartTitle') }}</h2>
      <div class="chart-wrap"><canvas ref="canvasRef"></canvas></div>
      <p v-if="isDemo" class="sample-note">{{ t('sampleNote') }}</p>
    </article>

    <p v-if="lastReport && !isDemo" class="data-note">{{ t('engineLong')[engineKey] || '' }}</p>
    <p v-if="lastReport && isDemo" class="data-note">{{ t('sampleNote') }}</p>
  </div>
</template>

<style scoped>
.panel {
  max-width: 100%;
  margin: 0;
  padding: 18px clamp(16px, 3vw, 28px) 40px;
}

.hint {
  font-size: 13px;
  color: var(--ink-2);
  margin-bottom: 10px;
}

.controls-gen {
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
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.status.error { color: #e08b7d; }

.spinner {
  display: inline-block;
  width: 13px;
  height: 13px;
  border: 2px solid var(--amber-deep);
  border-top-color: var(--amber-bright);
  border-radius: 50%;
  flex-shrink: 0;
  animation: spin 0.8s linear infinite;
}

.loading-text {
  animation: breathe 2s ease-in-out infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }
@keyframes breathe {
  0%, 100% { opacity: 0.65; }
  50% { opacity: 1; }
}

/* Loading skeleton with breathing animation */
.loading-skeleton {
  margin-top: 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.breath-line {
  height: 14px;
  border-radius: 6px;
  background: linear-gradient(90deg, var(--bg-raised), var(--bg-panel), var(--bg-raised));
  background-size: 200% 100%;
  animation: shimmer 2.5s ease-in-out infinite;
}

.breath-line.short { width: 60%; }
.breath-line.mid { width: 85%; }

@keyframes shimmer {
  0%, 100% { background-position: 200% 0; opacity: 0.5; }
  50% { background-position: 0% 0; opacity: 0.8; }
}

/* Empty state */
.empty-state {
  margin-top: 14px;
}

.steps {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.step {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--ink-2);
}

.step-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--amber-deep);
  color: var(--amber-bright);
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}

.step-arrow {
  color: var(--ink-3);
  font-size: 14px;
}

/* KPI summary row */
.kpi-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-top: 14px;
}

.kpi-card {
  background: var(--bg-raised);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 12px 10px;
  text-align: center;
}

.kpi-label {
  font-size: 11px;
  color: var(--ink-3);
  margin-bottom: 6px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.kpi-value {
  font-size: 18px;
  font-weight: 700;
  color: var(--ink);
  font-family: var(--font-serif);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
}

.kpi-sub {
  font-size: 12px;
  font-weight: 400;
  color: var(--ink-3);
}

.kpi-sat {
  font-size: 10px;
  color: var(--ink-3);
  margin-top: 3px;
  letter-spacing: 0.03em;
}

.health-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.health-dot.good { background: var(--green); box-shadow: 0 0 6px rgba(127, 163, 136, 0.5); }
.health-dot.mid { background: var(--amber); box-shadow: 0 0 6px rgba(212, 164, 78, 0.5); }
.health-dot.low { background: var(--red); box-shadow: 0 0 6px rgba(194, 104, 86, 0.5); }

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

.badge--sub {
  font-size: 11px;
  opacity: 0.75;
}

.badge.rising { background: var(--amber-bright); }
.badge.stable { background: var(--blue); }
.badge.declining { background: var(--red); color: #fff; }
.badge.volatile { background: #a39472; }

/* Verdict bar */
.verdict-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 16px;
  border-radius: 8px;
  margin: -4px -4px 14px;
}

.verdict-bar.vigorous { background: rgba(127, 163, 136, 0.18); border: 1px solid rgba(127, 163, 136, 0.35); }
.verdict-bar.watch { background: rgba(212, 164, 78, 0.15); border: 1px solid rgba(212, 164, 78, 0.35); }
.verdict-bar.alert { background: rgba(194, 104, 86, 0.18); border: 1px solid rgba(194, 104, 86, 0.4); }

.verdict-label {
  font-size: 17px;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.verdict-bar.vigorous .verdict-label { color: var(--green); }
.verdict-bar.watch .verdict-label { color: var(--amber-bright); }
.verdict-bar.alert .verdict-label { color: #e08b7d; }

.engine-tag {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 4px;
  letter-spacing: 0.05em;
  white-space: nowrap;
}

.engine-tag.model { background: rgba(127, 163, 136, 0.25); color: var(--green); }
.engine-tag.fallback { background: var(--bg-panel); color: var(--ink-3); }
.engine-tag.sample { background: var(--amber-deep); color: var(--amber-bright); }

.gap-note {
  font-size: 12px;
  color: var(--ink-3);
  font-style: italic;
  margin: 6px 0 8px;
  padding: 6px 10px;
  border-left: 2px solid var(--line-strong);
  background: var(--bg-panel);
  border-radius: 0 4px 4px 0;
}

.season-note {
  font-size: 12.5px;
  color: var(--amber-bright);
  margin: 8px 0;
  padding: 8px 12px;
  border-left: 2px solid var(--amber);
  background: rgba(212, 164, 78, 0.06);
  border-radius: 0 6px 6px 0;
  line-height: 1.6;
}

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
  height: 240px;
  margin-top: 10px;
}

.data-note {
  margin-top: 14px;
  font-size: 11.5px;
  color: var(--ink-3);
}

.demo-badge {
  display: inline-block;
  padding: 1px 8px;
  border-radius: 3px;
  background: var(--amber-deep);
  color: var(--amber-bright);
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: 0.1em;
  vertical-align: middle;
}

.sample-note {
  margin-top: 8px;
  font-size: 11.5px;
  color: var(--ink-3);
  font-style: italic;
}

@media (max-width: 1023px) {
  .panel { padding: 16px clamp(14px, 4vw, 24px) 32px; }
}

@media (max-width: 600px) {
  .panel { padding: 14px clamp(12px, 4vw, 20px) 32px; }
  .controls-gen { flex-direction: column; }
  .crop, .gen { width: 100%; flex: none; }
  .card { padding: 14px; }
  .chart-wrap { height: 200px; }
  .summary { font-size: 14px; line-height: 1.65; }
  .advice { font-size: 13.5px; }
  .card-head h2 { font-size: 14px; }
  .hint { font-size: 12.5px; }
  .steps { flex-direction: column; align-items: flex-start; }
  .step-arrow { display: none; }
  .kpi-row { gap: 8px; }
  .kpi-card { padding: 10px 6px; }
  .kpi-value { font-size: 16px; }
  .kpi-label { font-size: 10px; }
}
</style>
