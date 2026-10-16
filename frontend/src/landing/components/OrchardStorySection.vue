<script setup lang="ts">
import { computed } from 'vue'
import { useT } from '../../i18n'

const t = useT()

// Two stories, alternating left/right image
const stories = computed(() => [
  {
    img: import.meta.env.BASE_URL + 'orchard/aerial-grove.jpg',
    kicker: t('orchardKicker1'),
    h: t('orchardH1'),
    p: t('orchardP1'),
  },
  {
    img: import.meta.env.BASE_URL + 'orchard/harvest-pomelos.jpg',
    kicker: t('orchardKicker2'),
    h: t('orchardH2'),
    p: t('orchardP2'),
  },
])
</script>

<template>
  <section class="orchard" id="orchard">
    <div class="shell orchard-inner">
      <p class="kicker">{{ t('orchardKickerTop') }}</p>
      <h2 class="orchard-title">{{ t('orchardTitle') }}</h2>

      <!-- Row 1: image left -->
      <article class="story story--img-left">
        <div class="story-img" :data-kicker="stories[0].kicker">
          <img :src="stories[0].img" :alt="stories[0].h" />
        </div>
        <div class="story-copy">
          <h3>{{ stories[0].h }}</h3>
          <p>{{ stories[0].p }}</p>
        </div>
      </article>

      <!-- Row 2: image right -->
      <article class="story story--img-right">
        <div class="story-img" :data-kicker="stories[1].kicker">
          <img :src="stories[1].img" :alt="stories[1].h" />
        </div>
        <div class="story-copy">
          <h3>{{ stories[1].h }}</h3>
          <p>{{ stories[1].p }}</p>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.orchard {
  padding: 110px 0 140px;
}

.orchard-inner {
  max-width: 1200px;
}

.orchard-title {
  font-size: clamp(28px, 3.4vw, 44px);
  margin-bottom: 72px;
}

/* Each story row: asymmetric 5/7 split, image column 420-520px */
.story {
  display: grid;
  gap: clamp(32px, 5vw, 64px);
  margin-bottom: 88px;
}

.story:last-child { margin-bottom: 0; }

/* Row 1 — image left, 5/7 split */
.story--img-left {
  grid-template-columns: 5fr 7fr;
}

/* Row 2 — image right, 7/5 split (mirror) */
.story--img-right {
  grid-template-columns: 7fr 5fr;
}

.story-img {
  position: relative;
  overflow: hidden;
  border-radius: 4px;
  filter: saturate(0.88) contrast(1.03);
}

.story-img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  aspect-ratio: 4 / 3;
  display: block;
}

/* Thin amber "tape" label on the image — hand-placed feel */
.story-img::after {
  content: attr(data-kicker);
  position: absolute;
  bottom: 14px;
  left: 14px;
  background: rgba(216, 178, 110, 0.9);
  color: #100e0a;
  font-size: 11px;
  letter-spacing: 0.1em;
  padding: 3px 10px;
  border-radius: 2px;
  font-weight: 600;
}

.story--img-right .story-img::after {
  left: auto;
  right: 14px;
}

.story-copy {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.story h3 {
  font-size: clamp(22px, 2.6vw, 30px);
  margin-bottom: 14px;
  line-height: 1.25;
}

.story p {
  color: var(--ink-2);
  font-size: 15px;
  line-height: 1.8;
  max-width: 520px;
}

@media (max-width: 820px) {
  .story--img-left,
  .story--img-right {
    grid-template-columns: 1fr;
  }
}
</style>
