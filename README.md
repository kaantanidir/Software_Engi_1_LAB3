# SmartBrew AI - Group 28

Lab 3 prototype and an explicit correction of the submitted Lab 2. SmartBrew is a coffee-machine ordering system with personal recipes, context-based recommendations, stock validation, checkout, loyalty, receipts and protected maintenance.

**AI assistance:** GPT-6.1 Sol, as confirmed by the student from the model selector, was used for Lab 3 Tasks A, B and C and this Lab 2 revision. The earlier Lab 2 submission was also assisted in this chat; its exact model/version was not recorded. See [the conversation record](docs/AI_CONVERSATION.md) and [the comparison](docs/LAB3_REPORT.md).

## Deliverables

| Item | Location |
| --- | --- |
| Corrected Lab 2 PDF | [output/pdf/G28Lab2_Corrected.pdf](output/pdf/G28Lab2_Corrected.pdf) |
| Corrected Astah project | [output/G28Lab2.asta](output/G28Lab2.asta) |
| Corrected Lab 2 package | [output/G28Lab2_Corrected.zip](output/G28Lab2_Corrected.zip) |
| Lab 3 report PDF | [output/pdf/G28Lab3_Report.pdf](output/pdf/G28Lab3_Report.pdf) |
| Editable Lab 2 / Lab 3 documents | [docs/LAB2_CORRECTED.md](docs/LAB2_CORRECTED.md), [docs/LAB3_REPORT.md](docs/LAB3_REPORT.md) |
| Original submitted comparison baseline | [docs/baseline](docs/baseline) with SHA-256 manifest |
| Use-case descriptions | [docs/USE_CASE_DESCRIPTIONS.md](docs/USE_CASE_DESCRIPTIONS.md) |
| Test evidence and actual limitations | [docs/QA_RESULTS.md](docs/QA_RESULTS.md), [evidence](evidence) |

## Environment

- Python **3.12**, verified with **3.12.14** on Windows. Python includes SQLite, HTTP serving and the test framework; no database server/compiler is required.
- A modern browser; verified with local Chrome. The application binds only to `127.0.0.1`.
- Runtime dependency: `qrcode==8.2`; Windows console support `colorama==0.4.6`. Exact pins are in `requirements.txt`.
- Lucide **1.8.0** is bundled with its ISC license, so icons work offline.
- Node.js is **not required to run the app**. Browser QA optionally uses Node 20+ and Playwright 1.62.1.
- Astah Professional 12.0.0 is needed only to open/edit the `.asta` deliverable, not to run the prototype.

## Install and Run

Open a terminal in the cloned repository on Windows:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py --port 8765
```

Open **http://127.0.0.1:8765**. Stop the server with `Ctrl+C`. If that port is occupied, choose another `--port` and use the matching browser URL. Network access is needed to install dependencies, then the app uses local assets/data only.

On macOS/Linux with Python 3.12 installed, the corresponding commands are:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py --port 8765
```

SQLite data is created automatically at `data/smartbrew.sqlite3`. To start a fresh demonstration without touching existing data:

```powershell
.\.venv\Scripts\python.exe app.py --port 8767 --database data/fresh-demo.sqlite3
```

Keep the same browser origin for a session. `localhost` and `127.0.0.1` are different cookie origins. Sessions expire after eight hours; signing out removes the current session. Credentials and sessions are hashed; demo accounts below are deliberately public simulator fixtures.

## Demo Accounts

| Role | Sign-in method | Fixture |
| --- | --- | --- |
| Customer | Email/password | `alex@smartbrew.test` / `DemoPass123!` |
| Customer | NFC tap simulator | `DEMO-NFC-001` |
| Technician | Technician tab / PIN | `246810` |
| Technician | NFC tap simulator | `MASTER-NFC-001` |

Alex starts with **250 loyalty points** and **SEK 200** employee prepaid balance. A newly registered customer starts at zero. No real card or financial account is connected. Guest menu/customization/purchase is supported; saved recipes, loyalty, prepaid and private history require customer login.

## Ten Feature Walkthrough

