/**
 * 统一识别入口：先条形码 → 后 OCR → 兜底手动。
 * 不修改 ocr/ 与 barcode/ 的导出。
 */
import { recognizeBarcodes, type BarcodeResult } from '@/barcode';
import { recognizeText, type OCRResult } from '@/ocr';

export type RecognizeSource = 'barcode' | 'ocr' | 'none';
export type RecognizeError = 'imageTooBlurry' | 'noMatch' | 'failed';

export interface RecognizeResult {
  isbn?: string;
  issn?: string;
  title?: string;
  author?: string;
  source: RecognizeSource;
  error?: RecognizeError;
  raw?: string;
  psm?: number;
  blur?: number;
}

export async function recognizeIdentifier(
  image: File | Blob,
): Promise<RecognizeResult> {
  const barcode: BarcodeResult = await recognizeBarcodes(image);
  if (barcode.isbn || barcode.issn) {
    return {
      isbn: barcode.isbn,
      issn: barcode.issn,
      source: 'barcode',
      raw: barcode.raw,
    };
  }
  const ocr: OCRResult = await recognizeText(image);
  if (ocr.isbn || ocr.issn) {
    return {
      isbn: ocr.isbn,
      issn: ocr.issn,
      title: ocr.title,
      author: ocr.author,
      source: 'ocr',
      error: ocr.error,
      raw: ocr.raw,
      psm: ocr.psm,
      blur: ocr.blur,
    };
  }
  return {
    source: 'none',
    error: ocr.error ?? 'noMatch',
    raw: ocr.raw,
    blur: ocr.blur,
  };
}
