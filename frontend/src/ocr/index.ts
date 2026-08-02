/**
 * PaddleOCR.js 客户端 OCR 懒加载封装。
 * 失败静默回退，不阻塞表单。
 * 单一入口 recognizeCopyrightPage：从版权页/封底 OCR 中提取书名、作者、ISBN/ISSN。
 */
import { PaddleOCR } from '@paddleocr/paddleocr-js';
import type { OcrRuntimeParamsInput, OcrResult } from '@paddleocr/paddleocr-js';
import { consoleMessages } from '@/i18n/zh';
import type { IdentifierType } from '@/api/identifiers';

export interface OCRResult {
  isbn?: string;
  issn?: string;
  identifierType?: IdentifierType;
  title?: string;
  author?: string;
  raw: string;
  blur?: number;
  error?: 'imageTooBlurry' | 'noMatch' | 'failed';
}

interface OCRRunner {
  predict(input: unknown, params?: OcrRuntimeParamsInput): Promise<OcrResult[]>;
  dispose(): Promise<void>;
}

const RECOGNIZE_TIMEOUT_MS = 60_000;
const BLUR_THRESHOLD = 30;
const MAX_DIM = 2000;

let ocrPromise: Promise<OCRRunner> | null = null;

async function getOCR(): Promise<OCRRunner> {
  if (!ocrPromise) {
    ocrPromise = PaddleOCR.create({
      lang: 'ch',
      ocrVersion: 'PP-OCRv5',
      textDetectionModelName: 'PP-OCRv5_mobile_det',
      textDetectionModelAsset: {
        url: '/models/PP-OCRv5_mobile_det.tar',
      },
      textRecognitionModelName: 'PP-OCRv5_mobile_rec',
      textRecognitionModelAsset: {
        url: '/models/PP-OCRv5_mobile_rec.tar',
      },
    }) as Promise<OCRRunner>;
  }
  return ocrPromise;
}

async function disposeOCR(): Promise<void> {
  const cached = ocrPromise;
  ocrPromise = null;
  if (!cached) return;
  try {
    const ocr = await cached;
    await ocr.dispose();
  } catch {
    // dispose 失败不影响下次重建
  }
}

// ===== ISBN / ISSN 校验 =====

function isValidIsbn13(s: string): boolean {
  if (!/^\d{13}$/.test(s)) return false;
  let sum = 0;
  for (let i = 0; i < 12; i++) {
    sum += parseInt(s[i], 10) * (i % 2 === 0 ? 1 : 3);
  }
  return ((10 - (sum % 10)) % 10) === parseInt(s[12], 10);
}

function isValidIsbn10(s: string): boolean {
  if (!/^\d{9}[\dX]$/.test(s)) return false;
  let sum = 0;
  for (let i = 0; i < 10; i++) {
    const d = s[i] === 'X' ? 10 : parseInt(s[i], 10);
    sum += d * (10 - i);
  }
  return sum % 11 === 0;
}

function isValidIssn(s: string): boolean {
  if (!/^\d{7}[\dX]$/.test(s)) return false;
  let sum = 0;
  for (let i = 0; i < 7; i++) {
    sum += parseInt(s[i], 10) * (8 - i);
  }
  const checkDigit = (11 - (sum % 11)) % 11;
  const expected = checkDigit === 10 ? 'X' : String(checkDigit);
  return s[7] === expected;
}

function expandToIsbn13(s: string): string | null {
  if (s.length !== 10 || !isValidIsbn10(s)) return null;
  const base = `978${s.slice(0, 9)}`;
  let sum = 0;
  for (let i = 0; i < 12; i++) {
    sum += parseInt(base[i], 10) * (i % 2 === 0 ? 1 : 3);
  }
  const check = (10 - (sum % 10)) % 10;
  return base + check;
}

function normalizeOcrDigits(s: string): string {
  return s
    .replace(/[-\s]/g, '')
    .replace(/ISBN/gi, '')
    .replace(/ISSN/gi, '')
    .replace(/O/g, '0')
    .replace(/I/g, '1')
    .replace(/l/g, '1');
}

