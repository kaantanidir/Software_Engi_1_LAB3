# SmartBrew AI - Group 28

A local coffee-machine prototype for Software Engineering Lab 3. Customers can customize drinks, keep personal recipes, pay through simulated card/wallet adapters and receive receipts. Technicians manage supplies, waste and diagnostic events. An optional local language model turns drink requests into recipes for the customer to review.

For the assessed artifacts, GitHub link and Canvas ZIP instructions, see [the submission guide](SUBMISSION.md).

## Start the App

Requirements: **Python 3.12** and a modern browser. Verified on Windows with Python 3.12.14. SQLite and the HTTP server are included with Python; runtime packages are pinned in `requirements.txt` (`qrcode==8.2`, plus `colorama==0.4.6` on Windows).

From the repository directory:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\tools\start_smartbrew.ps1
```

Open **http://127.0.0.1:8765/**. Stop with `Ctrl+C`. If that port is occupied, choose a different `--port` and use the matching address. Network access is needed for installation; normal ordering uses local assets and data afterward.

On Windows the launcher starts Ollama if needed, reuses an existing local server, and then runs SmartBrew. It uses already downloaded `qwen3:4b` weights; normal startup never downloads the model. If Ollama/the model is missing or startup fails, it reports that and starts the site with manual ordering available. Ollama stays running after the app stops so it can be reused.

Use `.\tools\start_smartbrew.ps1 -Port 8767` for another port, or add `-SkipAI` to skip Ollama preparation. An already running Ollama can still serve assistant requests with that switch. Direct `.\.venv\Scripts\python.exe app.py --port 8765` still works; that command expects Ollama to be running separately when using the optional assistant.

If Windows blocks `.ps1` files, use `powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\start_smartbrew.ps1`. This applies only to that process and does not change the machine's execution policy. The same prefix can run `tools/start_local_ai.ps1` during one-time setup.

On macOS/Linux, use `python3.12 -m venv .venv`, then `.venv/bin/python` for installation and `.venv/bin/python app.py --port 8765` to run the app; start Ollama separately for the optional assistant. The combined PowerShell launcher and documented evaluation environment are Windows-specific.

Data persists in `data/smartbrew.sqlite3`. For a fresh demonstration that preserves existing accounts and purchases:

```powershell
.\.venv\Scripts\python.exe app.py --port 8767 --database data/fresh-demo.sqlite3
```

## Accounts

Normal sign-in and registration fields start empty. **Use demo account** intentionally fills the public fixture; it does not replace the credentials entered for another account. Registration requires a name, unique email and a password of 10-128 characters.

| Role | Credentials |
| --- | --- |
| Demo customer | `alex@smartbrew.test` / `DemoPass123!` |
| Demo customer NFC simulator | `DEMO-NFC-001` |
| Technician tab | PIN `246810` |
| Technician NFC simulator | `MASTER-NFC-001` |

Alex starts with 250 points and SEK 200 prepaid credit. New accounts start at zero. Guest ordering is available; private recipes, history, loyalty and employee balance require customer sign-in. NFC is an explicit simulator, not a physical reader or production credential mechanism.

One browser profile shares one signed-in session across tabs. For simultaneous customer/technician demonstrations, use separate browser profiles or a normal window and a private window. Use the same hostname consistently: `localhost` and `127.0.0.1` have separate cookies.

## Demonstrate the Ten Features

| Feature | Steps and expected result |
| --- | --- |
| **F01 Accounts/preferences** | Create a new account, save defaults, sign out and sign back in with its email/password. A wrong password must fail. A second customer must have separate recipes, purchases and points. |
| **F02 Menu/nutrition** | Browse All drinks, Coffee and Chocolate. Inspect price, estimated calories and listed allergens. |
| **F03 Customization** | Select Latte, oat milk, strong, 75 C, two syrup shots and one extra espresso. The total is SEK 51. Review every setting before confirming payment. |
| **F04 Saved recipes** | Save a named recipe. In My recipes, rename it with the pencil, load it with Order, modify and save it, then delete it. Another account cannot modify it. |
| **F05 Availability** | As technician, use Test scenarios to set oat milk to 99 (minimum 100). An oat drink is blocked. Record a refill in Maintenance and verify availability returns. Quantity is checked as well as the threshold. |
| **F06 Recommendations** | Save oat preferences and enable Recommended first. Ranking uses completed purchase history, saved recipes, preference affinity, local clock or technician period override, and online temperature/weather condition. Selecting a recommendation applies its actual settings. Missing weather or ranking service falls back to local context and the standard menu. |
| **F07 Checkout/history** | Purchase with each payment-method simulator. Purchases show the original settings. For a decline, set the technician's external processor to Decline first; customer checkout cannot choose its result. Decline changes no stock, points or balance. Restore Normal afterward. |
| **F08 Loyalty** | As Alex, redeem 100 points for SEK 10 discount. A successful purchase earns one point per whole SEK actually paid. Rejected payments spend and earn no points. |
| **F09 Receipts** | Open a purchase receipt and its actual generated QR. It contains the purchased settings and totals. Email receipt writes to the local simulator outbox; unavailable email retains QR access. No external email is sent. |
| **F10 Maintenance/diagnostics** | Sign in through the Technician tab. Record refills/emptying in Maintenance. In Test scenarios, simulate a full bin or fault and verify ordering is blocked. Inspect the event log and Diagnostic export. Customer/admin requests are rejected by the server. |

For offline handling, the technician sets Network to Offline in Test scenarios. Prepaid balance can complete a purchase locally. A signed-in customer's online-only wallet request stays pending without charge or dispensing. Restore Online, sign in as that customer and select Retry in Purchases. Authorization and availability are checked again; repeated requests cannot create a second purchase.

Technician test settings persist until changed. **Normal** applies to external payment simulation; the internal prepaid method still checks its actual stored balance. A full bin, insufficient ingredients or a machine fault can block ordering in either mode.

## Optional Local Drink Assistant

The ten features above do **not** require a model. For the optional assistant, install Ollama and download the model **once**:

1. Install [Ollama](https://docs.ollama.com/windows). The verified runtime is **0.40.6**.
2. Run `.\tools\start_local_ai.ps1` to start/reuse Ollama, download `qwen3:4b` only if missing (approximately 2.5 GB), and warm it. With an already running installation, `ollama pull qwen3:4b` also prepares the model.
3. On later launches, run `.\tools\start_smartbrew.ps1`. It starts/reuses Ollama and launches the site together; a separate manual Ollama startup is unnecessary. It skips warm-up, so the first assistant request may take longer while the model loads.
4. SmartBrew connects only to the local API at `127.0.0.1:11434`. If you launch `app.py` directly instead, start Ollama separately (for example `ollama serve`, unless it is already running).
5. Ask: **Recommend three strong, slightly sweet oat drinks at 75 degrees with one vanilla syrup shot and no extra espresso.** Compare up to three cards showing drink names, settings, short reasons and server-calculated prices. Select **Use recipe** on the option you want. Further changes refer to that option; checkout remains a separate confirmation. A precise named-drink request or limited stock may yield fewer distinct choices.

For a quick demo, choose **Three strong oat options**, **Sweet oat chocolate** or **Classic cappuccino** beneath the input. These examples fill and focus the request; select **Ask** to send it. While the model responds, the loading indicator follows the browser's reduced-motion preference.

On this workspace both scripts can use the project-local portable runtime, with its runtime/models under ignored `data/local-ai`. Other machines use their installed Ollama; portable binaries/model weights are not bundled in the repository or source ZIP. No Windows service or PATH change is made by the scripts. Optional manual warm-up remains available with `ollama run qwen3:4b "Reply READY"`.

The adapter requests structured JSON for one primary recipe and up to two alternatives, rejects unsupported fields/options, removes duplicate or unavailable alternatives and recalculates all prices and stock availability on the server. Alternatives retain the primary recipe's milk, strength, temperature, syrup and extra-shot settings. Customer cards show choices and reasons; they do not show technical scores or AI confidence percentages. F06's separate menu-ranking rules remain documented in the architecture and backlog. A narrow guard ensures exact strength-only follow-ups such as **Make it mild** preserve the selected drink and other settings.

The assistant cannot place orders, edit accounts or authorize payment. Conversation is held in the page and cleared on account changes. The model is fallible: review its proposals. A missing model, invalid response or timeout leaves manual ordering available. The model wait is bounded at 90 seconds; it is not part of the menu/quote latency target. Three-option inference uses an 8192-token context and an output limit of 900 tokens in one local model request.

The verified hardware has about 32 GB RAM and an RTX 3060 Laptop GPU with 6 GB VRAM. This is a tested machine, not a promised minimum hardware specification. Model weights are not bundled in Git. The exact tested model digest and live responses are in `evidence/current/local-ai-results.json`.

## Run the Tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The unit suite runs **38 tests** against isolated temporary databases under `tmp/tests` (recorded in `evidence/current/unit-tests.txt`). Model-adapter unit tests use labelled test doubles and do not require Ollama. Actual local inference is tested separately:

```powershell
.\.venv\Scripts\python.exe tools/check_local_ai.py
.\.venv\Scripts\python.exe tools/check_assistant_conversations.py
.\.venv\Scripts\python.exe tools/check_assistant_long_chat.py
.\.venv\Scripts\python.exe tools/check_assistant_heldout_baseline.py
```

These commands test the original four live requests (`evidence/current/local-ai-results.json`), the 12-turn taste and follow-up conversation suite (`evidence/current/assistant-conversations.json`), the 9-turn extended drink-switching sequence (`evidence/current/assistant-long-chat.json`), and the 8-turn multi-turn context/constraint regression suite (`evidence/current/assistant-heldout-postchange.json`, with the pre-change baseline preserved in `evidence/history/assistant-heldout-baseline.json`). See the [assistant implementation update](docs/development/ASSISTANT_IMPLEMENTATION_UPDATE.md) for the integration and contribution record.

Optional browser audit (Node 20+, Playwright 1.62.1):

```powershell
npm install
npx playwright install chromium
$env:PYTHON = (Resolve-Path .\.venv\Scripts\python.exe).Path
npm run test:browser
```

The browser audit starts its own server on 8766 and uses separate temporary data, including a server restart. With `$env:SMARTBREW_LIVE_AI = '1'`, it runs **65 checks** (recorded in `evidence/current/browser-results.json`), covering all ten feature groups, F06 context controls/modes, and live F11 multi-turn conversation, three recipe choices, selected-option follow-ups, mobile layout and clearing. Set `CHROME_PATH` to an installed Chrome executable to use that instead of Playwright's browser. Recorded results and limitations are in [the verification record](docs/QA_RESULTS.md).

With Ollama/model running, set `$env:SMARTBREW_LIVE_AI = '1'` before the browser command to additionally test actual inference, explicit recipe application and conversation clearing. The normal browser audit does not require a model; its deliberate unavailable-model response is a failure-path test, not simulated evidence of real inference.

## Project Layout

| Location | Responsibility |
| --- | --- |
| `app.py` | Local HTTP routes, cookies, static files and QR receipts |
| `smartbrew/service.py` | Authentication, ownership, quotes, stock and atomic purchases |
| `smartbrew/assistant.py` | Optional local-model adapter and output validation |
| `web/` | Customer interface, protected technician views and receipt page |
| `tests/` | Isolated business-rule and assistant validation tests |
| `tools/` | Active Lab 3 browser/live-model checks and document exports (`tools/archive/` holds archived Lab 1-2 source scripts) |
| `docs/` | Current report, architecture, AI-use record and documentation index |
| `docs/baseline/` | Unchanged original submissions and source hashes |
| `docs/development/` | Internal engineering and handoff notes retained in Git |
| `docs/reference/lab2/` | Historical generated Lab 2 review aids, not submission materials |
| `evidence/` | Verification outputs (`evidence/current/`) and preserved historical/regression runs (`evidence/history/`) |
| `output/` | Final Lab 3 deliverables (`G28Lab3_Report.pdf`, `G28Lab3_AI_Appendix.pdf`, `SmartBrew_Lab3_Canvas.zip`, `G28Lab3_Project.zip`) |
| `data/`, `tmp/`, `.venv/` | Local data, scratch files and environment; excluded from Git |

## Report and AI Record

- [Lab 3 report PDF](output/G28Lab3_Report.pdf)
- [Model/prompt appendix PDF](output/G28Lab3_AI_Appendix.pdf)
- [Documentation index](docs/README.md)
- [Available original development conversation](docs/DEVELOPMENT_TRANSCRIPT.md) (251 visible messages; declared omissions/redactions and source hashes included)

Lab 3 Tasks A-C and the initial local integration of a student-relayed Gemini web-chat draft were developed with Codex using the student-confirmed **GPT-6.1 Sol** selector label (before Gemini had local IDE access; that earlier web-chat Gemini version was not recorded). After opening the repository in Google Antigravity, **Gemini 4 Argon Medium** inspected the local files, implemented and tested the focused F11 multi-turn assistant corrections and the expanded F06 deterministic recommendation scoring and browser checks, and recorded the local verification evidence. Local **Qwen3:4b** through Ollama 0.40.6 is the prototype's runtime drink model, not a development assistant that generated the project. The appendix and AI record document prompts, decisions, observed errors and revisions.

The comparison uses the group's submitted Assignment 2, preserved unchanged in docs/baseline. Later generated review drafts are kept separately in docs/reference/lab2 and are not substituted for the comparison baseline.

## Scope

Hardware brewing, NFC signals, weather/time, external payments and email delivery are simulated. Camera/mood inference, remote diagnostics deployment, password recovery and a real financial connection are not implemented. Nutrition is illustrative and is not an allergy-safety guarantee. Demo prices, quantities and point conversion are documented design choices.

This loopback HTTP prototype is for coursework demonstration, not public production deployment. No Celery, Redis, Docker or separate database server is needed.
