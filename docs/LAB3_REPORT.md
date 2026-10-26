# SmartBrew AI - Group 28 - Lab 3

Updated: 2026-10-26

## Task A - Elicitation

SmartBrew AI is a local coffee-machine prototype for customers and maintenance technicians. It implements ten selected feature groups: accounts, menu, customization, personal recipes, availability, recommendations, checkout/history, loyalty, receipts and maintenance. An additional optional local language model interprets drink requests into customer-confirmed recipes. The complete elicitation retains camera/privacy requirements even though camera inference is outside this implementation.

### Cross-lab continuity

Lab 1 received a positive grade, with Partial feedback on component scope and UI dependency on the AIEngine. Its nine domain concepts map to roles, preferences, recipes, purchase records and stock/waste state, not necessarily one code class each. The optional local-LLM responsibility is now implemented through a separate adapter; camera/mood inference remains deferred. Loyalty first appears in the supplied Lab 2, not the Lab 1 diagrams. See docs/CROSS_LAB_REVIEW.md for the detailed source mapping.

### Models and provenance

Codex with student-confirmed selector label GPT-6.1 Sol (2026-10-20/21, initial Lab 3 Tasks A-C and web-chat handoff integration; exact backend build not exposed) and Gemini 4 Argon Medium through Google Antigravity (2026-10-21, local repository inspection, F11 multi-turn assistant evaluation/correction and F06 deterministic recommendation expansion and verification).

These are the development assistants for Lab 3 Tasks A-C and the subsequent F11/F06 updates. The runtime drink model inside the application is separately identified as local Qwen3 4B (qwen3:4b) through Ollama 0.40.6. Earlier Lab 1-2 tutoring and an intermediate web-chat Gemini draft before local IDE access did not expose confirmed model version labels.

The comparison uses the group's actual submitted Assignment 2 files, preserved unchanged with hashes in docs/baseline. The student clarified that earlier AI assistance was limited and was not comparable to the extensive generation used for Lab 3. Later AI-generated review corrections are separate reference materials and are not substituted for the submitted version.

### Prompt strategy

Use the actual system description, feedback and course slides as grounding; constrain all requirements to the six-column lecture template; retain the submitted baseline; check each source capability against stories/requirements/backlog; separate source mandates from proposed design assumptions; select ten coherent demonstrable feature groups; implement and test approval, rejection, ownership, retry, safety and offline paths. This was one evolving chat request with student clarifications, not an invented sequence of separate prompting experiments.

Main prompts and selected responses are recorded in AI_CONVERSATION.md and the separate PDF appendix; generated code and revisions are retained in Git.

### Source inventory

| Source | System capability |
| --- | --- |
| S01 | Accounts, credential/NFC login and personal preference profiles. |
| S02 | Record every completed transaction with beverage customization parameters. |
| S03 | Save, modify and name personal recipes for one-touch ordering. |
| S04 | Recommend using time, weather and historical choices. |
| S05 | Use embedded-camera mood analysis for tailored suggestions. |
| S06 | Reorder and highlight menu items using recommendation scores. |
| S07 | Browse categories, inspect nutrition and customize in real time. |
| S08 | Prevent selection of drinks with depleted/below-threshold ingredients. |
| S09 | Support credit/debit EMV chip/contactless, Apple Pay/Google Pay and prepaid employee cards. |
| S10 | Offer receipts by QR scan or email. |
| S11 | Optional modular local LLM for natural-language interaction and customization. |
| S12 | Secure technician mode using physical key, master NFC card or PIN. |
| S13 | Register ingredient/cup refills and reset counters to maximum capacity. |
| S14 | Monitor liquid/grounds bins, alert before disposal and halt on overflow. |
| S15 | Display errors on admin dashboard and log events for remote diagnostics. |
| S16 | Facial images: infer only in memory, discard immediately, never persist/transmit. |
| S17 | Network/service failure: manual ordering and supported offline payment/deferred processing. |
| G01 | Group feature: loyalty points earned on completed purchases and redeemed at checkout. |

### User stories

| ID | Name | Story | Requirement links |
| --- | --- | --- | --- |
| US-01 | Account registration | As a Customer, I want to create an account so that my preferences and purchase history belong to me. | FR-01 |
| US-02 | Customer login | As a Customer, I want to log in with credentials or my registered NFC card so that I can access my profile quickly. | FR-02 |
| US-03 | Preferences | As a Customer, I want to change my default drink settings so that future orders reflect my preferences. | FR-03 |
| US-04 | Menu and nutrition | As a Customer, I want to browse categories and nutrition so that I can choose a suitable available drink. | FR-04 |
| US-05 | Customization | As a Customer, I want to change milk, strength, temperature, syrup and espresso shots so that my drink matches my taste. | FR-05 |
| US-06 | Saved recipes | As a Customer, I want to name, save and modify my recipes so that I can reorder them with one touch. | FR-06 |
| US-07 | Availability | As a Customer, I want unavailable recipes blocked before purchase so that I do not pay for an impossible drink. | FR-07 |
| US-08 | Recommendations | As a Customer, I want available drinks ranked using my history, time and weather so that relevant choices are easy to find. | FR-08 |
| US-09 | Mood suggestions | As a Customer, I want optional mood-based suggestions so that I can receive a suitable recommendation without losing manual ordering. | FR-09/NFR-01 |
| US-10 | Natural-language ordering | As a Customer, I want the optional local LLM to suggest up to three recipes for my request so that I can compare them, select one and refine it before confirming a purchase. | FR-10 |
| US-11 | Payment | As a Customer, I want to pay with a supported card, wallet or employee balance so that I can complete a purchase. | FR-11 |
| US-12 | Order records | As a Customer, I want completed orders to retain the original settings so that I can inspect what I purchased. | FR-12 |
| US-13 | Loyalty | As a Customer, I want to earn and redeem loyalty points so that repeat purchases can reduce my future cost. | FR-13 |
| US-14 | Receipts | As a Customer, I want QR or email receipts so that I can keep proof of payment. | FR-14 |
| US-15 | Protected administration | As a Technician, I want secure administrative access so that customers cannot change maintenance state. | FR-15/NFR-02 |
| US-16 | Refills | As a Technician, I want to register refills so that ingredient and cup counters reflect full capacity. | FR-16 |
| US-17 | Waste safety | As a Technician, I want waste warnings and an overflow halt so that the machine stops safely until bins are emptied. | FR-17 |
| US-18 | Diagnostics | As a Technician, I want persistent local and authorized remote diagnostic logs so that faults can be investigated even after an outage. | FR-18 |
| US-19 | Service failure | As a Customer, I want manual ordering to remain available during service failure so that I can still buy with an offline-capable method. | FR-19 |
| US-20 | Offline status | As a Customer, I want clear offline payment status so that I know whether payment is approved or still pending. | FR-20 |
| US-21 | Image privacy | As a Customer, I want facial images discarded without storage or transmission so that mood analysis does not retain my face. | NFR-01 |
| US-22 | Reliable purchase | As a Customer, I want retries to create only one completed purchase so that I am not charged twice. | NFR-03 |
| US-23 | Responsive ordering | As a Customer, I want menu and quote responses to appear promptly so that choosing a drink remains convenient. | NFR-04 |
| US-24 | Repeatable assessment | As an Evaluator, I want a documented setup and feature walkthrough so that I can run the prototype on an independent machine. | NFR-05 |

