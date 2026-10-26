# Architecture and Design Decisions

## Application Boundary

SmartBrew is one local Python application with a browser interface, SQLite storage and an optional local Ollama process. Customer and technician screens share the same application; role checks are enforced by the server, not by hiding buttons alone.

| Module | Responsibility |
| --- | --- |
| `app.py` | HTTP validation, session cookies, routing, static assets and generated QR receipts |
| `smartbrew/service.py` | Identity, ownership, recipe validation, stock/safety, ranking, checkout and maintenance |
| `smartbrew/assistant.py` | Local inference transport, bounded requests and independent validation of model proposals |
| `web/app.js` | Customer/technician workflows and rendering |
| `web/assistant.js` | In-page conversation, proposal review and explicit application to the customizer |
| `tests/` | Business-rule and adapter tests using temporary databases |
| `tools/` | Browser/live-model checks, exports and source inspection |

On Windows, `tools/start_smartbrew.ps1` coordinates startup: it starts/reuses local Ollama with already installed weights and then runs the Python server in the foreground. Missing optional AI produces a warning and leaves manual ordering available. `-SkipAI` skips preparation rather than disabling an already running assistant. The separate `tools/start_local_ai.ps1` performs one-time model download/warm-up; normal combined startup requests neither. Ollama remains running after SmartBrew exits for reuse by later launches. Direct Python and non-Windows launches still require a separately running Ollama when using the assistant.

## Identity and Ownership

Password sign-in sends only its method, email and password. NFC simulation is a separate explicit method; a request mixing the two is rejected. Registration sends only name, email and password. A successful account switch replaces the current session token. Passwords/PINs use per-credential salted PBKDF2 hashes; sessions store token hashes and expire after eight hours.

Private recipes, completed orders and pending requests are filtered by the authenticated owner's ID. Update/delete/email actions recheck ownership. Logout/account changes clear private UI, the current recipe/draft and any assistant conversation. Returning to a tab refreshes the session state. Different tabs within one browser profile share cookies; they are not independent users.

The original hidden-NFC defect caused password logins to select Alex. Correcting it does not retroactively transfer orders placed under Alex's identity to another account. Existing records retain their recorded owner; automatic reassignment would invent ownership.

## Ordering and Payment

The server validates recipe options, calculates money in integer ore and checks both minimum stock thresholds and the quantity required for a serving. Full waste bins or active faults block ordering. Checkout repeats those checks against current state rather than trusting a previously displayed quote.

A single SQLite write transaction commits the order snapshot, stock consumption, waste, prepaid balance and loyalty together. A request key and request signature make retries idempotent. A decline leaves these purchase values unchanged. The receipt/history use the purchase snapshot, not a later saved-recipe edit.

Customer requests cannot choose a payment outcome. Only a technician can change the persistent external-processor mode to Normal or Decline. That mode remains active until restored. Internal prepaid payment independently checks local balance; real card/wallet authorization is not connected.

With simulated network offline, prepaid can complete locally. Permitted online-only requests are recorded as pending without dispensing or charge. The customer retries after reconnect; authorization and stock are checked again before one completion.

## Technician Workspace

Maintenance contains operational tasks: record a refill, record a bin emptied, inspect events and export diagnostics. Test scenarios contains artificial conditions: sensor levels, full-bin readings, faults, network, outdoor temperature (`cold`, `mild`, `warm`, `hot`), weather condition (`unknown`, `sunny`, `cloudy`, `rainy`, `snowy`), period mode (`manual` technician override or `auto` local clock), time of day (`morning`, `afternoon`, `evening`, `night`), email availability and external payment response. Non-destructive schema checks add `condition` (default `unknown`) and `period_mode` (default `manual`) to `settings`. These are protected endpoints even if a customer manually constructs a request.

Demo credentials and NFC identifiers are public fixtures. This local demonstration is not a production access-control deployment or a real physical-key/NFC reader.

## Optional Language Model

