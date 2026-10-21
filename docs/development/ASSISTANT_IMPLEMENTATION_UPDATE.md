# Assistant and Recommendation Implementation Update - 2026-10-21

## Status for the Student and Evaluators

Implemented locally on top of published commit `ee153a9` and subsequently verified. This document and the current source files supersede earlier handoff notes stating that the multi-turn assistant corrections and F06 recommendation improvements were only proposed.

Generic recipe defaults (`Store.config()`), menu options, accounts, payment rules and the live database (`data/smartbrew.sqlite3`) were not changed. Both the F11 local drink assistant and the F06 deterministic recommendation engine have now been updated and verified against isolated temporary databases.

## Contributions and Provenance

1. **Earlier web-chat Gemini proposal (before local IDE access):** The student used a separate Gemini web chat to draft initial recipe-context state, validation, taste guidance and multi-turn test ideas, and relayed that diff into the Codex session. That earlier web chat had no direct access to local repository files or test execution, and its exact model/version label was not recorded.
2. **Codex (`GPT-6.1 Sol`, student-confirmed selector label):** Reviewed and integrated the relayed web-chat design locally, added positive/clarification examples, added `tools/check_assistant_conversations.py` and `tools/check_assistant_long_chat.py`, corrected browser waits and assertions, and recorded the intermediate 30-unit-test / 50-browser-check snapshot.
3. **Google Antigravity (`Gemini 4 Argon Medium`):** After gaining direct local IDE access to the repository, **Gemini 4 Argon Medium** inspected the repository read-only, built and ran `tools/check_assistant_heldout_baseline.py` against isolated temporary databases, implemented and verified the focused F11 correction in `smartbrew/assistant.py`, specified and implemented the expanded deterministic F06 recommendation scoring in `smartbrew/service.py`, `web/app.js`, and `web/styles.css`, and extended the unit (`tests/test_service.py`) and browser (`tools/browser_check.cjs`) suites to **33 unit tests** and **58 browser checks**.
4. **Runtime drink model (`Qwen3:4b` through Ollama 0.40.6):** Local inference model used inside the SmartBrew prototype to interpret customer drink requests; it did not generate or edit the coursework.

This is an assistant-written implementation record, not a student-authored reflection or fabricated first-person experiment report.

## Key Files Involved

- `smartbrew/assistant.py` and `web/assistant.js`
- `smartbrew/service.py`, `web/app.js` and `web/styles.css`
- `tests/test_assistant.py` and `tests/test_service.py`
- `tools/check_assistant_conversations.py`, `tools/check_assistant_long_chat.py` and `tools/check_assistant_heldout_baseline.py` (the original four-case `tools/check_local_ai.py` remains unchanged)
- `tools/browser_check.cjs`
- `evidence/current/assistant-conversations.json`, `evidence/current/assistant-long-chat.json`, `evidence/history/assistant-heldout-baseline.json`, `evidence/history/assistant-heldout-postchange-first-run.json`, `evidence/current/assistant-heldout-postchange.json`, `evidence/history/browser-f06-first-run-failure.json` and `evidence/current/browser-results.json`

The README, documentation index, architecture notes, QA record, AI interaction record and document-generation sources (`tools/coursework_data.py`, `tools/build_documents.py`, `docs/LAB3_REPORT.md`, `docs/LAB3_AI_APPENDIX.md`) were also updated. Original Lab 1/2 submissions in `docs/baseline/` were not altered.

## Implemented Behavior

### F11 Local Drink Assistant
- Browser stores the latest recipe separately from the displayed actionable proposal, retains it across clarification/errors and clears it on conversation reset or identity changes.
- Request includes `context_config`. Server rejects missing/extra fields, unsupported values/types and invalid temperature steps before inference; no silent defaulting for context.
- Prompt encourages sensible taste-based proposals without unnecessary confirmation. It preserves unknown-usual clarification, unsupported-request handling and medical/allergy-safety limitations. The unsupported cocoa-is-caffeine-free rule was removed.
- All proposals still require independent pricing/availability validation and explicit customer application/checkout. No recipe context grants ownership or authorization.
- Latest validated recipe is supplied after the textual history as a structured trailing `system` context block (`current_proposal`) rather than a synthetic `assistant` turn, preventing placeholder text from leaking into model replies while ensuring older drinks do not supersede the active recipe.
- `RESPONSE_SCHEMA` orders `kind`, `config`, and `message` so structured recipe parameters are generated before prose, and prompt rules allow flavor-driven base-drink switches (`latte` -> `mocha`/`cocoa`), forbid silent substitution of unsupported iced/caramel requests, and preserve unrelated fields when explaining machine setting limits (`0..4` syrup shots, `50..90 C`).
- `aria-busy` indicates completion of browser response processing; tests wait for it rather than racing the next request against an HTTP response.

