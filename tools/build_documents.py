"""Export the same structured coursework data to editable Markdown and readable PDFs."""

import base64
import json
import re
from pathlib import Path
from xml.sax.saxutils import escape

import reportlab
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image

from coursework_data import LAB3, GROUPS2, STORIES2, STORIES3, USECASES, SOURCES, COMPARISON, REJECTIONS, STORY_COMPARISON, ADDED_STORIES, STORY_COMPARISON_NOTE

ROOT = Path(__file__).resolve().parents[1]
DOCUMENT_DATE = "2026-10-26"
MODEL = "Codex with student-confirmed selector label GPT-6.1 Sol (2026-10-20/21, initial Lab 3 Tasks A-C and web-chat handoff integration; exact backend build not exposed) and Gemini 4 Argon Medium through Google Antigravity (2026-10-21, local repository inspection, F11 multi-turn assistant evaluation/correction and F06 deterministic recommendation expansion and verification)."
FEATURES = [
    ("F01", "Accounts, login and preferences", "FR-01/02/03, NFR-02", "Create account; password/NFC login; save default milk/strength/temperature; log out/in."),
    ("F02", "Menu, categories and nutrition", "FR-04", "Browse six drinks; filter Coffee/Chocolate; inspect estimated nutrition and allergens."),
    ("F03", "Validated custom drink quote", "FR-05", "Change milk, strength, temperature, syrup and shots; observe server-calculated quote."),
    ("F04", "Named personal recipes", "FR-06", "Save Morning Oat; rename; load and edit settings; save update; delete."),
    ("F05", "Ingredient/quantity checks", "FR-07, NFR-03", "Set oat level below threshold as technician; verify oat recipe cannot be purchased; refill."),
    ("F06", "Context/history recommendations", "FR-08/19", "Toggle Recommended first; switch local-clock or manual period (morning/afternoon/evening/night), temperature (cold/mild/warm/hot) and condition (unknown/sunny/cloudy/rainy/snowy); verify history, saved-recipe and preference reasons and offline fallback."),
    ("F07", "Checkout and immutable history", "FR-11/12/20, NFR-03", "Use five payment methods; set external decline in technician Test scenarios; inspect history/retries and offline reconciliation."),
    ("F08", "Earn and redeem loyalty", "FR-13", "Apply 100 points; verify SEK 10 discount and success-only deduction/earning."),
    ("F09", "QR receipt and email adapter", "FR-14", "Open receipt QR/text; send to local simulator outbox; fail email and retain QR fallback."),
    ("F10", "Protected maintenance/diagnostics", "FR-15/16/17/18", "PIN/master-NFC login; full refill; waste halt/empty; fault logging; authorized diagnostic export."),
]
OPTIONAL_FEATURE = [("F11", "Local drink assistant", "FR-10/19", "Ask for three strong oat options; compare names, short descriptions, settings and server prices without technical scores. Apply option two, request a strength change and verify that recipe remains active. Precise requests may yield fewer choices; checkout remains separate.")]

