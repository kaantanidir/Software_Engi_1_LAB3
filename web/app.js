/* SmartBrew browser adapter. All prices are integer ore until presentation. */
let state = {}, selected = 'latte', quote = null, category = 'All', recommendations = [], recommendationContext = '';
let authMode = 'login', editingRecipe = null, activeOrder = null, paymentKey = null, quoteRevision = 0, toastTimer;
let recommendationStatus = 'loading', refreshRevision = 0;
let adminTab = 'maintenance', maintenanceBusy = false;
const busyForms = new Set();

/** Purpose: resolve a DOM selector. Inputs: selector string. Returns: element or null. */
function $(selector) { return document.querySelector(selector); }
/** Purpose: escape untrusted text for template rendering. Inputs: any value. Returns: safe HTML string. */
function esc(value) { return String(value ?? '').replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#39;'); }
/** Purpose: format integer ore. Inputs: amount. Returns: currency label. */
function money(amount) { return new Intl.NumberFormat('en-SE', { style: 'currency', currency: 'SEK' }).format(amount / 100); }
/** Purpose: refresh local Lucide icons. Inputs: document. Returns: void. */
function icons() { lucide.createIcons(); }
/** Purpose: call a local JSON endpoint. Inputs: path, optional body, timeout and abort signal. Returns: parsed response or rejected error. */
async function api(path, body, timeoutMs = null, signal = null) {
  const options = body === undefined ? {} : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) };
  if (signal) options.signal = signal;
  else if (timeoutMs !== null) options.signal = AbortSignal.timeout(timeoutMs);
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Request failed.');
  return data;
}
/** Purpose: hide a transient message. Inputs: none. Returns: void. */
function hideToast() { $('#toast').hidden = true; }
/** Purpose: announce an action outcome. Inputs: message string. Returns: void. */
function toast(message) { $('#toast').textContent = message; $('#toast').hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(hideToast, 5500); }
/** Purpose: find a recipe by numeric id. Inputs: id. Returns: owned recipe or undefined. */
function findRecipe(id) { for (const recipe of state.recipes || []) if (recipe.id === Number(id)) return recipe; }
/** Purpose: read customization controls. Inputs: form DOM. Returns: normalized config object. */
function config() {
  const data = new FormData($('#customize-form'));
  return { drink: selected, milk: data.get('milk'), strength: data.get('strength'), temperature: Number(data.get('temperature')), syrup: Number(data.get('syrup')), extra: Number(data.get('extra')) };
}
/** Purpose: load settings into controls. Inputs: full/partial config. Returns: void. */
function applyConfig(value) {
  selected = value.drink || selected;
  const form = $('#customize-form');
  form.elements.milk.value = value.milk || 'dairy';
  form.elements.strength.value = value.strength || 'regular';
  form.elements.temperature.value = value.temperature ?? 70;
  form.elements.syrup.value = value.syrup ?? 0;
  form.elements.extra.value = value.extra ?? 0;
}
/** Purpose: clear identity-bound UI when the session changes. Inputs: current DOM/state. Returns: void. */
function clearPrivateState() {
  clearTimeout(toastTimer); hideToast();
  selected = 'latte'; category = 'All'; editingRecipe = null; activeOrder = null; paymentKey = null; quote = null;
  quoteRevision++; adminTab = 'maintenance';
  $('#customize-form').reset(); $('#auth-form').reset(); $('#payment-form').reset(); $('#recommend-toggle').checked = false;
  $('#recipe-name').value = ''; $('#receipt-content').replaceChildren(); $('#checkout-summary').replaceChildren();
  for (const dialog of document.querySelectorAll('dialog[open]')) dialog.close();
  for (const button of document.querySelectorAll('[data-category]')) button.classList.toggle('active', button.dataset.category === 'All');
  resetAssistant(); showView('menu');
}
/** Purpose: describe every purchased setting consistently. Inputs: recipe configuration. Returns: plain text. */
function recipeDetails(value) {
  return `${value.milk} milk · ${value.strength} · ${value.temperature} °C · ${value.syrup} syrup shots · ${value.extra} extra espresso shots`;
}
/** Purpose: load server state into all visible views. Inputs: none. Returns: Promise<void>. */
async function refresh() {
  const revision = ++refreshRevision;
  const result = await api('/api/state');
  if (revision !== refreshRevision) return;
  const identityChanged = (state.user?.id ?? null) !== (result.user?.id ?? null);
  state = result; recommendationStatus = 'loading'; recommendations = []; recommendationContext = '';
  if (identityChanged) { clearPrivateState(); if (state.user?.role === 'customer') applyConfig(state.user.preferences); }
  $('#maintenance-nav').hidden = state.user?.role !== 'technician';
  $('#account-name').textContent = state.user?.name || 'Sign in';
  $('#account-button').title = state.user?.name || 'Sign in';
  $('#connection').textContent = state.settings.network ? 'Machine online' : 'Offline · local ordering';
  $('#balance').innerHTML = state.user?.role === 'customer' ? `<strong>${state.user.points} points</strong><br>Employee balance ${esc(money(state.user.balance))}` : 'Guest ordering available';
  renderMenu(); renderRecipes(); renderHistory(); renderMaintenance();
  await updateQuote(); icons();
  try {
    const ranking = await api('/api/recommendations', undefined, 1200);
    if (revision !== refreshRevision) return;
    recommendations = ranking.recommendations; recommendationContext = ranking.context || ''; recommendationStatus = 'ready';
  } catch (error) {
    if (revision !== refreshRevision) return;
    recommendationStatus = 'unavailable';
  }
  renderMenu();
}
/** Purpose: show a view and active navigation. Inputs: view key. Returns: void. */
function showView(view) {
  for (const element of document.querySelectorAll('.view')) element.hidden = element.id !== view + '-view';
  for (const button of document.querySelectorAll('[data-view]')) button.classList.toggle('active', button.dataset.view === view);
}
/** Purpose: render menu/filter/recommendation choices. Inputs: global state/category. Returns: void. */
function renderMenu() {
  const useRecommendations = $('#recommend-toggle').checked;
  const ranked = useRecommendations && recommendationStatus === 'ready';
  const entries = ranked ? recommendations : state.menu || [];
  let html = '';
  for (const drink of entries) {
    if (category !== 'All' && drink.category !== category) continue;
    const id = drink.config.drink;
    const image = id === 'espresso' || id === 'americano' ? 'espresso' : id === 'mocha' || id === 'cocoa' ? 'chocolate' : 'latte';
    const reason = ranked ? drink.reasons[0] : (drink.available ? 'Available' : drink.reasons[0]);
    html += `<button class="drink-card ${id === selected ? 'selected' : ''} ${drink.available ? '' : 'unavailable'}" data-drink="${esc(id)}" aria-pressed="${id === selected}"><img class="drink-photo" src="/images/${image}.jpg" alt="${esc(drink.name)} serving illustration"><div class="drink-info"><strong>${esc(drink.name)}</strong><p class="drink-meta">${esc(drink.category)} · ${drink.kcal} kcal<br>${drink.allergens.length ? 'Contains ' + esc(drink.allergens.join(', ')) : 'No listed allergens'}</p><span class="recommend-label ${drink.available ? '' : 'blocked'}">${esc(reason)}</span><div class="drink-price"><span>${esc(money(drink.price))}</span><i data-lucide="${id === selected ? 'circle-check' : 'plus'}"></i></div></div></button>`;
  }
  $('#drink-grid').innerHTML = html || '<p class="empty">No available drinks in this selection.</p>';
  const fallbackSource = state.settings?.period_mode === 'auto' ? 'local clock' : 'technician override';
  const fallbackWeather = state.settings?.network ? `${state.settings.weather}${state.settings.condition && state.settings.condition !== 'unknown' ? ', ' + state.settings.condition : ''} weather (simulator)` : 'local history/preferences; weather unavailable';
  const fallbackContext = `Context: ${state.settings?.period} (${fallbackSource}) · ${fallbackWeather}`;
  $('#recommend-context').textContent = useRecommendations ? (ranked ? (recommendationContext || fallbackContext) : recommendationStatus === 'loading' ? 'Loading recommendations; standard menu shown.' : 'Recommendations unavailable; standard menu shown.') : 'Nutrition values are illustrative estimates. Final ingredients and availability follow your customization.';
  icons();
}
/** Purpose: update quote without allowing stale responses to overwrite newer choices. Inputs: control values. Returns: Promise<void>. */
async function updateQuote() {
  const revision = ++quoteRevision;
  $('#checkout-button').disabled = true;
  $('#temperature-value').textContent = config().temperature + ' °C';
  try {
    const result = await api('/api/quote', config());
    if (revision !== quoteRevision) return;
    quote = result;
    $('#selected-name').textContent = quote.name;
    $('#quote-price').textContent = money(quote.price);
    $('#nutrition').innerHTML = `<span>${quote.kcal} kcal</span><span>${quote.allergens.length ? 'Contains ' + esc(quote.allergens.join(', ')) : 'No listed allergens'}</span>`;
    $('#availability').textContent = quote.available ? 'Ingredients available' : quote.reasons.join(' · ');
    $('#availability').classList.toggle('error', !quote.available);
    $('#checkout-button').disabled = !quote.available || state.user?.role === 'technician';
    $('#checkout-button').title = state.user?.role === 'technician' ? 'Sign in as a customer or sign out to order' : '';
  } catch (error) { if (revision === quoteRevision) { $('#availability').textContent = error.message; $('#availability').classList.add('error'); } }
}
/** Purpose: render saved recipes with owner-only actions. Inputs: current state. Returns: void. */
function renderRecipes() {
  if (!state.user || state.user.role !== 'customer') { $('#recipe-list').innerHTML = '<div class="empty">Sign in as a customer to keep your recipes.<br><button data-open-auth>Sign in</button></div>'; return; }
  let html = '';
  for (const recipe of state.recipes) html += `<article class="list-item"><div><h3>${esc(recipe.name)}</h3><p>${esc(recipe.config.drink)} · ${esc(recipe.config.milk)} · ${esc(recipe.config.strength)} · ${recipe.config.temperature} °C<br>${recipe.config.syrup} syrup / ${recipe.config.extra} extra espresso</p></div><div class="item-actions"><button data-load-recipe="${recipe.id}"><i data-lucide="coffee"></i>Order</button><button class="icon" title="Rename recipe" data-rename="${recipe.id}"><i data-lucide="pencil"></i></button><button class="icon" title="Delete recipe" data-delete="${recipe.id}"><i data-lucide="trash-2"></i></button></div></article>`;
  $('#recipe-list').innerHTML = html ? '<div class="item-list">' + html + '</div>' : '<p class="empty">No saved recipes yet.</p>';
}
/** Purpose: render immutable purchase history/pending payments. Inputs: current state. Returns: void. */
function renderHistory() {
  let html = '';
  for (const order of state.orders || []) html += `<article class="list-item"><div><h3>#${order.id} · ${esc(order.recipe.name)} <span class="pill">${order.offline ? 'Offline approved' : 'Completed'}</span></h3><p>${esc(new Date(order.created).toLocaleString())} · ${esc(order.method)}<br>${esc(order.recipe.config.milk)} · ${esc(order.recipe.config.strength)} · ${order.recipe.config.temperature} °C · ${order.recipe.config.syrup} syrup · ${order.recipe.config.extra} extra espresso</p></div><div class="item-actions"><strong>${esc(money(order.paid))}</strong><button class="icon" title="View receipt" data-receipt="${order.id}"><i data-lucide="qr-code"></i></button></div></article>`;
  $('#history-list').innerHTML = html ? '<div class="item-list">' + html + '</div>' : '<p class="empty">' + (state.user ? 'No completed purchases yet.' : 'Sign in to see your purchase history.') + '</p>';
  let pending = '';
  for (const row of state.pending || []) if (row.status === 'pending') pending += `<article class="list-item"><div><h3>Awaiting external authorization</h3><p>${esc(row.method)} · No dispensing or charge</p></div><button data-pending="${esc(row.id)}"><i data-lucide="refresh-cw"></i>Retry</button></article>`;
  $('#pending-list').innerHTML = pending;
}
/** Purpose: render admin tables and simulation controls. Inputs: role-protected server state. Returns: void. */
function renderMaintenance() {
  const admin = state.user?.role === 'technician'; $('#export-logs').hidden = !admin;
  if (!admin) { $('#maintenance-content').innerHTML = '<div class="empty">Technician authentication required.<br><button data-tech-login><i data-lucide="key-round"></i>Technician sign in</button></div>'; return; }
  const settings = state.settings;
  let stocks = '', sensors = '', bins = '', wasteSensors = '', events = '', outbox = '';
  for (const item of state.ingredients) {
    stocks += `<tr><td><strong>${esc(item.name)}</strong></td><td><span class="meter"><span style="width:${Math.round(item.level / item.capacity * 100)}%"></span></span>${item.level} / ${item.capacity} ${esc(item.unit)}</td><td>${item.threshold}</td><td><button data-refill="${esc(item.id)}" title="Confirm full refill"><i data-lucide="package-plus"></i>Refill</button></td></tr>`;
    sensors += `<tr><td>${esc(item.name)}</td><td><input type="number" aria-label="${esc(item.name)} simulated level" id="stock-${esc(item.id)}" min="0" max="${item.capacity}" value="${item.level}"></td><td><button data-stock="${esc(item.id)}"><i data-lucide="gauge"></i>Set</button></td></tr>`;
  }
  for (const bin of state.bins) {
    bins += `<div class="bin-row service-bin"><strong>${esc(bin.id)} · ${bin.level}%</strong><button data-empty="${bin.id}"><i data-lucide="trash-2"></i>Record emptied</button></div>`;
    wasteSensors += `<div class="bin-row service-bin"><label>${esc(bin.id)} waste %<input type="number" min="0" max="150" value="${bin.level}" id="bin-${bin.id}" aria-label="${bin.id} waste percentage"></label><button data-waste="${bin.id}"><i data-lucide="gauge"></i>Set</button></div>`;
  }
  for (const event of state.events) events += `<tr><td>${esc(new Date(event.created).toLocaleTimeString())}</td><td><span class="pill ${event.severity === 'error' ? 'error' : ''}">${esc(event.severity)}</span></td><td>${esc(event.code)}</td><td>${esc(event.message)}</td></tr>`;
  for (const mail of state.outbox) outbox += `<tr><td>#${mail.order_id}</td><td>${esc(mail.recipient)}</td><td>Saved locally · ${esc(new Date(mail.created).toLocaleString())}</td></tr>`;
  $('#maintenance-content').innerHTML = `
    <div class="segments admin-tabs" role="tablist" aria-label="Technician workspace">
      <button role="tab" data-admin-tab="maintenance" aria-selected="${adminTab === 'maintenance'}" class="${adminTab === 'maintenance' ? 'active' : ''}">Maintenance</button>
      <button role="tab" data-admin-tab="testing" aria-selected="${adminTab === 'testing'}" class="${adminTab === 'testing' ? 'active' : ''}">Test scenarios</button>
    </div>
    <div ${adminTab === 'maintenance' ? '' : 'hidden'}>
      <section class="admin-band"><h2>Ingredients & cups</h2><div class="table-wrap"><table><thead><tr><th>Ingredient</th><th>Current / capacity</th><th>Minimum</th><th>Refill</th></tr></thead><tbody>${stocks}</tbody></table></div></section>
      <section class="admin-band"><h2>Waste bins</h2>${bins}</section>
      <section class="admin-band"><h2>Diagnostic event log</h2><div class="table-wrap"><table><thead><tr><th>Time</th><th>Severity</th><th>Code</th><th>Message</th></tr></thead><tbody>${events}</tbody></table></div></section>
      <section class="admin-band"><h2>Email simulator outbox</h2><div class="table-wrap"><table><thead><tr><th>Order</th><th>Recipient</th><th>Status</th></tr></thead><tbody>${outbox || '<tr><td colspan="3">No simulated emails yet.</td></tr>'}</tbody></table></div></section>
    </div>
    <div ${adminTab === 'testing' ? '' : 'hidden'}>
      <section class="admin-band"><h2>External payment processor <span class="pill ${settings.payment_mode === 'decline' ? 'error' : ''}">${settings.payment_mode === 'decline' ? 'Decline active' : 'Normal'}</span></h2>
        <form id="simulation-form" class="simulation-controls"><label>Payment simulation<select name="payment_mode"><option value="normal" ${settings.payment_mode === 'normal' ? 'selected' : ''}>Normal</option><option value="decline" ${settings.payment_mode === 'decline' ? 'selected' : ''}>Decline</option></select></label><button type="submit"><i data-lucide="check"></i>Apply</button></form>
      </section>
      <section class="admin-band"><h2>Service context</h2><form id="context-form" class="admin-context"><label>Network<select name="network"><option value="true" ${settings.network ? 'selected' : ''}>Online</option><option value="false" ${!settings.network ? 'selected' : ''}>Offline</option></select></label><label>Weather<select name="weather"><option value="cold" ${settings.weather === 'cold' ? 'selected' : ''}>Cold</option><option value="mild" ${settings.weather === 'mild' ? 'selected' : ''}>Mild</option><option value="warm" ${settings.weather === 'warm' ? 'selected' : ''}>Warm</option><option value="hot" ${settings.weather === 'hot' ? 'selected' : ''}>Hot</option></select></label><label>Condition<select name="condition"><option value="unknown" ${(settings.condition || 'unknown') === 'unknown' ? 'selected' : ''}>Unknown</option><option value="sunny" ${settings.condition === 'sunny' ? 'selected' : ''}>Sunny</option><option value="cloudy" ${settings.condition === 'cloudy' ? 'selected' : ''}>Cloudy</option><option value="rainy" ${settings.condition === 'rainy' ? 'selected' : ''}>Rainy</option><option value="snowy" ${settings.condition === 'snowy' ? 'selected' : ''}>Snowy</option></select></label><label>Period mode<select name="period_mode"><option value="manual" ${(settings.period_mode || 'manual') === 'manual' ? 'selected' : ''}>Technician override</option><option value="auto" ${settings.period_mode === 'auto' ? 'selected' : ''}>Local clock (auto)</option></select></label><label>Time of day<select name="period"><option value="morning" ${settings.period === 'morning' ? 'selected' : ''}>Morning</option><option value="afternoon" ${settings.period === 'afternoon' ? 'selected' : ''}>Afternoon</option><option value="evening" ${settings.period === 'evening' ? 'selected' : ''}>Evening</option><option value="night" ${settings.period === 'night' ? 'selected' : ''}>Night</option></select></label><label>Email service<select name="email_ok"><option value="true" ${settings.email_ok ? 'selected' : ''}>Available</option><option value="false" ${!settings.email_ok ? 'selected' : ''}>Unavailable</option></select></label><button type="submit" class="primary">Apply</button></form></section>
      <section class="admin-band"><h2>Ingredient sensors</h2><div class="table-wrap"><table><thead><tr><th>Ingredient</th><th>Simulated level</th><th>Apply</th></tr></thead><tbody>${sensors}</tbody></table></div></section>
      <section class="admin-band"><h2>Waste sensors</h2>${wasteSensors}</section>
      <section class="admin-band"><h2>Machine fault <span class="pill ${settings.fault ? 'error' : ''}">${esc(settings.fault || 'No active fault')}</span></h2><div class="fault-controls"><button data-fault="GRINDER_JAM">Simulate grinder jam</button><button data-fault="HEATER_FAULT">Simulate heater fault</button><button data-fault=""><i data-lucide="check"></i>Clear fault</button></div></section>
    </div>`;
  setMaintenanceBusy(maintenanceBusy); icons();
}
/** Purpose: select login/registration/NFC/technician controls. Inputs: mode. Returns: void. */
function setAuthMode(mode) {
  authMode = mode;
  const form = $('#auth-form'); form.reset();
  $('#name-field').hidden = mode !== 'register'; $('#email-field').hidden = mode === 'nfc' || mode === 'technician'; $('#password-field').hidden = mode === 'nfc'; $('#nfc-field').hidden = mode !== 'nfc';
  $('#auth-title').textContent = mode === 'register' ? 'Create account' : mode === 'technician' ? 'Technician access' : 'Sign in';
  $('#auth-submit').textContent = mode === 'register' ? 'Create account' : mode === 'nfc' ? 'Simulate card tap' : 'Sign in';
  $('#password-field').firstChild.textContent = mode === 'technician' ? 'Technician PIN' : 'Password';
  form.elements.name.disabled = mode !== 'register'; form.elements.name.required = mode === 'register';
  form.elements.email.disabled = mode === 'nfc' || mode === 'technician';
  form.elements.password.disabled = mode === 'nfc'; form.elements.password.minLength = mode === 'register' ? 10 : 0;
  form.elements.password.autocomplete = mode === 'register' ? 'new-password' : 'current-password';
  form.elements.nfc.disabled = mode !== 'nfc'; form.elements.nfc.required = mode === 'nfc';
  $('#fill-demo').hidden = mode === 'register';
  $('#fill-demo span').textContent = mode === 'technician' ? 'Use demo technician' : mode === 'nfc' ? 'Use demo NFC card' : 'Use demo account';
  for (const button of document.querySelectorAll('[data-auth]')) button.classList.toggle('active', button.dataset.auth === mode);
  $('#auth-error').textContent = '';
}
/** Purpose: show current account or sign-in dialog. Inputs: optional mode. Returns: void. */
function openAuth(mode = 'login') {
  const signedIn = Boolean(state.user);
  $('#auth-fields').hidden = signedIn; $('#logout').hidden = !signedIn;
  $('#signed-in-info').textContent = signedIn ? `${state.user.name} · ${state.user.email} · ${state.user.role}` : '';
  setAuthMode(mode); $('#auth-dialog').showModal();
}
/** Purpose: prepare checkout with a stable idempotency key. Inputs: optional pending record. Returns: void. */
function openCheckout(pending = null) {
  if (!quote?.available) { toast('Choose an available recipe.'); return; }
  paymentKey = pending?.id || crypto.randomUUID();
  $('#payment-form').reset(); if (pending) { $('#payment-form').elements.method.value = pending.method; $('#payment-form').elements.points.value = pending.points; }
  $('#checkout-summary').innerHTML = `<strong>${esc(quote.name)}</strong><p>${esc(recipeDetails(quote.config))}</p>`;
  $('#points-balance').textContent = `(${state.user?.points || 0} available · 1 point = SEK 0.10)`;
  $('#payment-form').elements.points.disabled = state.user?.role !== 'customer';
  $('#payment-form').elements.points.max = Math.min(state.user?.points || 0, Math.floor(quote.price / 10));
  $('#payment-error').textContent = ''; updatePaymentTotal(); $('#checkout-dialog').showModal();
}
/** Purpose: calculate displayed loyalty discount. Inputs: points control/quote. Returns: void. */
function updatePaymentTotal() {
  const points = Number($('#payment-form').elements.points.value || 0);
  $('#payment-subtotal').textContent = money(quote.price); $('#payment-discount').textContent = money(points * 10);
  $('#payment-total').textContent = money(Math.max(0, quote.price - points * 10));
}
/** Purpose: show a completed order and real QR. Inputs: order object. Returns: void. */
function showReceipt(order) {
  activeOrder = order;
  $('#receipt-content').innerHTML = `<p><strong>#${order.id} · ${esc(order.recipe.name)}</strong></p><p>${esc(recipeDetails(order.recipe.config))}</p><p>Subtotal ${esc(money(order.amount))}<br>Discount ${esc(money(order.discount))}<br>Paid ${esc(money(order.paid))}</p><img src="/receipt/${encodeURIComponent(order.receipt)}/qr.svg" alt="QR containing purchase receipt"><p><a href="/receipt/${encodeURIComponent(order.receipt)}" target="_blank" rel="noopener">Open receipt</a></p>`;
  $('#receipt-message').textContent = 'The QR contains receipt text and can be scanned without a network connection.';
  $('#email-receipt').hidden = state.user?.role !== 'customer'; $('#receipt-dialog').showModal();
}
/** Purpose: select recipe name/save mode. Inputs: optional saved recipe. Returns: void. */
function openRecipeDialog(recipe = null) {
  if (state.user?.role !== 'customer') { openAuth(); return; }
  if (recipe) editingRecipe = recipe.id;
  $('#recipe-title').textContent = editingRecipe ? 'Update recipe' : 'Save recipe';
  $('#recipe-name').value = recipe?.name || (editingRecipe ? findRecipe(editingRecipe)?.name : '') || '';
  $('#recipe-error').textContent = ''; $('#recipe-dialog').showModal();
}
/** Purpose: prevent edits being replaced by an in-flight maintenance refresh. Inputs: busy flag. Returns: void. */
function setMaintenanceBusy(value) {
  maintenanceBusy = value;
  for (const control of document.querySelectorAll('#maintenance-content button, #maintenance-content input, #maintenance-content select')) control.disabled = value;
}
/** Purpose: execute one protected maintenance update and render its committed state. Inputs: action/data. Returns: Promise<void>. */
async function maintain(action, data) {
  if (maintenanceBusy) return;
  setMaintenanceBusy(true);
  try { await api('/api/admin/' + action, data); await refresh(); toast('Maintenance state updated.'); }
  finally { setMaintenanceBusy(false); }
}
/** Purpose: dispatch button navigation and item actions. Inputs: click event. Returns: Promise<void>. */
async function handleClick(event) {
  const button = event.target.closest('button'); if (!button) return;
  try {
    if (button.classList.contains('close-dialog')) { button.closest('dialog').close(); return; }
    if (button.dataset.view) { showView(button.dataset.view); return; }
    if (button.dataset.category) { category = button.dataset.category; for (const item of document.querySelectorAll('[data-category]')) item.classList.toggle('active', item === button); renderMenu(); return; }
    if (button.dataset.drink) {
      selected = button.dataset.drink; editingRecipe = null;
      if ($('#recommend-toggle').checked && recommendationStatus === 'ready') for (const entry of recommendations) if (entry.config.drink === selected) { applyConfig(entry.config); break; }
      renderMenu(); await updateQuote(); return;
    }
    if (button.dataset.adminTab) { adminTab = button.dataset.adminTab; renderMaintenance(); return; }
    if (button.dataset.auth) { setAuthMode(button.dataset.auth); return; }
    if (button.id === 'fill-demo') {
      const form = $('#auth-form');
      if (authMode === 'nfc') form.elements.nfc.value = 'DEMO-NFC-001';
      else if (authMode === 'technician') form.elements.password.value = '246810';
      else { form.elements.email.value = 'alex@smartbrew.test'; form.elements.password.value = 'DemoPass123!'; }
      return;
    }
    if (button.id === 'assistant-apply') { await applyAssistantRecipe(); return; }
    if (button.id === 'assistant-clear') { resetAssistant(); return; }
    if (button.id === 'account-button' || button.hasAttribute('data-open-auth')) { openAuth(); return; }
    if (button.hasAttribute('data-tech-login')) { openAuth('technician'); return; }
    if (button.id === 'logout') { await api('/api/auth/logout', {}); $('#auth-dialog').close(); await refresh(); return; }
    if (button.id === 'save-defaults') { if (state.user?.role !== 'customer') { openAuth(); return; } await api('/api/auth/profile', config()); await refresh(); toast('Default preferences saved.'); return; }
    if (button.id === 'checkout-button') { openCheckout(); return; }
    if (button.id === 'save-recipe') { openRecipeDialog(); return; }
    if (button.dataset.loadRecipe) { const recipe = findRecipe(button.dataset.loadRecipe); editingRecipe = recipe.id; applyConfig(recipe.config); showView('menu'); renderMenu(); await updateQuote(); return; }
    if (button.dataset.rename) { const recipe = findRecipe(button.dataset.rename); applyConfig(recipe.config); await updateQuote(); openRecipeDialog(recipe); return; }
    if (button.dataset.delete) { await api('/api/recipes/delete', { id: Number(button.dataset.delete) }); editingRecipe = null; await refresh(); toast('Recipe deleted.'); return; }
    if (button.dataset.receipt) { for (const order of state.orders) if (order.id === Number(button.dataset.receipt)) { showReceipt(order); break; } return; }
    if (button.dataset.pending) { for (const pending of state.pending) if (pending.id === button.dataset.pending) { applyConfig(JSON.parse(pending.config)); await updateQuote(); openCheckout(pending); break; } return; }
    if (button.id === 'email-receipt') { const result = await api('/api/email-receipt', { id: activeOrder.id, email: state.user.email }); $('#receipt-message').textContent = result.message; return; }
    if (button.dataset.refill) await maintain('refill', { ingredient: button.dataset.refill });
    if (button.dataset.stock) await maintain('stock', { ingredient: button.dataset.stock, level: Number($('#stock-' + button.dataset.stock).value) });
    if (button.dataset.waste) await maintain('waste', { bin: button.dataset.waste, level: Number($('#bin-' + button.dataset.waste).value) });
    if (button.dataset.empty) await maintain('empty', { bin: button.dataset.empty });
    if (button.hasAttribute('data-fault')) await maintain('fault', { fault: button.dataset.fault });
  } catch (error) { toast(error.message); }
}
/** Purpose: submit account/recipe/payment/context forms. Inputs: submit event. Returns: Promise<void>. */
async function handleSubmit(event) {
  event.preventDefault();
  const form = event.target, data = Object.fromEntries(new FormData(form));
  if (busyForms.has(form.id)) return;
  busyForms.add(form.id);
  const submitter = event.submitter; if (submitter) submitter.disabled = true;
  try {
    if (form.id === 'auth-form') {
      $('#auth-error').textContent = '';
      const body = authMode === 'nfc' ? { method: 'nfc', nfc: data.nfc } : authMode === 'technician' ? { method: 'password', email: 'tech@smartbrew.test', password: data.password } : authMode === 'register' ? { name: data.name, email: data.email, password: data.password } : { method: 'password', email: data.email, password: data.password };
      await api('/api/auth/' + (authMode === 'register' ? 'register' : 'login'), body); $('#auth-dialog').close(); await refresh();
      if (state.user.role === 'customer') { applyConfig(state.user.preferences); await updateQuote(); }
    } else if (form.id === 'recipe-form') {
      const body = { name: $('#recipe-name').value, config: config() }; if (editingRecipe) body.id = editingRecipe;
      const result = await api('/api/recipes/' + (editingRecipe ? 'update' : 'save'), body); editingRecipe = result.id; $('#recipe-dialog').close(); await refresh(); toast('Recipe saved.');
    } else if (form.id === 'payment-form') {
      $('#pay-button').disabled = true; $('#payment-error').textContent = '';
      const result = await api('/api/checkout', { config: config(), key: paymentKey, method: data.method, points: Number(data.points || 0) });
      $('#checkout-dialog').close(); await refresh();
      if (result.status === 'completed') showReceipt(result.order); else { showView('history'); toast(result.message); }
    } else if (form.id === 'context-form') await maintain('context', { network: data.network === 'true', weather: data.weather, condition: data.condition || 'unknown', period_mode: data.period_mode || 'manual', period: data.period, email_ok: data.email_ok === 'true' });
    else if (form.id === 'simulation-form') await maintain('simulation', { payment_mode: data.payment_mode });
    else if (form.id === 'assistant-form') await askAssistant(data.request);
  } catch (error) {
    const errorElement = form.id === 'auth-form' ? $('#auth-error') : form.id === 'payment-form' ? $('#payment-error') : form.id === 'recipe-form' ? $('#recipe-error') : null;
    if (errorElement) errorElement.textContent = error.message; else toast(error.message);
  } finally { busyForms.delete(form.id); if (submitter) submitter.disabled = false; $('#pay-button').disabled = false; }
}
/** Purpose: update interactive controls. Inputs: input event. Returns: Promise<void>. */
async function handleInput(event) { if (event.target.closest('#customize-form')) await updateQuote(); if (event.target.name === 'points') updatePaymentTotal(); }
/** Purpose: toggle recommendation order. Inputs: change event. Returns: void. */
function handleChange(event) { if (event.target.id === 'recommend-toggle') renderMenu(); }
/** Purpose: refresh identity when returning from another session tab. Inputs: browser focus event. Returns: Promise<void>. */
async function refreshOnFocus() { try { await refresh(); } catch (error) { toast(error.message); } }
/** Purpose: initialize handlers/state with recoverable errors. Inputs: DOM ready. Returns: Promise<void>. */
async function boot() {
  document.addEventListener('click', handleClick); document.addEventListener('submit', handleSubmit); document.addEventListener('input', handleInput); document.addEventListener('change', handleChange);
  window.addEventListener('focus', refreshOnFocus);
  checkAssistant();
  try { await refresh(); if (state.user?.role === 'customer') { applyConfig(state.user.preferences); await updateQuote(); } } catch (error) { toast(error.message); }
}
boot();
