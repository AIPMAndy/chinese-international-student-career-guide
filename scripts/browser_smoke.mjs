#!/usr/bin/env node
/**
 * Chromium smoke coverage for source-generated GitHub Pages.
 * Source of truth: scripts/build_site.py + website/app.js.
 * Device viewports are browser emulations, NOT physical Safari/Android sign-off.
 */
import assert from 'node:assert/strict';
import { mkdir, readFile } from 'node:fs/promises';
import { chromium } from 'playwright';

const base = (process.env.SITE_URL || 'http://127.0.0.1:8765/').replace(/\/?$/, '/');
await mkdir('qa/browser', { recursive: true });
const browser = await chromium.launch({ headless: true });
const summary = [];
try {
  for (const width of [360, 390, 1280]) {
    const context = await browser.newContext({
      viewport: { width, height: 820 },
      deviceScaleFactor: 1,
      locale: 'zh-CN',
    });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    const response = await page.goto(base, { waitUntil: 'networkidle' });
    assert.equal(response.status(), 200, 'Homepage must respond HTTP 200');
    assert.equal(await page.locator('h1').count(), 1, 'Exactly one H1');
    assert.equal(await page.locator('[data-copy-wechat]').count() > 0, true);
    assert.equal(await page.locator('[data-region-reset]').count(), 1);

    const cards = page.locator('[data-region]');
    const total = await cards.count();
    assert.ok(total > 5, 'Country navigator should have real entries');
    assert.equal(await page.locator('[data-region]:visible').count(), total);

    await page.locator('[data-region-query]').fill('test-no-matching-region-000');
    assert.equal(await page.locator('[data-region]:visible').count(), 0);
    assert.equal(await page.locator('[data-region-empty]').isVisible(), true);

    await page.locator('[data-region-reset]').click();
    assert.equal(await page.locator('[data-region-query]').inputValue(), '');
    assert.equal(await page.locator('[data-region]:visible').count(), total);
    assert.equal(await page.locator('[data-region-empty]').isHidden(), true);

    await page.locator('[data-region-group]').selectOption({ label: '欧洲' });
    const european = await page.locator('[data-region]:visible').count();
    assert.ok(european > 0 && european < total, 'Regional filter should narrow results');
    await page.locator('[data-region-reset]').click();
    assert.equal(await page.locator('[data-region-group]').inputValue(), '');
    assert.equal(await page.locator('[data-region]:visible').count(), total);

    if (width <= 760) {
      const menu = page.locator('[data-menu]');
      assert.equal(await menu.isVisible(), true, 'Mobile navigation must be visible');
      await menu.click();
      assert.equal(await menu.getAttribute('aria-expanded'), 'true');
      await page.locator('#main-nav a').first().click();
      assert.equal(await menu.getAttribute('aria-expanded'), 'false');
    }

    await page.evaluate(() => {
      Object.defineProperty(navigator, 'clipboard', {
        configurable: true,
        value: { writeText: async text => { window.__smokeCopied = text; } },
      });
    });
    await page.locator('[data-copy-wechat]').first().click();
    assert.equal(await page.evaluate(() => window.__smokeCopied), 'AIPMAndy');
    assert.match(await page.locator('[data-copy-status]').textContent(), /已复制微信号/);

    await page.evaluate(() => {
      Object.defineProperty(navigator, 'clipboard', {
        configurable: true,
        value: { writeText: async () => { throw new Error('Not permitted'); } },
      });
    });
    await page.locator('[data-copy-wechat]').first().click();
    assert.match(await page.locator('[data-copy-status]').textContent(), /长按选择并复制/);

    const dimensions = await page.evaluate(() => ({
      viewport: window.innerWidth,
      html: document.documentElement.scrollWidth,
      body: document.body.scrollWidth,
    }));
    assert.ok(Math.max(dimensions.html, dimensions.body) <= dimensions.viewport + 1,
      'Horizontal overflow at ' + width + 'px: ' + JSON.stringify(dimensions));
    assert.deepEqual(errors, [], 'No runtime page errors');
    await page.screenshot({ path: 'qa/browser/home-' + width + '.png', fullPage: true });
    summary.push({ width, regionCards: total, european, copyAndFallback: 'passed', overflow: false });
    await context.close();
  }

  // Source evidence search, partial-state review, export bytes and GEO citation.
  const evidence = await browser.newContext({ acceptDownloads: true, viewport: { width: 390, height: 820 } });
  const sourcePage = await evidence.newPage();
  const sourceResponse = await sourcePage.goto(base + 'sources.html', { waitUntil: 'networkidle' });
  assert.equal(sourceResponse.status(), 200);
  const sourceTotal = await sourcePage.locator('[data-source]').count();
  assert.ok(sourceTotal >= 80, 'Source ledger must retain complete evidence records');
  assert.equal(await sourcePage.locator('[data-source]:visible').count(), sourceTotal);
  assert.match(await sourcePage.locator('[data-source-count]').textContent(), /建议复核/);
  assert.equal(await sourcePage.locator('script[type="application/ld+json"]').count(), 1);
  const sourceSchema = JSON.parse(await sourcePage.locator('script[type="application/ld+json"]').textContent());
  assert.ok(sourceSchema.citation.length >= 80, 'GEO citations must match visible sources');
  await sourcePage.locator('[data-source-filter]').selectOption('partial');
  const partial = await sourcePage.locator('[data-source]:visible').count();
  assert.ok(partial > 0 && partial < sourceTotal, 'Incomplete evidence must be filterable');
  const [download] = await Promise.all([
    sourcePage.waitForEvent('download'),
    sourcePage.locator('[data-source-export]').click(),
  ]);
  assert.equal(download.suggestedFilename(), 'career-source-review-list.txt');
  const txt = await readFile(await download.path(), 'utf-8');
  assert.match(txt, /历史核验日期/);
  assert.match(txt, /https:\/\/metaver.vip\/services/);
  assert.match(txt, /https:\/\/www.a6no1.cn\//);
  assert.match(txt, /官方原文/);
  await sourcePage.locator('[data-source-query]').fill('no-matching-evidence-000');
  assert.equal(await sourcePage.locator('[data-source]:visible').count(), 0);
  assert.equal(await sourcePage.locator('[data-source-empty]').isVisible(), true);
  await sourcePage.locator('[data-source-reset]').click();
  assert.equal(await sourcePage.locator('[data-source-query]').inputValue(), '');
  assert.equal(await sourcePage.locator('[data-source]:visible').count(), sourceTotal);
  assert.equal(await sourcePage.locator('[data-source-empty]').isHidden(), true);
  const sourceOverflow = await sourcePage.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1);
  assert.equal(sourceOverflow, false, 'Source dashboard must not overflow on mobile');
  await sourcePage.screenshot({ path: 'qa/browser/sources-390.png', fullPage: true });
  await evidence.close();

  const r = await browser.newPage();
  const file = await r.request.get(base + 'downloads/chinese-international-student-career-guide.pdf');
  assert.equal(file.status(), 200, 'Built PDF download must respond HTTP 200');
  const bytes = await file.body();
  assert.equal(bytes.subarray(0, 4).toString('utf-8'), '%PDF', 'Downloaded PDF signature');
  await r.close();
  console.log(JSON.stringify({ result: 'PASS', checks: summary, pdfBytes: bytes.length }, null, 2));
} finally {
  await browser.close();
}
