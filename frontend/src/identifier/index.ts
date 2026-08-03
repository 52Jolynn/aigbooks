import { recognizeBarcodes, type BarcodeResult } from '@/barcode';
import { recognizeCopyrightPage, type OCRResult } from '@/ocr';

export type RecognizeSource = 'barcode' | 'ocr' | 'none';
export type RecognizeError = 'imageTooBlurry' | 'noMatch' | 'failed';
export type RecognitionStep = 'barcode' | 'ocr';
export type RecognitionStepStatus = 'running' | 'matched' | 'noMatch' | 'failed';

export interface RecognizeResult {
  isbn?: string;
  issn?: string;
  title?: string;
  author?: string;
  summary?: string;
  source: RecognizeSource;
  error?: RecognizeError;
  raw?: string;
  blur?: number;
}

export interface RecognitionProgress {
  step: RecognitionStep;
  status: RecognitionStepStatus;
  result?: Partial<RecognizeResult>;
  error?: RecognizeError;
}

export interface RecognizeOptions {
  onProgress?: (progress: RecognitionProgress) => void;
}

function notify(options: RecognizeOptions, progress: RecognitionProgress) {
  try {
    options.onProgress?.(progress);
  } catch {
    return;
  }
}

function hasBarcodeResult(result: BarcodeResult): boolean {
  return Boolean(result.isbn || result.issn);
}

function hasOCRResult(result: OCRResult): boolean {
  return Boolean(result.isbn || result.issn || result.title || result.author || result.summary);
}

export async function recognizeIdentifier(
  image: File | Blob,
  options: RecognizeOptions = {},
): Promise<RecognizeResult> {
  notify(options, { step: 'barcode', status: 'running' });

  let barcode: BarcodeResult = { raw: '' };
  try {
    barcode = await recognizeBarcodes(image);
    notify(options, {
      step: 'barcode',
      status: hasBarcodeResult(barcode) ? 'matched' : 'noMatch',
      result: {
        isbn: barcode.isbn,
        issn: barcode.issn,
        source: hasBarcodeResult(barcode) ? 'barcode' : 'none',
        raw: barcode.raw,
      },
    });
  } catch {
    notify(options, { step: 'barcode', status: 'failed', error: 'failed' });
  }

  notify(options, { step: 'ocr', status: 'running' });

  let ocr: OCRResult = { raw: '' };
  try {
    ocr = await recognizeCopyrightPage(image);
    const matched = hasOCRResult(ocr);
    notify(options, {
      step: 'ocr',
      status: matched ? 'matched' : ocr.error === 'failed' ? 'failed' : 'noMatch',
      result: {
        isbn: ocr.isbn,
        issn: ocr.issn,
        title: ocr.title,
        author: ocr.author,
        summary: ocr.summary,
        source: matched ? 'ocr' : 'none',
        error: ocr.error,
        raw: ocr.raw,
        blur: ocr.blur,
      },
      error: ocr.error,
    });
  } catch {
    ocr = { raw: '', error: 'failed' };
    notify(options, { step: 'ocr', status: 'failed', error: 'failed' });
  }

  const isbn = barcode.isbn || ocr.isbn;
  const issn = barcode.issn || ocr.issn;
  const barcodeMatched = hasBarcodeResult(barcode);
  const ocrMatched = hasOCRResult(ocr);

  return {
    isbn,
    issn,
    title: ocr.title,
    author: ocr.author,
    summary: ocr.summary,
    source: barcodeMatched ? 'barcode' : ocrMatched ? 'ocr' : 'none',
    error: isbn || issn || ocr.title || ocr.author || ocr.summary ? undefined : ocr.error || 'noMatch',
    raw: ocr.raw || barcode.raw,
    blur: ocr.blur,
  };
}
