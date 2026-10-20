# SmartBrew AI - Group 28 - Lab 3

Date: 2026-10-20

## Task A - Elicitation

SmartBrew AI is a personalized coffee-machine system for office customers and maintenance technicians. The full requirements cover profiles, saved recipes, context/mood recommendations, customization, supplies, payments, receipts, diagnostics, privacy and service-failure fallback. The group's custom feature is loyalty redemption. The executable prototype implements ten selected feature groups with persistent local state and a browser interface.

### Models and provenance

GPT-6.1 Sol (model-selector label supplied by the student on 2026-10-20); exact backend build not exposed.

Tasks A, B and C in this revision use this same model through the Codex application. Earlier Lab 2 assistant model/version was not recorded and is not retroactively invented.

The preserved files in docs/baseline are exactly the submitted Lab 2 artifacts extracted from the supplied ZIP. This chat previously assisted creation of Lab 2; it would be inaccurate to label that submission an independently human-authored baseline. The comparison uses the actual submitted group version, then separates the feedback correction from the later LLM-assisted refinement. No later correction is silently substituted for the submitted baseline.

### Prompt strategy

Use the actual system description, feedback and course slides as grounding; constrain all requirements to the six-column lecture template; retain the submitted baseline; check each source capability against stories/requirements/backlog; separate source mandates from proposed design assumptions; select ten coherent demonstrable feature groups; implement and test approval, rejection, ownership, retry, safety and offline paths. This was one evolving chat request with student clarifications, not an invented sequence of separate prompting experiments.

Main prompts, student clarifications and assistant response excerpts are recorded in AI_CONVERSATION.md. Generated code is retained in Git; do not describe the artifacts as independently human authored.

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
| US-10 | Natural-language ordering | As a Customer, I want the optional local LLM to interpret a free-form request so that I can confirm a custom recipe without navigating every option. | FR-10 |
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
| FR-10 | Interpret natural-language requests<br>When the optional local LLM is enabled, the system shall translate a free-form request into supported recipe parameters and ask for confirmation or clarification. | Request text; local model; supported menu/options. | Validated recipe proposal or clarification question. | Optional module is installed and enabled. | Only customer-confirmed and validated parameters reach ordering. |
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

Same required format as corrected Lab 2. Importance 0-100, high first; estimate in relative story points. Proposed values are not measured team velocity or a promised delivery date. Dependencies: accounts before private recipes/history; quotes/availability before checkout; approved purchase before loyalty/receipts. Optional AI and physical integrations remain backlog work.

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
| PB-FR-08 | Rank recommendations | 75 | 8 | The system shall score available drinks using preferences, purchase history, time and weather, then reorder and highlight the best recommendations. | Switch cold/hot and morning/afternoon context; buy a drink and verify history affects ranking. | FR-08; S04/S06/S17; F06 |
| PB-FR-13 | Earn and redeem loyalty | 70 | 5 | The system shall let logged-in customers redeem earned points at checkout and award points after a completed paid purchase, with no changes on decline. | Redeem 100 points, inspect discount/new balance; repeat with declined payment and verify no deduction. | FR-13; G01; F08 |
| PB-FR-14 | Deliver receipts | 70 | 5 | After a completed purchase, the system shall offer a QR receipt or email delivery and offer QR as fallback on email failure. | Open a real QR; request email in local outbox; fail email and verify QR fallback. | FR-14; S10; F09 |
| PB-FR-09 | Analyze mood | 45 | 8 | The system shall use the embedded camera to infer a mood and optionally add it to the recommendation context; unavailable inference shall not prevent manual ordering. | With real module enabled, infer tired mood; deny consent and verify manual ordering still works. | FR-09; S05/S16; Deferred |
| PB-NFR-04 | Respond promptly | 45 | 3 | Proposed acceptance target: local menu and quote responses shall complete within 2 seconds in at least 95 of 100 sequential requests on the documented demo machine, excluding external services. | Measure 100 requests; report p95 and environment without claiming production SLA. | NFR-04; Design assumption; not in brief; F02/F03 |
| PB-FR-10 | Interpret natural-language requests | 30 | 13 | When the optional local LLM is enabled, the system shall translate a free-form request into supported recipe parameters and ask for confirmation or clarification. | Request sweet but low dairy; inspect parsed proposal; reject unsupported ingredients. | FR-10; S11; Deferred |