OVERVIEW = "SmartBrew AI is a local coffee-machine prototype for customers and maintenance technicians. It implements ten selected feature groups: accounts, menu, customization, personal recipes, availability, recommendations, checkout/history, loyalty, receipts and maintenance. An additional optional local language model interprets drink requests into customer-confirmed recipes. The complete elicitation retains camera/privacy requirements even though camera inference is outside this implementation."
POLICY = "Previously generated Lab 2 correction: AI-GENERATED REVIEW REFERENCE ONLY - NOT FOR LAB 1 OR LAB 2 SUBMISSION. The general course rules supplied after this reference was generated prohibit submitting generated text/models for those labs. Original submissions are unchanged. Lab 3 explicitly permits generation; disclosure does not override the Lab 1-2 restriction."
CROSS_LAB = "Lab 1 received a positive grade, with Partial feedback on component scope and UI dependency on the AIEngine. Its nine domain concepts map to roles, preferences, recipes, purchase records and stock/waste state, not necessarily one code class each. The optional local-LLM responsibility is now implemented through a separate adapter; camera/mood inference remains deferred. Loyalty first appears in the supplied Lab 2, not the Lab 1 diagrams. See docs/CROSS_LAB_REVIEW.md for the detailed source mapping."
EXPERIMENT = "The instructor strongly recommends additional experimentation, but does not state a fourth mandatory task. During Lab 3 verification, the project conducted an empirical before/after evaluation of multi-turn local-model behavior and deterministic recommendation ranking against isolated temporary databases: the 8-turn held-out assistant baseline (evidence/history/assistant-heldout-baseline.json, 5/8 turns passed) exposed a leaked synthetic context turn, base-drink rigidity, silent substitution of unsupported iced/caramel requests and unrequested extra espresso shots; replacing the synthetic assistant turn with a trailing system context snapshot and ordering config before message improved results to 7/8 on the first post-change run (evidence/history/assistant-heldout-postchange-first-run.json) and 8/8 on the final regression run (evidence/current/assistant-heldout-postchange.json), alongside 12/12 in the conversation suite (evidence/current/assistant-conversations.json), 9/9 recipe turns in the long-chat suite (evidence/current/assistant-long-chat.json) and the current extended 65/65 browser checks (evidence/current/browser-results.json, with first-run browser regressions preserved in evidence/history/browser-failure.json and evidence/history/browser-f06-first-run-failure.json). The evaluation records retain both the initial failures and the final regression results."
PROVENANCE = "The comparison uses the group's submitted Assignment 2 files, preserved unchanged with hashes in docs/baseline. Later review drafts are kept separately and do not replace the submitted baseline."
BASELINE_REVIEW = "Comparison baseline: the original group submission is the reference for the before-and-after analysis. Each original story is mapped to its revised counterpart, and new stories have separate justifications. The comparison evaluates coverage, clarity, traceability and the fit with the system description."
TRANSCRIPT_RECORD = "The development conversation is attached as docs/DEVELOPMENT_TRANSCRIPT.md: 251 recorded student/Codex messages with personal details redacted. Source hashes and transcript integrity information are in docs/DEVELOPMENT_TRANSCRIPT_MANIFEST.json. The AI appendix provides the prompting approach and selected interactions. The separate Gemini/Antigravity session is summarized in the interaction record; its original transcript was not available."
PROMPT_STRATEGY = "Ground the artifacts in the system description, feedback and course slides; use the six-column requirement template; retain the submitted baseline; trace capabilities to requirements, stories and backlog entries; distinguish source requirements from design assumptions; select ten demonstrable feature groups; implement and verify successful, rejected, ownership, retry and offline workflows. Refine the results through review and focused follow-up requests."
ASSUMPTIONS = [
    "Prototype money uses integer ore (100 ore = SEK 1); demo prices/nutrition/ingredient quantities are illustrative and are not production dietary specifications.",
    "Loyalty: earn one point per whole SEK actually paid; one point redeems SEK 0.10, bounded by balance and price. Demo Alex begins with 250 points and SEK 200 prepaid credit; new accounts begin with zero.",
    "Customer orders may be placed as guest; profile/recipe/history and prepaid/loyalty features require customer login. Guest receipts use an unguessable capability token.",
    "Mood opt-in and the proposed 2-second response target are design refinements; the original brief does not prescribe consent UI, a numerical latency target or point-conversion rules.",
    "Weather/time, NFC/key signals, machine sensors, payment approval and email are simulated locally. Recommendation scoring uses separate deterministic affinity tables (preserving generic recipe defaults), period mode (manual technician override or injectable local clock across morning/afternoon/evening/night), online temperature (cold/mild/warm/hot), online weather condition (unknown/sunny/cloudy/rainy/snowy), and customer-owned preferences, saved recipes (+15) and completed-order count (+12 per order up to +36 as 'A frequent choice'). Manual ordering and stored-value prepaid payments work while the simulated network is offline.",
    "Online-only payment requests can be persisted as pending without dispensing. Reconnect and customer Retry performs authorization/revalidation once; the prototype never assumes that a wallet can approve offline.",
    "Camera mood inference remains deferred. F11 adds actual optional local Qwen3 4B inference through Ollama 0.40.6, beyond the ten selected groups. A later approved UI refinement offers up to three supported recipes with short descriptions and server prices, without technical scores. Selected-option context is preserved for further changes; exact named-strength follow-ups also have a narrow consistency guard. No proposal or application purchases or modifies accounts.",
    "No physical brew command or real card authorization occurs. Admin diagnostics can be exported locally; there is no deployed remote diagnostic service or physical key reader.",
    "Technician-only Test scenarios controls the persistent external payment mode (Normal/Decline). Customer checkout cannot submit an outcome override. Existing accounts/orders are retained; historical purchases are not reassigned after the authentication fix.",
    "The model may need a cold load; server inference has a 90-second bound and manual ordering stays independent. The proposed menu/quote latency target excludes optional inference. Model proposals require customer review and fresh server validation.",
]


def lab2_records():
    """Purpose: retain original IDs while filling lecture fields. Inputs: module records. Returns: grouped requirements."""
    by_id = {r["id"]: r for r in LAB3}
    results = []
    for i, (name, ids, stories) in enumerate(GROUPS2, 1):
        selected = [by_id[key] for key in ids]
        row = {"id": f"REQ-{i:02d}", "name": name, "source": "; ".join(r["source"] for r in selected), "old": f"US-{i:02d}",
               "importance": [95,100,85,95,100,75,45,30,100,70,70,100,80][i-1], "estimate": [3,3,5,5,5,8,8,13,13,5,5,13,5][i-1]}
        for field in ("description", "inputs", "outputs", "precondition", "postcondition", "demo"):
            row[field] = "\n".join((r["name"] + ": " if len(selected) > 1 else "") + r[field] for r in selected)
        results.append(row)
    return results


def table_md(headers, rows):
    """Purpose: serialize readable Markdown tables. Inputs: headers/rows. Returns: table text."""
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell).replace("|", "/").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(lines)


def requirement_rows(records):
    """Purpose: map record fields to exact slide columns. Inputs: requirements. Returns: table rows."""
    return [[r["id"], r["name"] + "\n" + r["description"], r["inputs"], r["outputs"], r["precondition"], r["postcondition"]] for r in records]


def backlog_rows(records, lab):
    """Purpose: construct prioritized traceable backlog. Inputs: records/lab number. Returns: backlog rows."""
    sorted_records = sorted(records, key=backlog_sort)
    rows = []
    for r in sorted_records:
        suffix = r["id"].replace("REQ-", "") if lab == 2 else r["id"]
        notes = r["id"] + "; " + (r["old"] if lab == 2 else r["source"] + "; " + r["feature"])
        rows.append(["PB-" + suffix, r["name"], r["importance"], r["estimate"], r["description"], r["demo"], notes])
    return rows


