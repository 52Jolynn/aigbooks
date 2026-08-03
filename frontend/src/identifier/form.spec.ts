import { describe, expect, it } from 'vitest';
import { applyRecognitionProgress } from '@/identifier/form';

const emptyFields = {
  type: 'isbn' as const,
  identifier: '',
  title: '',
  author: '',
};

describe('applyRecognitionProgress', () => {
  it('条码步骤完成后立即填充编号', () => {
    const result = applyRecognitionProgress(emptyFields, {
      step: 'barcode',
      status: 'matched',
      result: { issn: '10037055', source: 'barcode' },
    });

    expect(result).toMatchObject({ type: 'issn', identifier: '10037055' });
  });

  it('OCR 步骤立即补充书名作者且不覆盖条码编号', () => {
    const result = applyRecognitionProgress(
      { ...emptyFields, identifier: '9787508675534' },
      {
        step: 'ocr',
        status: 'matched',
        result: {
          isbn: '9787115428028',
          title: '测试书名',
          author: '测试作者',
          source: 'ocr',
        },
      },
    );

    expect(result).toEqual({
      type: 'isbn',
      identifier: '9787508675534',
      title: '测试书名',
      author: '测试作者',
    });
  });
});
