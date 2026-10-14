<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import 'leaflet-draw'
import 'leaflet-draw/dist/leaflet.draw.css'

const emit = defineEmits<{ (e: 'geojson', g: object | null): void }>()
const el = ref<HTMLDivElement | null>(null)
let map: L.Map | null = null

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

  const drawnItems = new L.FeatureGroup()
  map.addLayer(drawnItems)

  map.addControl(
    new L.Control.Draw({
      draw: { polygon: true, polyline: false, rectangle: false, circle: false, marker: false, circlemarker: false },
      edit: { featureGroup: drawnItems },
    })
  )

  map.on(L.Draw.Event.CREATED, (e: any) => {
    drawnItems.clearLayers()
    drawnItems.addLayer(e.layer)
    emit('geojson', e.layer.toGeoJSON().geometry)
  })

  map.on(L.Draw.Event.DELETED, () => emit('geojson', null))
})

onBeforeUnmount(() => map?.remove())
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