def backlog_sort(record):
    """Purpose: sort high importance first with stable IDs. Inputs: requirement. Returns: sort tuple."""
    return (-record["importance"], record["id"])


def appendix_preface():
    """Purpose: assemble the Markdown text for the Lab 3 AI appendix. Inputs: MAIN_PROMPT.md and AI_CONVERSATION.md. Returns: combined appendix string."""
    conversation = (ROOT / "docs" / "AI_CONVERSATION.md").read_text(encoding="utf-8")
    main_prompt = (ROOT / "docs" / "MAIN_PROMPT.md").read_text(encoding="utf-8")
    return "\n\n".join([
        "# SmartBrew AI - Group 28 - Lab 3 AI appendix",
        f"Updated {DOCUMENT_DATE}. Requirements elicitation, prototype development and evaluation.",
        conversation.split("\n", 1)[1].strip(),
        "## Appendix - Original main prompt",
        main_prompt.split("\n", 1)[1].strip(),
    ])


def write_markdown(include_reference=False):
    """Purpose: export current artifacts and optional historical references. Inputs: module records/reference flag. Returns: None."""
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    records2 = lab2_records()
    headers = ["ID", "Description", "Inputs", "Outputs", "Precondition", "Postcondition"]
    backlog_headers = ["ID", "Name", "Importance", "Estimate", "Description", "How to demo", "Notes"]
    lab2 = ["# SmartBrew AI - Group 28 - Lab 2 review reference", "Policy clarification: 2026-10-21", POLICY, OVERVIEW,
            "## What changed after feedback", "The feedback gave a positive final grade. This revision fills the requirement template (Lecture 2, slide 47), places Customer/Technician on the left and Payment Processor on the right, makes Customize Beverage the customer's entry and the base of natural-language extension, and repairs the saved use-case descriptions. It also clarifies omissions found during source coverage review. The original archive is unchanged.",
            "## User stories", table_md(["ID", "Name", "Story"], [[f"US-{i:02d}", GROUPS2[i-1][0], story] for i, story in enumerate(STORIES2, 1)]),
            "## Requirements", "For combined operations, each labeled pre/postcondition applies to that operation; registration and login are alternative paths. This retains the original thirteen IDs.", table_md(headers, requirement_rows(records2)),
            "## Initial product backlog", "Importance is a proposed 0-100 ordering score (higher first). Estimate is relative story points, not hours. Estimates require group refinement. Description is retained in addition to the slide columns; Notes carries requirement/story links. No sprint commitment is asserted without team capacity.", table_md(backlog_headers, backlog_rows(records2, 2)),
            "## Use-case correction", "Customer -- Customize Beverage (solid association). Process Natural Language Order --<<extend>>--> Customize Beverage. Customize Beverage --<<include>>--> Check Ingredient Availability. Analyze Mood --<<extend>>--> Generate Recommendations when enabled/opted in. Redeem Loyalty --<<extend>>--> Process Payment. Technician has independent solid associations with Manage Inventory and View Error Logs; viewing logs is not a mandatory refill step. Extensions point toward their base use case.",
            "## Assumptions", "\n".join("- " + item for item in ASSUMPTIONS[:4]), "## Sources", "Provided system description and Lab 2 guidelines; instructor feedback page 1; Lecture-02-2026 slides 20-23, 30-31, 38, 43 and 47-48. The book reading remains the group's responsibility; no claim is made that the students have completed it."]
    reference = docs / "reference" / "lab2"
    if include_reference:
        reference.mkdir(parents=True, exist_ok=True)
        (reference / "REVIEW.md").write_text("\n\n".join(lab2) + "\n", encoding="utf-8", newline="\n")
    text3 = ["# SmartBrew AI - Group 28 - Lab 3", f"Updated: {DOCUMENT_DATE}", "## Task A - Elicitation", OVERVIEW,
             "### Cross-lab continuity", CROSS_LAB,
             "### Models and provenance", MODEL, "These are the development assistants for Lab 3 Tasks A-C and the subsequent F11/F06 updates. The runtime drink model inside the application is separately identified as local Qwen3 4B (qwen3:4b) through Ollama 0.40.6. Earlier Lab 1-2 tutoring and an intermediate web-chat Gemini draft before local IDE access did not expose confirmed model version labels.", PROVENANCE,
             "### Prompt strategy", PROMPT_STRATEGY, "Main prompts and selected responses are recorded in AI_CONVERSATION.md and the separate PDF appendix; generated code and revisions are retained in Git.",
             "### Source inventory", table_md(["Source", "System capability"], SOURCES),
             "### User stories", table_md(["ID", "Name", "Story", "Requirement links"], STORIES3),
             "### Functional requirements", table_md(headers, requirement_rows([r for r in LAB3 if r["id"].startswith("FR-") ])),
             "### Non-functional requirements", table_md(headers, requirement_rows([r for r in LAB3 if r["id"].startswith("NFR-") ])),
             "### Initial product backlog", "Lecture format with Description and trace links retained. Importance 0-100, high first; estimates are relative story points, not measured velocity. This is an initial planning artifact, not a claim that every full-system requirement is implemented. F01-F10 and optional F11 have demonstration steps; camera and physical integrations remain deferred.", table_md(backlog_headers, backlog_rows(LAB3, 3)),
             "### Comparison with the submitted Lab 2", PROVENANCE, table_md(["Topic", "Submitted Lab 2", "LLM revision", "Decision and reason"], COMPARISON),
             "### User-story comparison: original to revised", STORY_COMPARISON_NOTE, table_md(["Submitted story", "Original wording", "Revised story links", "Change and justification"], STORY_COMPARISON),
             "### Seven additional stories", table_md(["New story", "Requirement / source", "Reason for addition"], ADDED_STORIES),
             "### Comparison baseline", BASELINE_REVIEW,
             "### Rejected design alternatives", "These alternatives were evaluated against the system description and selected prototype scope.", table_md(["Option", "Decision / justification"], REJECTIONS),
             "### Critical evaluation of the assistant", "The earlier assistant checked names in a serialized Astah ZIP and PDF and overclaimed completeness. The actual feedback identified the missing requirement fields. A supported-API inspection in this revision additionally found that Process Payment contained the natural-language description, Analyze Mood had no completed fields, Check Ingredient Availability was absent from the diagram canvas, and optional/mandatory relationships conflicted with descriptions. This shows why matching names is insufficient. The expanded elicitation improves coverage and traceability, but point rules, consent and latency targets remain design proposals; hardware and external-service realism require separate validation.",
             "## Task B - Selected implementation", table_md(["Feature", "Functionality", "Requirements", "Demonstration"], FEATURES),
             "### Optional addition", table_md(["Feature", "Functionality", "Requirements", "Demonstration"], OPTIONAL_FEATURE),
             "### Scope and assumptions", "\n".join("- " + item for item in ASSUMPTIONS),
             "### Architecture", "The HTTP adapter and service layer enforce identity, ownership and purchase rules. SQLite holds persistent local state; checkout uses one write transaction and a unique request key. Customer ordering and technician maintenance/testing share one app but separate protected actions. The optional model adapter is loopback-only and has no ordering side effects. See ARCHITECTURE.md for responsibilities and trust boundaries.",
             "### Validation and revisions", "QA_RESULTS.md and evidence/ contain actual runs (38 unit tests in evidence/current/unit-tests.txt and 65 browser checks in evidence/current/browser-results.json), including the three-choice assistant and selected-option follow-up. The student exposed a browser authentication defect: hidden demo NFC data overrode entered passwords. A failing regression reproduced it; explicit methods and two-customer browser tests now verify identity, ownership and restart persistence. Earlier passing tests were insufficient because they only used Alex for browser customer login. Subsequent evaluation and implementation in Google Antigravity (Gemini 4 Argon Medium) resolved multi-turn F11 assistant context/constraint issues (replacing a leaked synthetic assistant turn with a trailing system context snapshot, ordering config before message in RESPONSE_SCHEMA, and refusing unsupported iced/caramel requests without silent substitution or unrequested extra espresso; 8/8 in evidence/current/assistant-heldout-postchange.json, 12/12 in evidence/current/assistant-conversations.json, and 9/9 recipe turns in evidence/current/assistant-long-chat.json) and expanded F06 recommendations across manual vs local-clock periods (morning/afternoon/evening/night), temperatures (cold/mild/warm/hot), weather conditions (unknown/sunny/cloudy/rainy/snowy), and customer-isolated preferences, saved recipes (+15) and completed-order frequency (+12 per order up to +36 as 'A frequent choice'). Simulator tests do not validate real hardware or financial/email processors.",
             "### Recommended extra experimentation", EXPERIMENT,
             "## Task C - Repository and documentation", "Repository: https://github.com/kaantanidir/Software_Engi_1_LAB3 . README.md contains environment, installation, execution, tests and all ten feature demos. Each authored Python/JavaScript/Java function documents purpose, inputs and outputs. Vendored Lucide is third-party library code with its license retained. Runtime data, local packages and temporary files are excluded from Git.",
             "### Submission package and clean installation", "SUBMISSION.md maps Tasks A-C to the included artifacts and identifies output/SmartBrew_Lab3_Canvas.zip as the compact Canvas upload, with Task B supplied through the repository link. GitHub visibility was verified public on 26 October 2026. The source archive was extracted separately and tested with a fresh Python 3.12.14 environment and pinned requirements: pip check passed, 38 unit tests passed, and a separate browser smoke check verified the actual model, example prompts, loading indicator and reduced-motion behavior without personal data or workspace packages. The complete live-model browser suite also passed all 65 checks on the final UI. See evidence/current/clean-install.txt and evidence/current/ux-polish.json. The source repository includes the full implementation and execution guide.",
             "### Review before submission", "Review point conversion, pending-payment policy, estimates and model limitations, then run the walkthrough. Detailed prompts/model use are in the appendix. Compare against the preserved group submission, not the later generated Lab 2 review aids; those review aids are not submission materials under the supplied policy.",
             "### AI appendix", "The required simple PDF is output/G28Lab3_AI_Appendix.pdf. It contains the student-confirmed model labels, prompt strategy, main prompt and key responses, subsequent clarifications and generated-code references.", TRANSCRIPT_RECORD,
             "### References", "Instructor feedback page 1; Lecture-02-2026 slides 20-23, 30-31, 38, 43 and 47-48; Lecture-03-2026 slides 17, 22, 28, 38-40; system description and assignment guidelines supplied in the chat. Henrik Kniberg, Scrum and XP from the Trenches: https://www.infoq.com/minibooks/download/scrum-xp-from-the-trenches/ (recommended course reading; student completion is not asserted)."]
    (docs / "LAB3_REPORT.md").write_text("\n\n".join(text3) + "\n", encoding="utf-8", newline="\n")
    (docs / "LAB3_AI_APPENDIX.md").write_text(appendix_preface() + "\n", encoding="utf-8", newline="\n")
    uc = ["# Use-case review reference descriptions", POLICY, "Template: Lecture 2 slides 30-31. The AI-generated Astah reference contains the same descriptions; neither is for Lab 2 submission."]
    tsv = []
    for name, values in USECASES.items():
        uc.append("## " + name)
        for key, value in zip(["Preconditions", "InitiatingActor", "Goal", "MainScenario", "Alternatives"], values):
            uc.append("**" + key + "**\n\n" + value)
        tsv.append(name + "\t" + "\t".join(base64.b64encode(value.encode()).decode() for value in values))
    if include_reference:
        (reference / "USE_CASE_DESCRIPTIONS.md").write_text("\n\n".join(uc), encoding="utf-8", newline="\n")
        (ROOT / "tmp").mkdir(exist_ok=True)
        (ROOT / "tmp" / "descriptions.tsv").write_text("\n".join(tsv), encoding="utf-8", newline="\n")


