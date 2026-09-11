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
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  page.setDefaultTimeout(20000);

  // 1) Home + search
  await page.goto(BASE + "/", { waitUntil: "networkidle" });
  await page.getByRole("heading", { name: "检索开放学术源" }).waitFor();
  ok("home loaded");

  const searchBox = page.getByPlaceholder("输入主题关键词，例如：large language model");
  await searchBox.waitFor();
  await searchBox.fill("graph neural network");
  await page.getByRole("button", { name: "搜索" }).click();
  await page.getByText(/找到\s*\d+\s*条结果/).waitFor({ timeout: 60000 });
  const resultText = await page.getByText(/找到\s*\d+\s*条结果/).innerText();
  ok("search returned: " + resultText);

  // 2) Topics page + create modal typing
  await page.getByRole("link", { name: "研究主题" }).click();
  await page.getByRole("heading", { name: "研究主题" }).waitFor();
  await page.getByRole("button", { name: "新建主题" }).click();

  const nameInput = page.getByLabel("主题名称");
  await nameInput.waitFor();
  await nameInput.click();
  await nameInput.pressSequentially("UI Verify Topic", { delay: 20 });
  const nameVal = await nameInput.inputValue();
  if (nameVal !== "UI Verify Topic") {
    fail(`name input not accepting text, got: "${nameVal}"`);
  } else {
    ok("topic name input accepts typing");
  }

  const queryInput = page.getByLabel("检索词");
  await queryInput.click();
  await queryInput.pressSequentially("transformer attention", { delay: 20 });
  const qVal = await queryInput.inputValue();
  if (!qVal.includes("transformer")) {
    fail(`query input not accepting text, got: "${qVal}"`);
  } else {
    ok("topic query input accepts typing");
  }

  await page.getByRole("button", { name: "创建并抓取" }).click();
  await page.getByText("主题已创建", { exact: false }).waitFor({ timeout: 15000 }).catch(() => {});
  // list should include the new topic
  await page.getByText("UI Verify Topic").first().waitFor({ timeout: 15000 });
  ok("topic created and visible in list");

  // 3) Health via page fetch
  const health = await page.evaluate(async (api) => {
    const r = await fetch(api + "/api/health");
    return r.json();
  }, API);
  if (health?.status !== "ok") fail("health not ok: " + JSON.stringify(health));
  else ok("api health ok");

  await page.screenshot({ path: "scripts/ui-verify-topics.png", fullPage: true });
  ok("screenshot saved scripts/ui-verify-topics.png");

  await browser.close();
  if (process.exitCode) {
    console.error("UI VERIFY FAILED");
  } else {
    console.log("UI VERIFY PASSED");
  }
}

main().catch((e) => {
  console.error("UI VERIFY ERROR", e);
  process.exit(1);
});
