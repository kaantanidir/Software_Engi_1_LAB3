# Use-case review reference descriptions

Previously generated Lab 2 correction: AI-GENERATED REVIEW REFERENCE ONLY - NOT FOR LAB 1 OR LAB 2 SUBMISSION. The general course rules supplied after this reference was generated prohibit submitting generated text/models for those labs. Original submissions are unchanged. Lab 3 explicitly permits generation; disclosure does not override the Lab 1-2 restriction.

Template: Lecture 2 slides 30-31. The AI-generated Astah reference contains the same descriptions; neither is for Lab 2 submission.

## Browse Menu and Nutrition

**Preconditions**

The machine has a local menu.

**InitiatingActor**

Customer

**Goal**

Choose a beverage using category, nutrition and availability information.

**MainScenario**

1. Customer opens the menu.
2. System shows categories, prices and availability.
3. Customer selects a drink.
4. System shows ingredients, allergens and nutrition.

**Alternatives**

2a. A drink is unavailable: system disables selection and explains why.
2b. Recommendations are unavailable: system keeps the standard local menu.

## Log In

**Preconditions**

A registered account or NFC credential exists.

**InitiatingActor**

Customer

**Goal**

Access the correct customer profile.

**MainScenario**

1. Customer selects Log In.
2. Customer provides credentials or taps a registered NFC card.
3. System verifies the credential.
4. System opens the customer's session and profile.

**Alternatives**

3a. Verification fails: system grants no access and allows retry at step 2.

## Create / Manage Profile

**Preconditions**

Machine is operational; editing an existing profile requires its owner's session.

**InitiatingActor**

Customer

**Goal**

Create an account or maintain preferences and named personal recipes.

**MainScenario**

1. Customer chooses account creation or profile management.
2. System shows the appropriate fields.
3. Customer supplies account details or edits preferences/named recipes.
4. System validates ownership and values.
5. System saves changes and confirms them.

**Alternatives**

4a. Email exists or fields are invalid: show errors and resume at step 3.
4b. User is unauthenticated for editing: require login before editing.

## Customize Beverage

**Preconditions**

Customer has selected a base drink; the machine is not halted.

**InitiatingActor**

Customer

**Goal**

Confirm a valid drink with the desired settings.

**MainScenario**

1. Customer opens customization for the selected drink.
2. Customer adjusts supported settings. Extension point: natural-language entry (Process Natural Language Order).
3. System updates recipe, nutrition and price.
4. System includes Check Ingredient Availability.
5. Customer confirms the validated recipe.

**Alternatives**

4a. Unavailable ingredients: system explains the restriction; resume at step 2.
2a. Local LLM unavailable: manual controls remain usable.

## Check Ingredient Availability

**Preconditions**

A base/modified recipe and current ingredient counters exist.

**InitiatingActor**

Customer (indirectly through Customize Beverage)

**Goal**

Prevent an order that cannot be prepared from available ingredients.

**MainScenario**

1. System identifies ingredients and quantities in the recipe.
2. System reads levels and minimum thresholds.
3. System checks depletion, thresholds and serving quantities.
4. System returns available or blocked, with reasons.

**Alternatives**

3a. Any check fails: system marks recipe unavailable; caller resumes customization.
3b. Counter data unavailable: deny purchase until verified; do not assume stock.

## Generate Recommendations

**Preconditions**

A local menu exists; customer profile/history is used when available.

**InitiatingActor**

Customer

**Goal**

Find suitable available drinks.

**MainScenario**

1. Customer requests recommendations.
2. System gathers preferences, history, time and weather. Extension point: optional mood context (Analyze Mood).
3. System excludes unavailable drinks and calculates scores.
4. System reorders and highlights recommended drinks with reasons.

**Alternatives**

2a. Weather/network unavailable: use local context and keep manual ordering.
2b. Mood disabled/unavailable: continue without mood.
2c. No account/history: use generic time/context choices.

## Analyze Mood

**Preconditions**

Camera module is enabled; customer opts in at the recommendation extension point.

**InitiatingActor**

Customer

**Goal**

Add transient mood context while protecting facial images.