STYLES = getSampleStyleSheet()
STYLES.add(ParagraphStyle(name="Cell", fontName="Helvetica", fontSize=8.3, leading=11.2, spaceAfter=0, alignment=TA_LEFT))
STYLES.add(ParagraphStyle(name="BodyCustom", fontName="Helvetica", fontSize=10, leading=14, spaceAfter=9))
STYLES.add(ParagraphStyle(name="SmallCustom", fontName="Helvetica", fontSize=8.5, leading=12, textColor=colors.HexColor("#4e635d")))
pdfmetrics.registerFont(TTFont("RecordVera", str(Path(reportlab.__file__).parent / "fonts" / "Vera.ttf")))
STYLES.add(ParagraphStyle(name="UnicodeQuote", parent=STYLES["SmallCustom"], fontName="RecordVera"))
STYLES.add(ParagraphStyle(name="Speaker", parent=STYLES["SmallCustom"], keepWithNext=True))
STYLES.add(ParagraphStyle(name="AppendixBody", parent=STYLES["BodyCustom"], fontSize=9.3, leading=13, spaceAfter=5))
STYLES.add(ParagraphStyle(name="AppendixBullet", parent=STYLES["AppendixBody"], leftIndent=10, firstLineIndent=0, bulletIndent=0))
STYLES.add(ParagraphStyle(name="OriginalPrompt", parent=STYLES["AppendixBody"], fontSize=8.6, leading=11.5, spaceAfter=4))
STYLES.add(ParagraphStyle(name="OriginalPromptBullet", parent=STYLES["OriginalPrompt"], leftIndent=10, bulletIndent=0))
STYLES["Heading2"].keepWithNext = True


