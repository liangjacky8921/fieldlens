<script setup lang="ts">
import { usePreferredReducedMotion } from '@vueuse/core'
import DotField from '../../vuebits/DotField.vue'
import { useT } from '../../i18n'

const t = useT()
const reduced = usePreferredReducedMotion()
// Respects Vite base so links work on Vercel (/static/) and EdgeOne (/) builds
const appHref = import.meta.env.BASE_URL + 'app.html'
</script>

<template>
  <section class="cta">
    <!-- Cursor = scouting lens over a 10 m pixel grid: the interaction mirrors the job the tool does -->
    <div v-if="reduced !== 'reduce'" class="cta-bg" aria-hidden="true">
      <DotField
        :dot-radius="1.5"
        :dot-spacing="18"
        :bulge-strength="80"
        :glow-radius="140"
        gradient-from="rgba(232, 183, 58, 0.22)"
        gradient-to="rgba(212, 164, 78, 0.12)"
        glow-color="#100e0a"
      />
    </div>

    <div class="shell cta-inner">
      <p class="kicker">{{ t('ctaKicker') }}</p>
      <h2 class="cta-title">{{ t('ctaTitle') }}</h2>
      <a class="btn btn--primary" :href="appHref">{{ t('ctaBtn') }}</a>
    </div>
  </section>
</template>

<style scoped>
.cta {
  position: relative;
  padding: 120px 0;
  border-top: 1px solid var(--line);
  overflow: hidden;
}

.cta-bg {
  position: absolute;
  inset: 0;
  opacity: 0.9;
}

.cta-inner {
  position: relative;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 18px;
}

.cta-title {
  font-size: clamp(30px, 4vw, 52px);
}

@media (max-width: 600px) {
  .cta { padding: 72px 0; }
}
</style>
