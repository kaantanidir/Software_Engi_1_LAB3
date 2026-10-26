# Group 28 - Software Engineering Lab 3

GitHub repository: **https://github.com/kaantanidir/Software_Engi_1_LAB3**

The repository was verified public on 26 October 2026. The instructor can access it without a collaborator invitation. The stated submission deadline is **26 October 2026**.

## Canvas upload

Upload **`output/SmartBrew_Lab3_Canvas.zip`**. This compact archive contains seven files: the report, AI appendix, main prompt, interaction record, original development transcript, transcript manifest and a README with the GitHub reference for Task B. Source code and execution instructions are available in the public repository.

Paste the GitHub repository URL above into the Canvas submission text and complete the Submit step. The larger `output/G28Lab3_Project.zip` is an optional full source bundle.

## Where to find the assessed work

| Task | Material |
| --- | --- |
| A - Requirements, user stories, product backlog and critical comparison | [Lab 3 report PDF](output/G28Lab3_Report.pdf) and [editable report](docs/LAB3_REPORT.md) |
| A - Prompt strategy, model versions, key responses and decisions | [AI appendix PDF](output/G28Lab3_AI_Appendix.pdf), [main prompt](docs/MAIN_PROMPT.md) and [interaction record](docs/AI_CONVERSATION.md) |
| A/B - Available original development conversation | [Transcript](docs/DEVELOPMENT_TRANSCRIPT.md) and [source/integrity manifest](docs/DEVELOPMENT_TRANSCRIPT_MANIFEST.json); the scope notice identifies unavailable material and redactions |
| B - Executable prototype and ten selected feature groups | Source in this archive and repository; [README setup, execution, tests and feature walkthrough](README.md) |
| B - Observed verification and screenshots | [QA results](docs/QA_RESULTS.md) and [evidence index](evidence/README.md) |
| C - Architecture and code documentation | [Architecture](docs/ARCHITECTURE.md), function comments and [documentation index](docs/README.md) |

## Evaluation environment

The documented evaluation platform is Windows with Python 3.12. Install the pinned dependencies from `requirements.txt` and follow the README. The ten core feature groups run without an LLM. F11 is an additional local drink assistant requiring a separate one-time Ollama installation and `qwen3:4b` model download; the Windows app launcher then starts or reuses Ollama automatically. Runtime binaries, model weights, virtual environments and personal databases are excluded from the ZIP.

Payment, NFC, weather/sensor inputs and email use documented local simulators. Camera mood inference is deferred. The report distinguishes implemented features, proposed requirements and these limits.