| Feature | Requirements | How to run and check |
| --- | --- | --- |
| **F01 Accounts and preferences** | FR-01..03, NFR-02 | Sign in using the demo password or NFC identifier. Change milk/strength/temperature and select **Save defaults**; sign out/in and verify retention. **Create account** rejects a duplicate email and passwords shorter than 10 characters. |
| **F02 Menu and nutrition** | FR-04 | Use **All drinks**, **Coffee**, **Chocolate**. Each drink shows price, estimated calories and allergens. Select a drink to see its customized quote. |
| **F03 Validated customization** | FR-05 | Select Latte; choose oat, strong, 75 C, two syrup shots and one extra espresso. Quote is **SEK 51**; changing options recalculates price/nutrition. Unsupported values are rejected by the service even if submitted outside the UI. |
| **F04 Named recipes** | FR-06 | Select **Save recipe**, name it Morning Oat, open **My recipes**. Rename it with the pencil. **Order** restores settings. Change settings then **Save recipe** to update the loaded recipe. Delete with the trash icon. Another account cannot access/edit it. |
| **F05 Ingredient availability** | FR-07, NFR-03 | Sign in as technician, open **Maintenance**, set oat's simulated level to 99 (minimum 100). Return to an oat drink: checkout is blocked. **Refill** resets oat to capacity. A level of 150 also cannot supply a 180 ml Latte, even though above threshold. Checkout rechecks stock. |
| **F06 Recommendations** | FR-08/19 | Toggle **Recommended first**. Buy a drink to add history. In Maintenance change simulated weather/time and observe scores/reasons. Offline mode excludes weather but keeps local ordering/recommendations. Scores are a documented local heuristic, not an LLM. |
| **F07 Checkout/history and offline handling** | FR-11/12/20, NFR-03 | Checkout using each EMV/contactless/wallet/prepaid simulator. Set processor **Decline** and verify no completed order/stock/points change. Approved orders appear in **Purchases** with original recipe settings. Turn network offline in Maintenance: prepaid can complete; a signed-in wallet request becomes pending, with no charge/dispense. Reconnect, sign in as the same customer, open Purchases and **Retry** the pending request. It completes once after approval and current-stock validation. |
| **F08 Loyalty** | FR-13 | As Alex, redeem 100 points at checkout for **SEK 10** discount. Points are deducted only on success; the purchase earns one point per whole SEK actually paid. Over-balance/over-price redemption is rejected. |
| **F09 Receipts** | FR-14 | Complete a purchase; inspect the generated QR or open its receipt page. The QR encodes actual receipt text and can be decoded offline. **Email receipt** writes a local simulator outbox entry, visible to the technician. Turn email off to show QR fallback. No external email is sent. |
| **F10 Maintenance/safety/diagnostics** | FR-15..18 | Technician signs in, refills ingredients/cups, sets a waste bin to 100%, verifies orders are blocked, then records **Empty**. Simulate a grinder jam/heater fault, inspect its timestamp/severity, then clear it. Use **Diagnostic export** for authorized JSON. Customer/guest admin requests are rejected. |

## Tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tests create independent temporary databases in `tmp/tests`, preserving live demo data. They cover all ten feature groups, failure rollback, ownership, concurrency, receipt snapshots and once-only offline reconciliation.

Optional browser checks (spawn a separate QA server on **8766**, separate data and a fresh browser):

```powershell
npm install
npx playwright install chromium
$env:PYTHON = (Resolve-Path .\.venv\Scripts\python.exe).Path
npm run test:browser
```

If using an already installed Chrome instead, set `CHROME_PATH` to its executable path before the last command. Run the unit suite without Node when only runtime verification is needed. Browser results/screenshots are written to `evidence`. If port 8766 is occupied, stop that separate process before running QA.

## Implementation and Limits

- `app.py`: local HTTP routes, session cookies, request validation, QR receipts and static UI.
- `smartbrew/service.py`: business rules and SQLite persistence. Purchases use `BEGIN IMMEDIATE`, a unique request key and a single commit for transaction, stock, waste, prepaid and points changes.
- `web/`: responsive interface with local photographs/icons. No CDN is contacted during ordering.
- `tests/`: isolated business-rule regressions. `tools/browser_check.cjs`: real browser walkthrough and responsive checks.
- `tools/coursework_data.py`: shared requirements/story/backlog source; `tools/build_documents.py` exports Markdown/PDF; `tools/AstahRepair.java` repairs a copy using the licensed Astah API.

The prototype **simulates** weather/time, NFC/key signals, sensors, dispensing, processor approval and email delivery. It does not connect to EMV hardware, Apple Pay/Google Pay, a camera, a physical machine or SMTP. Prepaid balance and loyalty are real local bookkeeping, not external financial services. Diagnostic JSON export is implemented; a remote diagnostic deployment is not.

Camera mood inference and the optional local LLM remain explicit backlog items outside the ten selected features. There is no fake keyword parser presented as an LLM. Nutrition and ingredient quantities are illustrative. Point conversion, opt-in and latency target are proposed design choices documented in the report. The local HTTP server is intended for coursework demonstration on loopback, not public deployment.

## Coursework Records

The original feedback gave Lab 2 a **positive grade** but requested complete requirement fields and layout/customer-entry fixes. The revised PDFs follow the exact six requirement columns from Lecture 2 slide 47. Backlogs use the slide's columns plus Description and trace notes; importance is 0-100 and estimates are relative story points.

The original submitted group artifact is preserved rather than relabeled as human-only work. Review the comparison, prompting record and all proposed assumptions, and run the walkthrough before presenting the assignment. The assigned Scrum reading remains the students' responsibility; this project does not assert that anyone has completed that reading.

To regenerate documents (optional; the PDFs are already included):

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-docs.txt
.\.venv\Scripts\python.exe tools/build_documents.py
```

Astah's supplied `InitiatingActor` template automatically displays **directly associated actors**. Included/extension-only use cases have their initiating customer explicitly described in their model definition and in `docs/USE_CASE_DESCRIPTIONS.md`; their auto-generated actor row can appear blank under that template. Open the corrected file directly in Astah, not by unzipping its internal `EntityStore`. The `.asta.lock` is a transient lock and is not a submission file.
