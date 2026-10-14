/**
 * Single analysis entry point for FieldLens — JS port of app/advise.py compute_features().
 * Both the demo rendering path and the backend Generate Report use the same logic.
 * No hardcoded verdicts: trend and verdict are always computed from the NDVI series.
 */

// --- Verified thresholds (must match advise.py) ---
const VEGETATION_THRESHOLD = 0.25  // R5: NDVI > 0.25 = vegetation
const ALERT_DROP = 0.10            // Project: sudden drop > 0.10 → field check 7d
const ALERT_LOW = 0.55             // Project: NDVI < 0.55 → watch
const CONSECUTIVE_DECLINE = 3      // Project: 3 consecutive declining points
const GAP_DAYS = 15                // Project: >15-day gap → flag

// --- Seasonal context by month (extensible) ---
const SEASON_CONFIG = {
  10: {
    zh: '10 月为采后恢复期，NDVI 季节性回落属正常，重点看是否跌破本块地历史同期水平。',
    en: "October is post-harvest recovery for Meizhou pomelo; a mild seasonal dip is normal — watch whether NDVI falls below this plot's own historical level for the season.",
  },
}

function getSeasonNote(dates) {
  if (!dates || !dates.length) return ''
  const last = dates[dates.length - 1]
  const month = parseInt(String(last).substring(5, 7), 10)
  return SEASON_CONFIG[month] || ''
}

/**
 * Compute deterministic trend features from the NDVI series.
 * Direct port of advise.py compute_features() — same thresholds, same logic.
 */
export function computeFeatures(ndviData) {
  const dates = ndviData.dates || []
  const ndvi = ndviData.ndvi || []

  if (!ndvi || ndvi.length < 3) {
    return {
      trend: 'stable',
      verdict: 'watch',
      slope: 0,
      last_drop: 0,
      consecutive_decline: 0,
      has_gap: true,
      cloud_points: Array.from({ length: ndvi.length }, (_, i) => i),
      cleaned_ndvi: [],
      gap_note: 'Insufficient valid observations in this period.',
    }
  }

  // Cloud-contaminated point detection: NDVI < vegetation threshold
  const cloudPoints = []
  for (let i = 0; i < ndvi.length; i++) {
    if (ndvi[i] < VEGETATION_THRESHOLD) cloudPoints.push(i)
  }

  // Cleaned series (exclude cloud points)
  let cleaned = ndvi.map((v, i) => ({ i, v })).filter(({ i }) => !cloudPoints.includes(i))
  if (cleaned.length < 3) {
    cleaned = ndvi.map((v, i) => ({ i, v }))
  }
  const cleanValues = cleaned.map(({ v }) => v)
  const n = cleanValues.length

  // Least-squares linear fit
  const xs = Array.from({ length: n }, (_, i) => i)
  const xMean = xs.reduce((a, b) => a + b, 0) / n
  const yMean = cleanValues.reduce((a, b) => a + b, 0) / n
  const denom = xs.reduce((sum, x) => sum + (x - xMean) ** 2, 0) || 1
  const slope = xs.reduce((sum, x, idx) => sum + (x - xMean) * (cleanValues[idx] - yMean), 0) / denom
  const intercept = yMean - slope * xMean

  const residuals = cleanValues.map((y, idx) => y - (intercept + slope * xs[idx]))
  const volatility = Math.sqrt(residuals.reduce((sum, r) => sum + r * r, 0) / n)

  // Trend classification
  let trend
  if (volatility > 0.08) trend = 'volatile'
  else if (slope > 0.005) trend = 'rising'
  else if (slope < -0.005) trend = 'declining'
  else trend = 'stable'

  // Last-step drop (on original series)
  let lastDrop = ndvi.length >= 2 ? (ndvi[ndvi.length - 2] - ndvi[ndvi.length - 1]) : 0
  if (lastDrop < 0) lastDrop = 0

  // Consecutive declining points at the tail
  let consec = 0
  for (let i = ndvi.length - 1; i > 0; i--) {
    if (ndvi[i] < ndvi[i - 1]) consec++
    else break
  }

  // Gap detection: check if any gap between consecutive dates > GAP_DAYS
  let hasGap = false
  if (dates.length >= 2) {
    for (let i = 1; i < dates.length; i++) {
      try {
        const d1 = new Date(String(dates[i - 1]).substring(0, 10))
        const d2 = new Date(String(dates[i]).substring(0, 10))
        if ((d2 - d1) / 86400000 > GAP_DAYS) {
          hasGap = true
          break
        }
      } catch { continue }
    }
  }

  let gapNote = ''
  if (hasGap) gapNote = 'Gaps in the observation window — some periods lack valid satellite data.'
  if (cloudPoints.length) {
    const cloudNote = `${cloudPoints.length} scene(s) excluded as cloud-contaminated.`
    gapNote = gapNote ? `${gapNote} ${cloudNote}` : cloudNote
  }

  // Verdict: vigorous / watch / alert
  let verdict
  if (lastDrop > ALERT_DROP || (consec >= CONSECUTIVE_DECLINE && trend === 'declining')) {
    verdict = 'alert'
  } else if (trend === 'declining' || trend === 'volatile' || consec >= 2 || ndvi[ndvi.length - 1] < ALERT_LOW) {
    verdict = 'watch'
  } else {
    verdict = 'vigorous'
  }

  return {
    trend,
    verdict,
    slope: Math.round(slope * 1e6) / 1e6,
    last_drop: Math.round(lastDrop * 1e4) / 1e4,
    consecutive_decline: consec,
    has_gap: hasGap,
    cloud_points: cloudPoints,
    cleaned_ndvi: cleanValues,
    gap_note: gapNote,
  }
}

