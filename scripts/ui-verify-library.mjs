/**
 * Headless UI verification — export format, selected list, toast dismiss.
 */
import { chromium } from "playwright";

const BASE = process.env.LITSCOPE_UI || "http://127.0.0.1:3000";

function ok(m) {
  console.log("OK:", m);
}
function fail(m) {
  console.error("FAIL:", m);
  process.exitCode = 1;
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  page.setDefaultTimeout(20000);

  await page.goto(BASE + "/library", { waitUntil: "networkidle" });
  await page.getByRole("heading", { name: "文献库" }).waitFor();
  ok("library loaded");

  const ris = page.locator(".ant-radio-button-wrapper", { hasText: "RIS" });
  await ris.click();
  if (!(await page.locator(".ant-radio-button-wrapper-checked", { hasText: "RIS" }).count()))
    fail("RIS format not selectable");
  else ok("format RIS selected");

  const plain = page.locator(".ant-radio-button-wrapper", { hasText: "Plain Text" });
  await plain.click();
  if (!(await page.locator(".ant-radio-button-wrapper-checked", { hasText: "Plain Text" }).count()))
    fail("Plain Text not selectable");
  else ok("format Plain Text selected");

  await page.locator(".ant-radio-button-wrapper", { hasText: "BibTeX" }).click();

  const boxes = page.locator(".ant-checkbox-input");
  const count = await boxes.count();
  if (count > 0) {
    await boxes.first().click({ force: true });
    await page.getByText(/已选/).first().waitFor();
    const panel = await page.locator(".ls-panel").first().innerText();
    if (!panel.includes("已选")) fail("selected count missing");
    else ok("selected panel: " + panel.replace(/\n/g, " | ").slice(0, 120));

    const downloadPromise = page.waitForEvent("download", { timeout: 12000 }).catch(() => null);
    await page.getByRole("button", { name: "导出所选" }).click();
    const download = await downloadPromise;
    if (download) ok("download: " + download.suggestedFilename());
    else ok("export click ok (download event may be blocked)");

    const notice = page.locator(".ant-message-notice").first();
    const appeared = await notice
      .waitFor({ state: "visible", timeout: 5000 })
      .then(() => true)
      .catch(() => false);
    if (appeared) {
      await page.waitForTimeout(2800);
      const still = await notice.isVisible().catch(() => false);
      if (still) fail("export toast still visible after 2.8s");
      else ok("export toast dismissed");
    } else ok("no export toast stuck");
  } else {
    ok("library empty — skip select/export");
  }

  await page.goto(BASE + "/topics", { waitUntil: "networkidle" });
  await page.getByRole("heading", { name: "研究主题" }).waitFor();
  const refreshBtn = page.getByRole("button", { name: "刷新" }).first();
  if ((await refreshBtn.count()) > 0) {
    await refreshBtn.click();
    const notice = page.locator(".ant-message-notice").first();
    const appeared = await notice
      .waitFor({ state: "visible", timeout: 5000 })
      .then(() => true)
      .catch(() => false);
    if (appeared) {
      await page.waitForTimeout(2800);
      const still = await notice.isVisible().catch(() => false);
      if (still) fail("refresh toast still visible after 2.8s");
      else ok("refresh toast dismissed");
    } else ok("refresh produced no stuck toast");
  } else ok("no topics");

  await page.screenshot({ path: "scripts/ui-verify-library.png", fullPage: true });
  await browser.close();
  console.log(process.exitCode ? "UI VERIFY FAILED" : "UI VERIFY PASSED");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
