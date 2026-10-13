<script setup lang="ts">
import { i18n, useT } from '../../i18n'

const t = useT()
const trend = 'rising' as const

// Realistic-looking demo NDVI time series (90 days, 13 observations like our real API)
// A gently rising curve — tells a plausible "healthy orchard, improving season" story
const SERIES = [0.62, 0.58, 0.60, 0.61, 0.65, 0.63, 0.67, 0.69, 0.72, 0.70, 0.74, 0.77, 0.79]
const DATES_EN = ['Jan','Jan','Feb','Feb','Feb','Mar','Mar','Mar','Apr','Apr','Apr','May','May']
const DATES_ZH = ['一月','一月','二月','二月','二月','三月','三月','三月','四月','四月','四月','五月','五月']
const values = i18n.lang === 'zh' ? DATES_ZH : DATES_EN

// Build SVG polyline points — viewBox 520x180, padding left=38 right=14 top=10 bottom=28
const W = 520, H = 180, L = 38, R = 14, T = 10, B = 28
const innerW = W - L - R, innerH = H - T - B
const minV = 0.45, maxV = 0.85
const xAt = (i: number) => L + (i / (SERIES.length - 1)) * innerW
const yAt = (v: number) => T + (1 - (v - minV) / (maxV - minV)) * innerH
const pts = SERIES.map((v, i) => `${xAt(i).toFixed(1)},${yAt(v).toFixed(1)}`).join(' ')
const areaPts = `${L},${yAt(SERIES[0]).toFixed(1)} ${pts} ${xAt(SERIES.length - 1).toFixed(1)},${T + innerH} ${L},${T + innerH}`

// Gradient fill stops (tied to our green palette)
const trendColor = '#e8b73a'   // amber-bright for rising
</script>

<template>
  <section class="data" id="data">
    <div class="shell data-inner">
      <div class="data-copy">
        <p class="kicker">{{ t('dataKicker') }}</p>
        <h2>{{ t('dataTitle') }}</h2>
        <p class="data-lede">{{ t('dataLede') }}</p>
        <div class="data-badge-row">
          <span class="badge rising">{{ t('trend')[trend] }}</span>
          <span class="data-note">{{ t('dataDemoNote') }}</span>
        </div>
        <ul class="data-list">
          <li v-for="item in t('dataFacts')" :key="item">{{ item }}</li>
        </ul>
      </div>

      <div class="data-card" aria-label="Example NDVI trend chart">
        <svg :viewBox="`0 0 ${W} ${H}`" class="data-chart" role="img" aria-hidden="true">
          <!-- Y axis baseline (min) -->
          <line :x1="L" :x2="W - R" :y1="yAt(minV)" :y2="yAt(minV)" stroke="rgba(232,239,233,0.08)" />
          <text :x="L - 8" :y="yAt(minV) + 3" text-anchor="end" class="axis-label">0.45</text>

          <!-- Mid grid line (0.65) -->
          <line :x1="L" :x2="W - R" :y1="yAt(0.65)" :y2="yAt(0.65)" stroke="rgba(232,239,233,0.06)" stroke-dasharray="2,4" />
          <text :x="L - 8" :y="yAt(0.65) + 3" text-anchor="end" class="axis-label">0.65</text>

          <!-- Top grid line (max) -->
          <line :x1="L" :x2="W - R" :y1="yAt(maxV)" :y2="yAt(maxV)" stroke="rgba(232,239,233,0.08)" />
          <text :x="L - 8" :y="yAt(maxV) + 3" text-anchor="end" class="axis-label">0.85</text>

          <!-- Area fill -->
          <defs>
            <linearGradient id="ndviGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#d4a44e" stop-opacity="0.35" />
              <stop offset="100%" stop-color="#d4a44e" stop-opacity="0.02" />
            </linearGradient>
          </defs>
          <polygon :points="areaPts" fill="url(#ndviGrad)" />

          <!-- Line -->
          <polyline :points="pts" fill="none" :stroke="trendColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />

          <!-- Points -->
          <g v-for="(v, i) in SERIES" :key="i">
            <circle :cx="xAt(i)" :cy="yAt(v)" r="2.5" :fill="trendColor" />
          </g>

          <!-- X axis month labels (every 3rd) -->
          <text
            v-for="(label, i) in values"
            v-show="i % 3 === 0"
            :key="`m${i}`"
            :x="xAt(i)"
            :y="H - 8"
            text-anchor="middle"
            class="axis-label"
          >{{ label }}</text>
        </svg>

        <div class="chart-caption">{{ t('dataCaption') }}</div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.data {
  padding: 110px 0 130px;
  border-top: 1px solid var(--line);
}

.data-inner {
  display: grid;
  grid-template-columns: minmax(0, 520px) minmax(0, 420px);
  gap: clamp(40px, 6vw, 84px);
  align-items: center;
}

.data h2 {
  font-size: clamp(28px, 3.4vw, 42px);
  margin-bottom: 16px;
}

.data-lede {
  color: var(--ink-2);
  font-size: 15.5px;
  line-height: 1.8;
  max-width: 480px;
  margin-bottom: 24px;
}

.data-badge-row {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 22px;
}

.badge.rising { background: var(--amber-bright); }
.badge.stable { background: var(--blue); }
.badge.declining { background: var(--red); }
.badge.volatile { background: #a39472; }

.badge {
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 12.5px;
  font-weight: 600;
  color: #100e0a;
}

.data-note {
  font-size: 12px;
  color: var(--ink-3);
  letter-spacing: 0.06em;
}

.data-list {
  list-style: none;
  border-top: 1px solid var(--line);
  padding-top: 16px;
}

.data-list li {
  font-size: 13.5px;
  color: var(--ink-2);
  padding: 6px 0;
  padding-left: 18px;
  position: relative;
}

.data-list li::before {
  content: '';
  position: absolute;
  left: 0; top: 13px;
  width: 8px; height: 1px;
  background: var(--amber);
}

.data-card {
  background: var(--bg-raised);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 24px 24px 18px;
}

.data-chart {
  width: 100%;
  height: auto;
  display: block;
}

.axis-label {
  fill: var(--ink-3);
  font-size: 10px;
  font-family: var(--font-sans);
  letter-spacing: 0.04em;
}

.chart-caption {
  text-align: right;
  font-size: 11px;
  color: var(--ink-3);
  margin-top: 10px;
}

@media (max-width: 820px) {
  .data-inner { grid-template-columns: 1fr; }
}
</style>
