# Cross-lab continuity review

Reviewed 2026-10-21. This is AI-assisted Lab 3 analysis, not replacement text or a replacement model for Labs 1 or 2.

## What the Lab 1 feedback actually says

The final grade is **Positive**. Every class-diagram criterion is marked Yes. The component diagram has two Partial findings: its major-component coverage is "A bit minimalistic", and the relationships comment asks "Every connection is a dependency, the UI really needs the AIEngine?" The remaining component criteria are Yes. These observations do not mean the whole submission failed.

Original files are preserved in `docs/baseline/lab1`; SHA-256 hashes and source locations are in its manifest. The API inspector opens without saving. Native diagram exports are in `evidence/lab1-export`.

## Actual domain model and implementation mapping

The saved class diagram shows **nine domain concepts**, rather than the eleven classes discussed earlier in the chat. A conceptual domain model does not require one identically named code class or database table per concept.

| Lab 1 concept | Lab 3 representation | Scope difference |
| --- | --- | --- |
| User, Customer, Technician | Users, role checks, sessions and protected HTTP actions | Shared persistence and authorization rather than a literal inheritance hierarchy |
| PreferenceProfile | Customer preference configuration | One active default configuration per customer in the prototype |
| BeverageRecipe | Menu/configuration and owned saved recipes | Named recipes support create, update, load and delete |
| Order | Completed order snapshot and pending requests | Guest ordering is allowed; an order need not have an account |
| Payment | Method, paid amount, discount and status in purchase/pending records | Processor approval is simulated; payment is not a separate deployed subsystem |
| Inventory, Ingredient | Ingredient counters/thresholds and waste-bin state | Refill, quantity validation, overflow halt and diagnostic events are implemented |

Separate technical observation: the visible name `User {Abstract}` communicates intent, but the saved Astah API abstract flag is false. The grader nevertheless accepted the class criteria. The original has not been changed; if the students revisit it, they can inspect Astah's actual Abstract property themselves.

## Component continuity and the feedback concern

| Lab 1 component | Lab 3 mapping |
| --- | --- |
| UserInterface_Touchscreen | Browser interface in `web/` |
| PaymentProcessingModule / CheckoutService | HTTP checkout adapter and transactional service logic |
| BrewingHardwareController / BeveragePreparationService | Simulated ingredient consumption, waste updates and safety checks; no physical brewing |
| AIEngine / RecommendationService | Context/history recommendation heuristic, not a trained LLM |
| Camera / FacialAnalysis; nested MoodAnalyzer and LocalLLMAgent | Requirements retained, but camera inference and actual local LLM are deferred |

The prototype also makes account, recipe, inventory, receipt and diagnostics responsibilities explicit. These are logical responsibilities inside a small local application, not a claim of identical deployment boundaries to the original component diagram.

The UI needs recommendations only for personalized ranking. It must not require them to browse, customize or purchase manually. A browser regression exposed a real violation: HTTP 503 from the recommendation endpoint left the menu blank because rendering waited for that optional response. The fix renders essential state and the quote first, limits the recommendation wait to 1.2 seconds, and falls back to the standard menu. Regression evidence is in `evidence/recommendation-regression-before.txt` and the final browser results. This is ordinary reliability validation, not a claimed student-performed optional experiment.

## Custom-feature chronology

No loyalty class, component or custom-feature note is present in the supplied Lab 1 diagrams. Loyalty redemption is documented in the submitted Lab 2 and retained as F08 in Lab 3. The records therefore call it **the custom extension documented in Lab 2**, rather than claiming it was visibly modeled in Lab 1. The instructor can clarify whether that chronology needs any further explanation; the baseline must not be retroactively rewritten.

## Course AI rules and student responsibilities

The general instructions newly supplied in this interaction limit AI in Labs 1-2 to concept explanations and grammar/spelling checks, and prohibit submitting generated text/models. The Lab 2 correction already generated before those rules were provided is now labeled **AI-generated review reference only, not for submission**. Its historical filename is retained for traceability. Neither original submission is modified. Any Lab 1-2 revision submitted by students must be their own work under the course policy; an AI appendix does not override that restriction.

Lab 3 expressly allows end-to-end generation. Its appendix records GPT-6.1 Sol as the student-confirmed selector label for Tasks A, B and C; the exact backend build and earlier model versions are unknown. The earlier submitted Lab 2 was AI-assisted in this chat and cannot honestly be called an independently human-elicited baseline. That limitation is disclosed; only the instructor can decide whether it satisfies the intended comparison.

The extra experimentation in the instructor's message is **strongly recommended**, not stated as a fourth mandatory task. No optional experiment has been selected or claimed as completed. Mutation testing, if later chosen, can deliberately break a disposable test copy and discard it afterward; it does not remove functionality from the submitted application. Any personal experience/reflection for that exercise must be written by the student. No such first-person reflection is generated here.
