import { beforeEach, describe, expect, it, vi } from 'vitest';

const { recognizeBarcodes, recognizeCopyrightPage } = vi.hoisted(() => ({
  recognizeBarcodes: vi.fn(),
  recognizeCopyrightPage: vi.fn(),
}));

vi.mock('@/barcode', () => ({ recognizeBarcodes }));
vi.mock('@/ocr', () => ({ recognizeCopyrightPage }));

import { recognizeIdentifier, type RecognitionProgress } from '@/identifier';

describe('recognizeIdentifier', () => {
  beforeEach(() => {
    recognizeBarcodes.mockReset();
    recognizeCopyrightPage.mockReset();
  });

  it('按条码后 OCR 的顺序执行并返回每一步结果', async () => {
    const calls: string[] = [];
    const progress: RecognitionProgress[] = [];
    recognizeBarcodes.mockImplementation(async () => {
      calls.push('barcode');
      return { isbn: '9787508675534', raw: '9787508675534' };
    });
    recognizeCopyrightPage.mockImplementation(async () => {
      calls.push('ocr');
      return {
        isbn: '9787115428028',
        title: '测试书名',
        author: '测试作者',
        raw: '测试书名 测试作者',
      };
    });

    const result = await recognizeIdentifier(new Blob(), {
      onProgress: (event) => progress.push(event),
    });

    expect(calls).toEqual(['barcode', 'ocr']);
    expect(progress.map(({ step, status }) => `${step}:${status}`)).toEqual([
      'barcode:running',
      'barcode:matched',
      'ocr:running',
      'ocr:matched',
    ]);
    expect(progress[1]?.result).toMatchObject({ isbn: '9787508675534' });
    expect(progress[3]?.result).toMatchObject({ title: '测试书名', author: '测试作者' });
    expect(result).toMatchObject({
      isbn: '9787508675534',
      title: '测试书名',
      author: '测试作者',
      source: 'barcode',
    });
  });

  it('条码失败后仍执行 OCR 并采用 OCR 结果', async () => {
    const progress: RecognitionProgress[] = [];
    recognizeBarcodes.mockRejectedValue(new Error('barcode failed'));
    recognizeCopyrightPage.mockResolvedValue({
      issn: '10037055',
      title: '测试期刊',
      author: '编辑部',
      raw: 'ISSN 1003-7055',
    });

    const result = await recognizeIdentifier(new Blob(), {
      onProgress: (event) => progress.push(event),
    });

    expect(recognizeCopyrightPage).toHaveBeenCalledOnce();
    expect(progress.map(({ step, status }) => `${step}:${status}`)).toEqual([
      'barcode:running',
      'barcode:failed',
      'ocr:running',
      'ocr:matched',
    ]);
    expect(result).toMatchObject({ issn: '10037055', source: 'ocr' });
  });

  it('条码未命中后执行 OCR 并采用 OCR 结果', async () => {
    const progress: RecognitionProgress[] = [];
    recognizeBarcodes.mockResolvedValue({ raw: '' });
    recognizeCopyrightPage.mockResolvedValue({ title: '测试书名', raw: '测试书名' });

    const result = await recognizeIdentifier(new Blob(), {
      onProgress: (event) => progress.push(event),
    });

    expect(progress.map(({ step, status }) => `${step}:${status}`)).toEqual([
      'barcode:running',
      'barcode:noMatch',
      'ocr:running',
      'ocr:matched',
    ]);
    expect(result).toMatchObject({ title: '测试书名', source: 'ocr' });
  });

  it('两阶段均未命中时返回未识别', async () => {
    recognizeBarcodes.mockResolvedValue({ raw: '' });
    recognizeCopyrightPage.mockResolvedValue({ raw: '' });

    const result = await recognizeIdentifier(new Blob());

    expect(result).toMatchObject({ source: 'none', error: 'noMatch' });
  });

  it('条码成功但 OCR 失败时保留条码结果', async () => {
    recognizeBarcodes.mockResolvedValue({ issn: '10037055', raw: '10037055' });
    recognizeCopyrightPage.mockRejectedValue(new Error('ocr failed'));

    const result = await recognizeIdentifier(new Blob());

    expect(result).toMatchObject({ issn: '10037055', source: 'barcode' });
    expect(result.error).toBeUndefined();
  });

  it('进度回调异常不会中断识别流程', async () => {
    recognizeBarcodes.mockResolvedValue({ isbn: '9787508675534', raw: '9787508675534' });
    recognizeCopyrightPage.mockResolvedValue({ title: '测试书名', raw: '测试书名' });

    const result = await recognizeIdentifier(new Blob(), {
      onProgress: () => {
        throw new Error('ui disposed');
      },
    });

    expect(result).toMatchObject({
      isbn: '9787508675534',
      title: '测试书名',
      source: 'barcode',
    });
  });
});
