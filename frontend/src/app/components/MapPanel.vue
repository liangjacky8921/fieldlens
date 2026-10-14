<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import 'leaflet-draw'
import 'leaflet-draw/dist/leaflet.draw.css'
import { i18n, useT } from '../../i18n'
import { LEGEND_STOPS } from '../../data/references'

const props = defineProps<{ ndviLevel?: number | null }>()
const emit = defineEmits<{
  (e: 'geojson', g: object | null): void
  (e: 'demo'): void
  (e: 'clear'): void
}>()
const t = useT()
const el = ref<HTMLDivElement | null>(null)
const hasPolygon = ref(false)
let map: L.Map | null = null
let drawnItems: L.FeatureGroup | null = null

const legendStops = LEGEND_STOPS

onMounted(() => {
  // Default view: Meizhou, Guangdong (pomelo / citrus country)
  map = L.map(el.value!).setView([24.28, 116.12], 13)

  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Esri World Imagery',
    maxZoom: 19,
  }).addTo(map)

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap',
    maxZoom: 19,
    opacity: 0.25,
  }).addTo(map)

  drawnItems = new L.FeatureGroup()
  map.addLayer(drawnItems)

  // Localize Leaflet.draw tooltips.
  const dh = L.drawLocal?.draw?.handlers
  if (dh?.polygon) {
    dh.polygon.tooltipStart = () => t('drawPolygon')
    dh.polygon.tooltipEnd = () => t('finish')
    dh.polygon.tooltipCont = () => ''
  }
  const eh = L.drawLocal?.edit?.edit?.handlers
  if (eh?.edit?.tooltip?.text) {
    eh.edit.tooltip.text.start = () => t('editLayers')
  }
  if (eh?.removeAll?.tooltip?.text) {
    eh.removeAll.tooltip.text = () => t('deleteLayers')
  }

  map.addControl(
    new L.Control.Draw({
      draw: { polygon: true, polyline: false, rectangle: false, circle: false, marker: false, circlemarker: false },
      edit: { featureGroup: drawnItems },
    })
  )

  map.on(L.Draw.Event.CREATED, (e: any) => {
    drawnItems!.clearLayers()
    drawnItems!.addLayer(e.layer)
    hasPolygon.value = true
    emit('geojson', e.layer.toGeoJSON().geometry)
    // Fit bounds so the drawn polygon is centered with padding
    const bounds = e.layer.getBounds()
    map!.fitBounds(bounds, { padding: [40, 40] })
  })

  map.on(L.Draw.Event.DELETED, () => {
    hasPolygon.value = false
    emit('geojson', null)
  })
})

// Dynamic polygon fill color based on latest NDVI value
watch(() => props.ndviLevel, (val) => {
  if (val === null || val === undefined || !drawnItems) return
  drawnItems.eachLayer((layer: any) => {
    if (layer.setStyle) {
      const fillColor = val >= 0.6 ? '#7fa388' : val >= 0.4 ? '#d4a44e' : '#c26856'
      layer.setStyle({ fillColor, fillOpacity: 0.22, color: '#d4a44e', weight: 2 })
    }
  })
})

onBeforeUnmount(() => map?.remove())

function loadDemoPolygon(geojson: object) {
  if (!map || !drawnItems) return
  drawnItems.clearLayers()
  const layer = L.geoJSON(geojson, { color: '#d4a44e', weight: 2, fillOpacity: 0.15 })
  drawnItems.addLayer(layer)
  hasPolygon.value = true
  // Fly to the polygon with comfortable padding
  const bounds = layer.getBounds()
  map.fitBounds(bounds, { padding: [40, 40] })
  emit('geojson', geojson)
}

function clearAll() {
  if (!drawnItems) return
  drawnItems.clearLayers()
  hasPolygon.value = false
  emit('geojson', null)
}

defineExpose({ loadDemoPolygon, clearAll })
</script>

