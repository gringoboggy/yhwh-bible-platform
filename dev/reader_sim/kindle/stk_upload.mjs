#!/usr/bin/env node
/**
 * Agent-owned Send-to-Kindle upload (Mac lane).
 * Uses the persistent Amazon session in ~/.yhwh-browser-profile (see TOOLCHAIN.md).
 *
 * Usage:
 *   node dev/reader_sim/kindle/stk_upload.mjs <path/to.epub>
 */
import { createRequire } from "node:module";
import { existsSync } from "node:fs";
import { resolve } from "node:path";

const require = createRequire(import.meta.url);
const pwRoot =
  process.env.PLAYWRIGHT_MODULE_ROOT ||
  "/Users/gringoboggy/.local/opt/node-v24.16.0-darwin-x64/lib/node_modules/@playwright/mcp/node_modules/playwright";
const { chromium } = require(pwRoot);

const epub = resolve(process.argv[2] || "");
if (!epub || !existsSync(epub)) {
  console.error("usage: stk_upload.mjs <epub>");
  process.exit(2);
}

const profile =
  process.env.YHWH_BROWSER_PROFILE ||
  (process.env.YHWH_CHROME_PROFILE === "default"
    ? `${process.env.HOME}/Library/Application Support/Google/Chrome`
    : `${process.env.HOME}/.yhwh-browser-profile`);

const context = await chromium.launchPersistentContext(profile, {
  channel: "chrome",
  headless: false,
  args: ["--disable-blink-features=AutomationControlled"],
});

const page = context.pages()[0] ?? (await context.newPage());
const stkUrl =
  process.env.YHWH_STK_URL ||
  (process.env.YHWH_AMAZON_TLD === "com"
    ? "https://www.amazon.com/sendtokindle"
    : "https://www.amazon.ca/sendtokindle");
await page.goto(stkUrl, {
  waitUntil: "domcontentloaded",
  timeout: 120_000,
});

// Amazon STK: file input is often hidden behind "Upload" / drag-drop.
const fileInput = page.locator('input[type="file"]').first();
await fileInput.waitFor({ state: "attached", timeout: 60_000 });
await fileInput.setInputFiles(epub);

// Submit if a send button appears (wording varies by locale/skin).
const send = page.getByRole("button", { name: /send|upload|submit/i }).first();
if (await send.isVisible({ timeout: 15_000 }).catch(() => false)) {
  await send.click();
}

await page.waitForTimeout(5_000);
console.log(`STK upload staged: ${epub}`);
console.log("Run stk_poll_watch.sh in background to detect Kindle library arrival.");
await context.close();