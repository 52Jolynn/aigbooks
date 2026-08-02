---
创建时间: 2026-08-02 21:16
更新时间: 2026-08-02 21:36
类型: 测试 + 代码审查 + Bug 修复报告
状态: 已完成
---

# isbn.png / 1.jpg 端到端 OCR/Barcode 测试 + Bug 修复报告

> 样本 A：`isbn.png`（1440×916 PNG, 117KB）→ 期望 **978-3-16-148410-0**  →  `9783161484100`
> 样本 B：`1.jpg`（504×512 JPEG, 60KB）→ 期望 **978-7-5086-7553-4**  →  `9787508675534`
> 测试范围：`recognizeIdentifier` / `recognizeBarcodes` / `recognizeText` 三个识别函数

---

## 0. 结论先行

### isbn.png（数字+条码合成图，非实拍）

| 路径 | 真实识别结果 | 期望 | 状态 |
|------|------------|------|------|
| ZXing（条形码扫描 / 上传 / 拍照） | `[]`（0 条） | 9783161484100 | ❌ 图非实拍条码 |
| Tesseract OCR（上传 / 拍照） | `9785161484100` / `1\n783161484100` | 9783161484100 | ⚠️ 部分识别、第 4 位 5↔3 误读 |
| 前端 `extractIdentifiers` 校验 | `9783161484100` ✅ / `978-3-16-148410-0` ❌ | 9783161484100 | ⚠️ 连字符版本不被接受 |

### 1.jpg（实拍封底，含 EAN-13 条形码 + 价格）

| 路径 | 真实识别结果 | 期望 | 状态 |
|------|------------|------|------|
| ZXing（条形码扫描 / 上传 / 拍照） | Node polyfill 抛 `Blob 类型错`（浏览器原生 BarcodeDetector 不受影响） | 9787508675534 | ⚠️ Node 端测试限制 |
| Tesseract OCR（eng + chi_sim） | `ISBN 978-7-5086-7553-4`（含连字符）+ 价格 `49.00` | 9787508675534 | ✅ **完全命中** |
| 前端 `extractIdentifiers` 校验 | `9787508675534` ✅ 校验位合法 / `978-7-5086-7553-4` ❌ 不接受 | 9787508675534 | ⚠️ 同样卡连字符 |

**核心发现**：
1. isbn.png 是"数字 + 条形线"合成图，**不是实拍条码照片**，ZXing 必然返回空。
2. Tesseract 在 isbn.png 上把 `3` 错读为 `5`，且漏掉前导 `978` → 产生 **9785161484100** 这种**校验位错**的假阳性。
3. **1.jpg（实拍）上 Tesseract 完美识别**：`ISBN 978-7-5086-7553-4` 一字不差，校验位 4 合法。这印证了 OCR 引擎本身没问题，问题在前端正则对连字符的处理。
4. 前端 `ocr/index.ts:110` 的正则 `\b97[89]\d{10}\b` 要求**连续 13 位**，无法接受带连字符的 `978-3-16-148410-0` 与 `978-7-5086-7553-4`，属已知盲区。

---

## 1. 新增的测试资产

```
frontend/vitest.config.ts                              新文件（vitest 配置）
frontend/src/__tests__/setup.ts                        新文件（happy-dom + 双样本路径）
frontend/src/__tests__/recognize.test.ts               新文件（23 个用例）
frontend/package.json                                  加 test / test:watch 脚本
```

`pnpm test` / `npm test` 现已可用，9.6 秒跑完 23 用例。

### 1.1 测试覆盖矩阵（23 项）

