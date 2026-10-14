<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Chart, CategoryScale, Filler, Legend, LineController, LineElement, LinearScale, PointElement, Tooltip } from 'chart.js'
import { i18n, useT } from '../../i18n'
import { SAMPLE_NDVI, SAMPLE_REPORT, LEGEND_STOPS } from '../../data/references'

const props = defineProps<{ geojson: object | null }>()
const emit = defineEmits<{ (e: 'load-demo'): void; (e: 'clear'): void }>()

const t = useT()

Chart.register(LineController, LineElement, PointElement, LinearScale, CategoryScale, Tooltip, Filler)
Chart.defaults.color = '#a7b8ad'
Chart.defaults.borderColor = 'rgba(232, 239, 233, 0.08)'

const API_BASE = (import.meta as any).env?.VITE_API_BASE_URL || ''

const crop = ref('pomelo')
const loading = ref(false)
const statusMsg = ref('')
const statusKind = ref<'info' | 'error'>('info')
const lastReport = ref<any>(null)
const isDemo = ref(false)
const canvasRef = ref<HTMLCanvasElement | null>(null)
let chart: Chart | null = null

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

function loadDemo() {
  isDemo.value = true
  lastReport.value = { ndvi: SAMPLE_NDVI, report: SAMPLE_REPORT, crop: 'pomelo' }
  statusMsg.value = ''
  statusKind.value = 'info'
  emit('load-demo')
}

function clearAll() {
  isDemo.value = false
  lastReport.value = null
  statusMsg.value = ''
  statusKind.value = 'info'
  emit('clear')
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
    const ctrl = new AbortController()
    const tid = setTimeout(() => ctrl.abort(), 15000)

    const resp = await fetch(`${API_BASE}/api/report`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      signal: ctrl.signal,
      body: JSON.stringify({ geojson: props.geojson, crop: crop.value, lang: 'both' }),
    })
    clearTimeout(tid)

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
  } catch {
    statusMsg.value = t('errNetwork')
    statusKind.value = 'error'
  } finally {
    loading.value = false
  }
}

const legendStops = computed(() => LEGEND_STOPS)
</script>

<template>
  <div class="panel">
    <!-- Controls: demo field + clear + crop select + generate -->
    <div class="controls">
      <button class="btn btn--ghost demo-btn" type="button" @click="loadDemo">
        {{ t('loadDemo') }}
      </button>
      <button class="btn btn--ghost clear-btn" type="button" @click="clearAll" v-if="lastReport">
        {{ t('clearBtn') }}
      </button>
    </div>

    <p class="hint">{{ t('drawHint') }}</p>

    <div class="controls controls-gen">
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
      <span v-if="isDemo" class="demo-badge">{{ t('sampleBadge') }}</span>
    </p>

    <!-- Empty state: 3-step guide + NDVI legend -->
    <div v-if="!lastReport && !loading" class="empty-state">
      <div class="steps">
        <div class="step"><span class="step-num">1</span><span>{{ t('emptyStep1') }}</span></div>
        <div class="step-arrow" aria-hidden="true">→</div>
        <div class="step"><span class="step-num">2</span><span>{{ t('emptyStep2') }}</span></div>
        <div class="step-arrow" aria-hidden="true">→</div>
        <div class="step"><span class="step-num">3</span><span>{{ t('emptyStep3') }}</span></div>
      </div>

      <div class="legend">
        <p class="legend-title">{{ t('ndviLegend') }}</p>
        <div class="legend-bar">
          <div class="legend-row" v-for="s in legendStops" :key="s.range">
            <span class="legend-swatch" :style="{ background: s.color }"></span>
            <span class="legend-range">{{ s.range }}</span>
            <span class="legend-label">{{ i18n.lang === 'zh' ? s.labelZh : s.label }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Report card -->
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

    <!-- NDVI chart -->
    <article v-if="lastReport?.ndvi?.dates?.length" class="card">
      <h2>{{ t('chartTitle') }}</h2>
      <div class="chart-wrap"><canvas ref="canvasRef"></canvas></div>
      <p v-if="isDemo" class="sample-note">{{ t('sampleNote') }}</p>
    </article>

    <p v-if="lastReport && !isDemo" class="data-note">{{ t('dataNote') }}</p>
    <p v-if="lastReport && isDemo" class="data-note">{{ t('sampleNote') }}</p>
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

.controls-gen {
  margin-bottom: 8px;
}

.demo-btn, .clear-btn {
  flex: 1;
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 14px;
  border: 1px solid var(--line-strong);
  background: var(--bg-raised);
  color: var(--ink-2);
  cursor: pointer;
  transition: border-color 0.2s, color 0.2s;
}

.demo-btn:hover {
  border-color: var(--amber);
  color: var(--amber-bright);
}

.clear-btn:hover {
  border-color: #e08b7d;
  color: #e08b7d;
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

.legend {
  background: var(--bg-raised);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 14px;
}

.legend-title {
  font-size: 13px;
  color: var(--ink);
  margin-bottom: 10px;
  font-weight: 600;
}

.legend-bar {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.legend-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.legend-swatch {
  width: 16px;
  height: 16px;
  border-radius: 3px;
  flex-shrink: 0;
}

.legend-range {
  color: var(--ink-2);
  font-weight: 600;
  min-width: 70px;
}

.legend-label {
  color: var(--ink-3);
}

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

.sample-note {
  margin-top: 8px;
  font-size: 11.5px;
  color: var(--ink-3);
  font-style: italic;
}

@media (max-width: 600px) {
  .panel { padding: 14px clamp(12px, 4vw, 20px) 32px; }
  .controls, .controls-gen { flex-direction: column; }
  .crop, .gen, .demo-btn, .clear-btn { width: 100%; flex: none; }
  .card { padding: 14px; }
  .chart-wrap { height: 200px; }
  .summary { font-size: 14px; line-height: 1.65; }
  .advice { font-size: 13.5px; }
  .card-head h2 { font-size: 14px; }
  .hint { font-size: 12.5px; }
  .steps { flex-direction: column; align-items: flex-start; }
  .step-arrow { display: none; }
}
</style>