### Functional requirements

| ID | Description | Inputs | Outputs | Precondition | Postcondition |
| --- | --- | --- | --- | --- | --- |
| FR-01 | Create an account<br>The system shall register a customer account with unique credentials and a preference profile. | Email, password, display name. | Account identifier or validation error. | Email is not already registered; required values are valid. | One account/profile is stored; invalid registration makes no change. |
| FR-02 | Authenticate customers<br>The system shall authenticate credentials or a registered NFC/card identifier and load only the corresponding customer's profile. | Credentials or NFC identifier. | Authenticated session/profile or denial. | An account exists; supplied credential is registered. | Successful login creates a session; failed login grants no access. |
| FR-03 | Maintain preferences<br>The system shall let authenticated customers update their default milk, strength and temperature. | Customer session; preference values. | Saved preference profile. | Customer is authenticated; settings are supported. | Updated defaults persist across logout/restart. |
| FR-04 | Browse menu and nutrition<br>The system shall display beverage categories, ingredients, allergens, nutrition, prices and availability. | Category/filter; menu and stock data. | Matching drinks and nutritional details. | Local menu is available. | Customer can inspect drinks; unavailable items cannot be ordered. |
| FR-05 | Customize a beverage<br>The system shall validate milk, coffee strength, temperature, syrup and extra-shot choices and update the recipe, price and nutrition before confirmation. | Base drink and supported customization choices. | Validated recipe, price, nutrition or error. | A base drink has been selected. | The exact validated settings are visible; invalid options cannot be confirmed. |
| FR-06 | Manage named recipes<br>The system shall save, rename, modify and delete personal recipes and restore their settings for one-touch ordering, subject to current stock checks. | Customer session, recipe name/settings. | Stored recipe or restored order draft. | Customer is authenticated; recipe settings are valid. | Only the owner can change a recipe; later orders recheck availability. |
| FR-07 | Check ingredient availability<br>The system shall reject menu selections and confirmed recipes if an ingredient is depleted, below its minimum threshold or insufficient for the requested serving. | Recipe quantities; stock levels/thresholds. | Availability result and missing-ingredient reasons. | Recipe and current counters exist. | Unavailable recipes cannot be purchased; stock is revalidated at checkout. |
| FR-08 | Rank recommendations<br>The system shall score available drinks using preferences, purchase history, time and weather, then reorder and highlight the best recommendations. | Profile/history, time, weather, available menu. | Ranked available drinks and recommendation reasons. | Local menu exists; history/profile may be empty. | Only available drinks are recommended; missing weather falls back to local context. |
| FR-09 | Analyze mood<br>The system shall use the embedded camera to infer a mood and optionally add it to the recommendation context; unavailable inference shall not prevent manual ordering. | Consented transient camera frame. | Mood label or unavailable result. | Camera/mood module enabled and customer opts in (design assumption). | Recommendations can use the label; no image is retained. |
| FR-10 | Interpret natural-language requests<br>When the optional local LLM is enabled, the system shall translate a broad drink request into up to three distinct supported recipe choices with short reasons and server-calculated prices; precise requests may return fewer choices. The customer selects a recipe before checkout, and follow-up changes use the selected recipe. | Request text; local model; supported menu/options; active selected recipe. | One to three validated recipe choices, a clarification question or an unavailable explanation. | Optional module is installed and enabled. | Only customer-confirmed and validated parameters reach ordering; proposing/applying recipes does not purchase. No technical scores are shown in the assistant. |
| FR-11 | Process supported payments<br>The system shall support EMV chip/contactless credit/debit, Apple Pay, Google Pay and prepaid employee cards and distinguish approved, declined and pending outcomes. | Confirmed recipe; method; provider response/prepaid balance. | Payment result and transaction reference. | Recipe is available; machine is not halted. | Only approved payment completes an order; declines change no stock, points or balance. |
| FR-12 | Record completed transactions<br>The system shall record each completed purchase once with owner/guest reference, timestamp, original recipe settings, price and payment outcome and show the owner's history. | Approved purchase; recipe snapshot; idempotency key. | Persistent completed transaction/history entry. | Payment approved; checkout validations still hold. | Receipt/history preserve the purchased settings even after a saved recipe is edited. |
| FR-13 | Earn and redeem loyalty<br>The system shall let logged-in customers redeem earned points at checkout and award points after a completed paid purchase, with no changes on decline. | Customer balance; requested points; order total. | Discount, paid total and updated points. | Logged-in customer has enough points; redemption does not exceed price. | Spend/earn is committed once with purchase; a rejected purchase leaves points unchanged. |
| FR-14 | Deliver receipts<br>After a completed purchase, the system shall offer a QR receipt or email delivery and offer QR as fallback on email failure. | Purchase reference; selected channel; email if needed. | Receipt QR/link or email-delivery result. | A completed transaction exists; recipient choice is valid. | Receipt reflects the immutable transaction; a failed email does not lose the purchase. |
| FR-15 | Authenticate maintenance personnel<br>The system shall restrict administrative actions to technicians authenticated by physical key, registered master NFC card or technician PIN. | Technician PIN/master card/key signal. | Admin session or access denial. | Credential/key is registered for technician role. | Customers cannot refill ingredients, empty bins or read administrative diagnostics. |
| FR-16 | Register refills<br>The system shall allow authenticated technicians to register full ingredient/cup refills and reset the selected counter to its configured maximum. | Admin session; selected ingredient; refill confirmation. | Updated counter and audit event. | Technician has performed/confirmed the physical refill. | Counter equals maximum; unrelated stock is unchanged; availability is recalculated. |
| FR-17 | Monitor waste and halt safely<br>The system shall monitor liquid and grounds bins, warn near capacity and halt dispensing on full/overflow status until a technician records emptying. | Waste sensor/counter readings; emptying confirmation. | Warning/halt status and event log. | Bin capacities and current readings are known. | A full bin blocks ordering; authorized emptying resets that bin and re-evaluates the halt. |
| FR-18 | Diagnose errors<br>The system shall show real-time faults on the admin dashboard and persist diagnostic events for authorized remote diagnostics when connectivity is available. | Fault code, message, severity, timestamp; diagnostic request. | Dashboard event and diagnostic log/export. | Fault reporting is active; diagnostics access is authorized. | Events remain available locally during a remote outage. |
| FR-19 | Keep manual ordering available<br>When network, weather or optional AI services fail, the system shall continue basic local menu/customization subject to ingredient, payment and safety rules. | Unavailable service; local menu/profile/stock. | Manual ordering interface and fallback indication. | Local machine hardware and required supplies are operational. | External-service loss alone does not block local selection/customization. |
| FR-20 | Handle offline payment honestly<br>The system shall use an approved offline-capable method or securely queue permitted pending payments and reconcile once on reconnect; it shall never present an unapproved online-only wallet payment as successful. | Connectivity; method policy; payment reference. | Offline approval, pending entry or denial; reconciliation result. | Payment method supports the chosen offline policy. | Pending authorizations do not dispense; approved prepaid orders and queued diagnostics persist. |