### F06 Context-Aware Recommendations
- Generic recipe defaults in `Store.config()` (`milk="dairy"`, `strength="regular"`, `temperature=70`, `syrup=0`, `extra=0`) remain unchanged; recommendation drink affinities are evaluated through separate deterministic lookup tables in `smartbrew/service.py`.
- Non-destructive SQLite migration adds `condition TEXT NOT NULL DEFAULT 'unknown'` and `period_mode TEXT NOT NULL DEFAULT 'manual'` to `settings`. Legacy callers that omit `condition` default to `'unknown'` (`0` points, no invented weather reason).
- Scoring combines base points (`10`), effective time period (`morning`, `afternoon`, `evening`, `night` from either `manual` technician override or `auto` injectable local clock), online-only outdoor temperature (`cold`, `mild`, `warm`, `hot`), online-only weather condition (`unknown`, `sunny`, `cloudy`, `rainy`, `snowy`), and customer-scoped personalization (milk/strength drink affinity, saved recipes at `+15`, and completed-order count at `+12` per order capped at `+36` for 3+ orders with reason `"A frequent choice"`).
- Night comfort scoring uses neutral wording (`"Late-hour comfort pick"`) with no caffeine, medical, health or sleep claims.
- Offline mode (`network = false`) zeroes out both temperature and weather-condition bonuses while preserving local period and customer-owned signals, and reports `"local history/preferences; weather unavailable"`.

## Actual Failures Found During Integration and Evaluation

1. Initial prompt-only changes still asked questions for explicit recipes and ordinary taste preferences. Negative-only examples biased the responses. Positive recipe examples improved the tested requests (`evidence/history/assistant-conversations-first-run.json`).
2. An unspecified addition was incorrectly rejected as unavailable. A clarification example distinguished missing information from unsupported ingredients (`evidence/history/assistant-conversations-second-run.json`).
3. Direct multi-turn tests passed, but browser history containing an older latte caused the model to modify that latte rather than the latest cappuccino (`evidence/history/browser-failure.json`). Codex initially addressed this with a synthetic `assistant` turn after history.
4. When **Gemini 4 Argon Medium** ran the 8-turn evaluation (`tools/check_assistant_heldout_baseline.py`), the pre-change baseline (`evidence/history/assistant-heldout-baseline.json`, **5/8 passed**) exposed four concrete defects: the synthetic `assistant` placeholder leaked verbatim into the reply on open-ended follow-up (`A3`), the model kept `drink="latte"` when asked for a chocolatey drink (`B2`), silently substituted a hot vanilla latte for an unsupported iced caramel latte (`C1`), and added unrequested `extra: 1` when asked for sweetness above the 4-shot syrup cap (`C2`).
5. Replacing the synthetic `assistant` turn with a structured trailing `system` message (`current_proposal`), ordering `config` before `message` in `RESPONSE_SCHEMA`, and adding explicit rules resolved `B2`, `C1`, and `C2` on the first post-change run (`evidence/history/assistant-heldout-postchange-first-run.json`, **7/8 passed**) and all **8/8 turns** after clarifying that alternative requests (`"what else"`) should return `kind="recipe"` (`evidence/current/assistant-heldout-postchange.json`, **8/8 passed**).
6. On the first run of the expanded 58-check browser suite, 7 of the 8 new F06 checks passed and the 8th check (`F06: manual ordering remains usable when weather context is unavailable`) failed because `page.waitForLoadState('networkidle')` resolved before `updateQuote()` finished re-enabling `#checkout-button`. The failure was preserved in `evidence/history/browser-f06-first-run-failure.json`, and awaiting quote readiness in `tools/browser_check.cjs` resolved the check (**58/58 passed** in `evidence/current/browser-results.json`).

No failed run is presented as a pass. Passing these cases does not establish universal conversational correctness; customer confirmation and independent server validation remain mandatory.

## Verified Final Results

- **33 unit tests passed** (`evidence/current/unit-tests.txt`; increased from the earlier 30-test Codex snapshot by adding 3 comprehensive F06 unit test methods). Adapter unit tests use explicitly mocked model output and do not prove linguistic ability.
- **58 browser checks passed** (`evidence/current/browser-results.json`; increased from the earlier 50-check Codex snapshot by adding 8 end-to-end F06 checks) using Chrome and an isolated server/database on port 8766 with `SMARTBREW_LIVE_AI=1`.
- **8/8 multi-turn regression turns passed** in `tools/check_assistant_heldout_baseline.py` (`evidence/current/assistant-heldout-postchange.json`), **12/12 turns passed** in `tools/check_assistant_conversations.py` (`evidence/current/assistant-conversations.json`), and **9/9 recipe turns passed** in `tools/check_assistant_long_chat.py` (`evidence/current/assistant-long-chat.json`), all using isolated temporary databases with zero persistent side effects.

### Follow-up: Generic / Repeated Wording Observation

The student earlier reported replies such as "A strong coffee with no milk and a little sweetness" for "I want something sweet but also bitter." An isolated nine-turn real-model reproduction (`tools/check_assistant_long_chat.py` / `evidence/current/assistant-long-chat.json`) switched between Americano, latte, cocoa, cappuccino and espresso accurately without resetting the page. Recipe assertions (`passed: true`) and prose quality (`wordingChecksPassed: false`) are recorded separately: a generic first-turn reply that omitted the drink name is retained as a documented wording limitation (`evidence/history/assistant-long-chat-wording-failure.json`), not relabeled as solved.

## Current Status

Both the F11 multi-turn assistant correction and the F06 deterministic recommendation expansion are implemented, verified, and reflected in the editable documentation sources. The circular-arrow button clears the in-page assistant conversation without reloading, and Technician > Test scenarios exposes all supported `network`, `weather` (`cold`, `mild`, `warm`, `hot`), `condition` (`unknown`, `sunny`, `cloudy`, `rainy`, `snowy`), `period_mode` (`manual`, `auto`), `period` (`morning`, `afternoon`, `evening`, `night`) and `email_ok` controls.
