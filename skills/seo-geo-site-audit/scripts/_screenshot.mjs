// One-off screenshot helper for visual review of the audit-report HTML.
// Usage: node _screenshot.mjs <input.html> <output.png> [width] [height] [selector]
//   When [selector] is supplied, only that element is captured.
import { launch } from 'chrome-launcher';
import puppeteer from 'puppeteer-core';
import fs from 'node:fs/promises';
import path from 'node:path';

const [, , inputHtml, outputPng, widthArg, heightArg, selectorArg] = process.argv;
if (!inputHtml || !outputPng) {
  console.error('Usage: node _screenshot.mjs <input.html> <output.png> [width] [height] [selector]');
  process.exit(2);
}
const width = parseInt(widthArg || '1280', 10);
const height = parseInt(heightArg || '900', 10);

const fileUrl = 'file://' + path.resolve(inputHtml);
const chrome = await launch({
  chromeFlags: ['--headless=new', '--disable-gpu', '--disable-dev-shm-usage', `--window-size=${width},${height}`],
});
try {
  const wsRes = await fetch(`http://127.0.0.1:${chrome.port}/json/version`);
  const { webSocketDebuggerUrl } = await wsRes.json();
  const browser = await puppeteer.connect({ browserWSEndpoint: webSocketDebuggerUrl });
  const page = (await browser.pages())[0] || (await browser.newPage());
  await page.setViewport({ width, height, deviceScaleFactor: 1 });
  await page.goto(fileUrl, { waitUntil: 'networkidle0', timeout: 30000 });

  let buf;
  if (selectorArg) {
    const el = await page.$(selectorArg);
    if (!el) throw new Error(`Selector not found: ${selectorArg}`);
    buf = await el.screenshot({ type: 'png' });
  } else {
    buf = await page.screenshot({ fullPage: true, type: 'png' });
  }
  await fs.writeFile(outputPng, buf);
  console.log(`wrote ${outputPng} (${buf.length} bytes @ ${width}x${height}${selectorArg ? ` selector=${selectorArg}` : ' fullPage'})`);
  await browser.disconnect();
} finally {
  try { await chrome.kill(); } catch { /* ignore */ }
}
