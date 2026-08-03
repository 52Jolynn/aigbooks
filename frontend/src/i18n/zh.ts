/**
 * AIGBooks · 中文文案与时间格式化常量
 * 单一信息源：所有固定界面文案必须从这里导出，测试与组件同步引用。
 */

export const site = {
  brand: 'AI 图书检疫所',
  brandEn: 'AIGBooks',
  title: 'AI 图书检疫所 · AIGBooks',
  description: '读者自治的 AI 生成内容风险档案库。匿名举报，按 ISBN 或 ISSN 即查风险线索。',
  keywords:
    'AI 生成书, AI 书, 机器印刷, 读者举报, ISBN 查询, ISSN 查询, AI 图书检疫所, 期刊预警',
  themeColor: '#0E6B52',
} as const;

export const nav = {
  primary: '主导航',
  shortcuts: '快捷操作',
  latest: '最新',
  search: '搜索',
  submit: '提交举报',
  rss: 'RSS 订阅',
} as const;

export const masthead = {
  volumeLabel: '第',
  volumeUnit: '卷',
  issueLabel: '第',
  issueUnit: '期',
  tagline: '读者自治的 AI 生成书风险档案库',
  caseLabel: '案号',
  dateLabel: '登记日期',
} as const;

export const home = {
  sectionNum: '§ 01 —',
  sectionTitle: '最新登记',
  sectionMeta: (count: number) => `共 ${count} 条 · 按登记时间倒序`,
  loading: '加载中…',
  empty: '尚无举报记录。',
} as const;

export const search = {
  sectionNum: '§ 02 —',
  sectionTitle: '检索档案',
  sectionMeta: (q: string) => `关键词：${q || '—'}`,
  prompt: '请输入关键词进行检索。',
  empty: (q: string) => `未找到与“${q}”相关的举报。`,
  cardLabel: '图书检索',
  stationLabel: '检索台',
  archiveLabel: '检索目录',
  archiveCount: (count: number) => `共 ${count} 条`,
  archiveEmpty: '馆藏目录暂无匹配条目',
  field: {
    label: '检索范围',
    all: '全部',
    identifier: '编号',
    title: '书名',
    author: '作者',
    description: '描述',
  },
  actionLabel: '检索',
  placeholder: '按书名、作者、编号（ISBN/ISSN）或举报描述搜索',
} as const;

export const detail = {
  sectionNum: '§ 03 —',
  sectionTitle: '举报清单',
  sectionMeta: (count: number) => `共 ${count} 条举报`,
  loading: '加载中…',
  empty: '该编号暂无举报。',
  notFound: '未找到该编号的档案记录。',
  loadFailed: '加载失败。',
  coverFallback: '无封面 / 无记录',
  evidenceAlt: '证据材料',
  earliestLabel: '最早举报于',
  totalLabel: '累计收到',
  timesLabel: '次举报',
  evidenceCount: (n: number) => `共 ${n} 份证据`,
  warningTitle: '风险提示',
  warningBody:
    '此书收到的举报较为集中，票数差也较明显。读者购书前请综合多方信息自行判断，本记录不构成事实认定。',
} as const;

export const report = {
  sectionNum: '§ 04 —',
  sectionTitle: '提交举报',
  sectionMeta: '匿名提交 · 通过 IP + 浏览器指纹限流 · 每小时 5 次',
  sectionOcr: 'OCR 扫描',
  sectionOcrHint: '可选',
  sectionMeta_: '书籍/期刊信息',
  sectionAttach: '附件',
  fieldTypeLabel: '编号类型',
  fieldIsbn: '020 ISBN',
  fieldIssn: '022 ISSN',
  fieldTitle: '245 题名',
  fieldAuthor: '100 作者',
  fieldDescription: '520 摘要',
  fieldCover: '封面（可选）',
  fieldEvidence: '证据文件（可选）',
  fieldDescriptionPlaceholder: '请描述可疑之处，至少 10 个字…',
  scanLabel: '扫描 ISBN/ISSN 或书脊',
  scanRunning: '识别中…',
  scanAction: '运行识别',
  ocrModeLabel: 'OCR 文件来源',
  ocrModeUpload: '上传图片',
  ocrModeBarcode: '条形码识别',
  ocrModeCamera: '拍照识别',
  ocrEmptyHint: '请选择文件或拍照后自动识别',
  cameraStart: '启动摄像头',
  cameraStarting: '启动中…',
  cameraCapture: '拍摄',
  cameraRetake: '重拍',
  cameraUse: '使用此照片',
  cameraSwitchFacing: '切换前后置',
  cameraCancel: '取消',
  cameraInsecureContext: '请使用 HTTPS 或 localhost 访问以使用摄像头',
  cameraNotAllowed: '摄像头权限被拒绝，请检查浏览器设置',
  cameraNotFound: '未检测到可用摄像头',
  cameraInUse: '摄像头正被其他程序占用',
  cameraNotReady: '视频流尚未就绪，请稍候再试',
  cameraGeneric: '摄像头启动失败',
  cameraCapturedAlt: '已拍摄的照片预览',
  retry: '重试',
  imageTooBlurry: '图片太模糊，请重新拍摄',
  imageTooBlurryHint: '建议在光线充足处对准 ISBN/ISSN 条形码或书脊文字',
  noMatch: '未识别到有效编号，请手动输入或重拍',
  recognitionSource: '识别来源',
  sourceBarcode: '条形码',
  sourceOcr: '文字 OCR',
  sourceNone: '未识别',
  barcodeScannerStart: '启动扫码',
  barcodeScannerStarting: '启动中…',
  barcodeScannerHint: '将条形码对准取景框内',
  barcodeScannerScanned: '已识别',
  barcodeRetake: '重新扫码',
  tipUpload: '从相册或文件管理器选择图片，系统将自动识别编号与题名',
  tipBarcode: '对准封底右下角的 ISBN/ISSN 条形码，识别成功自动填表（无需点击）',
  tipCamera: '拍封底（条形码最快）或版权页（拿到题名+作者）；系统将自动识别编号与题名',
  submit: '提交举报',
  submitting: '提交中…',
  uploadHint: '拖放或点击上传',
  uploadMax: (mb: number) => `· 最大 ${mb}MB`,
  uploadSize: (kb: number) => `（${kb} KB）`,
  removeFile: '移除文件',
  errors: {
    identifier: '编号格式不正确',
    titleRequired: '题名必填',
    authorRequired: '作者必填',
    descriptionMin: '描述至少 10 字',
    rateLimited: '举报过于频繁，请稍后再试',
    submitFailed: '提交失败，请重试',
  },
} as const;