function extractIdentifiers(raw: string): {
  isbn?: string;
  issn?: string;
  identifierType?: IdentifierType;
} {
  const text = normalizeOcrDigits(raw);
  const isbn13Match = text.match(/\b97[89]\d{10}\b/);
  if (isbn13Match && isValidIsbn13(isbn13Match[0])) {
    return { isbn: isbn13Match[0], identifierType: 'isbn' };
  }
  const isbn10Match = text.match(/\b\d{9}[\dX]\b/);
  if (isbn10Match) {
    const expanded = expandToIsbn13(isbn10Match[0]);
    if (expanded) return { isbn: expanded, identifierType: 'isbn' };
  }
  const issnMatch = text.match(/\b\d{7}[\dX]\b/);
  if (issnMatch && isValidIssn(issnMatch[0])) {
    return { issn: issnMatch[0], identifierType: 'issn' };
  }
  return {};
}

function extractCipInfo(raw: string): { title?: string; author?: string } {
  const text = raw.replace(/\s+/g, ' ').trim();
  const cipMatch = text.match(
    /(?:CIP[)）]\s*)?数据\s*\n?\s*(.+?)\s*\/\s*(.+?)(?:\s*[.．]\s*--|\s*编著|\s*编\s|$)/m,
  );
  if (cipMatch) {
    const title = cipMatch[1].replace(/[.．]\s*--.*$/, '').trim();
    const author = cipMatch[2]
      .replace(/编著|主编|编$|著$/, '')
      .replace(/[.．]\s*--.*$/, '')
      .trim();
    if (title && author) return { title, author };
  }
  const slashMatch = text.match(/^(.{2,}?)\s*\/\s*(.{2,}?)(?:\s*[.．]\s*--|$)/m);
  if (slashMatch) {
    return {
      title: slashMatch[1].trim(),
      author: slashMatch[2].replace(/编著|主编|编$|著$/, '').trim(),
    };
  }
  return {};
}

// ===== 图像预处理 =====

async function toImageBitmap(blob: Blob): Promise<ImageBitmap> {
  if (typeof createImageBitmap === 'function') {
    return createImageBitmap(blob);
  }
  const url = URL.createObjectURL(blob);
  try {
    const img = await new Promise<HTMLImageElement>((resolve, reject) => {
      const el = new Image();
      el.onload = () => resolve(el);
      el.onerror = () => reject(new Error('image-decode-failed'));
      el.src = url;
    });
    return img as unknown as ImageBitmap;
  } finally {
    URL.revokeObjectURL(url);
  }
}

async function scaleImage(blob: Blob): Promise<Blob> {
  const bitmap = await toImageBitmap(blob);
  const w0 = bitmap.width;
  const h0 = bitmap.height;
  const scale = Math.min(1, MAX_DIM / Math.max(w0, h0));
  if (scale >= 1) return blob;
  const w = Math.max(1, Math.round(w0 * scale));
  const h = Math.max(1, Math.round(h0 * scale));
  const useOffscreen = typeof OffscreenCanvas !== 'undefined';
  const canvas: OffscreenCanvas | HTMLCanvasElement = useOffscreen
    ? new OffscreenCanvas(w, h)
    : Object.assign(document.createElement('canvas'), { width: w, height: h });
  const ctx = canvas.getContext('2d') as
    | CanvasRenderingContext2D
    | OffscreenCanvasRenderingContext2D
    | null;
  if (!ctx) return blob;
  ctx.drawImage(bitmap as unknown as CanvasImageSource, 0, 0, w, h);
  if (canvas instanceof OffscreenCanvas) {
    return canvas.convertToBlob({ type: 'image/png' });
  }
  return new Promise<Blob>((resolve) => {
    (canvas as HTMLCanvasElement).toBlob((b) => resolve(b ?? blob), 'image/png');
  });
}