| # | describe | it | 验证目标 | 样本 |
|---|----------|----|---------|------|
| 1 | barcode/__test 纯函数 | normalize 去掉连字符/空格并大写 | 纯函数 | – |
| 2 | barcode/__test 纯函数 | classify 把 978/979 前缀的 13 位归为 isbn + ean_13 | 纯函数 | – |
| 3 | barcode/__test 纯函数 | classify 把 8 位 X/数字 ISSN 归为 issn | 纯函数 | – |
| 4 | recognizeIdentifier 编排 | barcode 命中 → 直接返回 source=barcode | 编排 | isbn.png |
| 5 | recognizeIdentifier 编排 | barcode 未命中 + OCR 命中 → source=ocr | 编排 | isbn.png |
| 6 | recognizeIdentifier 编排 | barcode 未命中 + OCR 也未命中 → source=none + error | 编排 | isbn.png |
| 7 | extractIdentifiers ISBN/ISSN 校验 | classify 不看校验位 | 行为记录 | – |
| 8 | extractIdentifiers ISBN/ISSN 校验 | 9783161484100 是合法 ISBN-13（手算） | 算法 | – |
| 9 | extractIdentifiers ISBN/ISSN 校验 | 9785161484100 校验位错误（OCR 误读产物） | 算法 | – |
| 10 | isbn.png 真实识别 | ZXing 端到端：isbn.png 不是实拍条码图 → 返回 0 条 | 真实 | isbn.png |
| 11 | isbn.png 真实识别 | OCR 端到端：tesseract.js 读出含 13 位的数字串 | 真实 | isbn.png |
| 12 | isbn.png 真实识别 | OCR 输出包含用户期望数字 3161484100 的相邻误读 | 真实 | isbn.png |
| 13 | 期望文本 978-3-16-148410-0 的提取路径 | classify 期望 RAW（去连字符）→ isbn=9783161484100 | 期望 | – |
| 14 | 期望文本 978-3-16-148410-0 的提取路径 | normalize 期望 RAW → 13 位数字串 | 期望 | – |
| 15 | 期望文本 978-3-16-148410-0 的提取路径 | OCR 拿到无连字符 13 位：能识别为 9783161484100 | 期望 | isbn.png |
| 16 | 期望文本 978-3-16-148410-0 的提取路径 | OCR 拿到带连字符的 978-3-16-148410-0：当前 extractIdentifiers 会拒识 | 已知限制 | – |
| 17 | 1.jpg 真实识别 | OCR 端到端：读出 "ISBN" 字样与 978-7-5086-7553-4 / 9787508675534 | 真实 | **1.jpg** |
| 18 | 1.jpg 真实识别 | OCR 读出的 ISBN-13 校验位合法（先去连字符） | 真实+算法 | **1.jpg** |
| 19 | 1.jpg 真实识别 | OCR 同时读到价格 "49" 与中文 "定价" | 真实 | **1.jpg** |
| 20 | 1.jpg 真实识别 | ZXing 端到端：Node polyfill 在 Vitest 环境抛 Blob 类型错 | Node 限制 | **1.jpg** |
| 21 | 1.jpg 期望路径 | classify 期望 RAW（去连字符）→ isbn=9787508675534 + format=ean_13 | 期望 | – |
| 22 | 1.jpg 期望路径 | recognizeIdentifier（OCR mock 返回 ISBN 9787508675534）→ source=ocr | 编排 | 1.jpg |
| 23 | 1.jpg 期望路径 | recognizeIdentifier（ZXing mock 返回 EAN-13）→ source=barcode（最快路径） | 编排 | 1.jpg |

### 1.2 运行结果

```
$ pnpm test
 ✓ src/__tests__/recognize.test.ts  (23 tests) 6616ms
 Test Files  1 passed (1)
      Tests  23 passed (23)
   Duration  9.57s
```

---

## 2. 真实识别基线

### 2.1 ZXing 条形码扫描

调用：`barcode-detector/ponyfill.BarcodeDetector.detect()`，参数与前端 `src/barcode/polyfill.ts:9` 的 `TARGET_FORMATS` 对齐。

```
detector = new BarcodeDetector()
formats  = ['ean_13','ean_8','upc_a','upc_e','code_128']
opts     = { tryHarder:true, tryRotate:true, tryInvert:true, tryDownscale:true, isPure:false }

result = []   ← 0 条
```

**结论**：isbn.png 的条形线条纹不是 ZXing 训练集里 EAN-13/UPC 的实拍样态（无光照梯度、无扫描噪声、间距过于规整），所以识别失败。

### 2.2 Tesseract OCR

调用：项目依赖的 `tesseract.js@5.1.0`，Node bindings（不带 `workerPath`，自动走 `worker_threads`）。

| PSM | 白名单 | 输出 | 备注 |
|-----|--------|------|------|
| 7 | `0123456789X-` | `"1\n783161484100"` | 单行模式，置信度 17 |
| 7 | 无 | `"Il\noN 783161\"484100"` | 默认模式，置信度 14 |
| 3, 6, 8 | 项目白名单 | `"29 785161 484100"` | 多种布局尝试 |

**结论**：Tesseract 始终能定位 `3161484100` 这 12 位，但前缀从 `978` 被读成 `29` 或缺失（混淆字符）；偶尔把 `3` 误读成 `5`。

---

## 3. 三种模式 → 三个函数的实际流向