The local model receives the supported menu/options, ingredient levels, current fault status and the current customer's preference settings. It does not receive passwords, email addresses, payment details or other users' histories. Conversation remains in page memory and is cleared on identity changes.

The adapter accepts only a loopback HTTP endpoint, bypasses system proxies and refuses HTTP redirects. The project-local runtime is started with cloud features disabled. Model output must match a bounded recipe/clarification schema: a primary configuration and at most two alternatives, each with a short reason. Unsupported options and extra fields such as price are rejected. All candidate prices/stock are calculated on the server after inference. Duplicate alternatives, unavailable alternatives and alternatives that change the interpreted milk/strength/temperature/syrup/extra settings are excluded. The primary unavailable quote can remain visible with its reason and a disabled action, rather than silently substituting another drink. No model output is executed as code or a database command.

Three recipe cards are requested for broad taste requests; exact named drinks, precise refinements or limited distinct available options may yield fewer. Choosing any card updates both the customizer and `context_config` for subsequent conversation. The compatibility `quote` response remains the primary recipe, while `suggestions` contains all validated choices. A narrowly matched strength-only command (for example "Make it mild") is merged with the validated active recipe to prevent an observed model switch from the chosen cappuccino to a latte; other free-form interpretation remains the LLM's responsibility. This guard is not claimed to understand arbitrary follow-ups. Inference still uses one local request, with `num_ctx=8192` and `num_predict=900` to accommodate the three-choice schema/output.

For a small set of explicit alternative requests (for example "What else do you have that fits that?"), the server removes the active base drink from the already validated model suggestions and promotes another available model-generated choice. It invents no replacement recipe. If the model proposed no different available option, the response explains that rather than repeating the active drink as an alternative. Negated or arbitrary free-form phrasing is outside this narrowly matched guard.

The customer must select Use recipe, review the customizer and separately confirm payment. Suggestions have no purchase side effects. Only one inference runs at a time; concurrent requests return a busy response. The server wait is bounded at 90 seconds to allow cold loading, with a slightly longer browser deadline. Manual ordering is independent of that wait.

The contextual recommendation ranking (`Store.recommendations`) is a deterministic, additive heuristic separate from the generic recipe defaults in `Store.config()`. Available candidates are quoted with the authenticated customer's preferences, unavailable drinks are excluded before ranking, and scores combine base points (`10`), time period (`morning`, `afternoon`, `evening`, `night` from either technician override or an injectable local clock), online-only outdoor temperature (`cold`, `mild`, `warm`, `hot`), online-only weather condition (`sunny`, `cloudy`, `rainy`, `snowy`; `unknown` adds `0` points and no reason), and customer-owned signals (milk/strength drink-category affinity, saved recipes at `+15`, and completed-order frequency at `+12` per order up to `+36` with reason `"A frequent choice"`). Offline mode zeroes out both temperature and weather-condition bonuses while retaining local period and customer signals. It is distinct from the actual local LLM that interprets free-form drink requests. Neither is camera mood analysis.

The assistant cards intentionally expose no technical score or confidence percentage. Their order comes from the model's recipe choices, not the F06 menu score. The F06 point rules above remain technical documentation and backlog rationale; they are not presented as numerical LLM confidence or added to the three-choice assistant's customer flow.

## Scope and Evidence

The ten selected feature groups are F01-F10. F11 is an optional implemented local drink assistant linked to FR-10; it does not replace one of the ten required groups. Camera inference remains deferred, so the application never captures facial images.

Unit adapter fixtures test validation and failure handling; they are not evidence of real model intelligence. `tools/check_local_ai.py`, `tools/check_assistant_conversations.py`, `tools/check_assistant_long_chat.py` and `tools/check_assistant_heldout_baseline.py` separately record actual inference, including failed baselines and clarifications found during development. Selected examples passing do not guarantee correct interpretation of every request. See QA_RESULTS.md for recorded runs and limits.
