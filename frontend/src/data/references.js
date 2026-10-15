/**
 * Verified reference data for FieldLens.
 * Every constant below is sourced from a published, publicly accessible resource.
 * Do NOT add unsourced "facts" here — see ../data/references.js comments for each source.
 */

// R1 · Dapu pomelo geographical indication (location & copy)
// Source: https://finance.sina.cn/2026-09-27/detail-initfhut5013732.d.html
export const GI_BOUNDS = {
  // Dapu pomelo GI protection area coordinates
  lonMin: 116 + 18 / 60,  // 116°18′E
  lonMax: 116 + 56 / 60,  // 116°56′E
  latMin: 24 + 1 / 60,    // 24°01′N
  latMax: 24 + 41 / 60,   // 24°41′N
  giStatus: 'National GI product (April 2025)',
  towns: 'Huliao, Baihou, Fenglang and 12 other towns',
}

// R2 · Dapu pomelo industry scale (copy)
// Source: https://finance.sina.cn/2026-09-14/detail-inirutnu9437436.d.html
export const INDUSTRY_STATS = {
  dapuArea: '220,000 mu',         // 22 万亩
  dapuProduction: '330,000 t',     // 33 万吨
  meizhouTotal: '660,900 mu',     // 66.09 万亩
  meizhouJinyou: '341,600 mu',    // 34.16 万亩
  qingxiBase: '1,300+ mu',        // 1300 余亩
}

// R3 · Citrus high-vigor NDVI threshold (report logic & legend)
// Source: https://www.mdpi.com/2071-1050/18/3/1324
export const VIGOR_THRESHOLD = 0.70  // "NDVI ≥ 0.70 as 'high-vigor'"

// R4 · Citrus orchard NDVI time-series ranges (sample curve bounds)
// Source: https://www.mdpi.com/2071-1050/16/13/5748
export const NDVI_FIELD_RANGES = {
  CF1: [0.15, 0.97],
  CF2: [0.51, 0.91],
  CF3: [0.19, 0.92],
  CF4: [0.55, 0.96],
  overallMin: 0.15,
  overallMax: 0.97,
  note: 'Lowest values occurring around August',
}

// R5 · Vegetation detection threshold (legend & report logic)
// Source: https://www.mdpi.com/2073-4395/15/6/1342
export const VEGETATION_THRESHOLD = 0.25  // "threshold of 0.25 to differentiate plants and soil"

// R6 · NDVI formula, bands, dataset, legend stops
// Source 1: https://github.com/bilihubbili/ndvi-vegetation-monitoring-tool-for-netherlands-based-on-sentinel-2-msi-data
// Source 2: https://github.com/apricotcomputers/worldview_hy/blob/HEAD/config/default/common/config/metadata/layers/multi-mission/hls/HLS_NDVI_Sentinel.md
export const NDVI_FORMULA = {
  expression: '(B8 − B4) / (B8 + B4)',
  nirBand: 'B8',
  nirWavelength: '842 nm',
  redBand: 'B4',
  redWavelength: '665 nm',
  resolution: '10 m',
}

export const S2_DATASET = {
  name: 'COPERNICUS/S2_SR_HARMONIZED',
  revisit: '5 days',
  cloudFilter: '< 20%',
  composite: 'median',
}

export const LEGEND_STOPS = [
  { range: '0.0 – 0.2', label: 'Bare soil / built-up', labelZh: '裸土 / 建设用地', color: '#8a7355' },
  { range: '0.2 – 0.4', label: 'Low vegetation', labelZh: '低植被', color: '#c4a574' },
  { range: '0.4 – 0.6', label: 'Moderate farmland', labelZh: '中等农田', color: '#d4a44e' },
  { range: '0.6 – 1.0', label: 'High-density vegetation', labelZh: '高密度植被', color: '#5a7a3e' },
]

// --- Project-defined thresholds (NOT from published papers) ---
// These are FieldLens project settings, not research conclusions.
export const PROJECT_THRESHOLDS = {
  alertDrop: 0.10,     // NDVI drop > 0.10 from previous → "watch"
  alertLow: 0.55,      // NDVI < 0.55 → "watch"
  alertCritical: 0.40, // NDVI < 0.40 → "inspect"
  label: 'Project-defined thresholds (not from published research)',
}

// --- Sample field polygon (illustrative, within GI bounds R1) ---
export const SAMPLE_FIELD = {
  name: 'Sample Pomelo Orchard · 示例金柚园',
  crop: 'pomelo',
  polygon: {
    type: 'Polygon',
    coordinates: [[
      [116.395, 24.285],
      [116.405, 24.285],
      [116.408, 24.278],
      [116.398, 24.274],
      [116.392, 24.279],
      [116.395, 24.285],
    ]],
  },
  note: 'Illustrative polygon within the Dapu pomelo GI protection area — not a real farm boundary',
}

// --- Data source list (for landing page "Data sources" section) ---
export const DATA_SOURCES = [
  {
    id: 'R1',
    title: 'Dapu Pomelo Geographical Indication',
    titleZh: '大埔蜜柚地理标志',
    url: 'https://finance.sina.cn/2026-09-27/detail-initfhut5013732.d.html',
    use: 'Sample field location & landing copy',
    useZh: '示例地块位置与首页文案',
  },
  {
    id: 'R2',
    title: 'Dapu Pomelo Industry Scale',
    titleZh: '大埔蜜柚产业规模',
    url: 'https://finance.sina.cn/2026-09-14/detail-inirutnu9437436.d.html',
    use: 'Landing page industry statistics',
    useZh: '首页产业数据',
  },
  {
    id: 'R3',
    title: 'Citrus High-Vigor NDVI Threshold',
    titleZh: '柑橘高活力 NDVI 阈值',
    url: 'https://www.mdpi.com/2071-1050/18/3/1324',
    use: 'Report logic & legend (NDVI ≥ 0.70)',
    useZh: '报告逻辑与图例（NDVI ≥ 0.70）',
  },
  {
    id: 'R4',
    title: 'Citrus Orchard NDVI Ranges',
    titleZh: '柑橘园 NDVI 范围',
    url: 'https://www.mdpi.com/2071-1050/16/13/5748',
    use: 'Sample curve value bounds',
    useZh: '示例曲线取值范围',
  },
  {
    id: 'R5',
    title: 'Vegetation Detection Threshold',
    titleZh: '植被判定阈值',
    url: 'https://www.mdpi.com/2073-4395/15/6/1342',
    use: 'Legend & report logic (NDVI > 0.25)',
    useZh: '图例与报告逻辑（NDVI > 0.25）',
  },
  {
    id: 'R6',
    title: 'NDVI Formula & Legend',
    titleZh: 'NDVI 公式与图例',
    url: 'https://github.com/bilihubbili/ndvi-vegetation-monitoring-tool-for-netherlands-based-on-sentinel-2-msi-data',
    use: 'Formula, bands, dataset, legend stops',
    useZh: '公式、波段、数据集、图例分段',
  },
]
