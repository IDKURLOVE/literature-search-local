/**
 * Headless UI verification for LitScope Local.
 * Run: node scripts/ui-verify.mjs
 */
import { chromium } from "playwright";

const BASE = process.env.LITSCOPE_UI || "http://127.0.0.1:3000";
const API = process.env.LITSCOPE_API || "http://127.0.0.1:8000";

function fail(msg) {
  console.error("FAIL:", msg);
  process.exitCode = 1;
}

function ok(msg) {
  console.log("OK:", msg);
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  page.setDefaultTimeout(20000);

  await page.goto(BASE + "/", { waitUntil: "networkidle" });
  await page.getByRole("heading", { name: "检索开放学术源" }).waitFor();
  ok("home loaded");

  // Source checkboxes must toggle
  const s2 = page.getByLabel("Semantic Scholar");
  const before = await s2.isChecked();
  await s2.click();
  const after = await s2.isChecked();
  if (before === after) fail(`Semantic Scholar checkbox did not toggle (${before})`);
  else ok(`source checkbox toggled: ${before} -> ${after}`);
  await s2.click(); // restore

  const searchBox = page.getByPlaceholder("输入主题关键词，例如：large language model");
  await searchBox.fill("graph neural network");
  await page.getByRole("button", { name: "搜索" }).click();
  await page.getByText(/找到\s*\d+\s*条结果/).waitFor({ timeout: 60000 });
  ok("search: " + (await page.getByText(/找到\s*\d+\s*条结果/).innerText()));

  // Topics: open form must be instant
  await page.getByRole("link", { name: "研究主题" }).click();
  await page.getByRole("heading", { name: "研究主题" }).waitFor();

  const t0 = Date.now();
  await page.getByRole("button", { name: "新建主题" }).click();
  await page.locator("#topic-name-input").waitFor({ state: "visible", timeout: 3000 });
  const openMs = Date.now() - t0;
  if (openMs > 1500) fail(`create form open too slow: ${openMs}ms`);
  else ok(`create form opened in ${openMs}ms`);

  await page.locator("#topic-name-input").fill("UI Verify Topic 2");
  await page.getByLabel("检索词").fill("transformer attention");
  // toggle a source checkbox in form
  const pubmed = page.locator(".ant-checkbox-wrapper", { hasText: "PubMed" }).first();
  await pubmed.click();
  await page.getByRole("button", { name: "创建并抓取" }).click();
  await page.getByText("UI Verify Topic 2").first().waitFor({ timeout: 15000 });
  ok("topic created");

  const health = await page.evaluate(async (api) => (await fetch(api + "/api/health")).json(), API);
  if (health?.status !== "ok") fail("health " + JSON.stringify(health));
  else ok("health ok");

  await page.screenshot({ path: "scripts/ui-verify-topics.png", fullPage: true });
  await browser.close();
  console.log(process.exitCode ? "UI VERIFY FAILED" : "UI VERIFY PASSED");
}

main().catch((e) => {
  console.error("UI VERIFY ERROR", e);
  process.exit(1);
});
