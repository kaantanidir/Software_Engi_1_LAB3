# Verification record

Session: 20-21 October 2026, Europe/Berlin. These are observed simulator results, not claims of real appliance, financial processor, SMTP or AI-module certification.

## Automated Business Rules

Command: `python -m unittest discover -s tests -v`.

Final result: **16 tests passed**, 10.774 seconds, Python 3.12.14. Full output: `evidence/unit-tests.txt`.

Coverage includes all ten selected feature groups: registration/password/NFC/default persistence; category/nutrition data; custom price/option validation; owned recipe CRUD; threshold and quantity checks; contextual/history ranking; all payment simulators; immutable snapshots; decline rollback; insufficient prepaid balance; concurrent idempotency; bounded/full loyalty redemption; receipt/outbox/fallback; protected refills/waste/fault diagnostics; offline pending/reconciliation.

Tests use independent databases below `tmp/tests` and do not consume demo stock. The pending-payment regression includes **100 loyalty points** and verifies the value is retained. Full redemption also verifies a zero-total purchase earns no new points.

## Browser Walkthrough

Command: `npm run test:browser`, with the Python and Chrome executable paths configured for the local machine. This starts its own QA server on 8766 with isolated data and shuts it down afterward.

Final result: **23 checks passed**, no uncaught browser exceptions. Tested Chrome **155.0.8059.41**, Node **24.19.0**, Playwright **1.62.1**, on Windows. Machine-readable results: `evidence/browser-results.json`.

- Desktop viewport: **1440 x 1000**.
- Mobile viewport: **390 x 844**, root content width **390**: no horizontal page overflow.
- All six displayed menu image elements loaded local assets.
- 100 sequential state/menu requests: **p95 15.74 ms**.
- 100 sequential quote requests: **p95 12.13 ms**.
- The numerical 2-second response target is a proposed design criterion, not a value specified by the assignment. These local sequential measurements are not load-test or production SLA claims.

Browser steps exercise filtering, customer authentication, live customization, recipe save/rename/restore, loyalty checkout, generated QR and email outbox, decline/no duplicate history, technician authentication/counters, ingredient blocking, full-bin halt/empty, fault logging, offline recommendations/prepaid/pending wallet, reconnect/retry and HTTP role enforcement. The offline retry retains the requested loyalty redemption.

Screenshots: `evidence/desktop.png`, `mobile.png`, `maintenance.png`, `receipt.png`. Transient success notifications can be visible in screenshots. Actual camera inference, local LLM execution, EMV hardware, real external payment/email and remote-diagnostic deployment are outside the implemented feature set.

## Astah and Documents

- Used installed **Astah Professional 12.0.0** API, not string matching in `EntityStore`.
- Saved a separate corrected `.asta`; Astah model validation succeeded.
- Audited all 13 use cases and their five textual fields in the model, plus use-case relationships. Reopened/exported the saved result with Astah's command-line exporter.
- Main diagram exported to `evidence/use-cases.png`; native use-case description exports are under `evidence/astah-export`.
- The native template's computed actor row is populated by direct associations. Indirect actors for included/extension use cases are explicitly recorded in the model Definition and Markdown descriptions; the README explains the native template behavior.
- Both PDFs were generated from the same structured data as the editable Markdown, rendered with Poppler and reviewed as images for wrapping, page splits and clipping. `evidence/artifact-checks.json` records source coverage, original baseline hash checks and function-documentation checks.
- Original baseline files are preserved byte-for-byte; SHA-256 values are in `docs/baseline/manifest.json`.
- Git attributes explicitly preserve PDF, Astah, ZIP and image bytes, while normalizing source text. This prevents Windows newline conversion from altering binary deliverables when cloned.

## Limits and Student Review

The comparison truthfully discloses earlier AI assistance in Lab 2. The source does not supply loyalty conversion rates, exact nutrition/stock quantities, a latency target or opt-in UI; these are documented proposals/fixtures. The optional local LLM and camera privacy requirements are present in the elicitation but deferred, not falsely marked as tested.

The students still need to understand the code, review the proposed design decisions and add any subsequent personal evaluation. No student reading completion or independent human-authored baseline is asserted.
