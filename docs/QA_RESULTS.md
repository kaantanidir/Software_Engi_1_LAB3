# Verification record

Session: 20-21 October 2026, Europe/Berlin. These are observed simulator results, not claims of real appliance, financial processor, SMTP or AI-module certification.

## Automated Business Rules

Command: `python -m unittest discover -s tests -v`.

Latest rerun: **16 tests passed**, 7.736 seconds, Python 3.12.14. The original successful run's full output remains in `evidence/unit-tests.txt`; this follow-up changed only the UI and coursework documentation.

Coverage includes all ten selected feature groups: registration/password/NFC/default persistence; category/nutrition data; custom price/option validation; owned recipe CRUD; threshold and quantity checks; contextual/history ranking; all payment simulators; immutable snapshots; decline rollback; insufficient prepaid balance; concurrent idempotency; bounded/full loyalty redemption; receipt/outbox/fallback; protected refills/waste/fault diagnostics; offline pending/reconciliation.

Tests use independent databases below `tmp/tests` and do not consume demo stock. The pending-payment regression includes **100 loyalty points** and verifies the value is retained. Full redemption also verifies a zero-total purchase earns no new points.

## Browser Walkthrough

Command: `npm run test:browser`, with the Python and Chrome executable paths configured for the local machine. This starts its own QA server on 8766 with isolated data and shuts it down afterward.

Latest result: **26 checks passed**, no uncaught browser exceptions. Tested Chrome **155.0.8059.41**, Node **24.19.0**, Playwright **1.62.1**, on Windows. Machine-readable results: `evidence/browser-results.json`.

- Desktop viewport: **1440 x 1000**.
- Mobile viewport: **390 x 844**, root content width **390**: no horizontal page overflow.
- All six displayed menu image elements loaded local assets.
- 100 sequential state/menu requests: **p95 26.66 ms**.
- 100 sequential quote requests: **p95 19.34 ms**.
- The numerical 2-second response target is a proposed design criterion, not a value specified by the assignment. These local sequential measurements are not load-test or production SLA claims.

Browser steps exercise filtering, customer authentication, live customization, recipe save/rename/restore, loyalty checkout, generated QR and email outbox, decline/no duplicate history, technician authentication/counters, ingredient blocking, full-bin halt/empty, fault logging, offline recommendations/prepaid/pending wallet, reconnect/retry and HTTP role enforcement. The offline retry retains the requested loyalty redemption.

The Lab 1 feedback prompted an additional normal service-failure regression. Before the fix, a QA-browser HTTP 503 response from `/api/recommendations` left the menu empty; the new assertion failed (`evidence/recommendation-regression-before.txt`). After rendering essential state/quote first and bounding optional ranking to 1.2 seconds, all six menu items remain usable, recommended mode falls back, and manual checkout completes. The three new checks pass. This is not a claimed student-performed optional mutation experiment, and it removes none of the ten features. The 503 path is browser-tested; the 1.2-second timeout is an implementation bound, not a measured performance result in that test.

Screenshots: `evidence/desktop.png`, `mobile.png`, `maintenance.png`, `receipt.png`. Transient success notifications can be visible in screenshots. Actual camera inference, local LLM execution, EMV hardware, real external payment/email and remote-diagnostic deployment are outside the implemented feature set.

## Astah and Documents

- Used installed **Astah Professional 12.0.0** API, not string matching in `EntityStore`.
- Saved a separate AI-generated reference `.asta`; Astah model validation succeeded. After the general course rules were supplied, it was labeled review-only, not for Lab 2 submission.
- Audited all 13 use cases and their five textual fields in the model, plus use-case relationships. Reopened/exported the saved result with Astah's command-line exporter.
- Main diagram exported to `evidence/use-cases.png`; native use-case description exports are under `evidence/astah-export`.
- The native template's computed actor row is populated by direct associations. Indirect actors for included/extension use cases are explicitly recorded in the model Definition and Markdown descriptions; the README explains the native template behavior.
- The Lab 2 reference, Lab 3 report and separate Lab 3 AI appendix PDFs were generated from their editable records, rendered with Poppler and reviewed as images for wrapping, page splits and clipping. `evidence/artifact-checks.json` records source coverage, original baseline hash checks and function-documentation checks.
- Original baseline files are preserved byte-for-byte; SHA-256 values are in `docs/baseline/manifest.json`.
- The original Lab 1 model was inspected without saving and exported natively. Its hash is checked against `docs/baseline/lab1/manifest.json`; its feedback and mapping are recorded in `docs/CROSS_LAB_REVIEW.md`.
- Git attributes explicitly preserve PDF, Astah, ZIP and image bytes, while normalizing source text. This prevents Windows newline conversion from altering binary deliverables when cloned.

## Limits and Student Review

The comparison truthfully discloses earlier AI assistance in Lab 2. The source does not supply loyalty conversion rates, exact nutrition/stock quantities, a latency target or opt-in UI; these are documented proposals/fixtures. The optional local LLM and camera privacy requirements are present in the elicitation but deferred, not falsely marked as tested.

The students still need to understand the code, review the proposed design decisions and add any subsequent personal evaluation. No student reading completion or independent human-authored baseline is asserted.

The optional extra exercise is recommended, not claimed as completed. No personal student reflection is generated. General policy prohibits submitting AI-generated Lab 1-2 text/models; those generated review references must not be treated as corrected submissions. Lab 3 allows generation and includes the model/prompt PDF appendix.