### Non-functional requirements

| ID | Description | Inputs | Outputs | Precondition | Postcondition |
| --- | --- | --- | --- | --- | --- |
| NFR-01 | Protect facial-image privacy<br>All camera frames shall be processed only in volatile memory, discarded immediately after inference and never written to disk, logs, databases or external servers. | Transient camera frame and inference lifecycle. | Mood label without image retention/transmission. | Any camera-based inference runs. | No facial-image bytes remain in persistent storage or outbound traffic. |
| NFR-02 | Enforce access control<br>The system shall check role/ownership on each protected request, hash passwords and technician PINs with per-credential salts, and never store raw payment card details. | Session; requested action; credentials. | Authorized response or denial; protected credentials. | A protected operation or credential storage is requested. | Other customers/admin data cannot be modified through forged requests. |
| NFR-03 | Commit purchases consistently<br>The system shall commit payment outcome, transaction snapshot, stock, waste, prepaid balance and loyalty changes atomically and idempotently. | Checkout/retry; current persistent state. | One consistent success or no completed purchase effects. | Checkout starts with a unique request key. | Retries cannot double charge/dispense; failure leaves no partial purchase. |
| NFR-04 | Respond promptly<br>Proposed acceptance target: local menu and quote responses shall complete within 2 seconds in at least 95 of 100 sequential requests on the documented demo machine, excluding external services. | 100 local menu/quote requests. | Recorded durations and pass/fail count. | Demo environment is documented; server warmed up. | Measured results meet the target or the limitation is reported. |
| NFR-05 | Provide reproducible setup<br>The prototype shall run on a clean Python 3.12 environment with a modern browser using pinned runtime dependencies and documented setup, test and launch commands. | Source checkout; Python 3.12; dependency file. | Running prototype and repeatable test results. | Evaluator follows documented installation steps. | All ten selected features have executable demo steps; simulated integrations are identified. |

### Initial product backlog

Lecture format with Description and trace links retained. Importance 0-100, high first; estimates are relative story points, not measured velocity. This is an initial planning artifact, not a claim that every full-system requirement is implemented. F01-F10 and optional F11 have demonstration steps; camera and physical integrations remain deferred.

