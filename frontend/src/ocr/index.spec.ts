import { describe, expect, it } from 'vitest';
import { __test } from '@/ocr';

const heartFlowText = `心流：最优体验心理学
著者：[美]米哈里·契克森米哈赖
译者：张定编
出版发行：中信出版集团股份有限公司
（北京市朝阳区惠新东街甲4号富盛大厦2 座邮编100029）
承印者：北京诚信伟业印刷有限公司
开本：880mm×1230mm1/32
印张：12.25
版次：2017年12月第1版
字数：237千字
印次：2022 年 10 月第52次印刷
京权图字：01-2011-1722
书号：ISBN
978-7-5086-7553-4
定价：49.00元`;

describe('extractBookInfo', () => {
  it('按行提取用户样本的题名、著者、ISBN 和摘要', () => {
    const result = __test.extractBookInfo(heartFlowText);

    expect(result).toMatchObject({
      title: '心流：最优体验心理学',
      author: '[美]米哈里·契克森米哈赖',
      isbn: '9787508675534',
    });
    expect(result.summary).toContain('译者：张定编');
    expect(result.summary).toContain('出版发行：中信出版集团股份有限公司');
    expect(result.summary).not.toContain('心流：最优体验心理学');
    expect(result.summary).not.toContain('著者：[美]米哈里·契克森米哈赖');
    expect(result.summary).not.toContain('978-7-5086-7553-4');
  });

  it('无作者标签时提取国别姓名格式', () => {
    const result = __test.extractBookInfo(`测试书名\n[美]约翰·史密斯\n出版：测试出版社`);

    expect(result.author).toBe('[美]约翰·史密斯');
  });

  it('无作者和国别姓名时回退译者', () => {
    const result = __test.extractBookInfo(`测试书名\n译者：张三\nISBN 978-7-5086-7553-4`);

    expect(result.author).toBe('张三');
  });
});

describe('formatIsbn13', () => {
  it('按指定分组格式化 ISBN-13', () => {
    expect(__test.formatIsbn13('9787508675534')).toBe('978-7-5086-7553-4');
  });
});