def paragraph(value, style="BodyCustom"):
    """Purpose: safely render arbitrary text. Inputs: text/style. Returns: ReportLab Paragraph."""
    return Paragraph(escape(str(value)).replace("\n", "<br/>"), STYLES[style])


def table(headers, rows, widths, padding=8):
    """Purpose: lay out wrapped table cells. Inputs: rows/widths/optional padding. Returns: repeating-header Table."""
    cells = [[paragraph(cell, "Cell") for cell in headers]] + [[paragraph(cell, "Cell") for cell in row] for row in rows]
    result = Table(cells, colWidths=[width * mm for width in widths], repeatRows=1, hAlign="LEFT")
    result.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#e0ece7")),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white,colors.HexColor("#f5f8f6")]),
        ("GRID", (0,0), (-1,-1), .4, colors.HexColor("#c9d8d0")),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 6), ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), padding), ("BOTTOMPADDING", (0,0), (-1,-1), padding),
    ]))
    return result


def footer(canvas, doc):
    """Purpose: draw page identity/number. Inputs: canvas/document. Returns: None."""
    canvas.saveState(); canvas.setFont("Helvetica", 8); canvas.setFillColor(colors.HexColor("#5b7066"))
    canvas.drawString(16*mm, 10*mm, "SmartBrew AI | Group 28 | " + DOCUMENT_DATE)
    canvas.drawRightString(doc.pagesize[0]-16*mm, 10*mm, str(doc.page)); canvas.restoreState()


def heading(flow, title, page=False):
    """Purpose: add a section title. Inputs: flow/title/page-break flag. Returns: None."""
    if page: flow.append(PageBreak())
    flow.extend([paragraph(title, "Heading1"), Spacer(1, 5*mm)])


