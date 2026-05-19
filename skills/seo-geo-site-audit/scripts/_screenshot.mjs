// One-off screenshot helper for visual review of the audit-report HTML.
// Usage: node _screenshot.mjs <input.html> <output.png> [width] [height] [selector|"clip:x,y,w,h"]
import { launch } from 'chrome-launcher';
import puppeteer from 'puppeteer-core';
import fs from 'node:fs/promises';
import path from 'node:path';

const [, , inputHtml, outputPng, widthArg, heightArg, modeArg] = process.argv;
if (!inputHtml || !outputPng) {
  console.error('Usage: node _screenshot.mjs <input.html> <output.png> [width] [height] [selector|"clip:x,y,w,h"]');
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
  if (modeArg && modeArg.startsWith('clip:')) {
    const [x, y, w, h] = modeArg.slice(5).split(',').map(Number);
    buf = await page.screenshot({ clip: { x, y, width: w, height: h }, type: 'png' });
  } else if (modeArg) {
    const el = await page.$(modeArg);
    if (!el) throw new Error(`Selector not found: ${modeArg}`);
    buf = await el.screenshot({ type: 'png' });
  } else {
    buf = await page.screenshot({ fullPage: true, type: 'png' });
  }
  await fs.writeFile(outputPng, buf);
  console.log(`wrote ${outputPng} (${buf.length} bytes @ ${width}x${height} mode=${modeArg || 'fullPage'})`);
  await browser.disconnect();
} finally {
  try { await chrome.kill(); } catch { /* ignore */ }
}
