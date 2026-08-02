/**
 * Tesseract.js 客户端 OCR 懒加载封装。
 * 失败静默回退，不阻塞表单。
 */
import type { Worker as TesseractWorker } from 'tesseract.js';
import { consoleMessages } from '@/i18n/zh';
import type { IdentifierType } from '@/api/identifiers';

export interface OCRResult {
  isbn?: string;
  issn?: string;
  identifierType?: IdentifierType;
  title?: string;
  author?: string;
  raw: string;
}

const ISBN_REGEX =
  /\b(?:97[89])?[-\s]?\d{1,5}[-\s]?\d{1,7}[-\s]?\d{1,7}[-\s]?\d\b/;
const ISSN_REGEX = /\b\d{4}[-\s]?\d{3}[\dX]\b/;
const HEIC_TYPES = new Set(['image/heic', 'image/heif']);
const RECOGNIZE_TIMEOUT_MS = 30_000;

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

export async function recognizeText(image: File | Blob): Promise<OCRResult> {
  let timer: ReturnType<typeof setTimeout> | undefined;
  try {
    const normalized = await normalizeImage(image);
    const worker = await getWorker();

    const recognizePromise = worker.recognize(normalized);
    const timeoutPromise = new Promise<never>((_, reject) => {
      timer = setTimeout(
        () => reject(new Error('ocr-recognize-timeout')),
        RECOGNIZE_TIMEOUT_MS,
      );
    });
    const { data } = await Promise.race([recognizePromise, timeoutPromise]);

    const raw = data.text;
    const isbnMatch = raw.match(ISBN_REGEX);
    const issnMatch = raw.match(ISSN_REGEX);
    const lines = raw.split('\n').map((s) => s.trim()).filter(Boolean);

    let identifierType: IdentifierType | undefined;
    let primary: string | undefined;
    if (isbnMatch) {
      identifierType = 'isbn';
      primary = isbnMatch[0].replace(/[-\s]/g, '');
    } else if (issnMatch) {
      identifierType = 'issn';
      primary = issnMatch[0].replace(/[-\s]/g, '');
    }

    return {
      isbn: isbnMatch?.[0]?.replace(/[-\s]/g, ''),
      issn: issnMatch?.[0]?.replace(/[-\s]/g, ''),
      identifierType,
      title: lines[0],
      author: lines[1],
      raw,
      ...(primary !== undefined ? { identifier: primary } : {}),
    } as OCRResult;
  } catch (e) {
    console.warn(consoleMessages.ocrFailed, e);
    void disposeWorker();
    return { raw: '' };
  } finally {
    if (timer) clearTimeout(timer);
  }
}