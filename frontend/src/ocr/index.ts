/**
 * Tesseract.js 客户端 OCR 懒加载封装。
 * 失败静默回退，不阻塞表单。
 */
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

export async function recognizeText(image: File | Blob): Promise<OCRResult> {
  try {
    const { createWorker } = await import('tesseract.js');
    const worker = await createWorker(['chi_sim', 'eng'], 1, {
      logger: () => {},
    });
    const { data } = await worker.recognize(image);
    await worker.terminate();

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
    return { raw: '' };
  }
}