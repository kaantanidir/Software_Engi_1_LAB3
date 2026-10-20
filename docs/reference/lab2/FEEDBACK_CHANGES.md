# Feedback and the concrete correction

**AI-generated review reference only, not for Lab 1 or Lab 2 submission.** The general policy supplied later prohibits submitting generated text/models for those labs. The original files remain untouched. This comparison is retained as Lab 3 analysis and historical provenance.

Source: instructor feedback, page 1 of the provided feedback PDF; Lecture 2 slides 20-23, 30-31 and 47-48.

| Finding | Original | Correction |
| --- | --- | --- |
| Requirements incomplete (negative) | ID, name and a shall sentence only | Every retained REQ-01..13 has Description, Inputs, Outputs, Precondition and Postcondition. |
| Boundary/layout (partial) | Payment Processor on left, Technician below | Customer and Technician outside the boundary on left; secondary processor outside on right. |
| Customer entry/extension (partial) | Customer associated directly with natural-language use case; customization has no direct customer association | Customer participates in Customize Beverage; optional natural-language use case extends that base, with a named extension point. |
| Other relationships | Mood always included despite optional descriptions; logs included on every inventory operation | Optional mood extends recommendations; technician independently accesses inventory and logs; customization includes ingredient availability. |
| Saved descriptions found during API inspection | Payment contained the LLM description; mood description empty; some names had trailing whitespace/newlines | All thirteen descriptions rewritten consistently; whitespace removed; same use-case identities retained. |
| Canvas coverage | Ingredient Availability existed in model but was not shown on canvas | Included use case visible and connected on corrected diagram. |
| Extra coverage review | Saved named recipes, transaction snapshots, offline behavior and overflow halt underrepresented in PDF | Clarified in the same 13 grouped requirements; separately decomposed and compared in Lab 3. |

The feedback's final grade is positive. This is a documented revision, not a claim that the original was rejected. Model-only checks of string presence were insufficient; the new diagram is checked through Astah's supported model API and image export.

Dashed `<<include>>` points from **Customize Beverage** to **Check Ingredient Availability**. Dashed `<<extend>>` points from each optional feature to its **base**. A use-case diagram describes participation/reuse/variation, not the chronological ordering of checkout steps.

The original course template's InitiatingActor row is derived from direct associations. For extension/included behavior, the indirect actor is explicitly recorded in the use case's Definition and the accompanying textual artifact. Blank auto-actor cells are not silently presented as manually filled cells.
