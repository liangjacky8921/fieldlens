import { createApp } from 'vue'
import Lenis from 'lenis'
import 'lenis/dist/lenis.css'
import './styles/base.css'
import LandingApp from './landing/App.vue'

createApp(LandingApp).mount('#app')

// Smooth scroll for the marketing page only. The field tool (app.html) never
// loads Lenis, so map panning/zooming keeps native behavior.
// respectReducedMotion (default true) disables smoothing for users who opt out.
new Lenis({ autoRaf: true, anchors: true })