| ID | Name | Importance | Estimate | Description | How to demo | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| PB-FR-01 | Create an account | 100 | 3 | The system shall register a customer account with unique credentials and a preference profile. | Register a new email; retry the same email and verify rejection. | FR-01; S01; F01 |
| PB-FR-02 | Authenticate customers | 100 | 5 | The system shall authenticate credentials or a registered NFC/card identifier and load only the corresponding customer's profile. | Use password and DEMO-NFC-001; wrong password is denied. | FR-02; S01; F01 |
| PB-FR-07 | Check ingredient availability | 100 | 5 | The system shall reject menu selections and confirmed recipes if an ingredient is depleted, below its minimum threshold or insufficient for the requested serving. | Refill then exhaust milk; verify milk drink blocked and black coffee still available. | FR-07; S08; F05 |
| PB-FR-11 | Process supported payments | 100 | 8 | The system shall support EMV chip/contactless credit/debit, Apple Pay, Google Pay and prepaid employee cards and distinguish approved, declined and pending outcomes. | Run each method using the simulator; decline one; prepaid insufficient funds is denied. | FR-11; S09; F07 |
| PB-FR-12 | Record completed transactions | 100 | 5 | The system shall record each completed purchase once with owner/guest reference, timestamp, original recipe settings, price and payment outcome and show the owner's history. | Buy an oat recipe, edit it to dairy and verify old history remains oat; retry checkout key and verify one charge. | FR-12; S02; F07 |
| PB-FR-15 | Authenticate maintenance personnel | 100 | 5 | The system shall restrict administrative actions to technicians authenticated by physical key, registered master NFC card or technician PIN. | Technician PIN creates admin session; customer token on maintenance endpoint is denied. | FR-15; S12; F10 |
| PB-FR-17 | Monitor waste and halt safely | 100 | 8 | The system shall monitor liquid and grounds bins, warn near capacity and halt dispensing on full/overflow status until a technician records emptying. | Simulate full grounds, verify checkout blocked, empty grounds and verify ordering resumes. | FR-17; S14; F10 |
| PB-NFR-01 | Protect facial-image privacy | 100 | 5 | All camera frames shall be processed only in volatile memory, discarded immediately after inference and never written to disk, logs, databases or external servers. | Inspect filesystem/database and capture network traffic during a real inference run. | NFR-01; S16; Deferred |
| PB-NFR-02 | Enforce access control | 100 | 5 | The system shall check role/ownership on each protected request, hash passwords and technician PINs with per-credential salts, and never store raw payment card details. | Call admin endpoints as customer; edit another user's recipe; inspect credential storage. | NFR-02; S01/S09/S12; security refinement; F01/F10 |
| PB-NFR-03 | Commit purchases consistently | 100 | 8 | The system shall commit payment outcome, transaction snapshot, stock, waste, prepaid balance and loyalty changes atomically and idempotently. | Retry same checkout; force decline/full bin and compare all counters before/after. | NFR-03; S02/S08/S09/G01; integrity refinement; F05/F07/F08 |
| PB-FR-04 | Browse menu and nutrition | 95 | 3 | The system shall display beverage categories, ingredients, allergens, nutrition, prices and availability. | Filter Coffee and Chocolate; inspect calories/allergens and availability. | FR-04; S07/S08; F02 |
| PB-FR-05 | Customize a beverage | 95 | 5 | The system shall validate milk, coffee strength, temperature, syrup and extra-shot choices and update the recipe, price and nutrition before confirmation. | Choose Latte/oat/strong/75 C/two syrup shots; verify quote and invalid value rejection. | FR-05; S07; F03 |
| PB-FR-16 | Register refills | 90 | 3 | The system shall allow authenticated technicians to register full ingredient/cup refills and reset the selected counter to its configured maximum. | Refill milk and cups; verify exact capacity and audit event. | FR-16; S13; F10 |
| PB-FR-19 | Keep manual ordering available | 90 | 5 | When network, weather or optional AI services fail, the system shall continue basic local menu/customization subject to ingredient, payment and safety rules. | Disable network/weather; browse/customize and buy using prepaid balance. | FR-19; S17; F06/F07 |
| PB-NFR-05 | Provide reproducible setup | 90 | 3 | The prototype shall run on a clean Python 3.12 environment with a modern browser using pinned runtime dependencies and documented setup, test and launch commands. | Install pinned dependency, run unit tests and follow the ten-feature walkthrough. | NFR-05; Lab3 Task B/C; F01-F10 |
| PB-FR-03 | Maintain preferences | 85 | 3 | The system shall let authenticated customers update their default milk, strength and temperature. | Save oat milk/strong/75 C, log out/in and verify retained settings. | FR-03; S01; F01 |
| PB-FR-20 | Handle offline payment honestly | 85 | 8 | The system shall use an approved offline-capable method or securely queue permitted pending payments and reconcile once on reconnect; it shall never present an unapproved online-only wallet payment as successful. | Offline prepaid succeeds; wallet stays pending without stock/points changes; reconnect reconciles once. | FR-20; S17; F07 |
| PB-FR-06 | Manage named recipes | 80 | 5 | The system shall save, rename, modify and delete personal recipes and restore their settings for one-touch ordering, subject to current stock checks. | Save Morning Oat, rename/edit it and order it again; another user cannot edit it. | FR-06; S03; F04 |
| PB-FR-18 | Diagnose errors | 80 | 5 | The system shall show real-time faults on the admin dashboard and persist diagnostic events for authorized remote diagnostics when connectivity is available. | Inject a grinder jam; verify time/severity/local log and authorized JSON export. | FR-18; S15; F10 |
| PB-FR-08 | Rank recommendations | 75 | 8 | The system shall score available drinks using preferences, purchase history, time and weather, then reorder and highlight the best recommendations. | Switch period mode (local clock or manual morning/afternoon/evening/night), temperature (cold/mild/warm/hot) and weather condition (unknown/sunny/cloudy/rainy/snowy); buy a drink and verify ranking and reasons. | FR-08; S04/S06/S17; F06 |
| PB-FR-13 | Earn and redeem loyalty | 70 | 5 | The system shall let logged-in customers redeem earned points at checkout and award points after a completed paid purchase, with no changes on decline. | Redeem 100 points, inspect discount/new balance; repeat with declined payment and verify no deduction. | FR-13; G01; F08 |
| PB-FR-14 | Deliver receipts | 70 | 5 | After a completed purchase, the system shall offer a QR receipt or email delivery and offer QR as fallback on email failure. | Open a real QR; request email in local outbox; fail email and verify QR fallback. | FR-14; S10; F09 |
| PB-FR-09 | Analyze mood | 45 | 8 | The system shall use the embedded camera to infer a mood and optionally add it to the recommendation context; unavailable inference shall not prevent manual ordering. | With real module enabled, infer tired mood; deny consent and verify manual ordering still works. | FR-09; S05/S16; Deferred |
| PB-NFR-04 | Respond promptly | 45 | 3 | Proposed acceptance target: local menu and quote responses shall complete within 2 seconds in at least 95 of 100 sequential requests on the documented demo machine, excluding external services. | Measure 100 requests; report p95 and environment without claiming production SLA. | NFR-04; Design assumption; not in brief; F02/F03 |
| PB-FR-10 | Interpret natural-language requests | 30 | 13 | When the optional local LLM is enabled, the system shall translate a broad drink request into up to three distinct supported recipe choices with short reasons and server-calculated prices; precise requests may return fewer choices. The customer selects a recipe before checkout, and follow-up changes use the selected recipe. | Request three strong oat options; compare names, settings, short reasons and prices; apply option two and refine its strength. Verify no automatic purchase, unsupported-option refusal and manual fallback. Keep F06 scoring rationale in technical documentation, not assistant cards. | FR-10; S11; approved three-choice UI refinement; F11 (optional) |