def build_pdf(lab):
    """Purpose: generate final lecture-format report. Inputs: lab number. Returns: PDF path."""
    if lab == 2:
        output = ROOT / "docs" / "reference" / "lab2"
        output.mkdir(parents=True, exist_ok=True)
        path = output / "G28Lab2_Corrected.pdf"
    else:
        output = ROOT / "output"
        output.mkdir(parents=True, exist_ok=True)
        path = output / "G28Lab3_Report.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=landscape(A4), rightMargin=16*mm, leftMargin=16*mm, topMargin=15*mm, bottomMargin=18*mm, title=f"SmartBrew AI - Group 28 - Lab {lab}", author="Group 28 (LLM-assisted revision)")
    flow = []
    heading(flow, f"SmartBrew AI - Group 28 - Lab {lab}" + (" review reference" if lab == 2 else " report"))
    flow.append(paragraph(OVERVIEW))
    if lab == 2:
        flow.append(paragraph(POLICY))
        flow.append(paragraph("Feedback: positive overall. Main correction: requirements now include Inputs, Outputs, Precondition and Postcondition, following Lecture 2 slide 47. Diagram layout, customer entry, saved descriptions and optional relationships are repaired. Thirteen original requirement/story IDs are retained; added clarifications are documented."))
        heading(flow, "User stories")
        flow.append(table(["ID","Name","Story"],[[f"US-{i:02d}",GROUPS2[i-1][0],story] for i,story in enumerate(STORIES2,1)],[19,58,188]))
        records = lab2_records()
    else:
        flow.append(paragraph("Task A - Requirements elicitation, critical comparison and prompt record"))
        flow.append(paragraph("Development models: " + MODEL)); flow.append(paragraph("Runtime drink model: local Qwen3 4B (qwen3:4b) through Ollama 0.40.6. The development and runtime model roles are distinct.")); flow.append(paragraph(PROVENANCE)); flow.append(paragraph(PROMPT_STRATEGY))
        flow.append(paragraph("Main student prompt and selected key responses: output/G28Lab3_AI_Appendix.pdf and docs/AI_CONVERSATION.md. The appendix presents the prompting strategy and selected interactions; the original conversation is attached separately. Tasks A, B and C and subsequent F11/F06 updates use the recorded models; earlier Lab 1-2 tutoring and an intermediate web-chat Gemini draft before local IDE access did not expose confirmed model version labels."))
        heading(flow,"User stories",True)
        flow.append(table(["ID","Name","Story","Requirements"], STORIES3,[18,42,157,48]))
        records = LAB3
    heading(flow,"Requirements - lecture template" if lab == 2 else "Functional requirements - lecture template",True)
    flow.append(paragraph("The six columns follow Lecture 2 slide 47. Functional and non-functional items are labeled separately in Lab 3. For grouped Lab 2 items, labeled conditions apply to the corresponding operation."))
    headers = ["ID","Description","Inputs","Outputs","Precondition","Postcondition"]
    if lab == 2:
        flow.append(table(headers,requirement_rows(records),[19,69,42,41,46,48]))
    else:
        flow.append(table(headers,requirement_rows([r for r in records if r["id"].startswith("FR-")]),[19,69,42,41,46,48]))
        heading(flow,"Non-functional requirements - lecture template",True)
        flow.append(table(headers,requirement_rows([r for r in records if r["id"].startswith("NFR-")]),[19,69,42,41,46,48]))
    heading(flow,"Initial product backlog",True)
    flow.append(paragraph("Importance: proposed 0-100 ordering score, higher first. Estimate: relative story points, not hours. Initial planning values require group review. Description supplements the slide's fields; Notes provides traceability. No sprint commitment is made without team capacity."))
    flow.append(table(["ID","Name","Importance","Estimate","Description","How to demo","Notes"],backlog_rows(records,lab),[22,35,21,17,57,79,34]))
    if lab == 2:
        heading(flow,"Diagram and use-case correction",True)
        for text in ["Customer and Technician are primary actors on the left; Payment Processor is secondary on the right. Customer starts Customize Beverage. The thirteen saved use cases all have complete textual descriptions.",
                     "Process Natural Language Order extends Customize Beverage. Customize Beverage includes Check Ingredient Availability. Analyze Mood optionally extends Generate Recommendations. Redeem Loyalty extends Process Payment. Dashed extension arrows point toward the base; inclusion points toward the included case.",
                     "Technician participates independently in Manage Inventory and View Error Logs; the previous mandatory log-view inclusion was removed. The custom-feature note is anchored to Redeem Loyalty."]:
            flow.append(paragraph(text))
        for item in ASSUMPTIONS[:4]: flow.append(paragraph(item,"SmallCustom"));flow.append(Spacer(1,3*mm))
        flow.append(paragraph("Sources: supplied system description/guidelines and feedback page 1; Lecture-02-2026 slides 20-23, 30-31, 38, 43 and 47-48. The original submission remains in docs/baseline. Reading the assigned Scrum chapters remains the group's responsibility.","SmallCustom"))
        diagram = ROOT / "evidence" / "history" / "use-cases.png"
        if diagram.exists():
            heading(flow,"Corrected Astah diagram",True)
            flow.append(Image(str(diagram), width=230*mm, height=150*mm, kind="proportional"))
    else:
        heading(flow,"Comparison with the submitted Lab 2",True)
        flow.append(paragraph(PROVENANCE))
        flow.append(table(["Topic","Submitted Lab 2","LLM-assisted revision","Decision and reason"], COMPARISON,[41,67,91,66]))
        heading(flow,"User-story comparison: original to revised",True)
        flow.append(paragraph(STORY_COMPARISON_NOTE))
        flow.append(table(["Submitted story","Original wording","Revised story links","Change and justification"], STORY_COMPARISON,[42,86,48,89]))
        heading(flow,"Seven additional stories and baseline provenance",True)
        flow.append(table(["New story","Requirement / source","Reason for addition"],ADDED_STORIES,[47,64,154]))
        flow.append(Spacer(1,6*mm))
        flow.append(paragraph(BASELINE_REVIEW))
        heading(flow,"Rejected alternatives and critical evaluation",True)
        flow.append(paragraph("These alternatives were evaluated against the system description and selected prototype scope."))
        flow.append(table(["Option","Justification"],REJECTIONS,[90,175]))
        flow.append(Spacer(1,6*mm))
        flow.append(paragraph("Initial name-only model checks missed requirement fields and wrong/empty use-case descriptions. Later, the student found a browser login defect that passing tests had missed: a hidden NFC value selected Alex instead of checking the entered password. The new regressions verify separate identities and ownership. Real-model testing also found an invented usual-drink recipe; the failed output was retained and clarification rules were refined. Subsequent Google Antigravity (Gemini 4 Argon Medium) evaluation and implementation resolved multi-turn F11 context/constraint defects (8/8 in evidence/current/assistant-heldout-postchange.json) and expanded F06 recommendation scoring and verification. The subsequent three-choice assistant revision passes 38 unit tests (evidence/current/unit-tests.txt) and 65 browser checks (evidence/current/browser-results.json), including the reproduced selected-option strength correction. These observations distinguish observed evidence from an unsupported claim of completeness."))
        heading(flow,"Cross-lab continuity and revisions",True)
        flow.append(paragraph(CROSS_LAB))
        flow.append(paragraph("Read-only Lab 1 inspection preserved the original model and hashes. The visible User {Abstract} label is not backed by Astah's native abstract flag, although the grader accepted the class criteria. No original model is silently rewritten. Conceptual model mappings and implementation scope differences are documented in the cross-lab review."))
        flow.append(paragraph("Reliability follow-up: HTTP 503 from recommendations reproduced a blank menu in the isolated browser test. Essential ordering now renders before optional ranking, whose wait is limited to 1.2 seconds. Manual browsing, customization and payment retain their standard-menu path. This is an ordinary regression fix, not the unselected optional student experiment."))
        flow.append(paragraph("Customer checkout no longer controls its payment result. Only the technician's Test scenarios area changes the persistent external-processor mode. Normal sign-in fields start empty, mixed authentication requests are rejected, and account changes clear private UI and assistant conversation. Existing data is preserved; historical orders are not automatically reassigned."))
        flow.append(paragraph("Course policy: the earlier generated Lab 2 corrections remain review aids only, not submission materials. Original Lab 1-2 sources are unchanged. Lab 3 permits generation; the separate appendix records assistance and source provenance."))
        flow.append(paragraph(EXPERIMENT))
        heading(flow,"Task B - Ten selected feature groups",True)
        flow.append(table(["ID","Functionality","Requirements","Demonstration"],FEATURES,[16,59,52,138]))
        heading(flow,"Optional F11 - Local drink assistant",True)
        flow.append(table(["ID","Functionality","Requirements","Demonstration"],OPTIONAL_FEATURE,[16,59,52,138]))
        flow.append(Spacer(1, 6*mm))
        flow.append(paragraph("One-time Windows setup: install Ollama and run tools/start_local_ai.ps1 to start it, download qwen3:4b if missing and warm the model. Later, tools/start_smartbrew.ps1 starts/reuses Ollama and launches SmartBrew together, using existing model weights without a download or warm-up wait. Missing AI leaves manual ordering available. Direct app.py launches require Ollama to be running separately. The model download is about 2.5 GB. The tested system has about 32 GB RAM and a 6 GB RTX 3060 Laptop GPU. Actual model digest, requests, responses and timings are in evidence/current/local-ai-results.json; these are selected examples, not a general accuracy guarantee."))
        flow.append(paragraph("The model returns a bounded recipe or clarification schema. The server rejects unsupported fields/options, recalculates price and checks current stock. Use recipe applies the proposal only after customer confirmation; checkout is separate. Inference cannot execute code or purchase. Missing/invalid/slow inference leaves manual ordering available. The cold-load wait is bounded at 90 seconds and excluded from menu/quote latency measurements."))
        flow.append(paragraph("Broad taste requests produce up to three distinct choices in one model response; precise named drinks, exact refinements or limited availability may produce fewer. Cards show names, short descriptions, settings and server prices, with no technical score or confidence percentage. The separate F06 scoring rationale stays in the architecture/backlog. Choosing any card makes it the active recipe for further requests. An observed wrong-drink response to 'Make it mild' is preserved; a narrow strength-only guard and real-model regression verify that this command changes only the selected recipe's strength. Other free-form interpretation remains fallible."))
        heading(flow,"Implementation scope and assumptions",True)
        for index, item in enumerate(ASSUMPTIONS):
            if index:
                flow.append(Spacer(1,2*mm))
            flow.append(paragraph(item))
        heading(flow,"Task C - Setup, repository and validation",True)
        flow.append(paragraph("Repository: https://github.com/kaantanidir/Software_Engi_1_LAB3"))
        flow.append(paragraph("Submission: SUBMISSION.md maps the assessed artifacts; upload output/SmartBrew_Lab3_Canvas.zip to Canvas; Task B is referenced through the repository. Repository visibility was verified public on 26 October 2026. A ZIP-extracted source copy passed 38 unit tests in a fresh Python environment with the pinned dependencies and no workspace packages or personal data. A separate clean-install browser check verified three example prompts, real local inference, mobile layout and the reduced-motion loading indicator; the complete live-model browser suite passed 65 checks. Evidence: evidence/current/clean-install.txt and evidence/current/ux-polish.json. The repository contains the source and execution guide."))
        flow.append(paragraph(TRANSCRIPT_RECORD))
        flow.append(paragraph("Runtime: Python 3.12 (verified 3.12.14), modern browser, pinned qrcode 8.2 (colorama 0.4.6 on Windows). SQLite and HTTP service use the Python standard library. Setup: python -m venv .venv; activate; python -m pip install -r requirements.txt. Windows run: powershell -NoProfile -ExecutionPolicy Bypass -File tools/start_smartbrew.ps1. This starts/reuses optional Ollama without downloading weights; -SkipAI omits AI preparation. Direct Python alternative: python app.py --port 8765. Visit http://127.0.0.1:8765. Tests: python -m unittest discover -s tests -v."))
        flow.append(paragraph("Demo customer: alex@smartbrew.test / DemoPass123!; registered NFC DEMO-NFC-001. Technician PIN 246810; master NFC MASTER-NFC-001. These are public simulator fixtures, not production credentials."))
        flow.append(paragraph("README.md contains all feature walkthroughs. docs/README.md indexes architecture, verification, prompt records and historical sources; older Lab 2 notes are in docs/reference/lab2. All authored functions document purpose/input/output. Runtime data, model weights and local packages are excluded from Git. See docs/QA_RESULTS.md and evidence/ for actual tests. Simulator approval is not financial or hardware validation."))
        flow.append(paragraph("References: provided feedback, system description and assignment instructions; Lecture 2 slides 20-23, 30-31, 38, 43, 47-48; Lecture 3 slides 17, 22, 28 and 38-40. Recommended reading: Henrik Kniberg, Scrum and XP from the Trenches (InfoQ).","SmallCustom"))
        heading(flow,"Appendix - Source coverage",True)
        flow.append(table(["Source","Capability","Requirement(s)"],[[sid,description,"; ".join(r["id"] for r in LAB3 if sid in r["source"].split(";")[0].split("/"))] for sid,description in SOURCES],[20,140,105],padding=5))
    doc.build(flow,onFirstPage=footer,onLaterPages=footer)
    print(path)
    return path