### Comparison with the submitted Lab 2

The preserved files in docs/baseline are exactly the submitted Lab 2 artifacts extracted from the supplied ZIP. This chat previously assisted creation of Lab 2; it would be inaccurate to label that submission an independently human-authored baseline. The comparison uses the actual submitted group version, then separates the feedback correction from the later LLM-assisted refinement. No later correction is silently substituted for the submitted baseline.

| Topic | Submitted Lab 2 | LLM revision | Decision and reason |
| --- | --- | --- | --- |
| Requirement format | 13 short ID/name/shall rows; no inputs, outputs or conditions. | All FR/NFR rows use the six lecture fields; failure postconditions are explicit. | Accept: directly addresses the negative feedback. |
| REQ-01 / menu | Categories and nutrition specified. | FR-04 keeps scope; FR-08 explicitly reorders/highlights scored recommendations. | Accept: menu scoring behavior is in the system description. |
| REQ-02/03 / accounts | Login/profile; creation is ambiguous; saved recipes absent. | FR-01/02/03 separate registration, auth and defaults; FR-06 names/modifies/restores recipes. | Accept: account and recipe requirements were underrepresented. |
| REQ-04/05 / drink | Customization and threshold checks present. | FR-05 validates options and quote; FR-07 also checks serving quantity and rechecks at purchase. | Accept: prevents invalid or stale-stock orders. |
| REQ-06/07 / AI | Context recommendations and in-memory mood present; consent and fallbacks unclear. | FR-08/09 plus NFR-01 preserve mood privacy and provide explicit opt-in/failure handling. | Accept source behavior; opt-in is a design assumption requiring group review. |
| REQ-08 / LLM | Local LLM required as if always installed. | FR-10 explicitly optional/modular and validates customer-confirmed output. | Accept: optional status matches the brief; defer real LLM from ten-feature prototype. |
| REQ-09 / payment | Contactless, wallets, employee card; chip and offline flow absent. | FR-11 adds EMV chip; FR-20 distinguishes offline prepaid, pending wallet and once-only reconciliation. | Accept coverage; pending/non-dispensing is an explicit conservative demo policy. |
| Transaction recording | No explicit requirement for immutable customization history. | FR-12 and NFR-03 record snapshots atomically and prevent duplicate purchase effects. | Accept: S02 requires every completed transaction to be recorded. |
| REQ-10 / loyalty | Redemption only; how points are earned is undefined. | FR-13 defines earning after success, bounded redemption and no deduction on failure. | Accept with documented demo conversion rules; group must review those rules. |
| REQ-11 / receipt | QR/email included. | FR-14 adds delivery failure/QR fallback and immutable receipt source. | Accept: concrete observable behavior for existing story. |
| REQ-12 / maintenance | Secure admin/refills/waste monitoring stated together. | FR-15/16/17 identify credentials, exact counter reset, alerts and overflow halt. | Accept: explicit safety behavior was missing. |
| REQ-13 / diagnostics | Store/display real-time faults for diagnostics. | FR-18 adds authorized remote diagnostic availability and local preservation during outage. | Accept: matches source; prototype supplies export, not a deployed remote service. |
| Non-functional requirements | Privacy mixed into mood; no separate integrity/setup/performance criteria. | NFR-01..05 define privacy, security, atomicity, proposed response target and reproducible setup. | Accept privacy/security/integrity; 2-second target is proposed, not a source mandate. |
| Backlog | 13 rows with accepted demos and estimates, no explicit trace links/units. | 25 rows use same required columns plus notes, FR/NFR/story links and story-point units. | Accept: preserves artifact structure; estimates remain planning judgments. |

### Rejected design alternatives

These are options evaluated and rejected during this generation, not fabricated earlier model responses.

