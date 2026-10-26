/** End-to-end feature and responsive-layout checks against an isolated QA server. */
const { chromium } = require('playwright');
const { spawn } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { setTimeout: delay } = require('node:timers/promises');
const { once } = require('node:events');
const root = path.resolve(__dirname, '..');
const errors = [];
const checks = [];
const assistantTurns = [];
let page, browser, child;

/** Purpose: record a browser exception. Inputs: Error. Returns: void. */
function recordError(error) { errors.push(error.message); }
/** Purpose: assert and record a completed test. Inputs: label/condition. Returns: void or throws. */
function check(label, condition) { assert.ok(condition, label); checks.push(label); console.log('PASS', label); }
/** Purpose: wait for an exact visible text value. Inputs: selector/text. Returns: Promise<void>. */
async function textEquals(selector, value) { await page.locator(selector).filter({ hasText: value }).waitFor(); }
/** Purpose: authenticate through visible controls. Inputs: technician flag or customer email/password/name. Returns: Promise<void>. */
async function signIn(technician = false, email = null, password = null, name = 'Alex') {
  await page.locator('#account-button').click();
  await page.locator(`[data-auth="${technician ? 'technician' : 'login'}"]`).click();
  if (email) { await page.locator('#auth-form [name=email]').fill(email); await page.locator('#auth-form [name=password]').fill(password); }
  else await page.locator('#fill-demo').click();
  await page.locator('#auth-submit').click();
  await textEquals('#account-name', technician ? 'Technician' : name);
  await page.waitForLoadState('networkidle');
}
/** Purpose: sign out through the account dialog. Inputs: current page session. Returns: Promise<void>. */
async function signOut() { await page.locator('#account-button').click(); await page.locator('#logout').click(); await textEquals('#account-name', 'Sign in'); }
/** Purpose: submit the current recipe without controlling authorization. Inputs: method/points. Returns: Promise<void>. */
async function purchase(method = 'contactless', points = 0) {
  await page.locator('#recipe-dialog').waitFor({ state: 'hidden' });
  await page.locator('#checkout-button:not([disabled])').waitFor();
  await page.locator('#checkout-button').click();
  await page.locator('#payment-form [name=method]').selectOption(method);
  if (points) await page.locator('#payment-form [name=points]').fill(String(points));
  await page.locator('#pay-button').click();
  await page.waitForLoadState('networkidle');
}
/** Purpose: change the network simulator through the technician UI. Inputs: online boolean. Returns: Promise<void>. */
async function network(online) {
  await page.locator('[data-view=maintenance]').click();
  await page.getByRole('tab', { name: 'Test scenarios' }).click();
  await page.locator('#context-form [name=network]').selectOption(String(online));
  await page.locator('#context-form button[type=submit]').click();
  await textEquals('#connection', online ? 'Machine online' : 'Offline');
}
/** Purpose: apply service context controls through the technician UI. Inputs: partial context object. Returns: Promise<void>. */
async function setContext(fields) {
  await page.locator('[data-view=maintenance]').click();
  await page.getByRole('tab', { name: 'Test scenarios' }).click();
  for (const [name, value] of Object.entries(fields)) {
    await page.locator(`#context-form [name=${name}]`).selectOption(String(value));
  }
  await page.locator('#context-form button[type=submit]').click();
  await page.locator('#context-form button[type=submit]:not([disabled])').waitFor();
  await page.waitForLoadState('networkidle');
}
/** Purpose: verify F06 context selectors, clock/manual modes, offline rules and deterministic ranking. Inputs: technician session. Returns: Promise<void>. */
async function auditRecommendations() {
  const seenConditions = [];
  for (const condition of ['unknown', 'sunny', 'cloudy', 'rainy', 'snowy']) {
    await setContext({ condition });
    const current = await (await page.request.get('/api/state')).json();
    if (current.settings.condition === condition) seenConditions.push(condition);
  }
  check('F06: technician selects unknown, sunny, cloudy, rainy and snowy conditions', seenConditions.length === 5);

  const seenWeathers = [];
  for (const weather of ['cold', 'mild', 'warm', 'hot']) {
    await setContext({ weather });
    const current = await (await page.request.get('/api/state')).json();
    if (current.settings.weather === weather) seenWeathers.push(weather);
  }
  check('F06: technician selects cold, mild, warm and hot temperatures', seenWeathers.length === 4);

  const seenPeriods = [];
  for (const period of ['morning', 'afternoon', 'evening', 'night']) {
    await setContext({ period_mode: 'manual', period });
    const current = await (await page.request.get('/api/state')).json();
    if (current.settings.period === period && current.settings.period_mode === 'manual') seenPeriods.push(period);
  }
  check('F06: technician selects all four manual periods', seenPeriods.length === 4);

  await setContext({ network: true, weather: 'mild', condition: 'unknown', period_mode: 'auto', period: 'morning' });
  const autoState = await (await page.request.get('/api/state')).json();
  await page.locator('[data-view=menu]').click();
  await page.locator('#recommend-toggle').check();
  const autoContextText = await page.locator('#recommend-context').textContent();
  await setContext({ network: true, weather: 'mild', condition: 'unknown', period_mode: 'manual', period: 'morning' });
  const manualState = await (await page.request.get('/api/state')).json();
  await page.locator('[data-view=menu]').click();
  const manualContextText = await page.locator('#recommend-context').textContent();
  check('F06: technician switches between manual override and local-clock automatic mode', autoState.settings.period_mode === 'auto' && manualState.settings.period_mode === 'manual');
  check('F06: recommendation context visibly identifies local clock versus technician override', autoContextText.includes('(local clock)') && manualContextText.includes('(technician override)'));

  await setContext({ network: true, weather: 'cold', condition: 'rainy', period_mode: 'manual', period: 'morning' });
  await page.locator('[data-view=menu]').click();
  const topRainyMorning = await page.locator('#drink-grid .drink-card').first().getAttribute('data-drink');

  await setContext({ network: true, weather: 'warm', condition: 'sunny', period_mode: 'manual', period: 'afternoon' });
  await page.locator('[data-view=menu]').click();
  const topSunnyAfternoon = await page.locator('#drink-grid .drink-card').first().getAttribute('data-drink');

  await setContext({ network: true, weather: 'cold', condition: 'snowy', period_mode: 'manual', period: 'night' });
  await page.locator('[data-view=menu]').click();
  const topSnowyNight = await page.locator('#drink-grid .drink-card').first().getAttribute('data-drink');
  const nightReason = await page.locator('#drink-grid .drink-card').first().locator('.recommend-label').textContent();
  check('F06: changing context deterministically updates top recommendation across three scenarios', topRainyMorning === 'cappuccino' && topSunnyAfternoon === 'latte' && topSnowyNight === 'cocoa' && nightReason === 'Late-hour comfort pick');

  await setContext({ network: false, weather: 'cold', condition: 'snowy', period_mode: 'manual', period: 'morning' });
  await page.locator('[data-view=menu]').click();
  const offlineContextText = await page.locator('#recommend-context').textContent();
  const topOfflineMorning = await page.locator('#drink-grid .drink-card').first().getAttribute('data-drink');
  check('F06: offline mode reports weather unavailable and ignores temperature and condition bonuses', offlineContextText.includes('weather unavailable') && topOfflineMorning === 'espresso');

  await signOut();
  await page.waitForLoadState('networkidle');
  await page.locator('#checkout-button:not([disabled])').waitFor();
  await page.locator('[data-view=menu]').click();
  await page.locator('#recommend-toggle').check();
  await page.locator('[data-drink=americano]').click();
  await textEquals('#selected-name', 'Americano');
  await page.locator('#customize-form [name=syrup]').fill('1');
  await page.locator('#checkout-button:not([disabled])').waitFor();
  check('F06: manual ordering remains usable when weather context is unavailable', !(await page.locator('#checkout-button').isDisabled()) && (await page.locator('#selected-name').textContent()) === 'Americano');
  await page.locator('#recommend-toggle').uncheck();
  await signIn(true);
  await setContext({ network: true, weather: 'cold', condition: 'unknown', period_mode: 'manual', period: 'morning', email_ok: true });
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
/** Purpose: simulate an unavailable recommendation service. Inputs: Playwright route. Returns: fulfilled 503 response. */
async function failRecommendations(route) { await route.fulfill({ status: 503, contentType: 'application/json', body: '{"error":"Recommendations unavailable"}' }); }
/** Purpose: simulate only the optional model endpoint being down. Inputs: Playwright route. Returns: fulfilled 503 response. */
async function failAssistant(route) { await route.fulfill({ status: 503, contentType: 'application/json', body: '{"error":"Local model unavailable. Manual ordering is still available."}' }); }
/** Purpose: identify a model response without replacing it. Inputs: Playwright response. Returns: boolean. */
function isAssistantResponse(response) { return response.url().endsWith('/api/assistant') && response.request().method() === 'POST'; }
/** Purpose: await real response and completed UI processing. Inputs: request text. Returns: response/payload/timing record. */
async function assistantTurn(message) {
  await page.locator('#assistant-request').fill(message);
  const started = performance.now();
  const reply = page.waitForResponse(isAssistantResponse, { timeout: 100000 });
  await page.locator('#assistant-submit').click();
  const response = await reply;
  const result = await response.json();
  await page.locator('#assistant-result[aria-busy="false"]').waitFor({ timeout: 100000 });
  assert.ok(response.ok(), JSON.stringify(result));
  const record = { request: response.request().postDataJSON(), response: result, milliseconds: performance.now() - started };
  assistantTurns.push(record);
  return record;
}
/** Purpose: prove exact context survives clarification in browser. Inputs: isolated signed-in page. Returns: actual turn records. */
async function auditAssistantConversation() {
  const before = await (await page.request.get('/api/state')).json();
  const base = await assistantTurn('A regular cappuccino at 75 degrees with two syrup shots and one extra espresso.');
  check('F11: new conversational request selects cappuccino', base.response.kind === 'recipe' && base.response.quote.config.drink === 'cappuccino');
  const config = base.response.quote.config;
  assert.equal(config.strength, 'regular'); assert.equal(config.extra, 1);
  const clarify = await assistantTurn('Can I add something?');
  assert.deepEqual(clarify.request.context_config, config);
  check('F11: clarification retains full recipe context', clarify.response.kind === 'clarify' && clarify.response.quote === null);
  const follow = await assistantTurn('Make it oat and stronger.');
  assert.deepEqual(follow.request.context_config, config);
  assert.deepEqual(follow.response.quote.config, { ...config, milk: 'oat', strength: 'strong' });
  check('F11: follow-up changes only requested fields after clarification', follow.response.kind === 'recipe');
  const after = await (await page.request.get('/api/state')).json();
  assert.deepEqual(after, before);
  check('F11: multi-turn proposals have no persistent side effects', true);
  return [base, clarify, follow];
}
/** Purpose: verify three actual model options, mobile layout and selected-option context. Inputs: isolated signed-in page and evidence folder. Returns: live turn records. */
async function auditAssistantOptions(currentEvidence) {
  await page.locator('#assistant-clear').click();
  const before = await (await page.request.get('/api/state')).json();
  await page.getByRole('button', { name: 'Three strong oat options', exact: true }).click();
  const choices = await assistantTurn(await page.locator('#assistant-request').inputValue());
  const suggestions = choices.response.suggestions;
  check('F11: real model supplies three distinct supported recipe options', suggestions.length === 3 && new Set(suggestions.map(optionConfigKey)).size === 3);
  check('F11: every option preserves requested settings and shows server price', suggestions.every(isRequestedOatOption) && await page.locator('.assistant-option').count() === 3);
  const cardsText = await page.locator('.assistant-options').textContent();
  check('F11: customer recipe choices omit technical scores and confidence percentages', !/score|confidence|\d\s*%/i.test(cardsText));
  await page.screenshot({ path: path.join(currentEvidence, 'assistant-options.png'), fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  const mobileChoices = await page.evaluate(inspectLayout);
  check('F11: three recipe options fit the mobile viewport', mobileChoices.scrollWidth <= mobileChoices.width && await page.locator('.assistant-option').count() === 3);
  await page.screenshot({ path: path.join(currentEvidence, 'assistant-options-mobile.png'), fullPage: true });
  await page.setViewportSize({ width: 1440, height: 1000 });
  const chosen = suggestions[1].quote;
  await page.locator('[data-assistant-apply="1"]').click();
  await page.locator('[data-assistant-option="1"].is-active').waitFor();
  assert.deepEqual(await page.evaluate(currentCustomizerConfig), chosen.config);
  check('F11: the second option applies its own exact recipe', (await page.locator('#quote-price').textContent()).includes(String(chosen.price / 100)));
  const follow = await assistantTurn('Make it mild.');
  assert.deepEqual(follow.request.context_config, chosen.config);
  assert.deepEqual(follow.response.quote.config, { ...chosen.config, strength: 'mild' });
  check('F11: follow-up refines the chosen second recipe rather than the first', true);
  const after = await (await page.request.get('/api/state')).json();
  assert.deepEqual(after, before);
  check('F11: proposing and applying any option has no purchase effects', true);
  return [choices, follow];
}
/** Purpose: compare normalized option identities. Inputs: suggestion. Returns: stable configuration JSON. */
function optionConfigKey(suggestion) { return JSON.stringify(suggestion.quote.config); }
/** Purpose: verify request constraints and server-owned prices on each option. Inputs: suggestion. Returns: boolean. */
function isRequestedOatOption(suggestion) {
  const config = suggestion.quote.config;
  return suggestion.quote.available && Number.isInteger(suggestion.quote.price) && config.milk === 'oat' && config.strength === 'strong' && config.temperature === 75 && config.syrup === 1 && config.extra === 0;
}
/** Purpose: read the selected drink and actual controls after applying an option. Inputs: browser DOM. Returns: normalized recipe configuration. */
function currentCustomizerConfig() {
  const form = document.querySelector('#customize-form');
  return { drink: document.querySelector('.drink-card.selected').dataset.drink, milk: form.elements.milk.value, strength: form.elements.strength.value, temperature: Number(form.elements.temperature.value), syrup: Number(form.elements.syrup.value), extra: Number(form.elements.extra.value) };
}
/** Purpose: inspect visible button targets and input focus. Inputs: browser DOM. Returns: size/focus observations. */
function inspectAccessibility() {
  let smallButtons = 0;
  for (const button of document.querySelectorAll('button')) {
    const box = button.getBoundingClientRect();
    if (box.width > 0 && box.height > 0 && (box.width < 24 || box.height < 24)) smallButtons++;
  }
  const focus = getComputedStyle(document.activeElement);
  return { smallButtons, focusVisible: focus.outlineStyle !== 'none' && parseFloat(focus.outlineWidth) > 0 };
}
/** Purpose: wait for committed maintenance state rather than an old network-idle event. Inputs: browser DOM. Returns: boolean. */
function maintenanceReady() {
  const button = document.querySelector('[data-empty=grounds]');
  return Boolean(button && !button.disabled && button.closest('.bin-row').textContent.includes('grounds · 0%'));
}
/** Purpose: register a real customer via UI. Inputs: name/email/password fixtures. Returns: Promise<void>. */
async function register(name, email, password) {
  await page.locator('#account-button').click(); await page.locator('[data-auth=register]').click();
  await page.locator('#auth-form [name=name]').fill(name); await page.locator('#auth-form [name=email]').fill(email);
  await page.locator('#auth-form [name=password]').fill(password); await page.locator('#auth-submit').click();
  await textEquals('#account-name', name); await page.waitForLoadState('networkidle');
}
/** Purpose: exercise two distinct customer identities and restart persistence. Inputs: owned-server restart callback. Returns: Promise<void>. */
async function auditAccounts(restart) {
  await page.locator('#account-button').click();
  check('F01: ordinary login starts empty with NFC disabled', await page.locator('#auth-form [name=email]').inputValue() === '' && await page.locator('#auth-form [name=password]').inputValue() === '' && await page.locator('#auth-form [name=nfc]').isDisabled());
  await page.locator('#auth-dialog .close-dialog').click();
  await register('First customer', 'first@browser.test', 'FirstCustomer123!');
  await page.locator('#save-recipe').click(); await page.locator('#recipe-name').fill('First private recipe');
  await page.locator('#recipe-form button[type=submit]').click(); await page.waitForLoadState('networkidle');
  await purchase(); await page.locator('#receipt-dialog').waitFor(); await page.locator('#receipt-dialog .close-dialog').click();
  const owned = await (await page.request.get('/api/state')).json();
  await signOut();
  check('F01: logout clears receipt and private records', (await page.locator('#receipt-content').textContent()) === '' && !(await page.locator('#recipe-list').textContent()).includes('First private recipe'));
  await register('Second customer', 'second@browser.test', 'SecondCustomer123!');
  const second = await (await page.request.get('/api/state')).json();
  check('F01/F04/F07: new customer is not Alex and sees no other records', second.user.name === 'Second customer' && second.user.id !== owned.user.id && second.recipes.length === 0 && second.orders.length === 0);
  const forbiddenRecipe = await page.request.post('/api/recipes/delete', { data: { id: owned.recipes[0].id } });
  const forbiddenReceipt = await page.request.post('/api/email-receipt', { data: { id: owned.orders[0].id } });
  check('HTTP: another account cannot delete recipes or email purchases', forbiddenRecipe.status() === 404 && forbiddenReceipt.status() === 404);
  const mixed = await page.request.post('/api/auth/login', { data: { email: 'missing@browser.test', password: 'WrongPassword', nfc: 'DEMO-NFC-001' } });
  check('HTTP: hidden NFC cannot bypass password sign-in', mixed.status() === 400);
  await signOut(); await page.locator('#account-button').click();
  await page.locator('#auth-form [name=email]').fill('first@browser.test'); await page.locator('#auth-form [name=password]').fill('WrongPassword');
  await page.locator('#auth-submit').click(); await textEquals('#auth-error', 'not recognized');
  check('F01: wrong password does not sign in as Alex', (await page.locator('#account-name').textContent()) === 'Sign in');
  await page.locator('#auth-dialog .close-dialog').click();
  await signIn(false, 'first@browser.test', 'FirstCustomer123!', 'First customer');
  await restart();
  const restored = await (await page.request.get('/api/state')).json();
  check('F01/F04/F07: restart preserves the correct account and its records', restored.user.id === owned.user.id && restored.recipes[0].id === owned.recipes[0].id && restored.orders[0].id === owned.orders[0].id);
  await page.locator('[data-view=recipes]').click(); await page.locator('[data-delete]').click(); await page.locator('[data-delete]').waitFor({ state: 'detached' });
  check('F04: owner can delete their saved recipe', await page.locator('[data-delete]').count() === 0);
  await signOut(); await page.locator('#account-button').click(); await page.locator('[data-auth=nfc]').click();
  await page.locator('#fill-demo').click(); await page.locator('#auth-submit').click(); await textEquals('#account-name', 'Alex');
  check('F01: explicit NFC sign-in remains available', true); await signOut();
}
/** Purpose: safely remove only the current browser run's temporary directory under tmp/. Inputs: tempDir/tmpRoot paths. Returns: void. */
function removeTempDir(tempDir, tmpRoot) {
  if (!tempDir) return;
  const resolvedTmpRoot = path.resolve(tmpRoot);
  const resolvedTemp = path.resolve(tempDir);
  assert.ok(resolvedTemp !== resolvedTmpRoot, 'Refusing to delete tmp root directory');
  assert.equal(path.dirname(resolvedTemp), resolvedTmpRoot, 'Temporary directory must be a direct child of tmp/');
  assert.ok(path.basename(resolvedTemp).startsWith('browser-'), 'Temporary directory must match browser-* prefix');
  if (fs.existsSync(resolvedTemp)) {
    fs.rmSync(resolvedTemp, { recursive: true, force: true, maxRetries: 5, retryDelay: 100 });
  }
}
/** Purpose: execute the full QA flow with isolated temporary database cleanup. Inputs: environment PYTHON/CHROME_PATH. Returns: Promise<void>. */
async function main() {
  const tmpRoot = path.join(root, 'tmp');
  const currentEvidence = path.join(root, 'evidence', 'current');
  fs.mkdirSync(tmpRoot, { recursive: true }); fs.mkdirSync(currentEvidence, { recursive: true });
  const temp = fs.mkdtempSync(path.join(tmpRoot, 'browser-'));
  console.log('TEMP_DIR_CREATED', temp);
  child = spawn(process.env.PYTHON || 'python', ['app.py', '--port', '8766', '--database', path.join(temp, 'qa.db')], { cwd: root, windowsHide: true, stdio: 'pipe' });
  let serverOutput = ''; child.stdout.on('data', captureOutput); child.stderr.on('data', captureOutput);
  /** Purpose: retain server diagnostics. Inputs: output buffer. Returns: void. */
  function captureOutput(buffer) { serverOutput += buffer.toString(); }
  /** Purpose: restart only the isolated QA server with the same database. Inputs: captured QA path/process. Returns: Promise<void>. */
  async function restartServer() {
    const stopped = once(child, 'exit'); child.kill(); await stopped; serverOutput = '';
    child = spawn(process.env.PYTHON || 'python', ['app.py', '--port', '8766', '--database', path.join(temp, 'qa.db')], { cwd: root, windowsHide: true, stdio: 'pipe' });
    child.stdout.on('data', captureOutput); child.stderr.on('data', captureOutput);
    for (let i = 0; i < 60 && !serverOutput.includes('ready at'); i++) { if (child.exitCode !== null) throw new Error(serverOutput); await delay(100); }
    assert.ok(serverOutput.includes('ready at')); await page.reload(); await page.waitForLoadState('networkidle');
  }
  try {
    for (let i = 0; i < 60 && !serverOutput.includes('ready at'); i++) { if (child.exitCode !== null) throw new Error(serverOutput); await delay(100); }
    assert.ok(serverOutput.includes('ready at'), 'Isolated QA server started');
    browser = await chromium.launch({ headless: true, ...(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {}) });
    page = await browser.newPage({ baseURL: 'http://127.0.0.1:8766', viewport: { width: 1440, height: 1000 } }); page.on('pageerror', recordError);
    await page.goto('http://127.0.0.1:8766'); await page.waitForLoadState('networkidle');
    check('F02: six menu drinks load', await page.locator('.drink-card').count() === 6);
    await page.locator('[data-category=Chocolate]').click(); check('F02: category filter', await page.locator('.drink-card').count() === 2);
    await page.locator('[data-category=All]').click(); await auditAccounts(restartServer); await signIn();
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
    await page.screenshot({ path: path.join(currentEvidence, 'desktop.png'), fullPage: true });
    await purchase('contactless', 100); await page.locator('#receipt-dialog').waitFor();
    check('F07/F08: checkout with loyalty discount', (await page.locator('#receipt-content').textContent()).includes('10'));
    check('F03/F09: receipt contains syrup and extra-shot settings', (await page.locator('#receipt-content').textContent()).includes('2 syrup shots') && (await page.locator('#receipt-content').textContent()).includes('1 extra espresso shots'));
    await page.locator('#receipt-content img').waitFor();
    const svg = await page.request.get((await page.locator('#receipt-content img').getAttribute('src')));
    check('F09: actual QR SVG generated', svg.ok() && (await svg.text()).includes('<svg'));
    await page.locator('#email-receipt').click(); await textEquals('#receipt-message', 'local email simulator outbox');
    await page.screenshot({ path: path.join(currentEvidence, 'receipt.png'), fullPage: true });
    await page.locator('#receipt-dialog .close-dialog').click();
    const admin = await browser.newContext({ baseURL: 'http://127.0.0.1:8766' });
    await admin.request.post('/api/auth/login', { data: { method: 'password', email: 'tech@smartbrew.test', password: '246810' } });
    await admin.request.post('/api/admin/simulation', { data: { payment_mode: 'decline' } });
    await page.locator('#checkout-button').click();
    check('Customer checkout has no payment-outcome control', await page.locator('#payment-form [name=outcome]').count() === 0);
    check('Complete order review includes syrup and extra shots', (await page.locator('#checkout-summary').textContent()).includes('2 syrup shots') && (await page.locator('#checkout-summary').textContent()).includes('1 extra espresso shots'));
    await page.locator('#pay-button').click(); await textEquals('#payment-error', 'declined');
    check('F07: declined payment reported', true); await page.locator('#checkout-dialog .close-dialog').click();
    const override = await page.request.post('/api/checkout', { data: { config: { drink: 'espresso' }, key: 'forged-outcome-browser', method: 'contactless', points: 0, outcome: 'approve' } });
    check('HTTP: customer cannot override payment simulation', override.status() === 400);
    await admin.request.post('/api/admin/simulation', { data: { payment_mode: 'normal' } }); await admin.close();
    await page.locator('[data-view=history]').click(); check('F07: one completed history entry', await page.locator('#history-list .list-item').count() === 1);
    await signOut(); await signIn(true); await page.locator('[data-view=maintenance]').click();
    check('F10: seven ingredient counters', await page.locator('[data-refill]').count() === 7);
    await page.getByRole('tab', { name: 'Test scenarios' }).click();
    await page.locator('#simulation-form [name=payment_mode]').selectOption('decline'); await page.locator('#simulation-form button[type=submit]').click();
    await textEquals('#maintenance-content', 'Decline active');
    check('F10: technician UI controls processor simulation', true);
    await page.locator('#simulation-form [name=payment_mode]').selectOption('normal'); await page.locator('#simulation-form button[type=submit]').click(); await page.waitForLoadState('networkidle');
    await page.locator('#stock-oat').fill('99'); await page.locator('[data-stock=oat]').click(); await page.waitForLoadState('networkidle');
    await page.locator('[data-view=menu]').click();
    await page.locator('#customize-form [name=milk]').selectOption('oat');
    await textEquals('#availability', 'Oat milk unavailable');
    check('F05: depleted customized ingredient blocks checkout', await page.locator('#checkout-button').isDisabled());
    await page.locator('[data-view=maintenance]').click(); await page.getByRole('tab', { name: 'Maintenance', exact: true }).click(); await page.locator('[data-refill=oat]').click(); await page.waitForLoadState('networkidle');
    await page.getByRole('tab', { name: 'Test scenarios' }).click();
    await page.locator('#bin-grounds').fill('100'); await page.locator('[data-waste=grounds]').click(); await page.waitForLoadState('networkidle');
    await page.locator('[data-view=menu]').click(); await textEquals('#availability', 'Grounds bin full'); check('F10: full bin halts checkout', await page.locator('#checkout-button').isDisabled());
    await page.locator('[data-view=maintenance]').click(); await page.getByRole('tab', { name: 'Maintenance', exact: true }).click(); await page.locator('[data-empty=grounds]').click(); await page.waitForLoadState('networkidle');
    await page.waitForFunction(maintenanceReady);
    await page.screenshot({ path: path.join(currentEvidence, 'maintenance.png'), fullPage: true });
    await page.getByRole('tab', { name: 'Test scenarios' }).click();
    await page.locator('[data-fault=GRINDER_JAM]').click(); await page.waitForLoadState('networkidle');
    await textEquals('#maintenance-content', 'GRINDER_JAM');
    check('F10: diagnostic fault logged', (await page.locator('#maintenance-content').textContent()).includes('GRINDER_JAM'));
    await page.screenshot({ path: path.join(currentEvidence, 'test-scenarios.png'), fullPage: true });
    await page.locator('[data-fault=""]').click(); await textEquals('#maintenance-content', 'No active fault');
    await auditRecommendations();
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
    let liveAI = null;
    if (process.env.SMARTBREW_LIVE_AI === '1') {
      await page.locator('[data-view=menu]').click();
      await page.locator('#customize-form [name=milk]').selectOption('dairy');
      await page.locator('#customize-form [name=syrup]').fill('0'); await page.waitForLoadState('networkidle');
      const before = await (await page.request.get('/api/state')).json();
      await page.locator('#assistant-request').fill('A strong oat latte at 75 degrees with one syrup shot and no extra espresso.');
      const reply = page.waitForResponse(isAssistantResponse, { timeout: 100000 });
      await page.locator('#assistant-submit').click(); const actual = await (await reply).json();
      await page.locator('#assistant-apply').waitFor({ timeout: 100000 });
      check('F11: real local model returns a supported oat-latte proposal', actual.local === true && actual.model === 'qwen3:4b' && actual.quote.config.milk === 'oat' && actual.quote.price === 4200);
      const after = await (await page.request.get('/api/state')).json();
      check('F11: inference does not apply settings or purchase automatically', await page.locator('#customize-form [name=milk]').inputValue() === 'dairy' && after.orders.length === before.orders.length && after.user.points === before.user.points);
      await page.screenshot({ path: path.join(currentEvidence, 'local-assistant.png'), fullPage: true });
      await page.locator('#assistant-apply').click(); await textEquals('#quote-price', '42');
      check('F11: explicit confirmation applies the validated settings', await page.locator('#customize-form [name=milk]').inputValue() === 'oat' && await page.locator('#customize-form [name=syrup]').inputValue() === '1');
      liveAI = { realInference: true, mockedModel: false, response: actual };
      liveAI.conversation = await auditAssistantConversation();
      liveAI.options = await auditAssistantOptions(currentEvidence);
      await signOut();
      check('F11: account change clears conversation and proposal', (await page.locator('#assistant-result').textContent()) === '' && await page.locator('#assistant-request').inputValue() === '');
      await signIn();
    }
    await page.locator('[data-view=menu]').click();
    await page.route('**/api/assistant', failAssistant);
    await page.locator('#assistant-request').fill('A latte, please'); await page.locator('#assistant-submit').click();
    await textEquals('#assistant-result', 'Manual ordering is still available');
    check('F11: model failure leaves manual checkout available', !(await page.locator('#checkout-button').isDisabled()));
    await page.unroute('**/api/assistant', failAssistant);
    await page.locator('[data-view=menu]').click(); await page.setViewportSize({ width: 390, height: 844 }); await page.waitForLoadState('networkidle');
    const mobile = await page.evaluate(inspectLayout); check('Mobile root has no horizontal overflow', mobile.scrollWidth <= mobile.width); check('Menu photograph assets loaded', mobile.images > 0 && mobile.loadedImages === mobile.images);
    await page.screenshot({ path: path.join(currentEvidence, 'mobile.png'), fullPage: true });
    await page.locator('#assistant-request').focus();
    const accessibility = await page.evaluate(inspectAccessibility);
    check('Visible controls have usable targets and input focus is visible', accessibility.smallButtons === 0 && accessibility.focusVisible);
    await page.route('**/api/recommendations', failRecommendations);
    await page.reload(); await page.waitForLoadState('networkidle');
    check('Service failure: standard menu still loads', await page.locator('.drink-card').count() === 6);
    await page.locator('#recommend-toggle').check();
    check('Service failure: recommended mode falls back to usable menu', await page.locator('.drink-card').count() === 6 && !(await page.locator('#checkout-button').isDisabled()));
    await purchase(); await page.locator('#receipt-dialog').waitFor();
    check('Service failure: manual checkout still completes', (await page.locator('#receipt-content').textContent()).includes('Paid'));
    check('No uncaught browser errors', errors.length === 0);
    fs.writeFileSync(path.join(currentEvidence, 'browser-results.json'), JSON.stringify({ recordedAt: new Date().toISOString(), checks, errors, responseSample: { count: 100, p95ms: p95 }, quoteSample: { count: 100, p95ms: quoteP95 }, mobile, accessibility, liveAI, browser: browser.version(), node: process.version, simulatedIntegrations: true }, null, 2));
  } catch (error) {
    fs.writeFileSync(path.join(root, 'tmp', 'browser-failure.json'), JSON.stringify({ recordedAt: new Date().toISOString(), passed: false, checks, errors, assistantTurns, error: error.stack }, null, 2));
    if (page) await page.screenshot({ path: path.join(root, 'tmp', 'browser-failure.png'), fullPage: true });
    throw error;
  } finally {
    if (browser) await browser.close();
    if (child && child.exitCode === null) {
      const stopped = once(child, 'exit');
      child.kill();
      await Promise.race([stopped, delay(3000)]);
    }
    removeTempDir(temp, tmpRoot);
    console.log('TEMP_DIR_REMOVED', temp, !fs.existsSync(temp));
  }
}
/** Purpose: surface failed QA without orphaning the browser/server. Inputs: Error. Returns: void. */
function failed(error) { console.error(error); process.exitCode = 1; }
main().catch(failed);
