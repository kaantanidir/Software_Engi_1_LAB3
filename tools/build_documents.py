"""Export the same structured coursework data to editable Markdown and readable PDFs."""

import base64
import json
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image

from coursework_data import LAB3, GROUPS2, STORIES2, STORIES3, USECASES, SOURCES, COMPARISON, REJECTIONS

ROOT = Path(__file__).resolve().parents[1]
MODEL = "GPT-6.1 Sol (model-selector label supplied by the student on 2026-10-20); exact backend build not exposed."
FEATURES = [
    ("F01", "Accounts, login and preferences", "FR-01/02/03, NFR-02", "Create account; password/NFC login; save default milk/strength/temperature; log out/in."),
    ("F02", "Menu, categories and nutrition", "FR-04", "Browse six drinks; filter Coffee/Chocolate; inspect estimated nutrition and allergens."),
    ("F03", "Validated custom drink quote", "FR-05", "Change milk, strength, temperature, syrup and shots; observe server-calculated quote."),
    ("F04", "Named personal recipes", "FR-06", "Save Morning Oat; rename; load and edit settings; save update; delete."),
    ("F05", "Ingredient/quantity checks", "FR-07, NFR-03", "Set oat level below threshold as technician; verify oat recipe cannot be purchased; refill."),
    ("F06", "Context/history recommendations", "FR-08/19", "Toggle Recommended first; change simulated weather/time; buy a drink and verify ranking reasons."),
    ("F07", "Checkout and immutable history", "FR-11/12/20, NFR-03", "Approve/decline five payment simulators; inspect history; retry a request; test offline pending then reconnect."),
    ("F08", "Earn and redeem loyalty", "FR-13", "Apply 100 points; verify SEK 10 discount and success-only deduction/earning."),
    ("F09", "QR receipt and email adapter", "FR-14", "Open receipt QR/text; send to local simulator outbox; fail email and retain QR fallback."),
    ("F10", "Protected maintenance/diagnostics", "FR-15/16/17/18", "PIN/master-NFC login; full refill; waste halt/empty; fault logging; authorized diagnostic export."),
]

