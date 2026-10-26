/* Optional local inference is independent of the manual ordering workflow. */
let assistantHistory = [], assistantProposal = null, assistantSuggestions = [], assistantContextConfig = null, assistantRevision = 0, assistantController = null;

/** Purpose: discard conversation/proposals on logout or explicit reset. Inputs: current assistant UI. Returns: void. */
function resetAssistant() {
  assistantRevision++; assistantController?.abort(); assistantController = null;
  assistantHistory = []; assistantProposal = null; assistantSuggestions = []; assistantContextConfig = null;
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
  assistantController = new AbortController(); assistantProposal = null; assistantSuggestions = [];
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
      assistantSuggestions = response.suggestions || [{ quote: response.quote, message: response.message }];
      html = `<div class="assistant-options-heading"><h3>${assistantSuggestions.length === 1 ? 'Your recipe' : `${assistantSuggestions.length} recipes to try`}</h3><p class="muted">Choose a recipe to review before checkout.</p></div><div class="assistant-options">`;
      for (let index = 0; index < assistantSuggestions.length; index++) html += assistantOptionCard(assistantSuggestions[index], index);
      html += '</div><p class="assistant-refine-hint muted">To refine a different option, choose Use recipe first.</p>';
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

/** Purpose: render one server-validated recipe without exposing technical scores. Inputs: suggestion and zero-based option index. Returns: escaped card HTML. */
function assistantOptionCard(suggestion, index) {
  const value = suggestion.quote;
  return `<article class="assistant-option ${index === 0 ? 'is-active' : ''}" data-assistant-option="${index}"><div class="assistant-option-title"><span class="eyebrow">OPTION ${index + 1}</span><strong>${esc(money(value.price))}</strong></div><h4>${esc(value.name)}</h4><p>${esc(suggestion.message)}</p><p class="muted">${esc(recipeDetails(value.config))}</p><p class="${value.available ? 'muted' : 'form-error'}">${value.available ? 'Ingredients available' : esc(value.reasons.join(' · '))}</p><p class="assistant-active-hint muted" ${index === 0 ? '' : 'hidden'}>Current recipe for further changes</p><button ${index === 0 ? 'id="assistant-apply"' : ''} data-assistant-apply="${index}" aria-label="Use ${esc(value.name)} recipe option ${index + 1}" ${value.available ? '' : 'disabled'}><i data-lucide="check"></i>Use recipe</button></article>`;
}

/** Purpose: apply one option and make it the active conversation recipe. Inputs: zero-based suggestion index. Returns: Promise<void>. */
async function applyAssistantRecipe(index = 0) {
  const proposal = assistantSuggestions[index]?.quote;
  if (!Number.isInteger(index) || !proposal?.available) return;
  assistantProposal = proposal; assistantContextConfig = { ...proposal.config };
  applyConfig(proposal.config); editingRecipe = null; category = 'All';
  for (const button of document.querySelectorAll('[data-category]')) button.classList.toggle('active', button.dataset.category === 'All');
  $('#recommend-toggle').checked = false; renderMenu(); await updateQuote();
  for (const card of document.querySelectorAll('[data-assistant-option]')) {
    const active = Number(card.dataset.assistantOption) === index;
    card.classList.toggle('is-active', active);
    card.querySelector('.assistant-active-hint').hidden = !active;
  }
  $('#customize-form [name=milk]').focus();
  toast('Recipe applied. Review your drink before checkout.');
}
