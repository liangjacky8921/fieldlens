import { reactive } from 'vue'

// Shared bilingual dictionary for landing + tool pages.
// EN default (international judges); instant switch, no reload.
const DICT = {
  en: {
    navHow: 'How it works',
    navTool: 'Open the tool',
    navOrchard: 'The orchard',
    backHome: 'About',
    heroKicker: 'Sentinel-2 × on-device LLM',
    heroTitle: "See your orchard's vigor from orbit.",
    heroSub:
      'FieldLens turns a drawn field boundary into a 90-day NDVI time series and a bilingual grower advisory — satellite data from Google Earth Engine, language model running on your own machine.',
    heroCta: 'Open the field tool',
    heroCta2: 'How it works',
    facts: ['~5-day revisit', '10 m near-infrared', 'cloud-masked series', 'LLM never leaves the machine'],
    howTitle: 'From boundary to advisory in three steps',
    howSteps: [
      { n: '01', t: 'Draw the field', d: 'Sketch the orchard boundary on the satellite basemap — no GPS loggers or survey files needed.' },
      { n: '02', t: 'Read the season', d: 'FieldLens queries Sentinel-2 through Google Earth Engine and builds a cloud-masked NDVI series for your polygon.' },
      { n: '03', t: 'Get the advice', d: 'A trend rule reads the curve, then a Gemma model running locally writes an advisory for your crop — in English and Chinese.' },
    ],
    ctaKicker: 'Every dot is a 10 m pixel — move your cursor to scout',
    ctaTitle: 'Ready to read your field?',
    ctaBtn: 'Draw your first field',
    footerNote: 'Hackathon build · Google Earth Engine Sentinel-2 · Gemma 2B via Ollama · No data leaves the laptop',
    // tool page (migrated from legacy index.html)
    subtitle: 'Satellite vigor monitoring for high-value orchards',
    drawHint: 'Draw your orchard boundary on the map, then generate a report.',
    cropPomelo: 'Pomelo · 金柚',
    cropCitrus: 'Citrus · 柑橘',
    generate: 'Generate Report',
    generating: 'Analyzing satellite imagery… (first request may take 30-60s to wake the server)',
    retrying: 'Server waking up, retrying…',
    trendTitle: 'Vigor trend',
    adviceTitle: 'Suggestions',
    chartTitle: 'NDVI time series (last 90 days)',
    needPolygon: 'Please draw a field polygon first.',
    errGeneric: 'Something went wrong. Please try again.',
    errGee: 'Satellite service unavailable. Check GEE authentication.',
    errNetwork: 'Network error. Is the backend running?',
    noData: 'No usable satellite scenes for this plot (clouds or coverage). Try a larger area.',
    trend: { rising: 'Rising', stable: 'Stable', declining: 'Declining', volatile: 'Variable' },
    langBtn: '中文',
    dataNote: 'Source: Copernicus Sentinel-2 via Google Earth Engine (real query). Advisory: local LLM or rule fallback.',
    // Demo field & empty state
    loadDemo: 'Load demo field',
    clearBtn: 'Clear',
    sampleBadge: 'Sample · 示例数据',
    sampleNote: 'Illustrative NDVI series based on published citrus reference ranges',
    emptyStep1: 'Draw a field',
    emptyStep2: 'Generate report',
    emptyStep3: 'Read advice',
    ndviLegend: 'NDVI legend',
    toolFooter: 'GEE Sentinel-2 NDVI · Local Gemma LLM · FieldLens hackathon demo',
    // Data sources section
    sourcesKicker: 'Verified data',
    sourcesTitle: 'Data sources',
    sourcesDesc: 'Every fact on this site traces back to a published, publicly accessible resource.',
    // Leaflet draw tooltip localization
    drawPolygon: 'Draw a field boundary',
    editLayers: 'Edit layers',
    deleteLayers: 'Delete layers',
    finish: 'Finish',
    cancel: 'Cancel',
    clearAll: 'Clear all',
    // Data preview section (static demo NDVI chart)
    dataKicker: '90 days of growing',
    dataTitle: 'One curve, one decision',
    dataLede:
      'Every polygon you draw becomes a cloud-masked NDVI time series. The trend rule reads the curve, then the model writes an advisory — in English and Chinese.',
    dataDemoNote: 'Example curve, representative season',
    dataFacts: [
      '13 Sentinel-2 scenes across the window',
      'QA60 cloud-masked, same-day pairs averaged',
      'Trend rule: slope + volatility, thresholded',
      'LLM advisory never leaves the laptop',
    ],
    dataCaption: 'NDVI · last 90 days · demo',
    // Orchard story section
    orchardKickerTop: 'Where the data comes from',
    orchardTitle: 'From a pomelo branch to a satellite pixel',
    orchardKicker1: 'Southern China',
    orchardH1: 'A grid of pomelos, ten meters per row',
    orchardP1:
      'The Sentinel-2 satellites revisit this orchard every five days at ten-meter resolution — enough to tell a healthy canopy from a stressed one before the farmer sees it.',
    orchardKicker2: 'Meizhou · pomelo country',
    orchardH2: 'Where you see a pomelo, the satellite sees a number',
    orchardP2:
      'For a pomelo grower in Meizhou, NDVI is not a remote-sensing acronym. It is the story each leaf tells — recorded from orbit, translated into action by a model that runs on the same machine that wrote this page.',
  },
  zh: {
    navHow: '工作原理',
    navTool: '打开工具',
    navOrchard: '果园故事',
    backHome: '关于',
    heroKicker: 'Sentinel-2 卫星 × 本地大模型',
    heroTitle: '从轨道读懂果园长势。',
    heroSub:
      '在地图上圈出地块，FieldLens 生成近 90 天 NDVI 长势曲线与中英双语种植建议——卫星数据来自 Google Earth Engine，语言模型跑在你自己的电脑上。',
    heroCta: '打开监测工具',
    heroCta2: '工作原理',
    facts: ['约 5 天重访周期', '10 米近红外波段', '逐景去云处理', '模型不出本机'],
    howTitle: '三步，从地块边界到种植建议',
    howSteps: [
      { n: '01', t: '圈出地块', d: '在卫星底图上勾勒果园边界——不需要 GPS 记录仪，也不需要测绘文件。' },
      { n: '02', t: '读取长势', d: 'FieldLens 通过 Google Earth Engine 查询 Sentinel-2 影像，为你的地块生成去云后的 NDVI 时间序列。' },
      { n: '03', t: '获得建议', d: '趋势规则先读曲线，本地运行的 Gemma 模型再为你的作物写出种植建议——中英双语。' },
    ],
    ctaKicker: '每个圆点是一片 10 米像元——移动光标开始巡检',
    ctaTitle: '现在就读懂你的地块',
    ctaBtn: '圈出第一块果园',
    footerNote: '黑客松作品 · Google Earth Engine Sentinel-2 · 本地 Gemma 2B (Ollama) · 数据不出本机',
    subtitle: '高价值果园长势遥感监测',
    drawHint: '在地图上圈出你的果园地块，然后生成报告。',
    cropPomelo: '金柚 · Pomelo',
    cropCitrus: '柑橘 · Citrus',
    generate: '生成报告',
    generating: '正在分析卫星影像…（首次请求需 30-60 秒唤醒服务器）',
    retrying: '服务器唤醒中，正在重试…',
    trendTitle: '长势趋势',
    adviceTitle: '种植建议',
    chartTitle: 'NDVI 长势曲线（近 90 天）',
    needPolygon: '请先在地图上画一个地块多边形。',
    errGeneric: '出错了，请重试。',
    errGee: '卫星服务暂不可用，请检查 GEE 认证。',
    errNetwork: '网络错误，请确认后端已启动。',
    noData: '该地块近期无可用卫星影像（云层遮挡或覆盖不足），试试画大一点。',
    trend: { rising: '上升', stable: '平稳', declining: '下降', volatile: '波动' },
    langBtn: 'EN',
    dataNote: '数据来源：Google Earth Engine 的 Copernicus Sentinel-2（真实查询）。建议生成：本地大模型或规则兜底。',
    // Demo field & empty state
    loadDemo: '加载示例地块',
    clearBtn: '清除',
    sampleBadge: '示例 · Sample data',
    sampleNote: '示意曲线，数值范围来自已发表柑橘 NDVI 参考文献',
    emptyStep1: '圈出地块',
    emptyStep2: '生成报告',
    emptyStep3: '查看建议',
    ndviLegend: 'NDVI 图例',
    toolFooter: 'GEE Sentinel-2 NDVI · 本地 Gemma 大模型 · FieldLens 黑客松作品',
    // Data sources section
    sourcesKicker: '已验证资料',
    sourcesTitle: '数据来源',
    sourcesDesc: '本站展示的每一个事实型数值，均可追溯至公开发表的来源。',
    // Leaflet draw tooltip localization
    drawPolygon: '绘制地块边界',
    editLayers: '编辑图层',
    deleteLayers: '删除图层',
    finish: '完成',
    cancel: '取消',
    clearAll: '清除全部',
    dataKicker: '90 天生长季',
    dataTitle: '一条曲线，一个决策',
    dataLede:
      '你圈出的每块果园，都会生成去云后的 NDVI 时间序列。趋势规则先读曲线，模型再写种植建议——中英双语。',
    dataDemoNote: '示例曲线，代表性季节',
    dataFacts: [
      '窗口内 13 幅 Sentinel-2 影像',
      'QA60 去云，同日双景取均值',
      '趋势规则：斜率 + 波动率阈值判断',
      'LLM 建议不出本机',
    ],
    dataCaption: 'NDVI · 近 90 天 · 示例',
    orchardKickerTop: '数据从哪里来',
    orchardTitle: '从一根柚枝到一颗卫星像元',
    orchardKicker1: '华南果园',
    orchardH1: '柚子成行，每行十米',
    orchardP1:
      'Sentinel-2 卫星每五天重访这片果园一次，十米分辨率——足以在农民察觉之前，从太空分辨健康树冠和受胁迫的植株。',
    orchardKicker2: '梅州 · 金柚之乡',
    orchardH2: '你看到柚子，卫星看到数字',
    orchardP2:
      '对梅州的金柚种植户来说，NDVI 不是什么遥感术语。它是每一片叶子在讲述的故事——从轨道上记录，由本地运行的模型翻译成可操作的建议。',
  },
}

export const i18n = reactive({ lang: 'en' })

export function useT() {
  return (key) => DICT[i18n.lang][key] ?? key
}

export function toggleLang() {
  i18n.lang = i18n.lang === 'en' ? 'zh' : 'en'
  document.documentElement.lang = i18n.lang === 'zh' ? 'zh-CN' : 'en'
}