OVERVIEW = "SmartBrew AI is a personalized coffee-machine system for office customers and maintenance technicians. The full requirements cover profiles, saved recipes, context/mood recommendations, customization, supplies, payments, receipts, diagnostics, privacy and service-failure fallback. The group's custom feature is loyalty redemption. The executable prototype implements ten selected feature groups with persistent local state and a browser interface."
PROVENANCE = "The preserved files in docs/baseline are exactly the submitted Lab 2 artifacts extracted from the supplied ZIP. This chat previously assisted creation of Lab 2; it would be inaccurate to label that submission an independently human-authored baseline. The comparison uses the actual submitted group version, then separates the feedback correction from the later LLM-assisted refinement. No later correction is silently substituted for the submitted baseline."
PROMPT_STRATEGY = "Use the actual system description, feedback and course slides as grounding; constrain all requirements to the six-column lecture template; retain the submitted baseline; check each source capability against stories/requirements/backlog; separate source mandates from proposed design assumptions; select ten coherent demonstrable feature groups; implement and test approval, rejection, ownership, retry, safety and offline paths. This was one evolving chat request with student clarifications, not an invented sequence of separate prompting experiments."
ASSUMPTIONS = [
    "Prototype money uses integer ore (100 ore = SEK 1); demo prices/nutrition/ingredient quantities are illustrative and are not production dietary specifications.",
    "Loyalty: earn one point per whole SEK actually paid; one point redeems SEK 0.10, bounded by balance and price. Demo Alex begins with 250 points and SEK 200 prepaid credit; new accounts begin with zero.",
    "Customer orders may be placed as guest; profile/recipe/history and prepaid/loyalty features require customer login. Guest receipts use an unguessable capability token.",
    "Mood opt-in and the proposed 2-second response target are design refinements; the original brief does not prescribe consent UI, a numerical latency target or point-conversion rules.",
    "Weather/time, NFC/key signals, machine sensors, payment approval and email are simulated locally. Manual ordering and stored-value prepaid payments work while the simulated network is offline.",
    "Online-only payment requests can be persisted as pending without dispensing. Reconnect and customer Retry performs authorization/revalidation once; the prototype never assumes that a wallet can approve offline.",
    "Camera mood inference and the optional local LLM are elicited but deferred from the selected ten features. A keyword parser and a mood selector are not presented as AI implementations.",
    "No physical brew command or real card authorization occurs. Admin diagnostics can be exported locally; there is no deployed remote diagnostic service or physical key reader.",
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


def write_markdown():
    """Purpose: export editable artifacts and Astah descriptions. Inputs: module records. Returns: None."""
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    records2 = lab2_records()
    headers = ["ID", "Description", "Inputs", "Outputs", "Precondition", "Postcondition"]
    backlog_headers = ["ID", "Name", "Importance", "Estimate", "Description", "How to demo", "Notes"]
    lab2 = ["# SmartBrew AI - Group 28 - Lab 2 correction", "Date: 2026-10-20", OVERVIEW,
            "## What changed after feedback", "The feedback gave a positive final grade. This revision fills the requirement template (Lecture 2, slide 47), places Customer/Technician on the left and Payment Processor on the right, makes Customize Beverage the customer's entry and the base of natural-language extension, and repairs the saved use-case descriptions. It also clarifies omissions found during source coverage review. The original archive is unchanged.",
            "## User stories", table_md(["ID", "Name", "Story"], [[f"US-{i:02d}", GROUPS2[i-1][0], story] for i, story in enumerate(STORIES2, 1)]),
            "## Requirements", "For combined operations, each labeled pre/postcondition applies to that operation; registration and login are alternative paths. This retains the original thirteen IDs.", table_md(headers, requirement_rows(records2)),
            "## Initial product backlog", "Importance is a proposed 0-100 ordering score (higher first). Estimate is relative story points, not hours. Estimates require group refinement. Description is retained in addition to the slide columns; Notes carries requirement/story links. No sprint commitment is asserted without team capacity.", table_md(backlog_headers, backlog_rows(records2, 2)),
            "## Use-case correction", "Customer -- Customize Beverage (solid association). Process Natural Language Order --<<extend>>--> Customize Beverage. Customize Beverage --<<include>>--> Check Ingredient Availability. Analyze Mood --<<extend>>--> Generate Recommendations when enabled/opted in. Redeem Loyalty --<<extend>>--> Process Payment. Technician has independent solid associations with Manage Inventory and View Error Logs; viewing logs is not a mandatory refill step. Extensions point toward their base use case.",
            "## Assumptions", "\n".join("- " + item for item in ASSUMPTIONS[:4]), "## Sources", "Provided system description and Lab 2 guidelines; instructor feedback page 1; Lecture-02-2026 slides 20-23, 30-31, 38, 43 and 47-48. The book reading remains the group's responsibility; no claim is made that the students have completed it."]
    (docs / "LAB2_CORRECTED.md").write_text("\n\n".join(lab2) + "\n", encoding="utf-8")
    text3 = ["# SmartBrew AI - Group 28 - Lab 3", "Date: 2026-10-20", "## Task A - Elicitation", OVERVIEW,
             "### Models and provenance", MODEL, "Tasks A, B and C in this revision use this same model through the Codex application. Earlier Lab 2 assistant model/version was not recorded and is not retroactively invented.", PROVENANCE,
             "### Prompt strategy", PROMPT_STRATEGY, "Main prompts, student clarifications and assistant response excerpts are recorded in AI_CONVERSATION.md. Generated code is retained in Git; do not describe the artifacts as independently human authored.",
             "### Source inventory", table_md(["Source", "System capability"], SOURCES),
             "### User stories", table_md(["ID", "Name", "Story", "Requirement links"], STORIES3),
             "### Functional requirements", table_md(headers, requirement_rows([r for r in LAB3 if r["id"].startswith("FR-") ])),
             "### Non-functional requirements", table_md(headers, requirement_rows([r for r in LAB3 if r["id"].startswith("NFR-") ])),
             "### Initial product backlog", "Same required format as corrected Lab 2. Importance 0-100, high first; estimate in relative story points. Proposed values are not measured team velocity or a promised delivery date. Dependencies: accounts before private recipes/history; quotes/availability before checkout; approved purchase before loyalty/receipts. Optional AI and physical integrations remain backlog work.", table_md(backlog_headers, backlog_rows(LAB3, 3)),
             "### Comparison with the submitted Lab 2", PROVENANCE, table_md(["Topic", "Submitted Lab 2", "LLM revision", "Decision and reason"], COMPARISON),
             "### Rejected design alternatives", "These are options evaluated and rejected during this generation, not fabricated earlier model responses.", table_md(["Option", "Decision / justification"], REJECTIONS),
             "### Critical evaluation of the assistant", "The earlier assistant checked names in a serialized Astah ZIP and PDF and overclaimed completeness. The actual feedback identified the missing requirement fields. A supported-API inspection in this revision additionally found that Process Payment contained the natural-language description, Analyze Mood had no completed fields, Check Ingredient Availability was absent from the diagram canvas, and optional/mandatory relationships conflicted with descriptions. This shows why matching names is insufficient. The expanded elicitation improves coverage and traceability, but point rules, consent and latency targets remain design proposals; hardware and external-service realism require separate validation.",
             "## Task B - Selected implementation", table_md(["Feature", "Functionality", "Requirements", "Demonstration"], FEATURES),
             "### Scope and assumptions", "\n".join("- " + item for item in ASSUMPTIONS),
             "### Architecture", "A Python HTTP adapter serves a vanilla JavaScript interface. A service layer enforces authorization and business rules. SQLite persists accounts, hashed sessions, recipes, orders, stock, waste, pending requests, events and email simulator outbox. Checkout uses a write transaction and unique request key. QR generation uses the pinned qrcode library. No external service is required after installation.",
             "### Validation", "See QA_RESULTS.md and evidence/ for actual recorded runs. Unit tests use isolated temporary databases. Browser checks use a separate QA database and verify desktop/mobile layout and end-to-end flows. Passing simulator tests does not validate actual hardware, financial processors, SMTP or camera/LLM inference.",
             "## Task C - Repository and documentation", "Repository: https://github.com/kaantanidir/Software_Engi_1_LAB3 . README.md contains environment, installation, execution, tests and all ten feature demos. Each authored Python/JavaScript/Java function documents purpose, inputs and outputs. Vendored Lucide is third-party library code with its license retained. Runtime data, local packages and temporary files are excluded from Git.",
             "### Student review before submission", "Review the exact point conversion, pending-payment policy, estimates and optional-feature scope. Read and understand the implementation and run the walkthrough. The baseline comparison is intentionally labeled group submission previously assisted by AI; confirm that disclosure with the course if a strictly independent human baseline is required.",
             "### References", "Instructor feedback page 1; Lecture-02-2026 slides 20-23, 30-31, 38, 43 and 47-48; Lecture-03-2026 slides 17, 22, 28, 38-40; system description and assignment guidelines supplied in the chat. Henrik Kniberg, Scrum and XP from the Trenches: https://www.infoq.com/minibooks/download/scrum-xp-from-the-trenches/ (recommended course reading; student completion is not asserted)."]
    (docs / "LAB3_REPORT.md").write_text("\n\n".join(text3) + "\n", encoding="utf-8")
    uc = ["# Corrected use-case descriptions", "Template: Lecture 2 slides 30-31. The saved Astah project contains the same descriptions."]
    tsv = []
    for name, values in USECASES.items():
        uc.append("## " + name)
        for key, value in zip(["Preconditions", "InitiatingActor", "Goal", "MainScenario", "Alternatives"], values):
            uc.append("**" + key + "**\n\n" + value)
        tsv.append(name + "\t" + "\t".join(base64.b64encode(value.encode()).decode() for value in values))
    (docs / "USE_CASE_DESCRIPTIONS.md").write_text("\n\n".join(uc), encoding="utf-8")
    (ROOT / "tmp").mkdir(exist_ok=True)
    (ROOT / "tmp" / "descriptions.tsv").write_text("\n".join(tsv), encoding="utf-8")


STYLES = getSampleStyleSheet()
STYLES.add(ParagraphStyle(name="Cell", fontName="Helvetica", fontSize=8.3, leading=11.2, spaceAfter=0, alignment=TA_LEFT))
STYLES.add(ParagraphStyle(name="BodyCustom", fontName="Helvetica", fontSize=10, leading=14, spaceAfter=9))
STYLES.add(ParagraphStyle(name="SmallCustom", fontName="Helvetica", fontSize=8.5, leading=12, textColor=colors.HexColor("#4e635d")))


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
    canvas.drawString(16*mm, 10*mm, "SmartBrew AI | Group 28 | 2026-10-20")
    canvas.drawRightString(281*mm, 10*mm, str(doc.page)); canvas.restoreState()


def heading(flow, title, page=False):
    """Purpose: add a section title. Inputs: flow/title/page-break flag. Returns: None."""
    if page: flow.append(PageBreak())
    flow.extend([paragraph(title, "Heading1"), Spacer(1, 5*mm)])


def build_pdf(lab):
    """Purpose: generate final lecture-format report. Inputs: lab number. Returns: PDF path."""
    output = ROOT / "output" / "pdf"
    output.mkdir(parents=True, exist_ok=True)
    path = output / ("G28Lab2_Corrected.pdf" if lab == 2 else "G28Lab3_Report.pdf")
    doc = SimpleDocTemplate(str(path), pagesize=landscape(A4), rightMargin=16*mm, leftMargin=16*mm, topMargin=15*mm, bottomMargin=18*mm, title=f"SmartBrew AI - Group 28 - Lab {lab}", author="Group 28 (LLM-assisted revision)")
    flow = []
    heading(flow, f"SmartBrew AI - Group 28 - Lab {lab}" + (" correction" if lab == 2 else " report"))
    flow.append(paragraph(OVERVIEW))
    if lab == 2:
        flow.append(paragraph("Feedback: positive overall. Main correction: requirements now include Inputs, Outputs, Precondition and Postcondition, following Lecture 2 slide 47. Diagram layout, customer entry, saved descriptions and optional relationships are repaired. Thirteen original requirement/story IDs are retained; added clarifications are documented."))
        heading(flow, "User stories")
        flow.append(table(["ID","Name","Story"],[[f"US-{i:02d}",GROUPS2[i-1][0],story] for i,story in enumerate(STORIES2,1)],[19,58,188]))
        records = lab2_records()
    else:
        flow.append(paragraph("Task A - Requirements elicitation, critical comparison and prompt record"))
        flow.append(paragraph("Model: " + MODEL)); flow.append(paragraph(PROVENANCE)); flow.append(paragraph(PROMPT_STRATEGY))
        flow.append(paragraph("Exact student prompts and key assistant responses: docs/AI_CONVERSATION.md. Tasks A, B and C use the recorded model; the earlier Lab 2 version is unknown."))
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
        diagram = ROOT / "evidence" / "use-cases.png"
        if diagram.exists():
            heading(flow,"Corrected Astah diagram",True)
            flow.append(Image(str(diagram), width=230*mm, height=150*mm, kind="proportional"))
    else:
        heading(flow,"Comparison with the submitted Lab 2",True)
        flow.append(paragraph(PROVENANCE))
        flow.append(table(["Topic","Submitted Lab 2","LLM-assisted revision","Decision and reason"], COMPARISON,[41,67,91,66]))
        heading(flow,"Rejected alternatives and critical evaluation",True)
        flow.append(paragraph("These are options considered during this generation, not fabricated earlier model responses."))
        flow.append(table(["Option","Justification"],REJECTIONS,[90,175]))
        flow.append(Spacer(1,6*mm))
        flow.append(paragraph("The previous assistant overclaimed consistency after checking only serialized names. It missed required requirement fields, the wrong payment description, an empty mood description and inconsistent optional relationships. This revision improves format/coverage and tests the implementation, but proposed point rules, latency and hardware assumptions still need student/stakeholder review."))
        heading(flow,"Task B - Ten selected feature groups",True)
        flow.append(table(["ID","Functionality","Requirements","Demonstration"],FEATURES,[16,59,52,138]))
        heading(flow,"Implementation scope and assumptions",True)
        for item in ASSUMPTIONS: flow.append(paragraph(item)); flow.append(Spacer(1,2*mm))
        heading(flow,"Task C - Setup, repository and validation",True)
        flow.append(paragraph("Repository: https://github.com/kaantanidir/Software_Engi_1_LAB3"))
        flow.append(paragraph("Runtime: Python 3.12 (verified 3.12.14), modern browser, pinned qrcode 8.2 (colorama 0.4.6 on Windows). SQLite and HTTP service use the Python standard library. Setup: python -m venv .venv; activate; python -m pip install -r requirements.txt. Run: python app.py --port 8765. Visit http://127.0.0.1:8765. Tests: python -m unittest discover -s tests -v."))
        flow.append(paragraph("Demo customer: alex@smartbrew.test / DemoPass123!; registered NFC DEMO-NFC-001. Technician PIN 246810; master NFC MASTER-NFC-001. These are public simulator fixtures, not production credentials."))
        flow.append(paragraph("README.md provides every feature's walkthrough, reset procedure and limitations. All authored functions document purpose/input/output. Runtime data and packages are excluded from Git. See docs/QA_RESULTS.md and evidence/ for actual test records. Approval in the simulator is not financial or hardware validation."))
        flow.append(paragraph("References: provided feedback, system description and assignment instructions; Lecture 2 slides 20-23, 30-31, 38, 43, 47-48; Lecture 3 slides 17, 22, 28 and 38-40. Recommended reading: Henrik Kniberg, Scrum and XP from the Trenches (InfoQ). No student reading completion is claimed.","SmallCustom"))
        heading(flow,"Appendix - Source coverage",True)
        flow.append(table(["Source","Capability","Requirement(s)"],[[sid,description,"; ".join(r["id"] for r in LAB3 if sid in r["source"].split(";")[0].split("/"))] for sid,description in SOURCES],[20,140,105],padding=5))
    doc.build(flow,onFirstPage=footer,onLaterPages=footer)
    print(path)
    return path


def main():
    """Purpose: export editable content and optional PDFs. Inputs: --text-only. Returns: None."""
    import sys
    write_markdown()
    if "--text-only" not in sys.argv:
        build_pdf(2); build_pdf(3)


if __name__ == "__main__":
    main()
