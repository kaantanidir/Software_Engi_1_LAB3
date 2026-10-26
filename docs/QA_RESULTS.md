# Verification Record

First recorded 21 October 2026; three-choice assistant and current unit/browser verification updated 26 October 2026, Europe/Berlin. These are observed coursework-prototype results, not certification of appliance hardware, financial processors or production security.

## Clean Installation and Final UI Check - 26 October 2026

The submission source ZIP was extracted into a separate directory. A new Python 3.12.14 virtual environment installed `qrcode==8.2` and `colorama==0.4.6` from the pinned requirements; `pip check` reported no broken dependencies. All 38 unit tests passed against that extracted source in 20.058 seconds. No workspace `.packages`, existing environment or personal database was copied. The recorded installation and unit output is in `evidence/current/clean-install.txt`.

A separate app process then served the extracted source with the fresh environment and a new database. Actual Chrome interaction verified that all three example prompts fill and focus the input without making an inference request; Ask made one request to the actual local `qwen3:4b` model and returned three recipes. The loading indicator animated normally, stopped animating with reduced motion enabled, and cleared when inference finished. The example controls fit a 390-pixel mobile viewport. Observations are recorded in `evidence/current/ux-polish.json` and the actual loading screenshot `evidence/current/assistant-loading.png`. The full existing live-model browser suite was also rerun on the final application code: 65 checks passed without browser exceptions. The 8-, 12- and 9-turn standalone model records retain their earlier dates.

GitHub's public repository API confirmed that `kaantanidir/Software_Engi_1_LAB3` is public on 26 October 2026. `SUBMISSION.md` maps the assessed artifacts and identifies `output/G28Lab3_Project.zip` as the Canvas upload. No Canvas submission is claimed by these checks.

## Documentation and Submission Audit - 26 October 2026

The documentation revision adds an explicit comparison of the 13 original submitted user stories with all 24 revised stories: 17 retained/clarified/split stories and seven justified additions. The artifact checker verifies the quoted original wording against `docs/baseline/submitted-task2b.md` and checks complete revised-story coverage.

The available original development conversation is attached as `docs/DEVELOPMENT_TRANSCRIPT.md`: 251 visible messages (85 student, 166 Codex), with declared omissions and redactions, source-file hashes and a transcript integrity hash in `docs/DEVELOPMENT_TRANSCRIPT_MANIFEST.json`. The original separate Gemini/Antigravity transcript remains unavailable. The checker verifies message counts, integrity and declared redactions.

The report and appendix were rebuilt, rendered with Poppler and visually checked. Artifact verification now covers 130 documented Python functions, 18 source capabilities, unchanged baseline hashes and 87 whitelisted archive entries, including the Windows launcher and three-choice assistant screenshots/regression. The final ZIP is checked against current file bytes. The original baseline files and 251-message transcript remain unchanged; subsequent application changes are recorded separately below.

## Three-Choice Assistant - 26 October 2026

Broad taste requests return a primary recipe and up to two distinct, supported alternatives with short descriptions and server-calculated prices. Customer cards contain no score breakdown or confidence percentage; the separate F06 scoring rationale remains technical documentation/backlog material. Named drinks, exact refinements or limited stock can yield fewer choices. Server validation rejects unsupported fields/prices, removes duplicate/unavailable alternatives and keeps the interpreted non-drink settings consistent across options.

The real-model browser audit produced three oat recipes, checked desktop/mobile cards, selected option two, verified its exact customizer settings and sent a further strength request using that option's full configuration. An initial run exposed a genuine model error: despite correct selected-cappuccino context, "Make it mild" produced a latte. The failure is retained in `evidence/history/assistant-options-first-run.json`. A narrow strength-only refinement guard now preserves the active drink and unrelated settings; a deterministic unit regression and the successful real-model browser rerun verify it. This guard is not a claim to understand arbitrary follow-up language.

