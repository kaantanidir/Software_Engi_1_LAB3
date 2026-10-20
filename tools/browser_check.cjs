/** End-to-end feature and responsive-layout checks against an isolated QA server. */
const { chromium } = require('playwright');
const { spawn } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { setTimeout: delay } = require('node:timers/promises');
const root = path.resolve(__dirname, '..');
const errors = [];
const checks = [];
let page, browser, child;

/** Purpose: record a browser exception. Inputs: Error. Returns: void. */
function recordError(error) { errors.push(error.message); }
/** Purpose: assert and record a completed test. Inputs: label/condition. Returns: void or throws. */
function check(label, condition) { assert.ok(condition, label); checks.push(label); console.log('PASS', label); }
/** Purpose: wait for an exact visible text value. Inputs: selector/text. Returns: Promise<void>. */
async function textEquals(selector, value) { await page.locator(selector).filter({ hasText: value }).waitFor(); }
/** Purpose: authenticate the demo user through the UI. Inputs: optional technician flag. Returns: Promise<void>. */
async function signIn(technician = false) {
  await page.locator('#account-button').click();
  await page.locator(`[data-auth="${technician ? 'technician' : 'login'}"]`).click();
  await page.locator('#auth-submit').click();
  await textEquals('#account-name', technician ? 'Technician' : 'Alex');
  await page.waitForLoadState('networkidle');
}
/** Purpose: sign out through the account dialog. Inputs: current page session. Returns: Promise<void>. */
async function signOut() { await page.locator('#account-button').click(); await page.locator('#logout').click(); await textEquals('#account-name', 'Sign in'); }
/** Purpose: submit the current recipe for simulated purchase. Inputs: method/points/outcome. Returns: Promise<void>. */
async function purchase(method = 'contactless', points = 0, outcome = 'approve') {
  await page.locator('#checkout-button').click();
  await page.locator('#payment-form [name=method]').selectOption(method);
  if (points) await page.locator('#payment-form [name=points]').fill(String(points));
  await page.locator('#payment-form [name=outcome]').selectOption(outcome);
  await page.locator('#pay-button').click();
  await page.waitForLoadState('networkidle');
}
/** Purpose: change the network simulator through the technician UI. Inputs: online boolean. Returns: Promise<void>. */
async function network(online) {
  await page.locator('[data-view=maintenance]').click();
  await page.locator('#context-form [name=network]').selectOption(String(online));
  await page.locator('#context-form button[type=submit]').click();
  await textEquals('#connection', online ? 'Machine online' : 'Offline');
}
/** Purpose: inspect layout/assets in browser context. Inputs: DOM. Returns: dimension/asset checks. */
function inspectLayout() {
  const images = [...document.querySelectorAll('#drink-grid img')];
  let loadedImages = 0;
  for (const image of images) if (image.complete && image.naturalWidth > 0) loadedImages++;
  return { width: innerWidth, scrollWidth: document.documentElement.scrollWidth, loadedImages, images: images.length };
}
/** Purpose: compare durations numerically. Inputs: two numbers. Returns: numeric sort order. */
function compareNumbers(a, b) { return a - b; }
/** Purpose: execute the full QA flow with cleanup. Inputs: environment PYTHON/CHROME_PATH. Returns: Promise<void>. */
async function main() {
  fs.mkdirSync(path.join(root, 'tmp'), { recursive: true }); fs.mkdirSync(path.join(root, 'evidence'), { recursive: true });
  const temp = fs.mkdtempSync(path.join(root, 'tmp', 'browser-'));
  child = spawn(process.env.PYTHON || 'python', ['app.py', '--port', '8766', '--database', path.join(temp, 'qa.db')], { cwd: root, windowsHide: true, stdio: 'pipe' });
  let serverOutput = ''; child.stdout.on('data', captureOutput); child.stderr.on('data', captureOutput);
  /** Purpose: retain server diagnostics. Inputs: output buffer. Returns: void. */
  function captureOutput(buffer) { serverOutput += buffer.toString(); }
  try {
    for (let i = 0; i < 60 && !serverOutput.includes('ready at'); i++) { if (child.exitCode !== null) throw new Error(serverOutput); await delay(100); }
    assert.ok(serverOutput.includes('ready at'), 'Isolated QA server started');
    browser = await chromium.launch({ headless: true, ...(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {}) });
    page = await browser.newPage({ baseURL: 'http://127.0.0.1:8766', viewport: { width: 1440, height: 1000 } }); page.on('pageerror', recordError);
    await page.goto('http://127.0.0.1:8766'); await page.waitForLoadState('networkidle');
    check('F02: six menu drinks load', await page.locator('.drink-card').count() === 6);
    await page.locator('[data-category=Chocolate]').click(); check('F02: category filter', await page.locator('.drink-card').count() === 2);
    await page.locator('[data-category=All]').click(); await signIn();
    check('F01: customer credential login', (await page.locator('#account-name').textContent()) === 'Alex');
    await page.locator('[data-drink=latte]').click();
    await page.locator('#customize-form [name=milk]').selectOption('oat');
    await page.locator('#customize-form input[value=strong]').check();
    await page.locator('#customize-form [name=temperature]').fill('75');
    await page.locator('#customize-form [name=syrup]').fill('2');
    await page.locator('#customize-form [name=extra]').fill('1');
    await page.waitForLoadState('networkidle');
    await textEquals('#quote-price', '51');
    check('F03: live quote updates', (await page.locator('#quote-price').textContent()).includes('51'));
    await page.locator('#save-defaults').click(); await page.waitForLoadState('networkidle');
    await page.locator('#save-recipe').click(); await page.locator('#recipe-name').fill('Morning oat'); await page.locator('#recipe-form button[type=submit]').click();
    await page.waitForLoadState('networkidle'); await page.locator('[data-view=recipes]').click(); await page.getByRole('heading', { name: 'Morning oat' }).waitFor();
    await page.locator('[data-rename]').click(); await page.locator('#recipe-name').fill('Morning Focus'); await page.locator('#recipe-form button[type=submit]').click();
    await page.getByRole('heading', { name: 'Morning Focus' }).waitFor();
    check('F04: named recipe create/rename', true);
    await page.locator('[data-load-recipe]').click(); await page.waitForLoadState('networkidle');
    await page.screenshot({ path: path.join(root, 'evidence', 'desktop.png'), fullPage: true });
    await purchase('contactless', 100); await page.locator('#receipt-dialog').waitFor();
    check('F07/F08: checkout with loyalty discount', (await page.locator('#receipt-content').textContent()).includes('10'));
    await page.locator('#receipt-content img').waitFor();
    const svg = await page.request.get((await page.locator('#receipt-content img').getAttribute('src')));
    check('F09: actual QR SVG generated', svg.ok() && (await svg.text()).includes('<svg'));
    await page.locator('#email-receipt').click(); await textEquals('#receipt-message', 'local email simulator outbox');
    await page.screenshot({ path: path.join(root, 'evidence', 'receipt.png'), fullPage: true });
    await page.locator('#receipt-dialog .close-dialog').click();
    await purchase('contactless', 0, 'decline'); await textEquals('#payment-error', 'declined');
    check('F07: declined payment reported', true); await page.locator('#checkout-dialog .close-dialog').click();
    await page.locator('[data-view=history]').click(); check('F07: one completed history entry', await page.locator('#history-list .list-item').count() === 1);
    await signOut(); await signIn(true); await page.locator('[data-view=maintenance]').click();
    check('F10: seven ingredient counters', await page.locator('[data-refill]').count() === 7);
    await page.locator('#stock-oat').fill('99'); await page.locator('[data-stock=oat]').click(); await page.waitForLoadState('networkidle');
    await page.locator('[data-view=menu]').click();
    await textEquals('#availability', 'Oat milk unavailable');
    check('F05: depleted customized ingredient blocks checkout', await page.locator('#checkout-button').isDisabled());
    await page.locator('[data-view=maintenance]').click(); await page.locator('[data-refill=oat]').click(); await page.waitForLoadState('networkidle');
    await page.locator('#bin-grounds').fill('100'); await page.locator('[data-waste=grounds]').click(); await page.waitForLoadState('networkidle');
    await page.locator('[data-view=menu]').click(); await textEquals('#availability', 'Grounds bin full'); check('F10: full bin halts checkout', await page.locator('#checkout-button').isDisabled());
    await page.locator('[data-view=maintenance]').click(); await page.locator('[data-empty=grounds]').click(); await page.waitForLoadState('networkidle');
    await page.locator('[data-fault=GRINDER_JAM]').click(); await page.waitForLoadState('networkidle');
    await textEquals('#maintenance-content', 'GRINDER_JAM');
    check('F10: diagnostic fault logged', (await page.locator('#maintenance-content').textContent()).includes('GRINDER_JAM'));
    await page.screenshot({ path: path.join(root, 'evidence', 'maintenance.png'), fullPage: true });
    await page.locator('[data-fault=""]').click(); await textEquals('#maintenance-content', 'No active fault');
    await network(false); await signOut(); await signIn(); await page.locator('[data-view=menu]').click();
    await page.locator('#recommend-toggle').check();
    check('F06: offline recommendations use local context', (await page.locator('#recommend-context').textContent()).includes('weather unavailable'));
    await purchase('prepaid'); await page.locator('#receipt-dialog').waitFor(); await page.locator('#receipt-dialog .close-dialog').click();
    check('F07: prepaid completes offline', true);
    await purchase('apple_pay', 100); await page.locator('#history-view').waitFor(); await page.locator('[data-pending]').waitFor();
    check('F07: unsupported offline wallet is pending', await page.locator('#pending-list .list-item').count() === 1);
    await signOut(); await signIn(true); await network(true); await signOut(); await signIn(); await page.locator('[data-view=history]').click();
    await page.locator('[data-pending]').click(); await page.locator('#pay-button').click(); await page.locator('#receipt-dialog').waitFor(); await page.locator('#receipt-dialog .close-dialog').click();
    await page.locator('[data-view=history]').click(); await page.waitForLoadState('networkidle');
    await page.locator('#history-list .list-item').nth(2).waitFor();
    check('F07: pending payment reconciles on retry', await page.locator('#history-list .list-item').count() === 3);
    const forbidden = await page.request.post('/api/admin/refill', { data: { ingredient: 'oat' } }); check('HTTP authorization rejects customer admin request', forbidden.status() === 403);
    const durations = [], quoteDurations = [];
    for (let i = 0; i < 100; i++) { const start = performance.now(); const r = await page.request.get('/api/state'); assert.ok(r.ok()); durations.push(performance.now() - start); }
    durations.sort(compareNumbers); const p95 = durations[94]; check('Proposed local-response target: p95 below 2 seconds', p95 < 2000);
    for (let i = 0; i < 100; i++) { const start = performance.now(); const r = await page.request.post('/api/quote', { data: { drink: 'latte' } }); assert.ok(r.ok()); quoteDurations.push(performance.now() - start); }
    quoteDurations.sort(compareNumbers); const quoteP95 = quoteDurations[94]; check('Proposed quote-response target: p95 below 2 seconds', quoteP95 < 2000);
    await page.locator('[data-view=menu]').click(); await page.setViewportSize({ width: 390, height: 844 }); await page.waitForLoadState('networkidle');
    const mobile = await page.evaluate(inspectLayout); check('Mobile root has no horizontal overflow', mobile.scrollWidth <= mobile.width); check('Menu photograph assets loaded', mobile.images > 0 && mobile.loadedImages === mobile.images);
    await page.screenshot({ path: path.join(root, 'evidence', 'mobile.png'), fullPage: true });
    check('No uncaught browser errors', errors.length === 0);
    fs.writeFileSync(path.join(root, 'evidence', 'browser-results.json'), JSON.stringify({ recordedAt: new Date().toISOString(), checks, errors, responseSample: { count: 100, p95ms: p95 }, quoteSample: { count: 100, p95ms: quoteP95 }, mobile, browser: browser.version(), node: process.version, simulatedIntegrations: true }, null, 2));
  } finally { if (browser) await browser.close(); if (child && child.exitCode === null) child.kill(); }
}
/** Purpose: surface failed QA without orphaning the browser/server. Inputs: Error. Returns: void. */
function failed(error) { console.error(error); process.exitCode = 1; }
main().catch(failed);
