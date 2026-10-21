# Documentation Guide

Start with the repository README for installation and the ten-feature walkthrough.

## Current Lab 3

| Document | Read it for |
| --- | --- |
| [Lab 3 report](LAB3_REPORT.md) | Requirements, user stories, backlog and comparison with the submitted Lab 2 |
| [Architecture](ARCHITECTURE.md) | Responsibilities, data ownership, checkout and the optional model boundary |
| [Verification record](QA_RESULTS.md) | Actual test results, screenshots, failures found and remaining limitations |
| [Evidence index](../evidence/README.md) | Categorized index of verification outputs, runtime model evidence, regressions and baselines |
| [AI interaction record](AI_CONVERSATION.md) | Tool/model roles, main prompts, key responses and revisions |
| [Main supplied prompt](MAIN_PROMPT.md) | Original Lab 2 review / Lab 3 request and assignment text |
| [Cross-lab review](CROSS_LAB_REVIEW.md) | Lab 1 feedback, conceptual mapping and custom-feature chronology |
| [Asset credits](ASSETS.md) | Third-party images, icons and licenses |

Exported Lab 3 report and AI appendix PDFs are directly in `output/` (`output/G28Lab3_Report.pdf` and `output/G28Lab3_AI_Appendix.pdf`), alongside the final source bundle (`output/G28Lab3_Project.zip`). The editable appendix is `LAB3_AI_APPENDIX.md`; it is generated from the prompt and interaction records, not edited independently.

## Development & Handoff History

Internal engineering handoff notes in `docs/development/` remain in Git for development traceability, and are excluded from the final evaluator `output/G28Lab3_Project.zip`:

| Document | Read it for |
| --- | --- |
| [Assistant implementation update](development/ASSISTANT_IMPLEMENTATION_UPDATE.md) | Chronological F11 assistant and F06 recommendation updates, provenance and test outcomes |
| [Continuation handoff](development/GEMINI_HANDOFF.md) | Historical continuation brief written at commit `ee153a9` and post-handoff completion summary |

## Preserved Sources and Historical References

`baseline/` contains the original Lab 2 model/PDF and the Lab 1 model, extracted feedback and SHA-256 manifests. These are comparison evidence, not rewritten submissions.

`reference/lab2/` holds the earlier generated [review](reference/lab2/REVIEW.md), [use-case descriptions](reference/lab2/USE_CASE_DESCRIPTIONS.md), [feedback analysis](reference/lab2/FEEDBACK_CHANGES.md), and the associated historical Astah/PDF/ZIP files (`G28Lab2.asta`, `G28Lab2_Corrected.pdf`, `G28Lab2_Corrected.zip`). They are **review aids only, not for Lab 1-2 submission**, under the supplied course AI policy.

## Rebuilding Documents

Install `requirements-docs.txt`, then run `python tools/build_documents.py`. By default it updates only the current Lab 3 report and AI appendix. `--text-only` omits PDFs. The separate `--include-reference` flag also regenerates historical review aids; it never changes the original files in `baseline/`.

`tools/verify_artifacts.py` checks requirement coverage, source hashes, function documentation and PDF content. It does not turn an AI-generated Lab 1-2 reference into an acceptable submission.
