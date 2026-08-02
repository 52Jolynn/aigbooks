/**
 * ISBN/ISSN 条形码识别。
 * 优先浏览器原生 BarcodeDetector，Firefox/iOS 自动降级到 ZXing WASM。
 */
import { loadBarcodeDetector } from './polyfill';

export interface BarcodeResult {
  isbn?: string;
  issn?: string;
  format?: string;
  raw: string;
}

const ISBN13_REGEX = /^\d{13}$/;
const ISSN_REGEX = /^\d{7}[\dX]$/;
const EAN13_ISBN_PREFIX = ['978', '979'];
const TARGET_FORMATS = ['ean_13', 'ean_8', 'upc_a', 'upc_e', 'code_128'];

let detectorPromise: ReturnType<typeof loadBarcodeDetector> | null = null;

function getDetector() {
  if (!detectorPromise) detectorPromise = loadBarcodeDetector();
  return detectorPromise;
}

function normalize(text: string): string {
  return text.replace(/[-\s]/g, '').toUpperCase();
}

function isValidIsbn13(s: string): boolean {
  if (!/^\d{13}$/.test(s)) return false;
  let sum = 0;
  for (let i = 0; i < 12; i++) {
    sum += parseInt(s[i], 10) * (i % 2 === 0 ? 1 : 3);
  }
  return ((10 - (sum % 10)) % 10) === parseInt(s[12], 10);
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

function classify(raw: string): { isbn?: string; issn?: string; format?: string } {
  const text = normalize(raw);
  if (ISBN13_REGEX.test(text) && EAN13_ISBN_PREFIX.includes(text.slice(0, 3))) {
    // 加校验位：避免 ZXing 在脏图上误读出 13 位但校验位错的伪 ISBN
    if (!isValidIsbn13(text)) return {};
    return { isbn: text, format: 'ean_13' };
  }
  if (ISSN_REGEX.test(text)) {
    if (!isValidIssn(text)) return {};
    return { issn: text, format: 'issn' };
  }
  return {};
}

export async function recognizeBarcodes(
  image:
    | Blob
    | File
    | ImageBitmap
    | HTMLImageElement
    | HTMLVideoElement
    | HTMLCanvasElement
    | ImageData,
): Promise<BarcodeResult> {
  const Detector = await getDetector();
  if (!Detector) return { raw: '' };
  try {
    // HTMLVideoElement 兼容：用 canvas.drawImage 抓帧（同步、可靠）
    let input: unknown = image;
    if (image instanceof HTMLVideoElement) {
      if (image.readyState < 2 || image.videoWidth === 0 || image.videoHeight === 0) {
        return { raw: '' };
      }
      const canvas = document.createElement('canvas');
      canvas.width = image.videoWidth;
      canvas.height = image.videoHeight;
      const ctx = canvas.getContext('2d');
      if (!ctx) return { raw: '' };
      ctx.drawImage(image, 0, 0);
      input = canvas;
    }
    const instance = new Detector();
    const results = await instance.detect(input as never);
    if (results.length === 0) return { raw: '' };
    const first = results[0];
    const classified = classify(first.rawValue ?? '');
    return {
      ...classified,
      format: first.format ?? classified.format,
      raw: first.rawValue ?? '',
    };
  } catch (e) {
    console.warn('[barcode] detect 失败：', e);
    return { raw: '' };
  }
}

export function __resetForTest() {
  detectorPromise = null;
}

export const __test = {
  normalize,
  classify,
  TARGET_FORMATS,
};