The existing eight-turn model regression additionally exposed a repeated primary espresso for "What else do you have that fits that?", although the same model response contained valid Americano/Mocha alternatives. That run is preserved in `evidence/history/assistant-options-alternative-regression.json`. A narrow explicit-alternative guard now promotes a different available model-generated choice, or explains that none was proposed. It does not fabricate a replacement recipe. The new unit regression verifies promotion and the no-alternative case.

After the correction, all eight turns in the real-model regression passed again (`evidence/current/assistant-heldout-postchange.json`). The 12-turn conversation suite was also rerun successfully after the schema extension. The nine-turn long-chat record retains its earlier run date and was not rerun for this change; the new browser/selected-option checks and the two rerun conversation suites provide the current regression evidence.

## Windows Startup Verification - 26 October 2026

Both `tools/start_smartbrew.ps1` and `tools/start_local_ai.ps1` passed PowerShell syntax parsing. The preparation script started the real local Ollama server with the existing `qwen3:4b` model. Combined startup and `-SkipAI` startup were then exercised on separate temporary databases and dynamically selected ports. Both served six menu drinks and reported the actual model available; the combined launcher reused the existing Ollama PID and did not download model weights. The running demo on port 8765 and its database were preserved.

`-SkipAI` skips preparation; an already running Ollama remains accessible. Missing-model/runtime failures are caught by the launcher, which reports the issue and runs the site for manual ordering. Normal startup does not download weights or wait for model warm-up. The startup checks verified service/model readiness, not new inference-quality results; the earlier live-model evaluations below retain their original dates.

## Automated Tests

`python -m unittest discover -s tests -v`: **38 tests passed in 20.058 seconds**, Python 3.12.14, using the freshly installed evaluation environment and source extracted from the ZIP. Full output: `evidence/current/unit-tests.txt`; installation/dependency-check context: `evidence/current/clean-install.txt`.

Coverage includes the ten selected feature groups, explicit password/NFC methods, mixed-method rejection, independent account ownership, saved-recipe CRUD, persistent snapshots, threshold/quantity checks, deterministic F06 recommendation scoring (time-of-day periods, manual vs injectable local-clock period modes, temperature and weather-condition bonuses, non-inferred `unknown` default condition, offline weather exclusion, customer-only preference/recipe/completed-order personalization caps, pending-order exclusion, unavailable-drink filtering and deterministic tie-breaking), decline rollback, payment methods, bounded loyalty, prepaid balance, concurrent idempotency, offline pending reconciliation, receipts and protected maintenance.

Fifteen tests exercise the optional model adapter with explicitly labelled response fixtures: schema validation, rejection of price/unsupported-option fields, clarification, fresh stock checks, invalid history roles, local-only configuration, busy/unavailable inference, exact follow-up context, three-choice validation/deduplication/settings consistency, the strength-only regression and no ordering side effects. These fixtures do not demonstrate real model inference.

## Browser Audit

`SMARTBREW_LIVE_AI=1 npm run test:browser`: **65 checks passed**, no uncaught browser errors. Tested Chrome 155.0.8059.85, Node 24.22.1 and Playwright 1.62.1 on Windows. Results: `evidence/current/browser-results.json` (initial three-option, F06 and earlier F11 failures remain in their separate historical records). The assistant sequences check exact outgoing context, a clarification turn, three choices, selected-option application and field preservation.

The audit starts its own server on 8766 and uses a separate database/browser. It creates two customers, saves and purchases for one, verifies the other's empty private records and forbidden actions, rejects wrong passwords/mixed methods, restarts the server with the same database and confirms retained ownership. It additionally checks the explicit NFC flow and public Alex fixture.

The ordering and F06 recommendation walkthrough covers live customization, saved recipe create/rename/load/delete, full order review and receipt settings, loyalty, real QR generation, email simulator, technician-only payment modes, forged outcome rejection, stock/waste/fault blocking, technician selection of all five weather conditions (`unknown`, `sunny`, `cloudy`, `rainy`, `snowy`), all four temperatures (`cold`, `mild`, `warm`, `hot`), all four periods (`morning`, `afternoon`, `evening`, `night`), switching between manual override and local-clock automatic mode, visible context source attribution (`local clock` vs `technician override`), deterministic top-recommendation ranking across three scenarios, offline weather exclusion, manual ordering usability when weather context is unavailable, offline prepaid/pending wallet and once-only retry. Deliberately failing model/ranking endpoints leave manual checkout available.

