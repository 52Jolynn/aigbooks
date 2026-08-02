/**
 * 统一识别入口：条形码与 OCR 并行执行，合并结果。
 * 条形码获取 ISBN/ISSN，OCR 从版权页提取书名/作者/书号。
 */
import { recognizeBarcodes, type BarcodeResult } from '@/barcode';
import { recognizeCopyrightPage, type OCRResult } from '@/ocr';

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
  blur?: number;
}

export async function recognizeIdentifier(
  image: File | Blob,
): Promise<RecognizeResult> {
  const [barcode, ocr] = await Promise.all([
    recognizeBarcodes(image).catch(() => ({ raw: '' } as BarcodeResult)),
    recognizeCopyrightPage(image).catch(() => ({ raw: '' } as OCRResult)),
  ]);

  const isbn = barcode.isbn || ocr.isbn;
  const issn = barcode.issn || ocr.issn;

  let source: RecognizeSource = 'none';
  if (barcode.isbn || barcode.issn) {
    source = 'barcode';
  } else if (ocr.isbn || ocr.issn || ocr.title || ocr.author) {
    source = 'ocr';
  }

  return {
    isbn,
    issn,
    title: ocr.title,
    author: ocr.author,
    source,
    error: ocr.error,
    raw: ocr.raw || barcode.raw,
    blur: ocr.blur,
  };
}