**MainScenario**

1. System captures one transient frame into memory.
2. Local inference estimates mood.
3. System releases/discards the frame immediately.
4. System returns only the mood label to recommendations.

**Alternatives**

2a. Inference fails: discard frame and return unavailable; recommendations continue without mood.
1a. Customer does not opt in: do not capture a frame. No image is stored or transmitted.

## Process Natural Language Order

**Preconditions**

Customer is customizing a drink; optional local LLM is enabled.

**InitiatingActor**

Customer (at Customize Beverage extension point)

**Goal**

Translate a free-form request into a confirmed customization proposal.

**MainScenario**

1. Customer selects natural-language entry during customization.
2. Customer enters the request.
3. Local LLM proposes supported parameters.
4. System shows the proposal for confirmation.
5. Customer accepts; return to Customize Beverage step 3 for validation/availability.

**Alternatives**

3a. Ambiguous request: ask for clarification and resume at step 2.
3b. Unsupported ingredient: explain supported choices.
4a. Customer rejects proposal: return to manual customization.

## Process Payment

**Preconditions**

A recipe is confirmed; machine safety and availability are checked again.

**InitiatingActor**

Customer; Payment Processor supports external authorization.

**Goal**

Complete and record an approved purchase exactly once.

**MainScenario**

1. Customer opens checkout.
2. System shows total. Extension point: loyalty redemption (Redeem Loyalty).
3. Customer selects a supported payment method.
4. System checks stock/safety and obtains approval or prepaid debit.
5. System atomically records recipe snapshot, payment and stock/waste/points changes.
6. System confirms success and offers Receive Receipt.

**Alternatives**

4a. Declined/insufficient prepaid funds: no purchase effects; choose another method at step 3.
4b. Offline method unsupported: show pending/denied, do not dispense.
4c. Offline-capable approval: complete with explicit offline status.
5a. Retry: return the existing result for the same request key.

## Redeem Loyalty

**Preconditions**

Customer is logged in at checkout and has sufficient earned points.

**InitiatingActor**

Customer

**Goal**

Apply earned loyalty points to the current purchase.

**MainScenario**

1. Customer chooses to redeem points at Process Payment step 2.
2. System displays points and permitted discount.
3. Customer selects an amount.
4. System validates and updates the proposed total.
5. Return to Process Payment step 3; deduct points only on successful completion.

**Alternatives**

3a. Amount exceeds balance/price: reject it and resume at step 3.
5a. Payment fails or customer cancels: no points are deducted.

## Receive Receipt

**Preconditions**

A completed transaction exists.

**InitiatingActor**

Customer

**Goal**

Obtain proof of purchase.

**MainScenario**

1. System offers QR or email receipt.
2. Customer selects a channel.
3. System generates a receipt from the immutable transaction.
4. System displays a QR receipt or delivers email.

**Alternatives**

4a. Email unavailable: retain the purchase and offer QR.
2a. Customer declines receipt: stop without affecting purchase.

## Manage Inventory

**Preconditions**

Technician authenticated with physical key, master NFC or PIN.

**InitiatingActor**

Technician

**Goal**

Restore supplies and manage waste safely.

**MainScenario**

1. Technician opens maintenance dashboard.
2. System displays ingredient and waste counters and warnings.
3. Technician registers a physical refill or bin emptying.
4. System resets the selected counter to full capacity or zero waste.
5. System records an event and recalculates availability/halt state.

**Alternatives**

2a. Full/overflow bin: halt ordering until the affected bin is emptied.
3a. Unauthorized request: deny without counter changes.
5a. Other safety fault remains: keep machine halted.

## View Error Logs

**Preconditions**

Technician has an authorized admin session.

**InitiatingActor**

Technician

**Goal**

Diagnose faults using persistent events.

**MainScenario**

1. Technician opens diagnostics.
2. System shows timestamped events with severity/code/message.
3. Technician selects an event.
4. System displays details and offers authorized diagnostic export.

**Alternatives**

2a. No events: show empty state.
4a. Remote connection unavailable: preserve local events and retry later. Log viewing is independent of refilling.