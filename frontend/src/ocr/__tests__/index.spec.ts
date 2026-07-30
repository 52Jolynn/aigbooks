import { describe, expect, it } from 'vitest';
import { recognizeText } from '../index';

describe('OCR', () => {
  it('returns empty result on failure', async () => {
    // 即使没有 tesseract worker，失败时应静默回退
    const blob = new Blob(['x'], { type: 'image/png' });
    const result = await recognizeText(blob);
    expect(result).toHaveProperty('raw');
    expect(result.isbn).toBeUndefined();
  });
});
