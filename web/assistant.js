/* Optional local inference is independent of the manual ordering workflow. */
let assistantHistory = [], assistantProposal = null, assistantContextConfig = null, assistantRevision = 0, assistantController = null;

/** Purpose: discard conversation/proposals on logout or explicit reset. Inputs: current assistant UI. Returns: void. */
function resetAssistant() {
  assistantRevision++; assistantController?.abort(); assistantController = null;
  assistantHistory = []; assistantProposal = null; assistantContextConfig = null;
  document.getElementById('assistant-result').replaceChildren();
  document.getElementById('assistant-result').setAttribute('aria-busy', 'false');
  document.getElementById('assistant-request').value = '';
}

/** Purpose: display local model availability without blocking ordering. Inputs: local status endpoint. Returns: Promise<void>. */
async function checkAssistant() {
  try {
    const result = await api('/api/assistant/status', undefined, 2000);
    $('#assistant-status').textContent = result.available ? `${result.model} · Local` : 'Local model unavailable';
  } catch (error) { $('#assistant-status').textContent = 'Local model unavailable'; }
}

/** Purpose: request a validated recipe or clarification from the local model. Inputs: customer text. Returns: Promise<void>. */
async function askAssistant(request) {
  const message = request.trim(); if (!message) return;
  const revision = ++assistantRevision;
  const context_config = assistantContextConfig;
  assistantController = new AbortController(); assistantProposal = null;
  $('#assistant-result').setAttribute('aria-busy', 'true');
  $('#assistant-result').textContent = 'Thinking…';
  try {
    const signal = AbortSignal.any([assistantController.signal, AbortSignal.timeout(95000)]);
    const response = await api('/api/assistant', { message, history: assistantHistory.slice(-6), context_config }, null, signal);
    if (revision !== assistantRevision) return;
    assistantHistory.push({ role: 'user', content: message }, { role: 'assistant', content: response.message });
    $('#assistant-status').textContent = `${response.model} · Local`;
    $('#assistant-request').value = '';
    let html = `<p>${esc(response.message)}</p>`;
    if (response.quote) {
      assistantProposal = response.quote;
      assistantContextConfig = { ...response.quote.config };
      html += `<div class="assistant-proposal"><div><strong>${esc(response.quote.name)} · ${esc(money(response.quote.price))}</strong><p>${esc(recipeDetails(response.quote.config))}</p><p class="${response.quote.available ? 'muted' : 'form-error'}">${response.quote.available ? 'Ingredients available' : esc(response.quote.reasons.join(' · '))}</p></div><button id="assistant-apply" ${response.quote.available ? '' : 'disabled'}><i data-lucide="check"></i>Use recipe</button></div>`;
    }
    $('#assistant-result').innerHTML = html; icons();
  } catch (error) {
    if (revision !== assistantRevision) return;
    $('#assistant-result').textContent = error.name === 'TimeoutError' ? 'The local model took too long. Manual ordering is still available.' : error.message;
  } finally {
    if (revision === assistantRevision) {
      assistantController = null;
      $('#assistant-result').setAttribute('aria-busy', 'false');
    }
  }
}

/** Purpose: apply a proposal only after explicit customer confirmation. Inputs: last validated proposal. Returns: Promise<void>. */
async function applyAssistantRecipe() {
  if (!assistantProposal?.available) return;
  applyConfig(assistantProposal.config); editingRecipe = null; category = 'All';
  for (const button of document.querySelectorAll('[data-category]')) button.classList.toggle('active', button.dataset.category === 'All');
  $('#recommend-toggle').checked = false; renderMenu(); await updateQuote();
  $('#customize-form [name=milk]').focus();
  toast('Recipe applied. Review your drink before checkout.');
}
