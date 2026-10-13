<script setup lang="ts">
import { computed } from 'vue'
import SplitText from '../../vuebits/SplitText.vue'
import { i18n, useT } from '../../i18n'

const t = useT()
const splitType = computed(() => (i18n.lang === 'zh' ? 'chars' : 'words'))
</script>

<template>
  <section id="how" class="how">
    <div class="shell how-inner">
      <p class="kicker">Sentinel-2 · NDVI · Gemma</p>
      <SplitText
        :text="t('howTitle')"
        tag="h2"
        :split-type="splitType"
        text-align="left"
        :delay="i18n.lang === 'zh' ? 30 : 40"
        :duration="0.9"
        class-name="how-title"
        :threshold="0.6"
        root-margin="-60px"
      />
      <ol class="how-list">
        <li v-for="step in t('howSteps')" :key="step.n" class="how-row">
          <span class="how-n">{{ step.n }}</span>
          <div class="how-body">
            <h3>{{ step.t }}</h3>
            <p>{{ step.d }}</p>
          </div>
        </li>
      </ol>
    </div>
  </section>
</template>

<style scoped>
.how {
  padding: 110px 0 130px;
}

/* Asymmetric offset: the block sits left of center, balanced by hero whitespace */
.how-inner {
  max-width: 820px;
  margin-left: max(clamp(20px, 4vw, 48px), calc((100% - var(--w-max)) / 2 + clamp(20px, 4vw, 48px) + 4vw));
}

.how-title {
  font-size: clamp(28px, 3.4vw, 44px);
  margin-bottom: 44px;
}

.how-list {
  list-style: none;
}

.how-row {
  display: grid;
  grid-template-columns: 88px 1fr;
  gap: 18px;
  padding: 26px 0;
  border-top: 1px solid var(--line);
}

.how-row:last-child {
  border-bottom: 1px solid var(--line);
}

.how-n {
  font-size: 13px;
  letter-spacing: 0.14em;
  color: var(--amber-bright);
  padding-top: 5px;
}

.how-body h3 {
  font-size: 20px;
  margin-bottom: 8px;
}

.how-body p {
  color: var(--ink-2);
  line-height: 1.75;
  font-size: 15px;
  max-width: 560px;
}

@media (max-width: 760px) {
  .how-inner { margin-left: 0; }
  .how-row { grid-template-columns: 52px 1fr; }
}
</style>
