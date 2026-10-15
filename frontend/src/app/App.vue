<script setup lang="ts">
import { ref } from 'vue'
import MapPanel from './components/MapPanel.vue'
import ReportPanel from './components/ReportPanel.vue'
import { i18n, toggleLang, useT } from '../i18n'
import { SAMPLE_FIELD } from '../data/references'

const t = useT()
const geojson = ref<object | null>(null)
const latestNdvi = ref<number | null>(null)
const mapRef = ref<InstanceType<typeof MapPanel> | null>(null)
const reportRef = ref<InstanceType<typeof ReportPanel> | null>(null)

function onDemo() {
  geojson.value = SAMPLE_FIELD.polygon
  mapRef.value?.loadDemoPolygon(SAMPLE_FIELD.polygon)
  // Real GEE analysis for the demo polygon, via the same pipeline as Generate Report.
  reportRef.value?.loadDemo(SAMPLE_FIELD.polygon)
}

function onClear() {
  geojson.value = null
  latestNdvi.value = null
  mapRef.value?.clearAll()
  reportRef.value?.clearAll()
}

function onReport(data: any) {
  const arr = data?.ndvi?.ndvi
  latestNdvi.value = arr?.length ? arr[arr.length - 1] : null
}
</script>

<template>
  <header class="topbar">
    <div class="topbar-inner">
      <div class="brand-cell">
        <a class="brand" href="/">FieldLens</a>
        <span class="sep" aria-hidden="true">/</span>
        <p class="subtitle">{{ t('subtitle') }}</p>
      </div>
      <button class="lang-btn" type="button" @click="toggleLang">{{ t('langBtn') }}</button>
    </div>
  </header>

  <main class="tool-main">
    <div class="map-col">
      <MapPanel
        ref="mapRef"
        :ndvi-level="latestNdvi"
        @geojson="(g: object | null) => (geojson = g)"
        @demo="onDemo"
        @clear="onClear"
      />
    </div>
    <div class="report-col">
      <ReportPanel
        ref="reportRef"
        :geojson="geojson"
        @report="onReport"
      />
    </div>
  </main>

  <footer class="foot">{{ t('toolFooter') }} · <a class="foot-gh" href="https://github.com/liangjacky8921/fieldlens" target="_blank" rel="noopener">GitHub ↗</a></footer>
</template>

<style scoped>
.topbar {
  position: sticky;
  top: 0;
  z-index: 1000;
  background: rgba(16, 14, 10, 0.96);
  border-bottom: 1px solid var(--line);
}

.topbar-inner {
  max-width: 100%;
  margin: 0 auto;
  padding: 0 clamp(16px, 4vw, 32px);
  height: 58px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  overflow: hidden;
  min-width: 0;
}

.brand-cell {
  display: flex;
  align-items: baseline;
  gap: 10px;
  min-width: 0;
  overflow: hidden;
}

.brand {
  font-family: var(--font-serif);
  font-size: 19px;
  color: var(--ink);
  flex-shrink: 0;
}

.sep { color: var(--ink-3); flex-shrink: 0; }

.subtitle {
  font-size: 12px;
  color: var(--ink-3);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.lang-btn {
  background: transparent;
  border: 1px solid var(--line-strong);
  color: var(--ink);
  border-radius: 999px;
  padding: 5px 13px;
  font-size: 13px;
  cursor: pointer;
  flex-shrink: 0;
  white-space: nowrap;
}

/* Split-screen: map left (58%), report right (42%) */
.tool-main {
  display: grid;
  grid-template-columns: 58% 42%;
  min-height: calc(100vh - 58px - 62px);
}

.map-col {
  position: sticky;
  top: 58px;
  height: calc(100vh - 58px);
  overflow: hidden;
}

.report-col {
  height: calc(100vh - 58px);
  overflow-y: auto;
  overflow-x: hidden;
}

.foot {
  text-align: center;
  font-size: 11px;
  color: var(--ink-3);
  padding: 18px 0 28px;
  border-top: 1px solid var(--line);
}

.foot-gh {
  color: var(--amber);
  text-decoration: none;
}

.foot-gh:hover {
  color: var(--amber-bright, #e8bc66);
}

/* Mobile: stacked layout */
@media (max-width: 1023px) {
  .tool-main {
    grid-template-columns: 1fr;
  }
  .map-col {
    position: relative;
    top: 0;
    height: auto;
  }
  .report-col {
    height: auto;
    overflow-y: visible;
  }
}

@media (max-width: 480px) {
  .topbar-inner { height: 52px; gap: 8px; padding: 0 14px; }
  .brand { font-size: 16px; }
  .subtitle { display: none; }
  .sep { display: none; }
  .lang-btn { padding: 4px 10px; font-size: 12px; }
}
</style>
