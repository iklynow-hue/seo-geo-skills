#!/usr/bin/env node
// Programmatic Lighthouse runner used by pagespeed_batch.py.
// Usage: node run_lighthouse.mjs --url <url> [--strategy mobile|desktop] [--out <path>]
// Outputs the Lighthouse JSON report (`lhr`) to --out when supplied, otherwise stdout.
import fs from 'node:fs/promises';
import process from 'node:process';

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i++) {
    const flag = argv[i];
    if (flag === '--url') out.url = argv[++i];
    else if (flag === '--strategy') out.strategy = argv[++i];
    else if (flag === '--out') out.out = argv[++i];
    else if (flag === '--timeout') out.timeout = Number(argv[++i]);
  }
  return out;
}

const args = parseArgs(process.argv.slice(2));
if (!args.url) {
  console.error('Usage: run_lighthouse.mjs --url <url> [--strategy mobile|desktop] [--out <path>]');
  process.exit(2);
}
const strategy = args.strategy === 'desktop' ? 'desktop' : 'mobile';

let lighthouse;
let chromeLauncher;
try {
  ({ default: lighthouse } = await import('lighthouse'));
  chromeLauncher = await import('chrome-launcher');
} catch (err) {
  console.error(
    'Missing Lighthouse dependencies. Install them from the scripts directory:\n' +
      '  cd "$(dirname "$0")" && npm install\n' +
      `Underlying error: ${err && err.message ? err.message : err}`,
  );
  process.exit(1);
}

const desktopThrottling = {
  rttMs: 40,
  throughputKbps: 10 * 1024,
  cpuSlowdownMultiplier: 1,
  requestLatencyMs: 0,
  downloadThroughputKbps: 0,
  uploadThroughputKbps: 0,
};

const mobileThrottling = {
  rttMs: 150,
  throughputKbps: 1.6 * 1024,
  cpuSlowdownMultiplier: 4,
  requestLatencyMs: 562.5,
  downloadThroughputKbps: 1474.56,
  uploadThroughputKbps: 675,
};

const desktopScreen = { mobile: false, width: 1350, height: 940, deviceScaleFactor: 1, disabled: false };
const mobileScreen = { mobile: true, width: 412, height: 823, deviceScaleFactor: 1.75, disabled: false };

const desktopUA =
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';
const mobileUA =
  'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36';

// Chrome sandbox stays ON by default. The renderer audits arbitrary user-supplied URLs,
// so a renderer RCE in a malicious page would otherwise chain straight into host execution.
// Set SEO_GEO_ALLOW_NO_SANDBOX=1 only for trusted CI / container / root environments
// where the OS-level sandbox is unavailable.
const allowNoSandbox = process.env.SEO_GEO_ALLOW_NO_SANDBOX === '1';
const chromeFlags = ['--headless=new', '--disable-gpu', '--disable-dev-shm-usage'];
if (allowNoSandbox) {
  chromeFlags.push('--no-sandbox');
  console.error('[run_lighthouse] SEO_GEO_ALLOW_NO_SANDBOX=1 — Chrome sandbox disabled.');
}
const chrome = await chromeLauncher.launch({ chromeFlags });

try {
  const flags = {
    port: chrome.port,
    output: 'json',
    logLevel: 'error',
    onlyCategories: ['performance', 'accessibility', 'best-practices', 'seo'],
    formFactor: strategy,
    screenEmulation: strategy === 'desktop' ? desktopScreen : mobileScreen,
    throttling: strategy === 'desktop' ? desktopThrottling : mobileThrottling,
    emulatedUserAgent: strategy === 'desktop' ? desktopUA : mobileUA,
  };

  const result = await lighthouse(args.url, flags);
  if (!result || !result.lhr) {
    console.error('Lighthouse returned no result.');
    process.exit(1);
  }
  const json = JSON.stringify(result.lhr);
  if (args.out) {
    await fs.writeFile(args.out, json, 'utf-8');
  } else {
    process.stdout.write(json);
  }
} catch (err) {
  console.error(`Lighthouse error: ${err && err.message ? err.message : err}`);
  process.exit(1);
} finally {
  try {
    await chrome.kill();
  } catch {
    /* ignore */
  }
}
