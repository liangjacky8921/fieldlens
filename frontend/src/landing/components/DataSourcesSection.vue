<script setup lang="ts">
import { useT } from '../../i18n'
import { DATA_SOURCES, INDUSTRY_STATS } from '../../data/references'

const t = useT()
</script>

<template>
  <section class="sources" id="sources">
    <div class="shell sources-inner">
      <p class="kicker">{{ t('sourcesKicker') }}</p>
      <h2 class="sources-title">{{ t('sourcesTitle') }}</h2>
      <p class="sources-desc">{{ t('sourcesDesc') }}</p>

      <div class="source-grid">
        <a
          v-for="s in DATA_SOURCES"
          :key="s.id"
          :href="s.url"
          target="_blank"
          rel="noopener noreferrer"
          class="source-card"
        >
          <span class="source-id">{{ s.id }}</span>
          <div class="source-body">
            <p class="source-title">{{ t('') === '' ? '' : '' }}{{ s.title }}</p>
            <p class="source-use">{{ s.use }}</p>
          </div>
          <span class="source-link" aria-hidden="true">↗</span>
        </a>
      </div>

      <!-- Industry stats highlight -->
      <div class="stats-strip">
        <div class="stat">
          <span class="stat-num">{{ INDUSTRY_STATS.dapuArea }}</span>
          <span class="stat-label">Dapu pomelo area</span>
        </div>
        <div class="stat">
          <span class="stat-num">{{ INDUSTRY_STATS.dapuProduction }}</span>
          <span class="stat-label">Estimated production</span>
        </div>
        <div class="stat">
          <span class="stat-num">{{ INDUSTRY_STATS.meizhouJinyou }}</span>
          <span class="stat-label">Jinyou (golden pomelo)</span>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.sources {
  padding: 100px 0 120px;
  border-top: 1px solid var(--line);
}

.sources-inner {
  max-width: 1000px;
}

.sources-title {
  font-size: clamp(28px, 3.4vw, 44px);
  margin-bottom: 16px;
}

.sources-desc {
  font-size: 15px;
  color: var(--ink-2);
  line-height: 1.7;
  max-width: 560px;
  margin-bottom: 48px;
}

.source-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.source-card {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 18px 16px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  text-decoration: none;
  transition: border-color 0.2s, background 0.2s;
}

.source-card:hover {
  border-color: var(--line-strong);
  background: var(--bg-raised);
}

.source-id {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 28px;
  padding: 0 8px;
  border-radius: 6px;
  background: var(--amber-deep);
  color: var(--amber-bright);
  font-size: 12px;
  font-weight: 700;
  font-family: var(--font-sans);
  flex-shrink: 0;
}

.source-body {
  flex: 1;
  min-width: 0;
}

.source-title {
  font-size: 14px;
  color: var(--ink);
  font-weight: 600;
  line-height: 1.4;
}

.source-use {
  font-size: 12.5px;
  color: var(--ink-3);
  margin-top: 4px;
  line-height: 1.5;
}

.source-link {
  color: var(--ink-3);
  font-size: 14px;
  flex-shrink: 0;
}

.stats-strip {
  display: flex;
  gap: 40px;
  margin-top: 56px;
  flex-wrap: wrap;
}

.stat {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-num {
  font-family: var(--font-serif);
  font-size: clamp(24px, 3vw, 36px);
  color: var(--amber-bright);
  line-height: 1;
}

.stat-label {
  font-size: 12px;
  color: var(--ink-3);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

@media (max-width: 600px) {
  .sources { padding: 64px 0 80px; }
  .source-grid { grid-template-columns: 1fr; }
  .stats-strip { gap: 28px; }
}
</style>