// --- Bilingual fallback templates (must match advise.py FALLBACK) ---
const FALLBACK = {
  vigorous: {
    en: {
      verdict: 'vigorous',
      summary: 'Canopy vigor is healthy and stable. NDVI shows no concerning decline.',
      advice: [
        'Maintain current irrigation and fertilization; no urgent action needed this week.',
        'Do a routine pest and disease walk-through within the next 1–2 weeks.',
        'Watch the next satellite pass (about 5 days) for any sign of decline.',
      ],
    },
    zh: {
      verdict: 'vigorous',
      summary: '果树长势健康平稳，本时段 NDVI 没有明显下降。',
      advice: [
        '本周按常规水肥管理即可，暂无紧急事项。',
        '1–2 周内例行巡查一次病虫害。',
        '留意下一次卫星影像（约 5 天后），警惕由稳转弱。',
      ],
    },
  },
  watch: {
    en: {
      verdict: 'watch',
      summary: 'Canopy vigor shows some signs of stress. NDVI is declining or fluctuating.',
      advice: [
        'Check soil moisture within 7 days; increase irrigation if topsoil is dry.',
        'Inspect leaves for yellowing, spots, or curling within 7 days — rule out water stress first.',
        'Review water/fertilizer records within 7 days for any missed applications this month.',
      ],
    },
    zh: {
      verdict: 'watch',
      summary: '长势有些走弱迹象，NDVI 在下降或波动。',
      advice: [
        '7 天内检查土壤墒情，表层干了就及时补水。',
        '7 天内查看叶片有无发黄、斑点、卷叶，先排查是否缺水。',
        '7 天内核查本月水肥记录，有没有漏施。',
      ],
    },
  },
  alert: {
    en: {
      verdict: 'alert',
      summary: 'Canopy vigor dropped sharply. NDVI shows a sudden decline — immediate field check recommended.',
      advice: [
        'Walk the plot within 7 days; compare weak spots with healthy areas side by side.',
        'Check irrigation system coverage within 7 days — dry corners or blocked emitters may be the cause.',
        'If water and nutrition check out, consult the local agricultural extension within 2 weeks for diagnosis.',
      ],
    },
    zh: {
      verdict: 'alert',
      summary: '长势明显走弱，NDVI 突降——建议尽快下地查看。',
      advice: [
        '7 天内下地走一圈，对比长势弱和好的地方。',
        '7 天内检查灌溉有没有死角——边角干、滴头堵都可能导致局部差。',
        '水肥查不出问题，2 周内找当地农技站帮忙看看。',
      ],
    },
  },
}

/**
 * Generate a demo report using the same analysis as the backend.
 * Returns bilingual { trend, verdict, en, zh } with source='sample'.
 */
export function generateDemoReport(ndviData, crop = 'pomelo') {
  const features = computeFeatures(ndviData)
  const seasonNote = getSeasonNote(ndviData.dates)
  const verdict = features.verdict

  const reports = {}
  for (const lang of ['en', 'zh']) {
    const fb = FALLBACK[verdict][lang]
    reports[lang] = {
      verdict: fb.verdict,
      summary: fb.summary,
      advice: fb.advice,
      trend: features.trend,
      source: 'sample',
      gap_note: features.gap_note,
      season_note: seasonNote ? seasonNote[lang] : '',
    }
  }

  return {
    trend: features.trend,
    verdict,
    en: reports.en,
    zh: reports.zh,
  }
}
