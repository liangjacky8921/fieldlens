<script setup lang="ts">
import { computed } from 'vue'
import { usePreferredReducedMotion } from '@vueuse/core'
import Aurora from '../../vuebits/Aurora.vue'
import SplitText from '../../vuebits/SplitText.vue'
import { i18n, useT } from '../../i18n'

const t = useT()
const reduced = usePreferredReducedMotion()
const showAurora = computed(() => reduced.value !== 'reduce')
const splitType = computed(() => (i18n.lang === 'zh' ? 'chars' : 'words'))
</script>

<template>
  <section class="hero">
    <!-- Layer 1: Aurora shader, bottom of the stack -->
    <div v-if="showAurora" class="hero-aurora" aria-hidden="true">
      <Aurora
        :color-stops="['#100e0a', '#d4a44e', '#100e0a']"
        :amplitude="1.2"
        :blend="0.6"
        :speed="0.5"
      />
    </div>
    <div v-else class="hero-aurora hero-aurora--static" aria-hidden="true"></div>

    <!-- Layer 2: Dark shading mask on the left side (readability for copy) -->
    <div class="hero-shade" aria-hidden="true"></div>

    <!-- Layer 3: Pomelo photo on the right, asymmetric clip-path cut -->
    <div class="hero-photo" aria-hidden="true">
      <img src="/orchard/hero-pomelo.jpg" alt="" class="hero-photo-img" />
      <div class="hero-photo-fade" aria-hidden="true"></div>
    </div>

    <div class="shell hero-grid">
      <div class="hero-copy">
        <p class="kicker">{{ t('heroKicker') }}</p>
        <SplitText
          :text="t('heroTitle')"
          tag="h1"
          :split-type="splitType"
          text-align="left"
          :delay="i18n.lang === 'zh' ? 45 : 60"
          :duration="1.1"
          class-name="hero-title"
          :threshold="0.4"
          root-margin="0px"
        />
        <p class="hero-sub">{{ t('heroSub') }}</p>
        <div class="hero-ctas">
          <a class="btn btn--primary" href="/static/app.html">{{ t('heroCta') }}</a>
          <a class="btn btn--ghost" href="#how">{{ t('heroCta2') }}</a>
        </div>
        <ul class="hero-facts">
          <li v-for="f in t('facts')" :key="f">{{ f }}</li>
        </ul>
      </div>
    </div>
  </section>
</template>

<style scoped>
.hero {
  position: relative;
  min-height: 92vh;
  display: flex;
  align-items: center;
  overflow: hidden;
}

/* Layer 1 — Aurora shader */
.hero-aurora {
  position: absolute;
  inset: 0;
  -webkit-mask-image: linear-gradient(to bottom, #000 60%, transparent 100%);
  mask-image: linear-gradient(to bottom, #000 60%, transparent 100%);
}

.hero-aurora--static {
  background:
    radial-gradient(120% 90% at 78% 10%, rgba(212, 164, 78, 0.35), transparent 60%),
    radial-gradient(80% 60% at 60% 30%, rgba(104, 79, 36, 0.3), transparent 70%);
}

/* Layer 2 — Dark shading for copy side */
.hero-shade {
  position: absolute;
  inset: 0;
  background: linear-gradient(to right, rgba(16, 14, 10, 0.94) 0%, rgba(16, 14, 10, 0.72) 40%, rgba(16, 14, 10, 0.25) 72%, transparent 82%);
  pointer-events: none;
}

/* Layer 3 — Pomelo photo clipped diagonally on the left edge */
.hero-photo {
  position: absolute;
  top: 0;
  right: 0;
  height: 100%;
  width: 58%;
  overflow: hidden;
  /* Diagonal clip: photo sweeps in from bottom-right, the clip edge slants top-left */
  -webkit-clip-path: polygon(18% 0%, 100% 0%, 100% 100%, 0% 100%);
          clip-path: polygon(18% 0%, 100% 0%, 100% 100%, 0% 100%);
  /* Slightly warm-amber tint over the dark photo, ties to citrus theme */
  filter: saturate(0.85) contrast(1.05);
  z-index: 0;
}

.hero-photo-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  /* Slight rightward shift so the pomelo fruit sits in the right half */
  object-position: 60% 40%;
}

/* Left-side fade so the photo blends where it meets the copy column */
.hero-photo-fade {
  position: absolute;
  inset: 0;
  background: linear-gradient(to right, rgba(16, 14, 10, 0.85), transparent 35%);
  pointer-events: none;
}

.hero-grid {
  position: relative;
  width: 100%;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(0, 640px) 1fr;
}

.hero-title {
  font-size: clamp(42px, 6.5vw, 82px);
  line-height: 1.05;
  margin: 0 0 22px;
}

.hero-sub {
  color: var(--ink-2);
  font-size: clamp(15px, 1.4vw, 17px);
  line-height: 1.75;
  max-width: 560px;
  margin-bottom: 32px;
}

.hero-ctas {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  margin-bottom: 48px;
}

.hero-facts {
  list-style: none;
  display: flex;
  flex-wrap: wrap;
  gap: 8px 26px;
  border-top: 1px solid var(--line);
  padding-top: 16px;
  font-size: 12px;
  letter-spacing: 0.08em;
  color: var(--ink-3);
}

@media (max-width: 900px) {
  /* Photo tucks away behind copy on mobile, keeps readability */
  .hero-photo {
    width: 100%;
    opacity: 0.22;
    clip-path: none;
  }
  .hero-photo-fade {
    background: linear-gradient(to right, rgba(12, 19, 16, 0.96), rgba(12, 19, 16, 0.82));
  }
  .hero-grid { grid-template-columns: 1fr; }
}
</style>