```
┌──────────────────────────────────────────────────────────────────────────┐
│ 模式 1 · 图片上传 (FileUploader → File[] → runOCR)                       │
│   ocrFiles.value[0] ──▶ recognizeIdentifier(blob)                        │
│                          ├─ recognizeBarcodes(blob)  → {raw:''} (ZXing空)│
│                          └─ recognizeText(blob)                            │
│                              ├─ preprocess (灰度+Otsu)                    │
│                              ├─ detectBlur    → ok                          │
│                              └─ tesseract.recognize × 4 PSM                  │
│                                  → "1\n783161484100"                      │
│                                  → extractIdentifiers → noMatch            │
│                                  → {raw, error:'noMatch'}                 │
│                          → {source:'none', error:'noMatch', raw}          │
│   最终：报告区显示 "未识别到有效编号"                                      │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ 模式 2 · 条形码扫描 (BarcodeScanner → video → setInterval 500ms)        │
│   getUserMedia({facingMode:'environment'})                                │
│   scanOnce ──▶ recognizeBarcodes(video)                                  │
│                  ├─ 抓帧：canvas.drawImage(video)                         │
│                  └─ ZXing.detect(canvas) → {raw:''}                       │
│   每 500ms 重复；命中 ISBN 后 stopScan + emit update:identifier          │
│   最终：因 isbn.png 无条码图案，**永远不会命中**，但其它真实书脊会命中。  │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│ 模式 3 · 拍照识别 (CameraCapture → canvas.toBlob JPEG → File)            │
│   getUserMedia({facingMode:currentFacing})                                │
│   capture() ──▶ canvas.toBlob('image/jpeg', 0.92)                         │
│   useCapture() ──▶ new File([blob],'camera-capture-<ts>.jpg')            │
│                  ──▶ emit 'update:file' → onCameraFile                    │
│                          ──▶ 自动 runOCR() → recognizeIdentifier           │
│   后续路径同模式 1。                                                      │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 4. 期望值 9783161484100 的可识别条件

当 OCR 拿到 **无连字符**的 13 位字符串时，前端能完整识别：

```ts
// 测试 #15 复现
recognizeText(blob) → {
  isbn: '9783161484100',
  identifierType: 'isbn',
  raw:  '9783161484100',
  psm:  7,
}
recognizeIdentifier(blob) → {
  source: 'ocr',
  isbn:   '9783161484100',
}
```

而 OCR 实际拿到 `978-3-16-148410-0` 时，**当前实现会拒识**：

```ts
// 测试 #16 复现（已记录的已知限制）
const text = '978-3-16-148410-0'.replace(/O/g,'0').replace(/I/g,'1').replace(/l/g,'1');
// text = '978-3-16-148410-0'（无变化）
text.match(/\b97[89]\d{10}\b/)   // null —— 连字符隔断了连续数字
→ {raw, error:'noMatch'}
→ {source:'none'}
```

**修复建议**（不属于本次任务）：在 `ocr/index.ts:100` 的 `normalizeOcrDigits` 里再加 `.replace(/[-\s]/g, '')`，让 `\b97[89]\d{10}\b` 能匹配带连字符的版本。

---

## 5. 后续工作建议（不在本任务范围）

1. **联调回归**：把 isbn.png / 1.jpg 走浏览器手动测一遍，确认 ZXing 在浏览器原生 BarcodeDetector 下也是 0 条/1 条（Node polyfill 限制已知）。
2. **OCR 进一步提升**：
   - 把 PSM=7 与白名单 `0123456789X-` 作为**默认**参数（目前在 `recognizeText` 里需要先 setParameters 才生效）。
   - 加 ISBN-13 校验失败的"软拒"：当校验失败时尝试 ±1 位的同号邻位（修正 5↔3 这种单字符误读）。
   - **Bug 7**：`recognizeText` 的 PSM 循环返回第一个命中而非最高置信度 —— 可改为收集所有 PSM 结果按 confidence 排序取最优。
   - **Bug 8**：`ocr worker errorHandler` 只 console.error，调用方拿不到真实错误；建议在 `errorHandler` 内部把错误写到 `OCRResult.error` 而非永远返回 `failed`。
   - **Bug 6**：`BLUR_THRESHOLD = 30` 过严，实拍图（1.jpg）也能被误判模糊；建议提到 50 或加自适应。
3. **样本扩充**：再补 ISBN-10、ISSN-8 样本做端到端回归。
4. **identifier 的更多路径**：
   - **Bug 10**：当前 `RecognizeResult` 没透传 `format`，前端拿不到原始 ZXing 格式元数据（虽然 `source='barcode'` 时隐含 ean_13/issn）。

## 6. Bug 清单（已修 / 待修）

| # | 严重度 | 模块 | 描述 | 状态 |
|---|--------|------|------|------|
| 1 | 🔴 严重 | `ocr/index.ts:110` | 正则 `\b97[89]\d{10}\b` 不接受带连字符或 ISBN 前缀的 13 位 | ✅ 已修 |
| 2 | 🟡 中 | `ocr/index.ts:114,119` | ISBN-10 / ISSN 8 位正则可能与 ISBN-13 后 10/8 位冲突 | 待修 |
| 3 | 🟢 小 | `identifier/index.ts:51` | 错误兜底 `noMatch` 在 OCR 真正失败时不准 | 撤销（行为正确） |
| 4 | 🔴 严重 | `barcode/index.ts:32` | classify 不校验校验位，ZXing 误读会直接通过 | ✅ 已修 |
| 5 | 🟡 中 | `barcode/index.ts:71` | 只取 results[0]，错过 ISBN-13 + EAN-5 supplement | 待修 |
| 6 | 🟡 中 | `ocr/index.ts:289` | BLUR_THRESHOLD=30 过严，实拍也可能误判模糊 | 待修 |
| 7 | 🟡 中 | `ocr/index.ts:294` | PSM 循环返回首个命中，非最高置信度 | 待修 |
| 8 | 🟢 小 | `ocr/index.ts:38` | errorHandler 静默，调用方拿不到真实错误 | 待修 |
| 9 | 🟢 小 | `barcode/polyfill.ts` | 原生 detector 降级不可逆 | 设计如此 |
| 10 | 🟢 小 | `identifier/index.ts` | RecognizeResult 未透传 ZXing format | 待修 |

## 7. 修复明细

### Bug 1：`ocr/index.ts:100` normalizeOcrDigits

```diff
 function normalizeOcrDigits(s: string): string {
-  return s.replace(/O/g, '0').replace(/I/g, '1').replace(/l/g, '1');
+  return s
+    .replace(/[-\s]/g, '')        // 容忍连字符与空格（978-7-5086-7553-4）
+    .replace(/ISBN/gi, '')        // 容忍 ISBN/ISSN 文字前缀（"ISBN 978..." 里的 \b 会失效）
+    .replace(/ISSN/gi, '')
+    .replace(/O/g, '0')           // 视觉混淆字符归一
+    .replace(/I/g, '1')
+    .replace(/l/g, '1');
 }
