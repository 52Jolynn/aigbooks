import type { IdentifierType } from '@/api/identifiers';
import type { RecognitionProgress } from '@/identifier';
import { __test as ocrTest } from '@/ocr';

export interface RecognitionFields {
  type: IdentifierType;
  identifier: string;
  title: string;
  author: string;
  description: string;
}

export function applyRecognitionProgress(
  fields: RecognitionFields,
  progress: RecognitionProgress,
): RecognitionFields {
  const result = progress.result;
  if (!result) return fields;

  if (progress.step === 'barcode') {
    if (result.isbn) {
      return { ...fields, type: 'isbn', identifier: ocrTest.formatIsbn13(result.isbn) };
    }
    if (result.issn) {
      return { ...fields, type: 'issn', identifier: result.issn };
    }
    return fields;
  }

  const next = { ...fields };
  if (!next.identifier && result.isbn) {
    next.type = 'isbn';
    next.identifier = result.isbn;
  } else if (!next.identifier && result.issn) {
    next.type = 'issn';
    next.identifier = result.issn;
  }
  if (result.title) next.title = result.title;
  if (result.author) next.author = result.author;
  if (!next.description && result.summary) next.description = result.summary;
  return next;
}