### Comparison with the submitted Lab 2

The comparison uses the group's actual submitted Assignment 2 files, preserved unchanged with hashes in docs/baseline. The student clarified that earlier AI assistance was limited and was not comparable to the extensive generation used for Lab 3. Later AI-generated review corrections are separate reference materials and are not substituted for the submitted version.

| Topic | Submitted Lab 2 | LLM revision | Decision and reason |
| --- | --- | --- | --- |
| Requirement format | 13 short ID/name/shall rows; no inputs, outputs or conditions. | All FR/NFR rows use the six lecture fields; failure postconditions are explicit. | Accept: directly addresses the negative feedback. |
| REQ-01 / menu | Categories and nutrition specified. | FR-04 keeps scope; FR-08 explicitly reorders/highlights scored recommendations. | Accept: menu scoring behavior is in the system description. |
| REQ-02/03 / accounts | Login/profile; creation is ambiguous; saved recipes absent. | FR-01/02/03 separate registration, auth and defaults; FR-06 names/modifies/restores recipes. | Accept: account and recipe requirements were underrepresented. |
| REQ-04/05 / drink | Customization and threshold checks present. | FR-05 validates options and quote; FR-07 also checks serving quantity and rechecks at purchase. | Accept: prevents invalid or stale-stock orders. |
| REQ-06/07 / AI | Context recommendations and in-memory mood present; consent and fallbacks unclear. | FR-08/09 plus NFR-01 preserve mood privacy and provide explicit opt-in/failure handling. | Accept source behavior; opt-in is a design assumption requiring group review. |
| REQ-08 / LLM | Local LLM required as if always installed. | FR-10 explicitly optional/modular and validates customer-confirmed output. | Accept: optional status matches the brief. F11 now supplies real local inference beyond the ten core groups. |
| REQ-09 / payment | Contactless, wallets, employee card; chip and offline flow absent. | FR-11 adds EMV chip; FR-20 distinguishes offline prepaid, pending wallet and once-only reconciliation. | Accept coverage; pending/non-dispensing is an explicit conservative demo policy. |
| Transaction recording | No explicit requirement for immutable customization history. | FR-12 and NFR-03 record snapshots atomically and prevent duplicate purchase effects. | Accept: S02 requires every completed transaction to be recorded. |
| REQ-10 / loyalty | Redemption only; how points are earned is undefined. | FR-13 defines earning after success, bounded redemption and no deduction on failure. | Accept with documented demo conversion rules; group must review those rules. |
| REQ-11 / receipt | QR/email included. | FR-14 adds delivery failure/QR fallback and immutable receipt source. | Accept: concrete observable behavior for existing story. |
| REQ-12 / maintenance | Secure admin/refills/waste monitoring stated together. | FR-15/16/17 identify credentials, exact counter reset, alerts and overflow halt. | Accept: explicit safety behavior was missing. |
| REQ-13 / diagnostics | Store/display real-time faults for diagnostics. | FR-18 adds authorized remote diagnostic availability and local preservation during outage. | Accept: matches source; prototype supplies export, not a deployed remote service. |
| Non-functional requirements | Privacy mixed into mood; no separate integrity/setup/performance criteria. | NFR-01..05 define privacy, security, atomicity, proposed response target and reproducible setup. | Accept privacy/security/integrity; 2-second target is proposed, not a source mandate. |
| Backlog | 13 rows with accepted demos and estimates, no explicit trace links/units. | 25 rows use same required columns plus notes, FR/NFR/story links and story-point units. | Accept: preserves artifact structure; estimates remain planning judgments. |

### User-story comparison: original to revised

Story IDs are local to each assignment: Lab 2 US-04 and Lab 3 US-04 describe different goals. The left column and quoted wording below come from docs/baseline/submitted-task2b.md, not the later generated Lab 2 review reference. All 13 submitted stories are retained, clarified or split into 17 revised stories; seven additional stories bring the total to 24. No original customer/technician goal is silently dropped. More stories indicate finer granularity and restored coverage, not proof of higher quality or implementation of deferred capabilities.