async function detectBlur(blob: Blob): Promise<number> {
  const bitmap = await toImageBitmap(blob);
  const w = bitmap.width;
  const h = bitmap.height;
  if (w < 3 || h < 3) return 0;
  const canvas = typeof OffscreenCanvas !== 'undefined'
    ? new OffscreenCanvas(w, h)
    : Object.assign(document.createElement('canvas'), { width: w, height: h });
  const ctx = canvas.getContext('2d') as CanvasRenderingContext2D | OffscreenCanvasRenderingContext2D | null;
  if (!ctx) return 100;
  ctx.drawImage(bitmap as unknown as CanvasImageSource, 0, 0);
  const data = ctx.getImageData(0, 0, w, h).data;
  let sum = 0;
  let sumSq = 0;
  let count = 0;
  for (let y = 1; y < h - 1; y++) {
    for (let x = 1; x < w - 1; x++) {
      const i = (y * w + x) * 4;
      const lum = (data[i] + data[i + 1] + data[i + 2]) / 3;
      const lumTop = (data[i - w * 4] + data[i - w * 4 + 1] + data[i - w * 4 + 2]) / 3;
      const lumBot = (data[i + w * 4] + data[i + w * 4 + 1] + data[i + w * 4 + 2]) / 3;
      const lumL = (data[i - 4] + data[i - 3] + data[i - 2]) / 3;
      const lumR = (data[i + 4] + data[i + 5] + data[i + 6]) / 3;
      const lap = 4 * lum - lumTop - lumBot - lumL - lumR;
      sum += lap;
      sumSq += lap * lap;
      count++;
    }
  }
  if (count === 0) return 0;
  const mean = sum / count;
  return sumSq / count - mean * mean;
}

// ===== HEIC 转码 =====

const HEIC_TYPES = new Set(['image/heic', 'image/heif']);

async function normalizeImage(image: File | Blob): Promise<Blob> {
  if (!('type' in image) || !HEIC_TYPES.has(image.type)) {
    return image;
  }
  try {
    const url = URL.createObjectURL(image);
    try {
      const img = await new Promise<HTMLImageElement>((resolve, reject) => {
        const el = new Image();
        el.onload = () => resolve(el);
        el.onerror = () => reject(new Error('heic-decode-failed'));
        el.src = url;
      });
      const canvas = document.createElement('canvas');
      canvas.width = img.naturalWidth;
      canvas.height = img.naturalHeight;
      const ctx = canvas.getContext('2d');
      if (!ctx) return image;
      ctx.drawImage(img, 0, 0);
      const blob = await new Promise<Blob | null>((resolve) =>
        canvas.toBlob((b) => resolve(b), 'image/jpeg', 0.92),
      );
      return blob ?? image;
    } finally {
      URL.revokeObjectURL(url);
    }
  } catch (e) {
    console.warn('[ocr] HEIC 转码失败，使用原图：', e);
    return image;
  }
}

// ===== 主入口 =====

export async function recognizeCopyrightPage(image: File | Blob): Promise<OCRResult> {
  let timer: ReturnType<typeof setTimeout> | undefined;
  try {
    const normalized = await normalizeImage(image);
    const blur = await detectBlur(normalized);
    if (blur < BLUR_THRESHOLD) {
      return { raw: '', error: 'imageTooBlurry', blur };
    }
    const scaled = await scaleImage(normalized);

    const ocr = await getOCR();
    const predictPromise = ocr.predict(scaled);
    const timeoutPromise = new Promise<never>((_, reject) => {
      timer = setTimeout(
        () => reject(new Error('ocr-recognize-timeout')),
        RECOGNIZE_TIMEOUT_MS,
      );
    });

    try {
      const results = await Promise.race([predictPromise, timeoutPromise]);
      const first = results[0];
      const text = first?.items.map((item) => item.text).join('\n') ?? '';
      const identifiers = extractIdentifiers(text);
      const cip = extractCipInfo(text);
      if (!identifiers.isbn && !identifiers.issn && !cip.title && !cip.author) {
        return { raw: text, blur };
      }
      return { ...identifiers, ...cip, raw: text, blur };
    } finally {
      if (timer) clearTimeout(timer);
    }
  } catch (e) {
    if (e instanceof Error && e.message === 'ocr-recognize-timeout') {
      console.warn('[ocr] 识别超时');
    } else {
      console.warn(consoleMessages.ocrFailed, e);
    }
    void disposeOCR();
    return { raw: '', error: 'failed' };
  }
}

/**
 * 暴露纯函数与关键常量给测试，避免外部绕过识别流程直接复制粘贴算法。
 * 不计入公开 API；只在 __test 命名空间下导出。
 */
export const __test = {
  isValidIsbn10,
  isValidIsbn13,
  isValidIssn,
  expandToIsbn13,
  normalizeOcrDigits,
  extractIdentifiers,
  extractCipInfo,
  BLUR_THRESHOLD,
  MAX_DIM,
};