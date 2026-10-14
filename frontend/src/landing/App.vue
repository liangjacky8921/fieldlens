<script setup lang="ts">
import { useScroll } from '@vueuse/core'
import { ref, watch } from 'vue'
import HeroSection from './components/HeroSection.vue'
import HowSection from './components/HowSection.vue'
import DataPreviewSection from './components/DataPreviewSection.vue'
import OrchardStorySection from './components/OrchardStorySection.vue'
import CtaSection from './components/CtaSection.vue'
import DataSourcesSection from './components/DataSourcesSection.vue'
import LineWaves from '../vuebits/LineWaves.vue'
import { i18n, toggleLang, useT } from '../i18n'

const t = useT()

const navEl = ref<HTMLElement | null>(null)
const { y } = useScroll(window)
const scrolled = ref(false)
watch(y, (v) => { scrolled.value = v > 24 }, { immediate: true })
</script>

<template>
  <nav ref="navEl" class="nav" :class="{ 'nav--scrolled': scrolled }">
    <div class="shell nav-inner">
      <a class="brand" href="/">
        <span class="brand-mark" aria-hidden="true"></span>
        FieldLens
      </a>
      <div class="nav-links">
        <a class="nav-link" href="#orchard">{{ t('navOrchard') }}</a>
        <a class="nav-link" href="#how">{{ t('navHow') }}</a>
        <button class="lang-btn" type="button" @click="toggleLang">{{ t('langBtn') }}</button>
        <a class="btn btn--small" href="/static/app.html">{{ t('navTool') }}</a>
      </div>
    </div>
  </nav>

  <main>
    <HeroSection />
    <HowSection />
    <DataPreviewSection />
    <OrchardStorySection />
    <DataSourcesSection />
    <CtaSection />
  </main>

  <footer class="footer">
    <div class="footer-waves" aria-hidden="true">
      <LineWaves
        :speed="0.22"
        :inner-line-count="24"
        :outer-line-count="28"
        :brightness="0.14"
        color1="#3a2d15"
        color2="#d4a44e"
        color3="#100e0a"
        :enable-mouse-interaction="false"
        :mouse-influence="0"
      />
    </div>
    <div class="shell footer-inner">
      <div class="footer-left">
        <p class="footer-brand">FieldLens</p>
        <p class="footer-note">{{ t('footerNote') }}</p>
      </div>
      <div class="footer-right">
        <p class="footer-sign">Designed by <span class="footer-sign-name">Lam Jacky</span></p>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  transition: background 0.25s ease, border-color 0.25s ease;
  border-bottom: 1px solid transparent;
}

.nav--scrolled {
  background: rgba(16, 14, 10, 0.92);
  border-bottom-color: var(--line);
}

.nav-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
  min-width: 0;
  overflow: hidden;
}

.brand {
  font-family: var(--font-serif);
  font-size: 20px;
  color: var(--ink);
  display: inline-flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.brand-mark {
  width: 10px;
  height: 10px;
  background: var(--amber);
  border-radius: 2px;
  display: inline-block;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 22px;
  min-width: 0;
  overflow: hidden;
}

.nav-link {
  color: var(--ink-2);
  font-size: 14px;
  white-space: nowrap;
}

.nav-link:hover { color: var(--ink); }

.lang-btn {
  background: transparent;
  border: 1px solid var(--line-strong);
  color: var(--ink);
  border-radius: 999px;
  padding: 6px 14px;
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
}

.footer {
  border-top: 1px solid var(--line);
}

.footer-waves {
  height: 170px;
  border-bottom: 1px solid var(--line);
  overflow: hidden;
}

.footer-inner {
  padding: 26px 0 34px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.footer-brand {
  font-family: var(--font-serif);
  font-size: 16px;
}

.footer-note {
  font-size: 12px;
  color: var(--ink-3);
}

.footer-right {
  text-align: right;
}

.footer-sign {
  font-size: 12px;
  color: var(--ink-3);
}

.footer-sign-name {
  color: var(--ink);
  font-weight: 600;
}

@media (max-width: 560px) {
  .nav-inner { height: 56px; }
  .brand { font-size: 17px; gap: 8px; }
  .brand-mark { width: 8px; height: 8px; }
  .nav-links { gap: 10px; }
  .nav-link { font-size: 13px; }
  .lang-btn { padding: 5px 10px; font-size: 12px; }
  .btn--small { padding: 9px 14px; font-size: 13px; }
  .footer-inner { flex-direction: column; align-items: flex-start; gap: 8px; }
  .footer-right { text-align: left; }
  .footer-waves { height: 100px; }
}
@media (max-width: 440px) {
  .nav-links .nav-link[href="#orchard"],
  .nav-links .nav-link[href="#how"] { display: none; }
  .btn--small { display: none; }
  .nav-links { gap: 10px; }
}
</style>