| Submitted story | Original wording | Revised story links | Change and justification |
| --- | --- | --- | --- |
| Lab 2 US-01 / Browse Menu and Nutrition | As a Customer, I want to browse beverage categories and inspect nutrition information so that I can choose a drink that fits my preferences and dietary needs. | Lab 3 US-04 / Menu and nutrition | Retain: the customer goal is unchanged; availability is explicit. Illustrative nutrition does not establish dietary or allergy safety. |
| Lab 2 US-02 / Log In | As a Customer, I want to log in using credentials or an NFC/card tap so that I can quickly access my personal preference profile. | Lab 3 US-02 / Customer login | Retain and clarify: the card must be registered to the corresponding account. Explicit authentication and ownership checks address the observed Alex-login defect. |
| Lab 2 US-03 / Create or Manage Profile | As a Customer, I want to create and manage my preference profile so that the machine can remember my favorite drink settings. | Lab 3 US-01 / Account registration; US-03 / Preferences | Split: account creation and editing defaults have different authentication conditions and independently observable results. Saved recipes are separately added as US-06. |
| Lab 2 US-04 / Customize Beverage | As a Customer, I want to customize beverage parameters such as milk type, coffee strength, temperature, and syrup shots so that I receive the exact drink I want. | Lab 3 US-05 / Customization | Clarify: explicitly include extra espresso shots and supported settings; server validation and a visible quote make the existing goal testable. |
| Lab 2 US-05 / Check Ingredient Availability | As a Customer, I want the machine to prevent unavailable drink selections so that I do not order a beverage that cannot be prepared. | Lab 3 US-07 / Availability | Retain and strengthen: reject unavailable customized recipes before payment. Threshold, serving quantity and checkout revalidation are specified in FR-07. |
| Lab 2 US-06 / Generate Recommendations | As a Customer, I want to receive personalized beverage recommendations so that I can quickly choose a drink based on my preferences, history, time of day, and context. | Lab 3 US-08 / Recommendations | Clarify: identify weather as context and rank available drinks. Preferences remain an explicit input in FR-08. Service-failure behavior is separately added as US-19. |
| Lab 2 US-07 / Analyze Mood | As a Customer, I want the machine to analyze my mood when recommendation mode is used so that it can suggest drinks that match my current state. | Lab 3 US-09 / Mood suggestions; US-21 / Image privacy | Separate recommendation benefit from image protection. Opt-in is a proposed design refinement; in-memory disposal is a source constraint. Camera implementation remains deferred. |
| Lab 2 US-08 / Process Natural Language Order | As a Customer, I want to request a drink using free-form natural language so that I can order complex custom drinks without manually navigating every menu option. | Lab 3 US-10 / Natural-language ordering | Correct scope: the model is optional and proposes supported settings for confirmation. A later approved UI refinement offers up to three recipes with reasons/prices and selected-recipe follow-ups, without technical scores. Reject treating a proposal as permission to purchase. |
| Lab 2 US-09 / Process Payment | As a Customer, I want to pay using supported methods such as contactless card, digital wallet, or prepaid employee card so that I can complete checkout quickly. | Lab 3 US-11 / Payment | Retain: supported payment choice remains the customer goal. FR-11 specifies methods and outcomes; US-12, US-20 and US-22 separately expose recording, offline status and retry integrity. |
| Lab 2 US-10 / Redeem Loyalty Points | As a Customer, I want to redeem loyalty points earned from previous purchases so that I can receive discounts or free drinks. | Lab 3 US-13 / Loyalty | Expand: earning becomes explicit alongside redemption. Accept the group's extension; conversion rates are documented demo assumptions, not source requirements. |
| Lab 2 US-11 / Receive Receipt | As a Customer, I want to receive a receipt by QR code or email so that I can keep proof of my purchase. | Lab 3 US-14 / Receipts | Retain: the two channels and benefit are unchanged. FR-14 adds QR fallback when email fails; prototype email delivery is simulated. |
| Lab 2 US-12 / Manage Inventory | As a Technician, I want to register ingredient refills and monitor waste levels so that the machine remains operational and does not offer drinks with depleted ingredients. | Lab 3 US-15 / Protected administration; US-16 / Refills; US-17 / Waste safety | Split: authorization, full-counter refill and overflow protection are different outcomes. Accept explicit cup refills, warnings and halt behavior from the system description. |
| Lab 2 US-13 / View Error Logs | As a Technician, I want to view real-time machine error logs so that I can diagnose problems such as grinder jams, heater faults, and low ingredient thresholds. | Lab 3 US-18 / Diagnostics | Expand: include persistence through outages and authorized remote diagnosis from S15/S17. The prototype supplies local logs/export; remote deployment remains deferred. |

### Seven additional stories

| New story | Requirement / source | Reason for addition |
| --- | --- | --- |
| US-06 / Saved recipes | FR-06; S03 | Add: the submitted stories omitted naming, modifying and restoring personal recipes. Preferences alone do not cover reusable named recipes. |
| US-12 / Order records | FR-12; S02 | Add: record every completed transaction with its original customization settings. Payment alone does not express later history inspection. |
| US-19 / Service failure | FR-19; S17 | Add: preserve manual ordering when network or optional services fail, subject to payment, stock and safety rules. |
| US-20 / Offline status | FR-20; S17 | Add: distinguish pending online-only authorization from a completed offline-capable purchase. Pending without dispensing is the documented prototype policy. |
| US-22 / Reliable purchase | NFR-03; design refinement of S02/S09/S17 | Add: make once-only retry and consistent purchase effects observable. Atomicity/idempotency are engineering refinements, not verbatim source wording. |
| US-23 / Responsive ordering | NFR-04; proposed design assumption | Add: make responsiveness measurable. The two-second target is proposed and applies only to warmed local menu/quote calls. |
| US-24 / Repeatable assessment | NFR-05; Lab 3 Tasks B/C | Add: make independent-machine setup and feature demonstration explicit. This is an assessment need rather than a customer feature in the system description. |

### Assignment 2 authorship clarification