def appendix_paragraph(value, style="AppendixBody", bullet=None):
    """Purpose: format safe inline Markdown for the AI appendix. Inputs: text, style and optional bullet. Returns: ReportLab Paragraph."""
    text = escape(str(value))
    text = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r'\[([^\]]+)\]\((https?://[^\s)]+)(?:\s+"[^"]*")?\)', r'<link href="\2" color="#17654d">\1</link>', text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", text)
    return Paragraph(text.replace("\n", "<br/>"), STYLES[style], bulletText=bullet)


def build_ai_appendix():
    """Purpose: export required model/prompt PDF. Inputs: preserved prompt/interaction files. Returns: output PDF path."""
    preface = appendix_preface()
    (ROOT / "docs" / "LAB3_AI_APPENDIX.md").write_text(preface + "\n", encoding="utf-8", newline="\n")
    path = ROOT / "output" / "G28Lab3_AI_Appendix.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=16*mm, leftMargin=16*mm,
                            topMargin=16*mm, bottomMargin=18*mm, title="SmartBrew AI - Lab 3 model and prompt appendix",
                            author="Group 28 (LLM-assisted record)")
    flow = []
    original_prompt = False
    for block in preface.split("\n\n"):
        block = block.strip()
        if not block.strip() or block.strip() == "---":
            continue
        if block.startswith("#"):
            if block.startswith("## Appendix - Original main prompt"):
                original_prompt = True
                flow.append(PageBreak())
            elif block.startswith("## 3. Selected prompts"):
                flow.append(PageBreak())
            level = len(block) - len(block.lstrip("#"))
            style = "Title" if level == 1 else "Heading1" if level == 2 else "Heading2"
            flow.append(appendix_paragraph(block.lstrip("# "), style))
        elif block.startswith("| "):
            rows = [[cell.strip() for cell in line.strip().strip("|").split("|")] for line in block.splitlines()]
            flow.append(table(rows[0], rows[2:], [40, 35, 103], padding=6))
            flow.append(Spacer(1, 3*mm))
        elif block.startswith("- ") or re.match(r"\d+\. ", block):
            for line in block.splitlines():
                text = line.strip()
                bullet = "-" if text.startswith("- ") else None
                style = ("OriginalPromptBullet" if bullet else "OriginalPrompt") if original_prompt else ("AppendixBullet" if bullet else "AppendixBody")
                flow.append(appendix_paragraph(text[2:] if bullet else text, style, bullet))
        else:
            flow.append(appendix_paragraph(block, "OriginalPrompt" if original_prompt else "AppendixBody"))
    doc.build(flow, onFirstPage=footer, onLaterPages=footer)
    print(path)
    return path


def main():
    """Purpose: export current documents and optional references. Inputs: --text-only/--include-reference. Returns: None."""
    import sys
    include_reference = "--include-reference" in sys.argv
    write_markdown(include_reference)
    if "--text-only" not in sys.argv:
        if include_reference:
            build_pdf(2)
        build_pdf(3); build_ai_appendix()


if __name__ == "__main__":
    main()