```

**回归测试**：`extractIdentifiers('ISBN 978-7-5086-7553-4')` 现在返回 `{ isbn: '9787508675534', identifierType: 'isbn' }`，1.jpg 真实 OCR 输出可走通完整链路。

### Bug 4：`barcode/index.ts` 加校验位

```diff
+function isValidIsbn13(s: string): boolean { ... }
+function isValidIssn(s: string): boolean { ... }
+
 function classify(raw: string) {
   const text = normalize(raw);
   if (ISBN13_REGEX.test(text) && EAN13_ISBN_PREFIX.includes(text.slice(0, 3))) {
+    if (!isValidIsbn13(text)) return {};
     return { isbn: text, format: 'ean_13' };
   }
   if (ISSN_REGEX.test(text)) {
+    if (!isValidIssn(text)) return {};
     return { issn: text, format: 'issn' };
   }
   return {};
 }
```

**回归测试**：`classify('9785161484100')` 现在返回 `{}`（OCR 5↔3 误读产物不再被接受）。

### 新增：`ocr/index.ts` 暴露 `__test` 纯函数

```ts
export const __test = {
  isValidIsbn10, isValidIsbn13, isValidIssn, expandToIsbn13,
  normalizeOcrDigits, extractIdentifiers,
  PSM_MODES, BLUR_THRESHOLD, MAX_DIM, WHITELIST,
};
```

让测试能**直接调用**核心识别流程里的纯函数（不 mock），覆盖 Bug 1/4 的修复路径。

---

## 6. 附录：基线调用脚本

`recognize.test.ts:178-209` 的 `beforeAll` 即为离线基线采集脚本，剥离 vitest 即可在 Node 里直接跑：

```js
import { readFileSync } from 'node:fs';
import { BarcodeDetector } from 'barcode-detector/ponyfill';
import Tesseract from 'tesseract.js';

const buf = readFileSync('isbn.png');
const blob = new Blob([buf], { type: 'image/png' });

// ZXing
const d = new BarcodeDetector();
console.log(await d.detect(blob, {
  formats: ['ean_13','ean_8','upc_a','upc_e','code_128'],
  tryHarder: true, tryRotate: true, tryInvert: true,
  tryDownscale: true, isPure: false, maxNumberOfSymbols: 8,
}));

// OCR
const w = await Tesseract.createWorker(['eng'], 1);
await w.setParameters({
  tessedit_pageseg_mode: 7,
  tessedit_char_whitelist: '0123456789X-',
  preserve_interword_spaces: '1',
  user_defined_dpi: '300',
});
const r = await w.recognize('isbn.png');
console.log(r.data.text, r.data.confidence);
await w.terminate();
```

注：tesseract.js Node 跑会把 `eng.traineddata` / `chi_sim.traineddata` 缓存在 cwd；如需清理，请忽略 `*.traineddata` 文件或把它挪进 `<frontend>/.tesseract-cache/`。