Assignment 2 authorship clarification: earlier assistant statements inferred that AI assistance meant the submitted Assignment 2 was AI-generated or unsuitable as the human-elicited comparison baseline. That inference was unsupported and is withdrawn. The comparison is between the group's preserved submitted work and the Lab 3 LLM-generated artifacts. This clarification neither attributes Assignment 2 authorship to AI nor claims that no assistance occurred. Historical transcript statements are preserved as recorded messages, not endorsed as current findings.

### Rejected design alternatives

These are options evaluated and rejected during this generation, not fabricated earlier model responses.

| Option | Decision / justification |
| --- | --- |
| Cloud facial-image analysis or image retention | Reject: directly contradicts the mandatory in-memory/no-transmission constraint. |
| Force account login before any manual order | Reject: account-only ordering is not required and would weaken basic manual fallback. |
| Mark offline Apple Pay/Google Pay as approved without processor support | Reject: the prototype cannot assume external financial approval. Show pending and do not dispense. |
| Call a keyword parser a local LLM or call a mood dropdown computer vision | Reject: would misrepresent implementation. F11 uses actual local-model inference; camera/mood inference remains deferred. |
| Subscriptions, social sharing and multiple-drink baskets | Reject from scope: not requested; no need to enlarge the minimum usable prototype. |
| Conflate submitted Assignment 2 with later AI-generated review corrections | Reject: compare the preserved group submission. The student clarified that earlier limited AI assistance was not equivalent to Lab 3 generation; later generated review aids must not replace the baseline. |

### Critical evaluation of the assistant

The earlier assistant checked names in a serialized Astah ZIP and PDF and overclaimed completeness. The actual feedback identified the missing requirement fields. A supported-API inspection in this revision additionally found that Process Payment contained the natural-language description, Analyze Mood had no completed fields, Check Ingredient Availability was absent from the diagram canvas, and optional/mandatory relationships conflicted with descriptions. This shows why matching names is insufficient. The expanded elicitation improves coverage and traceability, but point rules, consent and latency targets remain design proposals; hardware and external-service realism require separate validation.

## Task B - Selected implementation

| Feature | Functionality | Requirements | Demonstration |
| --- | --- | --- | --- |
| F01 | Accounts, login and preferences | FR-01/02/03, NFR-02 | Create account; password/NFC login; save default milk/strength/temperature; log out/in. |
| F02 | Menu, categories and nutrition | FR-04 | Browse six drinks; filter Coffee/Chocolate; inspect estimated nutrition and allergens. |
| F03 | Validated custom drink quote | FR-05 | Change milk, strength, temperature, syrup and shots; observe server-calculated quote. |
| F04 | Named personal recipes | FR-06 | Save Morning Oat; rename; load and edit settings; save update; delete. |
| F05 | Ingredient/quantity checks | FR-07, NFR-03 | Set oat level below threshold as technician; verify oat recipe cannot be purchased; refill. |
| F06 | Context/history recommendations | FR-08/19 | Toggle Recommended first; switch local-clock or manual period (morning/afternoon/evening/night), temperature (cold/mild/warm/hot) and condition (unknown/sunny/cloudy/rainy/snowy); verify history, saved-recipe and preference reasons and offline fallback. |
| F07 | Checkout and immutable history | FR-11/12/20, NFR-03 | Use five payment methods; set external decline in technician Test scenarios; inspect history/retries and offline reconciliation. |
| F08 | Earn and redeem loyalty | FR-13 | Apply 100 points; verify SEK 10 discount and success-only deduction/earning. |
| F09 | QR receipt and email adapter | FR-14 | Open receipt QR/text; send to local simulator outbox; fail email and retain QR fallback. |
| F10 | Protected maintenance/diagnostics | FR-15/16/17/18 | PIN/master-NFC login; full refill; waste halt/empty; fault logging; authorized diagnostic export. |

### Optional addition

| Feature | Functionality | Requirements | Demonstration |
| --- | --- | --- | --- |
| F11 | Local drink assistant | FR-10/19 | Ask for three strong oat options; compare names, short descriptions, settings and server prices without technical scores. Apply option two, request a strength change and verify that recipe remains active. Precise requests may yield fewer choices; checkout remains separate. |

### Scope and assumptions

- Prototype money uses integer ore (100 ore = SEK 1); demo prices/nutrition/ingredient quantities are illustrative and are not production dietary specifications.
- Loyalty: earn one point per whole SEK actually paid; one point redeems SEK 0.10, bounded by balance and price. Demo Alex begins with 250 points and SEK 200 prepaid credit; new accounts begin with zero.
- Customer orders may be placed as guest; profile/recipe/history and prepaid/loyalty features require customer login. Guest receipts use an unguessable capability token.
- Mood opt-in and the proposed 2-second response target are design refinements; the original brief does not prescribe consent UI, a numerical latency target or point-conversion rules.
- Weather/time, NFC/key signals, machine sensors, payment approval and email are simulated locally. Recommendation scoring uses separate deterministic affinity tables (preserving generic recipe defaults), period mode (manual technician override or injectable local clock across morning/afternoon/evening/night), online temperature (cold/mild/warm/hot), online weather condition (unknown/sunny/cloudy/rainy/snowy), and customer-owned preferences, saved recipes (+15) and completed-order count (+12 per order up to +36 as 'A frequent choice'). Manual ordering and stored-value prepaid payments work while the simulated network is offline.
- Online-only payment requests can be persisted as pending without dispensing. Reconnect and customer Retry performs authorization/revalidation once; the prototype never assumes that a wallet can approve offline.
- Camera mood inference remains deferred. F11 adds actual optional local Qwen3 4B inference through Ollama 0.40.6, beyond the ten selected groups. A later approved UI refinement offers up to three supported recipes with short descriptions and server prices, without technical scores. Selected-option context is preserved for further changes; exact named-strength follow-ups also have a narrow consistency guard. No proposal or application purchases or modifies accounts.
- No physical brew command or real card authorization occurs. Admin diagnostics can be exported locally; there is no deployed remote diagnostic service or physical key reader.
- Technician-only Test scenarios controls the persistent external payment mode (Normal/Decline). Customer checkout cannot submit an outcome override. Existing accounts/orders are retained; historical purchases are not reassigned after the authentication fix.
- The model may need a cold load; server inference has a 90-second bound and manual ordering stays independent. The proposed menu/quote latency target excludes optional inference. Model proposals require customer review and fresh server validation.

