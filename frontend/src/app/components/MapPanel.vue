<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import 'leaflet-draw'
import 'leaflet-draw/dist/leaflet.draw.css'
import { i18n, useT } from '../../i18n'

const emit = defineEmits<{ (e: 'geojson', g: object | null): void }>()
const t = useT()
const el = ref<HTMLDivElement | null>(null)
let map: L.Map | null = null
let drawnItems: L.FeatureGroup | null = null

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

  // Localize Leaflet.draw tooltips
  L.drawLocal.draw.handlers.polygon.tooltipStart = () => t('drawPolygon')
  L.drawLocal.draw.handlers.polygon.tooltipEnd = () => t('finish')
  L.drawLocal.draw.handlers.polygon.tooltipCont = () => ''
  L.drawLocal.edit.edit.handlers.edit.tooltip.text.start = () => t('editLayers')
  L.drawLocal.edit.edit.handlers.removeAll.tooltip.text = () => t('deleteLayers')

  map.addControl(
    new L.Control.Draw({
      draw: { polygon: true, polyline: false, rectangle: false, circle: false, marker: false, circlemarker: false },
      edit: { featureGroup: drawnItems },
    })
  )

  map.on(L.Draw.Event.CREATED, (e: any) => {
    drawnItems!.clearLayers()
    drawnItems!.addLayer(e.layer)
    emit('geojson', e.layer.toGeoJSON().geometry)
  })

  map.on(L.Draw.Event.DELETED, () => emit('geojson', null))
})

onBeforeUnmount(() => map?.remove())

function loadDemoPolygon(geojson: object) {
  if (!map || !drawnItems) return
  drawnItems.clearLayers()
  const layer = L.geoJSON(geojson, { color: '#d4a44e', weight: 2, fillOpacity: 0.15 })
  drawnItems.addLayer(layer)
  // Fly to the polygon
  const bounds = layer.getBounds()
  map.fitBounds(bounds, { padding: [40, 40] })
  emit('geojson', geojson)
}

function clearAll() {
  if (!drawnItems) return
  drawnItems.clearLayers()
  emit('geojson', null)
}

defineExpose({ loadDemoPolygon, clearAll })
</script>

<template>
  <div ref="el" class="map"></div>
</template>

<style scoped>
.map {
  height: 46vh;
  min-height: 320px;
  width: 100%;
  background: var(--bg-raised);
}

@media (min-width: 900px) {
  .map { height: 54vh; }
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
}
</style>
