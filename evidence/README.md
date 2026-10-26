# Evidence Index

This directory preserves verification outputs, screenshots, local runtime-model evaluations, historical failure records, and UML exports for SmartBrew AI (Group 28, Lab 3), organized into `current/` (passing final verification outputs and screenshots) and `history/` (pre-change baselines, intermediate runs, regression failures, and historical UML exports).

## 1. Final Verification (`current/`)

| File | Description |
| --- | --- |
| [current/unit-tests.txt](current/unit-tests.txt) | Full output of `python -m unittest discover -s tests -v` (**38 unit tests passed** against isolated temporary SQLite databases, including three-choice validation and the selected-recipe strength regression). |
| [current/clean-install.txt](current/clean-install.txt) | Fresh Python 3.12.14 environment with pinned qrcode/colorama, successful `pip check` and 38 unit tests run from a ZIP-extracted source copy without workspace packages or personal data. |
| [current/ux-polish.json](current/ux-polish.json) | Actual browser verification on that clean source/environment: three examples fill/focus without sending; Ask invokes the real model; mobile layout, loading cleanup and reduced-motion behavior verified. |
| [current/assistant-loading.png](current/assistant-loading.png) | Actual model-wait state showing example prompts and the loading indicator on the clean installation. |
| [current/browser-results.json](current/browser-results.json) | End-to-end Playwright browser audit output (`SMARTBREW_LIVE_AI=1 npm run test:browser`, **65 browser checks passed** across F01-F10 and F11's three choices, selected-option follow-up, mobile layout and conversation clearing). |
| [current/artifact-checks.json](current/artifact-checks.json) | Output of `python tools/verify_artifacts.py` verifying requirement/source coverage, 132 authored Python function docstrings, local documentation links, unchanged baseline hashes, the 13-to-24 story comparison, the 251-message attachment, actual test counts and live three-choice/selected-option evidence. |
| [current/desktop.png](current/desktop.png) | Current desktop customer view (`1440 x 1000`) during the automated browser audit. |
| [current/receipt.png](current/receipt.png) | Current purchase receipt dialog with generated QR SVG and local email simulator confirmation. |
| [current/maintenance.png](current/maintenance.png) | Current protected technician Maintenance tab showing ingredient counters and waste bins. |
| [current/test-scenarios.png](current/test-scenarios.png) | Current protected technician Test scenarios tab showing fault logging, payment simulation, and F06 context controls. |
| [current/local-assistant.png](current/local-assistant.png) | Current F11 local drink assistant proposal card before explicit customer application. |
| [current/assistant-options.png](current/assistant-options.png) | Three real-model recipe cards on desktop, showing names, server prices, short descriptions and settings without technical scores. |
| [current/assistant-options-mobile.png](current/assistant-options-mobile.png) | The same three recipe choices stacked within the mobile viewport without horizontal overflow. |
| [current/mobile.png](current/mobile.png) | Current mobile customer view (`390 x 844`) verified for zero horizontal overflow. |

## 2. Local Runtime Model Evidence (`current/`)

| File | Description |
| --- | --- |
| [current/local-ai-results.json](current/local-ai-results.json) | Output of `python tools/check_local_ai.py` recording the four initial live requests against **Qwen3:4b** (`qwen3:4b` via local Ollama `0.40.6`, including model digest, timings, and validated server quotes). **Qwen3:4b** is the prototype's local runtime model that interprets customer drink requests at runtime, not a development assistant that generated or edited project code. |

## 3. Assistant Experiment and Multi-Turn Evaluation (`current/` and `history/`)

All multi-turn evaluation suites run against the live local `qwen3:4b` runtime using isolated temporary databases:

| File | Description |
| --- | --- |
| [history/assistant-heldout-baseline.json](history/assistant-heldout-baseline.json) | **8-turn pre-change baseline** (`tools/check_assistant_heldout_baseline.py` before the F11 context/schema refinement; 5 of 8 turns passed, exposing a leaked synthetic assistant placeholder on `A3`, base-drink rigidity on `B2`, silent substitution of an unsupported iced caramel request on `C1`, and unrequested extra espresso on `C2`). |
| [history/assistant-heldout-postchange-first-run.json](history/assistant-heldout-postchange-first-run.json) | **8-turn intermediate run** after replacing the synthetic assistant turn with a trailing `system` context block (`current_proposal`) and ordering `config` before `message` in `RESPONSE_SCHEMA` (7 of 8 turns passed before refining the alternative-drink rule on `A3`). |
| [current/assistant-heldout-postchange.json](current/assistant-heldout-postchange.json) | **8-turn final regression run** (`tools/check_assistant_heldout_baseline.py`; all 8 turns and all 55 internal field/constraint assertions within those turns passed). |
| [current/assistant-conversations.json](current/assistant-conversations.json) | **12-turn conversation suite** (`tools/check_assistant_conversations.py`; all 12 turns across 7 multi-turn scenarios and all 100 internal assertions within those scenarios passed). |
| [current/assistant-long-chat.json](current/assistant-long-chat.json) | **9-turn long-chat suite** (`tools/check_assistant_long_chat.py`; all 9 recipe-following turns and all 30 internal recipe assertions passed across Americano, latte, cocoa, cappuccino, and espresso). |
| [history/assistant-conversations-first-run.json](history/assistant-conversations-first-run.json) | Earlier failed run of the 12-turn suite before positive recipe examples were added to the system prompt. |
| [history/assistant-conversations-second-run.json](history/assistant-conversations-second-run.json) | Earlier failed run of the 12-turn suite before clarifying unspecified additions versus unsupported ingredients. |
| [history/assistant-long-chat-wording-failure.json](history/assistant-long-chat-wording-failure.json) | Preserved 9-turn run documenting a generic first-turn prose wording observation (`wordingChecksPassed: false`) kept distinct from recipe accuracy (`passed: true`). |

## 4. Preserved Regression Failures (`history/`)

| File | Description |
| --- | --- |
| [history/authentication-regression-before.txt](history/authentication-regression-before.txt) | Preserved failing unit regression reproducing the original authentication defect where a hidden default NFC value overrode entered password credentials. |
| [history/recommendation-regression-before.txt](history/recommendation-regression-before.txt) | Preserved failing regression from before the menu and recommendation failure path were decoupled. |
| [history/local-ai-initial-review.txt](history/local-ai-initial-review.txt) | Preserved initial `qwen3:4b` cold-start timeout and invented `"usual"` drink response before prompt/timeout refinement. |
| [history/browser-failure.json](history/browser-failure.json) | Preserved earlier F11 browser failure where conversation history containing an older latte caused the model to modify the latte instead of the active cappuccino. |
| [history/assistant-options-first-run.json](history/assistant-options-first-run.json) | First three-choice browser run: correct second-option context was sent, but the model changed cappuccino to latte on "Make it mild". A narrow strength-only guard, unit regression and the final live browser run verify the correction. |
| [history/assistant-options-alternative-regression.json](history/assistant-options-alternative-regression.json) | Intermediate eight-turn run where "What else" repeated the primary espresso despite two valid model-generated alternatives; retained before the explicit-alternative promotion guard and final regression rerun. |
| [history/browser-f06-first-run-failure.json](history/browser-f06-first-run-failure.json) | Preserved first-run F06 browser timing failure where `page.waitForLoadState('networkidle')` resolved before `updateQuote()` finished re-enabling `#checkout-button` after sign-out. |

## 5. Historical UML and Source Evidence (`history/`)

Generated Lab 2 corrections and diagram exports are **review references only, not valid Lab 1 or Lab 2 submission material** under the course AI policy. Original Lab 1 and Lab 2 submissions remain byte-for-byte unchanged in `docs/baseline/`.

| File / Directory | Description |
| --- | --- |
| [history/lab1-inspection.txt](history/lab1-inspection.txt) | Read-only inspection summary of the original `docs/baseline/lab1/G28Lab1.asta` model. |
| `history/lab1-export/G28Lab1/` | Native diagram exports (`Class Diagram.png`, `Component Diagram0.png`) from the unchanged Lab 1 Astah model. |
| [history/use-cases.png](history/use-cases.png) | Exported use-case diagram for the post-submission Lab 2 review reference (review aid only, not for Lab 2 submission). |
| `history/astah-export/G28Lab2/` | Diagram exports (`*.png`) from the Lab 2 review reference (review aid only, not for Lab 2 submission). |