### Architecture

The HTTP adapter and service layer enforce identity, ownership and purchase rules. SQLite holds persistent local state; checkout uses one write transaction and a unique request key. Customer ordering and technician maintenance/testing share one app but separate protected actions. The optional model adapter is loopback-only and has no ordering side effects. See ARCHITECTURE.md for responsibilities and trust boundaries.

### Validation and revisions

QA_RESULTS.md and evidence/ contain actual runs (38 unit tests in evidence/current/unit-tests.txt and 65 browser checks in evidence/current/browser-results.json), including the three-choice assistant and selected-option follow-up. The student exposed a browser authentication defect: hidden demo NFC data overrode entered passwords. A failing regression reproduced it; explicit methods and two-customer browser tests now verify identity, ownership and restart persistence. Earlier passing tests were insufficient because they only used Alex for browser customer login. Subsequent evaluation and implementation in Google Antigravity (Gemini 4 Argon Medium) resolved multi-turn F11 assistant context/constraint issues (replacing a leaked synthetic assistant turn with a trailing system context snapshot, ordering config before message in RESPONSE_SCHEMA, and refusing unsupported iced/caramel requests without silent substitution or unrequested extra espresso; 8/8 in evidence/current/assistant-heldout-postchange.json, 12/12 in evidence/current/assistant-conversations.json, and 9/9 recipe turns in evidence/current/assistant-long-chat.json) and expanded F06 recommendations across manual vs local-clock periods (morning/afternoon/evening/night), temperatures (cold/mild/warm/hot), weather conditions (unknown/sunny/cloudy/rainy/snowy), and customer-isolated preferences, saved recipes (+15) and completed-order frequency (+12 per order up to +36 as 'A frequent choice'). Simulator tests do not validate real hardware or financial/email processors.

### Recommended extra experimentation

The instructor strongly recommends additional experimentation, but does not state a fourth mandatory task. During Lab 3 verification, the project conducted an empirical before/after evaluation of multi-turn local-model behavior and deterministic recommendation ranking against isolated temporary databases: the 8-turn held-out assistant baseline (evidence/history/assistant-heldout-baseline.json, 5/8 turns passed) exposed a leaked synthetic context turn, base-drink rigidity, silent substitution of unsupported iced/caramel requests and unrequested extra espresso shots; replacing the synthetic assistant turn with a trailing system context snapshot and ordering config before message improved results to 7/8 on the first post-change run (evidence/history/assistant-heldout-postchange-first-run.json) and 8/8 on the final regression run (evidence/current/assistant-heldout-postchange.json), alongside 12/12 in the conversation suite (evidence/current/assistant-conversations.json), 9/9 recipe turns in the long-chat suite (evidence/current/assistant-long-chat.json) and the current extended 65/65 browser checks (evidence/current/browser-results.json, with first-run browser regressions preserved in evidence/history/browser-failure.json and evidence/history/browser-f06-first-run-failure.json). Only the factual test protocol and observed outcomes are reported here; no first-person student reflection is generated by the assistants.

## Task C - Repository and documentation

Repository: https://github.com/kaantanidir/Software_Engi_1_LAB3 . README.md contains environment, installation, execution, tests and all ten feature demos. Each authored Python/JavaScript/Java function documents purpose, inputs and outputs. Vendored Lucide is third-party library code with its license retained. Runtime data, local packages and temporary files are excluded from Git.

### Submission package and clean installation

SUBMISSION.md maps Tasks A-C to the included artifacts and identifies output/G28Lab3_Project.zip as the Canvas upload. GitHub visibility was verified public on 26 October 2026. The source archive was extracted separately and tested with a fresh Python 3.12.14 environment and pinned requirements: pip check passed, 38 unit tests passed, and a separate browser smoke check verified the actual model, example prompts, loading indicator and reduced-motion behavior without personal data or workspace packages. The complete live-model browser suite also passed all 65 checks on the final UI. See evidence/current/clean-install.txt and evidence/current/ux-polish.json. Preparing the package does not submit it to Canvas.

### Review before submission

Review point conversion, pending-payment policy, estimates and model limitations, then run the walkthrough. Detailed prompts/model use are in the appendix. Compare against the preserved group submission, not the later generated Lab 2 review aids; those review aids are not submission materials under the supplied policy.

### AI appendix

The required simple PDF is output/G28Lab3_AI_Appendix.pdf. It contains the student-confirmed model labels, prompt strategy, main prompt and key responses, subsequent clarifications and generated-code references.

The separate docs/DEVELOPMENT_TRANSCRIPT.md preserves available original student prompts and visible Codex replies from the development chat, with recorded timestamps and source hashes in docs/DEVELOPMENT_TRANSCRIPT_MANIFEST.json. It excludes private reasoning, tools, automatic context and declared sensitive details. The PDF appendix is a reading guide with selected interactions, not the full attachment. The separate Gemini/Antigravity session transcript was not available; relayed proposals and its documented contribution are identified as such.

### References

Instructor feedback page 1; Lecture-02-2026 slides 20-23, 30-31, 38, 43 and 47-48; Lecture-03-2026 slides 17, 22, 28, 38-40; system description and assignment guidelines supplied in the chat. Henrik Kniberg, Scrum and XP from the Trenches: https://www.infoq.com/minibooks/download/scrum-xp-from-the-trenches/ (recommended course reading; student completion is not asserted).