<template>
  <div class="map-wrap">
    <div ref="el" class="map"></div>

    <!-- Floating HUD: demo/clear capsule buttons (top-right) -->
    <div class="hud-actions">
      <button class="hud-btn" type="button" @click="emit('demo')">{{ t('loadDemo') }}</button>
      <button v-if="hasPolygon" class="hud-btn hud-btn--clear" type="button" @click="emit('clear')">{{ t('clearBtn') }}</button>
    </div>

    <!-- Floating NDVI legend (bottom-left) -->
    <div class="hud-legend">
      <p class="hud-legend-title">{{ t('ndviLegend') }}</p>
      <div class="hud-legend-rows">
        <div class="hud-legend-row" v-for="s in legendStops" :key="s.range">
          <span class="hud-swatch" :style="{ background: s.color }"></span>
          <span class="hud-range">{{ s.range }}</span>
          <span class="hud-label">{{ i18n.lang === 'zh' ? s.labelZh : s.label }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.map-wrap {
  position: relative;
  height: 100%;
  width: 100%;
}

.map {
  height: 100%;
  width: 100%;
  background: var(--bg-raised);
}

/* Floating HUD capsule buttons — top-right of map */
.hud-actions {
  position: absolute;
  top: 14px;
  right: 14px;
  z-index: 1000;
  display: flex;
  gap: 8px;
}

.hud-btn {
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  background: rgba(16, 14, 10, 0.65);
  border: 1px solid rgba(212, 164, 78, 0.3);
  color: var(--ink);
  font-size: 13px;
  padding: 7px 15px;
  border-radius: 999px;
  cursor: pointer;
  transition: border-color 0.2s, color 0.2s, background 0.2s;
  white-space: nowrap;
  font-family: var(--font-sans);
}

.hud-btn:hover {
  border-color: var(--amber-bright);
  color: var(--amber-bright);
  background: rgba(16, 14, 10, 0.8);
}

.hud-btn--clear:hover {
  border-color: #e08b7d;
  color: #e08b7d;
}

/* Floating NDVI legend — bottom-left of map */
.hud-legend {
  position: absolute;
  bottom: 14px;
  left: 14px;
  z-index: 1000;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  background: rgba(16, 14, 10, 0.65);
  border: 1px solid rgba(240, 235, 226, 0.12);
  border-radius: 10px;
  padding: 10px 12px;
  max-width: 210px;
}

.hud-legend-title {
  font-size: 11px;
  color: var(--ink-2);
  margin-bottom: 6px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.hud-legend-rows {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.hud-legend-row {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 11px;
}

.hud-swatch {
  width: 14px;
  height: 14px;
  border-radius: 3px;
  flex-shrink: 0;
}

.hud-range {
  color: var(--ink);
  font-weight: 600;
  min-width: 56px;
}

.hud-label {
  color: var(--ink-3);
}

:deep(.leaflet-draw-toolbar a) {
  background-color: #fff;
}

:deep(.leaflet-container) {
  font-family: var(--font-sans);
  touch-action: none;
}

/* Mobile: enlarge draw toolbar touch targets (44px min) */
@media (max-width: 600px) {
  :deep(.leaflet-draw-toolbar a) {
    width: 44px;
    height: 44px;
    background-size: 22px 22px;
  }
  :deep(.leaflet-bar) {
    border-radius: 6px;
  }
  :deep(.leaflet-control-zoom a) {
    width: 44px;
    height: 44px;
    line-height: 44px;
    font-size: 18px;
  }
  .hud-legend { max-width: 160px; padding: 8px 10px; }
  .hud-legend-row { font-size: 10px; }
  .hud-range { min-width: 48px; }
  .hud-btn { font-size: 12px; padding: 6px 12px; }
}

/* Mobile: map height stacks, min 42vh */
@media (max-width: 1023px) {
  .map-wrap { height: 42vh; min-height: 300px; }
}
</style>
