import { createApp } from 'vue'
import './styles/base.css'
import AppTool from './app/App.vue'

// The field tool never loads Lenis or the animated backgrounds:
// it is a task surface, and map gestures must stay native.
createApp(AppTool).mount('#app')
