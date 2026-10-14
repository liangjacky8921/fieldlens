<script setup lang="ts">
import { ref } from 'vue'
import MapPanel from './components/MapPanel.vue'
import ReportPanel from './components/ReportPanel.vue'
import { i18n, toggleLang, useT } from '../i18n'
import { SAMPLE_FIELD } from '../data/references'

const t = useT()
const geojson = ref<object | null>(null)
const mapRef = ref<InstanceType<typeof MapPanel> | null>(null)

function loadDemoField() {
  geojson.value = SAMPLE_FIELD.polygon
  mapRef.value?.loadDemoPolygon(SAMPLE_FIELD.polygon)
}

function clearField() {
  geojson.value = null
  mapRef.value?.clearAll()
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

  <main>
    <MapPanel ref="mapRef" @geojson="(g: object | null) => (geojson = g)" />
    <ReportPanel :geojson="geojson" @load-demo="loadDemoField" @clear="clearField" />
  </main>

  <footer class="foot">{{ t('toolFooter') }}</footer>
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
  max-width: 1180px;
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

.foot {
  text-align: center;
  font-size: 11px;
  color: var(--ink-3);
  padding: 18px 0 28px;
  border-top: 1px solid var(--line);
}

@media (max-width: 480px) {
  .topbar-inner { height: 52px; gap: 8px; padding: 0 14px; }
  .brand { font-size: 16px; }
  .subtitle { display: none; }
  .sep { display: none; }
  .lang-btn { padding: 4px 10px; font-size: 12px; }
}
</style>