| Option | Decision / justification |
| --- | --- |
| Cloud facial-image analysis or image retention | Reject: directly contradicts the mandatory in-memory/no-transmission constraint. |
| Force account login before any manual order | Reject: account-only ordering is not required and would weaken basic manual fallback. |
| Mark offline Apple Pay/Google Pay as approved without processor support | Reject: the prototype cannot assume external financial approval. Show pending and do not dispense. |
| Call a keyword parser a local LLM or call a mood dropdown computer vision | Reject: would misrepresent implementation. Real camera inference/local LLM are deferred and not counted as implemented features. |
| Subscriptions, social sharing and multiple-drink baskets | Reject from scope: not requested; no need to enlarge the minimum usable prototype. |
| Present Lab 2 as an independently human-authored baseline | Reject: this chat already assisted generation of Lab 2. Preserve the actual submitted version and disclose that provenance. |

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
| F06 | Context/history recommendations | FR-08/19 | Toggle Recommended first; change simulated weather/time; buy a drink and verify ranking reasons. |
| F07 | Checkout and immutable history | FR-11/12/20, NFR-03 | Approve/decline five payment simulators; inspect history; retry a request; test offline pending then reconnect. |
| F08 | Earn and redeem loyalty | FR-13 | Apply 100 points; verify SEK 10 discount and success-only deduction/earning. |
| F09 | QR receipt and email adapter | FR-14 | Open receipt QR/text; send to local simulator outbox; fail email and retain QR fallback. |
| F10 | Protected maintenance/diagnostics | FR-15/16/17/18 | PIN/master-NFC login; full refill; waste halt/empty; fault logging; authorized diagnostic export. |

### Scope and assumptions

- Prototype money uses integer ore (100 ore = SEK 1); demo prices/nutrition/ingredient quantities are illustrative and are not production dietary specifications.
- Loyalty: earn one point per whole SEK actually paid; one point redeems SEK 0.10, bounded by balance and price. Demo Alex begins with 250 points and SEK 200 prepaid credit; new accounts begin with zero.
- Customer orders may be placed as guest; profile/recipe/history and prepaid/loyalty features require customer login. Guest receipts use an unguessable capability token.
- Mood opt-in and the proposed 2-second response target are design refinements; the original brief does not prescribe consent UI, a numerical latency target or point-conversion rules.
- Weather/time, NFC/key signals, machine sensors, payment approval and email are simulated locally. Manual ordering and stored-value prepaid payments work while the simulated network is offline.
- Online-only payment requests can be persisted as pending without dispensing. Reconnect and customer Retry performs authorization/revalidation once; the prototype never assumes that a wallet can approve offline.
- Camera mood inference and the optional local LLM are elicited but deferred from the selected ten features. A keyword parser and a mood selector are not presented as AI implementations.
- No physical brew command or real card authorization occurs. Admin diagnostics can be exported locally; there is no deployed remote diagnostic service or physical key reader.

### Architecture

A Python HTTP adapter serves a vanilla JavaScript interface. A service layer enforces authorization and business rules. SQLite persists accounts, hashed sessions, recipes, orders, stock, waste, pending requests, events and email simulator outbox. Checkout uses a write transaction and unique request key. QR generation uses the pinned qrcode library. No external service is required after installation.

### Validation

See QA_RESULTS.md and evidence/ for actual recorded runs. Unit tests use isolated temporary databases. Browser checks use a separate QA database and verify desktop/mobile layout and end-to-end flows. Passing simulator tests does not validate actual hardware, financial processors, SMTP or camera/LLM inference.

## Task C - Repository and documentation

Repository: https://github.com/kaantanidir/Software_Engi_1_LAB3 . README.md contains environment, installation, execution, tests and all ten feature demos. Each authored Python/JavaScript/Java function documents purpose, inputs and outputs. Vendored Lucide is third-party library code with its license retained. Runtime data, local packages and temporary files are excluded from Git.

### Student review before submission

Review the exact point conversion, pending-payment policy, estimates and optional-feature scope. Read and understand the implementation and run the walkthrough. The baseline comparison is intentionally labeled group submission previously assisted by AI; confirm that disclosure with the course if a strictly independent human baseline is required.

### References

Instructor feedback page 1; Lecture-02-2026 slides 20-23, 30-31, 38, 43 and 47-48; Lecture-03-2026 slides 17, 22, 28, 38-40; system description and assignment guidelines supplied in the chat. Henrik Kniberg, Scrum and XP from the Trenches: https://www.infoq.com/minibooks/download/scrum-xp-from-the-trenches/ (recommended course reading; student completion is not asserted).