export const disclaimer = {
  title: '重要声明',
  body: '本站仅记录匿名读者提交的风险线索，不构成事实认定。读者购书前请综合多方信息自行判断。',
} as const;

export const colophon = {
  line1: '由',
  line1Bold: '匿名读者',
  line1Tail: '整理维护。',
  line2: '每一条记录都是读者的郑重证词，而非出版商的结论。',
  line3: '无账号。无追踪。无编辑审核；唯有编号将我们相连。',
} as const;

export const vote = {
  upvote: (n: number) => `赞同，当前 ${n} 票`,
  downvote: (n: number) => `反对，当前 ${n} 票`,
} as const;

export const card = {
  filedOn: '提交于',
  reportedCount: (n: number) => `已收到 × ${n} 次举报`,
  noCover: '无封面',
} as const;

export const utility = {
  rssLabel: '⏵ RSS 订阅',
  submitLabel: '＋ 提交举报',
} as const;

export const stamp = {
  defaultLabel: (count: number) => `已收到 × ${count} 次举报`,
} as const;

export const file = {
  ariaRemove: '移除文件',
  tooLarge: (name: string, max: number) => `${name} 超过 ${max}MB 上限`,
} as const;

export const searchBox = {
  cardLabel: '图书检索卡',
  ariaLabel: '检索条件',
} as const;

export const a11y = {
  skipLink: '跳到主要内容',
  main: '主要区域',
} as const;

export const consoleMessages = {
  recentFailed: '加载最新举报失败：',
  ocrFailed: 'OCR 识别失败：',
  voteFailed: '投票失败：',
  searchFailed: '检索失败：',
  apiRateLimited: '请求过于频繁，请稍后再试',
  apiServerError: '服务器错误',
} as const;

/**
 * 格式化相对时间（中文无复数）
 * @param date ISO 字符串、Date 或数字时间戳
 */
export function formatRelative(input: string | number | Date): string {
  const now = Date.now();
  const ts = input instanceof Date ? input.getTime() : new Date(input).getTime();
  if (Number.isNaN(ts)) return '';
  const diff = Math.max(0, now - ts);
  const minute = 60_000;
  const hour = 60 * minute;
  const day = 24 * hour;
  if (diff < minute) return '刚刚';
  if (diff < hour) return `${Math.floor(diff / minute)} 分钟前`;
  if (diff < day) return `${Math.floor(diff / hour)} 小时前`;
  if (diff < 30 * day) return `${Math.floor(diff / day)} 天前`;
  const d = new Date(ts);
  return `${d.getFullYear()} 年 ${d.getMonth() + 1} 月 ${d.getDate()} 日`;
}

/**
 * 格式化中文长日期
 */
export function formatLongDate(input: string | number | Date = Date.now()): string {
  const d = input instanceof Date ? input : new Date(input);
  if (Number.isNaN(d.getTime())) return '';
  const weekdays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六'];
  return `${d.getFullYear()} 年 ${d.getMonth() + 1} 月 ${d.getDate()} 日 · ${weekdays[d.getDay()]}`;
}

/**
 * 生成虚拟案号（仅 UI 展示用，并非后端真实编号）
 */
export function formatCaseNumber(seed: number | string, date: Date = new Date()): string {
  const id = typeof seed === 'number' ? seed : hashString(seed);
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, '0');
  const dd = String(date.getDate()).padStart(2, '0');
  const tail = String((Math.abs(id) % 9000) + 1000);
  return `AIG-${yyyy}${mm}${dd}-${tail}`;
}

function hashString(input: string): number {
  let h = 0;
  for (let i = 0; i < input.length; i += 1) {
    h = (h << 5) - h + input.charCodeAt(i);
    h |= 0;
  }
  return h;
}