/**
 * BarcodeDetector polyfill 加载逻辑。
 * 优先浏览器原生，Firefox/iOS Safari 自动降级到 ZXing WASM（本地化资源）。
 */

import { setZXingModuleOverrides } from 'barcode-detector';

const LOCAL_WASM_PREFIX = '/zxing/';
const TARGET_FORMATS = ['ean_13', 'ean_8', 'upc_a', 'upc_e', 'code_128'] as const;

let polyfillInitialized = false;

export async function loadBarcodeDetector(): Promise<typeof BarcodeDetector | null> {
  if (typeof window === 'undefined' || typeof globalThis === 'undefined') return null;

  const Ctor = globalThis.BarcodeDetector;
  if (typeof Ctor === 'function') {
    try {
      const supported: readonly string[] = await Ctor.getSupportedFormats();
      const formats = TARGET_FORMATS.filter((f) => supported.includes(f));
      if (formats.length > 0) return Ctor;
    } catch {
      // 忽略，降级到 polyfill
    }
  }

  if (!polyfillInitialized) {
    try {
      setZXingModuleOverrides({
        locateFile: (filename: string) => `${LOCAL_WASM_PREFIX}${filename}`,
      });
      await import('barcode-detector/polyfill');
      polyfillInitialized = true;
    } catch (e) {
      console.error('[barcode] polyfill 加载失败：', e);
      return null;
    }
  }

  return globalThis.BarcodeDetector ?? null;
}
