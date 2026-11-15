#!/usr/bin/env node
/**
 * Chromium smoke coverage for source-generated GitHub Pages.
 * Source of truth: scripts/build_site.py + website/app.js.
 * Device viewports are browser emulations, NOT physical Safari/Android sign-off.
 */
import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
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
