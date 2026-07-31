/**
 * Tesseract.js 客户端 OCR 懒加载封装。
 * 失败静默回退，不阻塞表单。
 */
import { consoleMessages } from '@/i18n/zh';

export interface OCRResult {
  isbn?: string;
  title?: string;
  author?: string;
  raw: string;
}

export async function recognizeText(image: File | Blob): Promise<OCRResult> {
  try {
    const { createWorker } = await import('tesseract.js');
    const worker = await createWorker(['chi_sim', 'eng'], 1, {
      logger: () => {},
    });
    const { data } = await worker.recognize(image);
    await worker.terminate();

    const raw = data.text;
    const isbnMatch = raw.match(
      /\b(?:97[89])?[-\s]?\d{1,5}[-\s]?\d{1,7}[-\s]?\d{1,7}[-\s]?\d\b/,
    );
    const lines = raw.split('\n').map((s) => s.trim()).filter(Boolean);

    return {
      isbn: isbnMatch?.[0]?.replace(/[-\s]/g, ''),
      title: lines[0],
      author: lines[1],
      raw,
    };
  } catch (e) {
    console.warn(consoleMessages.ocrFailed, e);
    return { raw: '' };
  }
}