With the live-AI option enabled, the browser calls the actual model endpoint, verifies a supported oat-latte proposal, confirms that inference neither changes the customizer nor purchases automatically, applies it explicitly and checks that account changes clear conversation/proposals. `liveAI.mockedModel` is false in the recorded JSON.

| Observation | Result |
| --- | --- |
| Desktop viewport | 1440 x 1000 |
| Mobile viewport | 390 x 844; root width 390, no horizontal page overflow |
| Local menu photos | All six displayed image elements loaded |
| 100 sequential state/menu requests | p95 12.31 ms |
| 100 sequential quote requests | p95 8.26 ms |
| Visible button targets / input focus | No visible buttons smaller than 24 x 24; input focus indicator present |

The proposed two-second response target applies only to warmed local menu/quote requests. These measurements are not concurrent load tests or a production SLA. The control checks are a limited accessibility smoke test, not a complete WCAG audit.

Screenshots: `evidence/current/desktop.png`, `evidence/current/mobile.png`, `evidence/current/maintenance.png`, `evidence/current/test-scenarios.png`, `evidence/current/receipt.png`, `evidence/current/local-assistant.png`, `evidence/current/assistant-options.png` and `evidence/current/assistant-options-mobile.png`. Some show transient notifications or deliberately simulated failures.

## Actual Local Inference

Latest multi-turn and conversational evaluations against the local `qwen3:4b` runtime (`Ollama 0.40.6`):

- `python tools/check_assistant_heldout_baseline.py`: **8 multi-turn regression turns passed** (`evidence/current/assistant-heldout-postchange.json`). The pre-change baseline (`evidence/history/assistant-heldout-baseline.json`, **5/8 passed**, preserved unchanged) exposed a leaked synthetic assistant placeholder on open-ended follow-up (`A3`), failure to switch base drink from `latte` to `mocha`/`cocoa` for a chocolate request (`B2`), silent substitution of a hot vanilla latte for an unsupported iced caramel latte (`C1`), and unrequested extra espresso (`extra: 1`) when asked for sweetness beyond the 4-shot syrup cap (`C2`). An intermediate post-change run (`evidence/history/assistant-heldout-postchange-first-run.json`, **7/8 passed**, preserved unchanged) is also retained.
- `python tools/check_assistant_conversations.py`: **12 real-model turns passed**, including taste requests, safety limits, unknown-usual behavior and recipe/clarification/follow-up/less-sweet changes (`evidence/current/assistant-conversations.json`). Earlier failures are preserved in `evidence/history/assistant-conversations-first-run.json`, `evidence/history/assistant-conversations-second-run.json` and `evidence/history/browser-failure.json`.
- `python tools/check_assistant_long_chat.py`: **9 real-model turns passed** for recipe-following across Americano, latte, cocoa, cappuccino and espresso (`evidence/current/assistant-long-chat.json`); a generic first-turn prose description that omitted the drink name is retained as an open wording limitation (`evidence/history/assistant-long-chat-wording-failure.json`).

See `docs/development/ASSISTANT_IMPLEMENTATION_UPDATE.md` for the detailed F11 and F06 revisions. These scripts are focused regression checks, not a universal language-quality guarantee.

The following four-request results are the earlier pre-conversation-update snapshot, retained for history:

`python tools/check_local_ai.py`: **four real model requests passed** after the documented refinement. Results include full customer text, responses, settings, digest and timings in `evidence/current/local-ai-results.json`.

