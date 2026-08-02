/**
 * Tesseract.js 客户端 OCR 懒加载封装。
 * 失败静默回退，不阻塞表单。
 */
import type { Worker as TesseractWorker, PSM } from 'tesseract.js';
import { consoleMessages } from '@/i18n/zh';
import type { IdentifierType } from '@/api/identifiers';

export interface OCRResult {
  isbn?: string;
  issn?: string;
  identifierType?: IdentifierType;
  title?: string;
  author?: string;
  raw: string;
  psm?: number;
  blur?: number;
  error?: 'imageTooBlurry' | 'noMatch' | 'failed';
}

const RECOGNIZE_TIMEOUT_MS = 30_000;
const PSM_MODES: readonly number[] = [6, 7, 8, 3];
const WHITELIST = '0123456789XISBNsni- ';
const BLUR_THRESHOLD = 30;
const MAX_DIM = 2000;

let workerPromise: Promise<TesseractWorker> | null = null;

async function getWorker(): Promise<TesseractWorker> {
  if (!workerPromise) {
    workerPromise = (async () => {
      const Tesseract = await import('tesseract.js');
      return Tesseract.createWorker(['chi_sim', 'eng'], 1, {
        workerPath: '/tesseract/worker.min.js',
        corePath: '/tesseract/core',
        langPath: '/tesseract/lang',
        logger: import.meta.env.DEV ? (m) => console.log('[ocr]', m) : () => {},
        errorHandler: (err) => console.error('[ocr] worker error:', err),
      });
    })();
  }
  return workerPromise;
}

async function disposeWorker(): Promise<void> {
  const cached = workerPromise;
  workerPromise = null;
  if (!cached) return;
  try {
    const w = await cached;
    await w.terminate();
  } catch {
    // terminate 失败不影响下次重建
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
  return s.replace(/O/g, '0').replace(/I/g, '1').replace(/l/g, '1');
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

function otsuThreshold(gray: Uint8ClampedArray): number {
  const hist = new Array<number>(256).fill(0);
  for (let i = 0; i < gray.length; i++) hist[gray[i]]++;
  const total = gray.length;
  let sum = 0;
  for (let t = 0; t < 256; t++) sum += t * hist[t];
  let sumB = 0;
  let wB = 0;
  let maxVar = 0;
  let threshold = 127;
  for (let t = 0; t < 256; t++) {
    wB += hist[t];
    if (wB === 0) continue;
    const wF = total - wB;
    if (wF === 0) break;
    sumB += t * hist[t];
    const mB = sumB / wB;
    const mF = (sum - sumB) / wF;
    const between = wB * wF * (mB - mF) * (mB - mF);
    if (between > maxVar) {
      maxVar = between;
      threshold = t;
    }
  }
  return threshold;
}

async function preprocessImage(blob: Blob): Promise<Blob> {
  const bitmap = await toImageBitmap(blob);
  const w0 = bitmap.width;
  const h0 = bitmap.height;
  const scale = Math.min(1, MAX_DIM / Math.max(w0, h0));
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
  const imageData = ctx.getImageData(0, 0, w, h);
  const data = imageData.data;
  const gray = new Uint8ClampedArray(w * h);
  for (let i = 0, j = 0; i < data.length; i += 4, j++) {
    gray[j] = Math.round(data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114);
  }
  const threshold = otsuThreshold(gray);
  for (let j = 0, k = 0; j < gray.length; j++, k += 4) {
    const v = gray[j] < threshold ? 0 : 255;
    data[k] = data[k + 1] = data[k + 2] = v;
    data[k + 3] = 255;
  }
  ctx.putImageData(imageData, 0, 0);
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

// ===== HEIC 转码（已有） =====

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

export async function recognizeText(image: File | Blob): Promise<OCRResult> {
  let timer: ReturnType<typeof setTimeout> | undefined;
  try {
    const normalized = await normalizeImage(image);
    const preprocessed = await preprocessImage(normalized);
    const blur = await detectBlur(preprocessed);
    if (blur < BLUR_THRESHOLD) {
      return { raw: '', error: 'imageTooBlurry', blur };
    }

    const worker = await getWorker();
    for (const psm of PSM_MODES) {
      try {
        await worker.setParameters({
          tessedit_pageseg_mode: psm as unknown as PSM,
          tessedit_char_whitelist: WHITELIST,
          preserve_interword_spaces: '1',
          user_defined_dpi: '300',
        });
      } catch (e) {
        console.warn('[ocr] setParameters 失败：', e);
      }
      const recognizePromise = worker.recognize(preprocessed);
      const timeoutPromise = new Promise<never>((_, reject) => {
        timer = setTimeout(
          () => reject(new Error('ocr-recognize-timeout')),
          RECOGNIZE_TIMEOUT_MS,
        );
      });
      try {
        const { data } = await Promise.race([recognizePromise, timeoutPromise]);
        const extracted = extractIdentifiers(data.text);
        if (extracted.isbn || extracted.issn) {
          return { ...extracted, raw: data.text, psm, blur };
        }
      } catch (e) {
        if (e instanceof Error && e.message === 'ocr-recognize-timeout') {
          console.warn(`[ocr] PSM=${psm} 超时`);
          void disposeWorker();
          return { raw: '', error: 'failed', blur };
        }
        throw e;
      } finally {
        if (timer) {
          clearTimeout(timer);
          timer = undefined;
        }
      }
    }
    return { raw: '', error: 'noMatch', blur };
  } catch (e) {
    console.warn(consoleMessages.ocrFailed, e);
    void disposeWorker();
    return { raw: '', error: 'failed' };
  }
}