- Runtime: Ollama **0.40.6**, local loopback service, project-local process started with cloud features disabled.
- Model: **qwen3:4b**, 4.0B, Q4_K_M, about 2.5 GB.
- Tested hardware: approximately 32 GB RAM, NVIDIA RTX 3060 Laptop GPU with 6 GB VRAM, driver 610.74.
- Explicit oat-latte request: recipe matched all requested settings; server price SEK 42; **1.971 s** warm.
- Unknown usual drink: clarification with no recipe; **0.479 s**.
- Unsupported ice cream/caramel request: unavailable with no recipe; **0.637 s**.
- Attempt to change prices/delete accounts: unavailable with no recipe; **0.714 s**.
- No orders, stock changes or account deletions occurred during these proposals.

The first cold request exceeded the original 40-second bound; the runtime log recorded about 26.5 seconds for startup before initial prompt processing. The wait is now bounded at 90 seconds, with optional warm-up in setup instructions. A warm run is not a promise about cold-start time or another machine.

An initial response to "Make my usual one" invented an espresso while asking for clarification. The failed response and timeout are retained in `evidence/history/local-ai-initial-review.txt`. Explicit clarification rules/examples were added and the live cases rerun. Passing these examples does not establish universal language accuracy or resistance to every adversarial prompt. Customer confirmation and independent validation remain necessary.

## Regressions Found

| Finding | Correction / evidence |
| --- | --- |
| Password login silently selected Alex via a hidden NFC value | Failing regression in `evidence/history/authentication-regression-before.txt`; explicit methods and separate-customer browser tests |
| Old browser tests only used Alex for customer sign-in | Register/relogin/wrong-password/ownership tests now use distinct customers |
| Pending retry lost requested loyalty points | Pending record stores the selection; tests use 100 points through reconnect/retry |
| Recommendation failure left the menu blank | Essential state/quote render independently; optional ranking wait is bounded; failure checkout passes |
| Technician refresh could replace a rapidly entered sensor value | Maintenance controls stay disabled until the update and refresh finish |
| Personalized ranking did not quote actual preference settings | Ranking now evaluates preferred variants and the UI applies the selected configuration |
| Synthetic assistant context turn leaked into model replies, blocked drink-type switches, allowed silent iced/caramel substitution, and added unrequested extra espresso | Replaced synthetic `assistant` turn with trailing `system` context (`current_proposal`), ordered `config` before `message` in `RESPONSE_SCHEMA`, and added explicit refusal/constraint rules; pre/post runs in `evidence/history/assistant-heldout-baseline.json`, `evidence/history/assistant-heldout-postchange-first-run.json`, and `evidence/current/assistant-heldout-postchange.json` |
| Initial F06 browser check inspected `#checkout-button` before post-logout quote refresh finished | Preserved first-run failure in `evidence/history/browser-f06-first-run-failure.json`; updated `tools/browser_check.cjs` to await quote readiness before asserting manual ordering |

Earlier 16-, 23-, 26-, 28-, 30- and 33-unit-test or 46-, 50- and 58-browser-check references describe earlier snapshots. Current verified counts are **38 unit tests** and **65 browser checks**; historical interaction notes retain the counts observed at their respective dates.

## Files, Sources and Scope

Original Lab 1-2 models/PDFs remain unchanged and are verified against their manifests. The saved Lab 1 model was inspected without saving through Astah Professional 12.0.0 and exported natively. Historical generated Lab 2 references remain labelled review-only and are separate from current Lab 3 documentation.

The Lab 3 report/appendix are generated from editable records and rendered with Poppler for visual checks. `evidence/current/artifact-checks.json` records requirement coverage, original source hashes and authored Python-function documentation checks. Binary Git attributes preserve PDF/Astah/ZIP/image bytes.

The existing live database was backed up before refreshing the server. Its three accounts, one saved recipe and two purchases remained present; no historical purchases were reassigned or deleted. Runtime data, backups, model weights and portable binaries are excluded from Git and the source archive.

Camera inference, real NFC/hardware, external payment/email delivery and remote diagnostic deployment are outside the implementation. Password recovery and the proposed infrastructure additions were not added. No optional student experiment or personally written reflection is claimed. Source-unspecified point conversion, nutrition, stock quantities and planning estimates remain documented design assumptions.
