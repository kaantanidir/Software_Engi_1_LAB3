"""Validate coursework coverage/function comments and assemble the labeled Lab 2 review bundle."""

import ast
import hashlib
import json
from pathlib import Path
import platform
import re
import sys
from zipfile import ZipFile, ZIP_DEFLATED

from coursework_data import LAB3, SOURCES, STORIES3, STORY_COMPARISON, ADDED_STORIES

ROOT = Path(__file__).resolve().parents[1]

FINAL_ZIP_WHITELIST = (
    ".gitattributes",
    ".gitignore",
    "README.md",
    "SUBMISSION.md",
    "app.py",
    "package.json",
    "requirements.txt",
    "requirements-docs.txt",
    "smartbrew/__init__.py",
    "smartbrew/assistant.py",
    "smartbrew/service.py",
    "web/app.js",
    "web/assistant.js",
    "web/images/chocolate.jpg",
    "web/images/espresso.jpg",
    "web/images/latte.jpg",
    "web/index.html",
    "web/receipt.html",
    "web/receipt.js",
    "web/styles.css",
    "web/vendor/LUCIDE-LICENSE",
    "web/vendor/lucide.min.js",
    "tests/__init__.py",
    "tests/test_assistant.py",
    "tests/test_service.py",
    "tools/browser_check.cjs",
    "tools/build_documents.py",
    "tools/check_assistant_conversations.py",
    "tools/check_assistant_heldout_baseline.py",
    "tools/check_assistant_long_chat.py",
    "tools/check_local_ai.py",
    "tools/coursework_data.py",
    "tools/export_development_transcript.py",
    "tools/start_local_ai.ps1",
    "tools/start_smartbrew.ps1",
    "tools/verify_artifacts.py",
    "docs/AI_CONVERSATION.md",
    "docs/DEVELOPMENT_TRANSCRIPT.md",
    "docs/DEVELOPMENT_TRANSCRIPT_MANIFEST.json",
    "docs/ARCHITECTURE.md",
    "docs/ASSETS.md",
    "docs/CROSS_LAB_REVIEW.md",
    "docs/LAB3_AI_APPENDIX.md",
    "docs/LAB3_REPORT.md",
    "docs/MAIN_PROMPT.md",
    "docs/QA_RESULTS.md",
    "docs/README.md",
    "docs/baseline/G28Lab2.asta",
    "docs/baseline/G28Lab2.pdf",
    "docs/baseline/feedback-text.md",
    "docs/baseline/manifest.json",
    "docs/baseline/submitted-task2b.md",
    "docs/baseline/lab1/G28Lab1.asta",
    "docs/baseline/lab1/feedback-text.md",
    "docs/baseline/lab1/manifest.json",
    "evidence/README.md",
    "evidence/current/artifact-checks.json",
    "evidence/current/assistant-options.png",
    "evidence/current/assistant-options-mobile.png",
    "evidence/current/assistant-conversations.json",
    "evidence/current/assistant-heldout-postchange.json",
    "evidence/current/assistant-long-chat.json",
    "evidence/current/browser-results.json",
    "evidence/current/desktop.png",
    "evidence/current/local-ai-results.json",
    "evidence/current/local-assistant.png",
    "evidence/current/maintenance.png",
    "evidence/current/mobile.png",
    "evidence/current/receipt.png",
    "evidence/current/test-scenarios.png",
    "evidence/current/unit-tests.txt",
    "evidence/current/clean-install.txt",
    "evidence/current/ux-polish.json",
    "evidence/current/assistant-loading.png",
    "evidence/history/assistant-conversations-first-run.json",
    "evidence/history/assistant-conversations-second-run.json",
    "evidence/history/assistant-heldout-baseline.json",
    "evidence/history/assistant-heldout-postchange-first-run.json",
    "evidence/history/assistant-long-chat-wording-failure.json",
    "evidence/history/assistant-options-first-run.json",
    "evidence/history/assistant-options-alternative-regression.json",
    "evidence/history/authentication-regression-before.txt",
    "evidence/history/browser-f06-first-run-failure.json",
    "evidence/history/browser-failure.json",
    "evidence/history/lab1-export/G28Lab1/Class Diagram.png",
    "evidence/history/lab1-export/G28Lab1/Component Diagram0.png",
    "evidence/history/lab1-inspection.txt",
    "evidence/history/local-ai-initial-review.txt",
    "evidence/history/recommendation-regression-before.txt",
    "output/G28Lab3_AI_Appendix.pdf",
    "output/G28Lab3_Report.pdf",
)

FORBIDDEN_ZIP_PREFIXES = (
    ".git/",
    ".venv/",
    ".packages/",
    "data/",
    "tmp/",
    "__pycache__/",
    "docs/development/",
    "docs/reference/lab2/",
    "evidence/history/astah-export/",
    "evidence/history/use-cases.png",
    "output/G28Lab3_Project.zip",
    "tools/archive/",
    "docs/baseline/lecture",
)

FORBIDDEN_ZIP_SUFFIXES = (
    ".pyc",
    ".pyo",
    ".bak",
    ".sqlite3",
    ".db",
    ".zip",
    ".gguf",
    ".exe",
    ".dll",
    ".log",
)


def validate_zip_entry(rel_path):
    """Purpose: reject forbidden paths, databases, models, environments or nested archives. Inputs: relative POSIX path string. Returns: None or raises AssertionError."""
    normalized = rel_path.replace("\\", "/").removeprefix("./").lstrip("/")
    assert normalized in FINAL_ZIP_WHITELIST, f"Non-whitelisted path in project ZIP: {normalized}"
    for prefix in FORBIDDEN_ZIP_PREFIXES:
        assert not normalized.startswith(prefix), f"Forbidden path prefix in project ZIP: {normalized}"
    assert "/__pycache__/" not in f"/{normalized}/", f"Cache path in project ZIP: {normalized}"
    for suffix in FORBIDDEN_ZIP_SUFFIXES:
        assert not normalized.lower().endswith(suffix), f"Forbidden file type in project ZIP: {normalized}"


def validate_project_zip_policy():
    """Purpose: verify all whitelisted Lab 3 ZIP entries exist and pass exclusion rules without building the ZIP. Inputs: FINAL_ZIP_WHITELIST. Returns: validated entry count."""
    assert len(FINAL_ZIP_WHITELIST) == len(set(FINAL_ZIP_WHITELIST)), "Duplicate entries in FINAL_ZIP_WHITELIST"
    for rel_path in FINAL_ZIP_WHITELIST:
        validate_zip_entry(rel_path)
        full_path = (ROOT / rel_path).resolve()
        assert full_path.is_relative_to(ROOT) and full_path.is_file(), f"Missing whitelisted file for project ZIP: {rel_path}"
    for forbidden_sample in (
        "docs/development/ASSISTANT_IMPLEMENTATION_UPDATE.md",
        "docs/development/GEMINI_HANDOFF.md",
        "docs/reference/lab2/REVIEW.md",
        "docs/reference/lab2/G28Lab2.asta",
        "docs/reference/lab2/G28Lab2_Corrected.zip",
        "docs/reference/lab2/G28Lab2_Corrected.pdf",
        "output/G28Lab3_Project.zip",
        "tools/archive/AstahRepair.java",
        "tools/archive/inspect_sources.py",
        "tools/archive/inspect_lab1.py",
        "evidence/history/use-cases.png",
        "evidence/history/astah-export/G28Lab2/UseCase Diagram0.png",
        "data/smartbrew.sqlite3",
        "data/local-ai/models/model.gguf",
        ".venv/Scripts/python.exe",
        ".packages/node_modules",
        "tmp/browser-abc/qa.db",
        "smartbrew/__pycache__/service.cpython-312.pyc",
    ):
        rejected = False
        try:
            validate_zip_entry(forbidden_sample)
        except AssertionError:
            rejected = True
        assert rejected, f"Forbidden sample was not rejected by ZIP policy: {forbidden_sample}"
    return len(FINAL_ZIP_WHITELIST)


def build_project_zip(destination=None):
    """Purpose: deterministically build and verify output/G28Lab3_Project.zip from FINAL_ZIP_WHITELIST. Inputs: optional destination Path. Returns: created ZIP Path."""
    validate_project_zip_policy()
    target = Path(destination) if destination else (ROOT / "output" / "G28Lab3_Project.zip")
    target.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(target, "w", ZIP_DEFLATED) as bundle:
        for rel_path in FINAL_ZIP_WHITELIST:
            bundle.write(ROOT / rel_path, rel_path)
    with ZipFile(target, "r") as bundle:
        names = bundle.namelist()
        assert tuple(names) == FINAL_ZIP_WHITELIST, "ZIP archive entries do not match exact whitelist order"
        for name in names:
            validate_zip_entry(name)
    return target


def check_document_links():
    """Purpose: validate navigation after documentation moves. Inputs: README and documentation index files. Returns: checked local-link count."""
    count = 0
    checked_files = (
        ROOT / "README.md",
        ROOT / "SUBMISSION.md",
        ROOT / "docs" / "README.md",
        ROOT / "docs" / "AI_CONVERSATION.md",
        ROOT / "evidence" / "README.md",
        ROOT / "docs" / "development" / "ASSISTANT_IMPLEMENTATION_UPDATE.md",
        ROOT / "docs" / "development" / "GEMINI_HANDOFF.md",
    )
    for file in checked_files:
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", file.read_text(encoding="utf-8")):
            if target.startswith(("https://", "http://", "mailto:", "#")):
                continue
            path = (file.parent / target.split("#", 1)[0]).resolve()
            assert path.is_relative_to(ROOT) and path.exists(), f"Broken local link in {file.name}: {target}"
            count += 1
    return count


def check_story_comparison():
    """Purpose: verify comparison against actual submitted wording and cover every revised story. Inputs: baseline and structured story tables. Returns: coverage counts."""
    baseline = " ".join((ROOT / "docs" / "baseline" / "submitted-task2b.md").read_text(encoding="utf-8").split())
    assert len(STORY_COMPARISON) == 13 and len(ADDED_STORIES) == 7
    original_ids, retained_ids = set(), set()
    for original, wording, revised, reason in STORY_COMPARISON:
        original_id = re.findall(r"US-\d{2}", original)
        assert len(original_id) == 1 and original_id[0] not in original_ids
        assert " ".join(wording.split()) in baseline, f"Comparison does not quote the submitted story: {original}"
        original_ids.update(original_id)
        retained_ids.update(re.findall(r"US-\d{2}", revised))
        assert reason.strip(), f"Missing story-change justification: {original}"
    assert original_ids == {f"US-{number:02d}" for number in range(1, 14)}
    added_ids = {row[0].split(" / ")[0] for row in ADDED_STORIES}
    assert len(retained_ids) == 17 and not retained_ids & added_ids
    assert retained_ids | added_ids == {row[0] for row in STORIES3}
    assert all(row[1].strip() and row[2].strip() for row in ADDED_STORIES)
    return {"originalStories": len(original_ids), "retainedOrSplitStories": len(retained_ids), "additionalStories": len(added_ids), "revisedStories": len(STORIES3), "submittedWordingVerified": True}


def check_development_transcript():
    """Purpose: validate attachment integrity, provenance counts and declared redactions. Inputs: transcript/manifest. Returns: exported message count."""
    path = ROOT / "docs" / "DEVELOPMENT_TRANSCRIPT.md"
    raw = path.read_bytes()
    transcript = raw.decode("utf-8")
    manifest = json.loads((ROOT / "docs" / "DEVELOPMENT_TRANSCRIPT_MANIFEST.json").read_text(encoding="utf-8"))
    assert hashlib.sha256(raw).hexdigest() == manifest["transcript_sha256"], "Conversation attachment changed after export"
    speakers = re.findall(r"^### \d{3} - (Student|Codex) - ", transcript, flags=re.M)
    assert len(speakers) == manifest["messages"] == sum(source["included_messages"] for source in manifest["sources"])
    assert speakers.count("Student") == manifest["roles"]["user"]
    assert speakers.count("Codex") == manifest["roles"]["assistant"]
    assert all(re.fullmatch(r"[a-f0-9]{64}", source["sha256"]) for source in manifest["sources"])
    assert not re.search(r"(?i)C:[/\\]Users[/\\]", transcript), "Unredacted home path in conversation"
    assert not re.search(r"\b(?:ghp_|github_pat_|sk-|hf_)[A-Za-z0-9_-]{20,}\b", transcript), "Possible token in conversation"
    assert manifest["redactions"].get("account_passwords", 0) > 0
    assert "separate Gemini/Antigravity session transcript is unavailable" in transcript
    return manifest["messages"]


def main():
    """Purpose: validate outputs and record evidence. Inputs: generated files. Returns: None; writes QA/ZIP/previews."""
    coverage = {}
    for source, _ in SOURCES:
        coverage[source] = [r["id"] for r in LAB3 if source in r["source"].split(";")[0].split("/")]
        assert coverage[source], "Uncovered source: " + source
    functions = 0
    for folder in (ROOT, ROOT / "smartbrew", ROOT / "tests", ROOT / "tools", ROOT / "tools" / "archive"):
        for file in folder.glob("*.py"):
            tree = ast.parse(file.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    doc = ast.get_docstring(node)
                    assert doc and "input" in doc.lower() and ("return" in doc.lower() or "output" in doc.lower() or "yield" in doc.lower()), f"Missing purpose/input/output: {file}:{node.lineno}"
                    functions += 1
    counts = {}
    manifest = json.loads((ROOT / "docs" / "baseline" / "manifest.json").read_text())
    for name in ("G28Lab2.pdf", "G28Lab2.asta"):
        assert hashlib.sha256((ROOT / "docs" / "baseline" / name).read_bytes()).hexdigest() == manifest[name], "Baseline changed"
    lab1 = ROOT / "docs" / "baseline" / "lab1"
    manifest1 = json.loads((lab1 / "manifest.json").read_text())
    assert hashlib.sha256((lab1 / "G28Lab1.asta").read_bytes()).hexdigest() == manifest1["G28Lab1.asta"], "Lab 1 baseline changed"
    whitelisted_count = validate_project_zip_policy()
    story_comparison = check_story_comparison()
    transcript_messages = check_development_transcript()
    unit_log = (ROOT / "evidence" / "current" / "unit-tests.txt").read_text(encoding="utf-8")
    unit_pass = re.search(r"Ran (\d+) tests in [\d.]+s\s+OK\s*$", unit_log)
    assert unit_pass, "Unit-test evidence does not contain a successful completion"
    unit_count = int(unit_pass[1])
    browser = json.loads((ROOT / "evidence" / "current" / "browser-results.json").read_text(encoding="utf-8"))
    assert browser["errors"] == []
    three_choices_verified = False
    live_ai = browser.get("liveAI") or {}
    if live_ai.get("options") is not None:
        assert live_ai.get("realInference") is True
        option_turn, followup_turn = live_ai["options"]
        assert len(option_turn["response"]["suggestions"]) == 3
        chosen = option_turn["response"]["suggestions"][1]["quote"]["config"]
        assert followup_turn["request"]["context_config"] == chosen
        assert followup_turn["response"]["quote"]["config"] == {**chosen, "strength": "mild"}
        three_choices_verified = True
    browser_count = len(browser["checks"])
    clean_log = (ROOT / "evidence" / "current" / "clean-install.txt").read_text(encoding="utf-8")
    assert "qrcode==8.2" in clean_log and "colorama==0.4.6" in clean_log and "No broken requirements found." in clean_log
    assert re.search(r"Ran 38 tests in [\d.]+s\s+OK\s*$", clean_log), "Clean-install unit test evidence incomplete"
    ux = json.loads((ROOT / "evidence" / "current" / "ux-polish.json").read_text(encoding="utf-8"))
    assert ux["freshVenv"] and ux["workspacePackagesAbsent"] and not ux["personalDatabaseUsed"]
    assert ux["exampleButtons"] == 3 and ux["examplesFillAndFocus"] and not ux["exampleClicksSendRequests"]
    assert ux["askRequests"] == 1 and ux["realInference"] and ux["loadingClearedAfterResponse"]
    assert ux["loadingAnimation"] == "assistant-loading" and ux["reducedMotionAnimation"] == "none"
    assert ux["mobile"]["scrollWidth"] <= ux["mobile"]["width"]
    if "--source-only" in sys.argv:
        summary = {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "pythonFunctionsDocumented": functions,
            "sourcesCovered": len(coverage),
            "baselineHashesVerified": True,
            "lab1BaselineHashVerified": True,
            "readmeAndIndexLocalLinksVerified": check_document_links(),
            "projectZipWhitelistVerified": whitelisted_count,
            "storyComparison": story_comparison,
            "developmentTranscriptMessagesVerified": transcript_messages,
            "unitTestsPassed": unit_count,
            "browserChecksPassed": browser_count,
            "threeAssistantChoicesAndSelectedFollowupVerified": three_choices_verified,
            "cleanInstallVerified": True,
            "examplePromptsAndReducedMotionVerified": True,
        }
        print(json.dumps(summary, indent=2))
        return
    from PIL import Image, ImageDraw
    from pypdf import PdfReader
    for label, pdf_path in (
        ("lab2", ROOT / "docs" / "reference" / "lab2" / "G28Lab2_Corrected.pdf"),
        ("lab3", ROOT / "output" / "G28Lab3_Report.pdf"),
    ):
        reader = PdfReader(pdf_path)
        text = "\n".join(p.extract_text() for p in reader.pages)
        for header in ("Description", "Inputs", "Outputs", "Precondition", "Postcondition", "Importance", "Estimate", "How to demo"):
            assert header in text, f"Missing {header} in {pdf_path.name}"
        if label == "lab3":
            for record in LAB3:
                assert record["id"] in text
            for value in ("F11", "Qwen3", "Ollama"):
                assert value in text
            for phrase in ("User-story comparison: original to revised", "Seven additional stories", "Assignment 2 authorship clarification", "DEVELOPMENT_TRANSCRIPT.md"):
                assert phrase in text, "Missing report revision: " + phrase
            for original, wording, revised, reason in STORY_COMPARISON:
                assert original in " ".join(text.split()), "Missing original-story comparison in PDF: " + original
        else:
            for i in range(1, 14):
                assert f"REQ-{i:02d}" in text and f"US-{i:02d}" in text
        counts[label] = len(reader.pages)
        pages = sorted((ROOT / "tmp").glob("pdf" + label[-1] + "-*.png"))[:len(reader.pages)]
        for start in range(0, len(pages), 6):
            sheet = Image.new("RGB", (1800, 1300), "#e0e5e2")
            draw = ImageDraw.Draw(sheet)
            for offset, file in enumerate(pages[start:start+6]):
                thumb = Image.open(file).convert("RGB")
                thumb.thumbnail((570, 590))
                x = (offset % 3) * 600 + 15
                y = (offset // 3) * 650 + 35
                sheet.paste(thumb, (x, y))
                draw.text((x, y - 20), file.stem, fill="black")
            sheet.save(ROOT / "tmp" / f"contact-{label}-{start//6+1}.png")
    appendix = PdfReader(ROOT / "output" / "G28Lab3_AI_Appendix.pdf")
    appendix_text = "\n".join(page.extract_text() for page in appendix.pages)
    for phrase in ("GPT-6.1 Sol", "Task A", "Task B", "Task C", "do we need to", "personal reflection", "DEVELOPMENT_TRANSCRIPT.md", "251 recorded messages"):
        assert phrase in appendix_text, "Missing appendix content: " + phrase
    counts["aiAppendix"] = len(appendix.pages)
    if "--include-reference" in sys.argv:
        with ZipFile(ROOT / "docs" / "reference" / "lab2" / "G28Lab2_Corrected.zip", "w", ZIP_DEFLATED) as bundle:
            bundle.write(ROOT / "docs" / "reference" / "lab2" / "G28Lab2.asta", "Lab2_G28/G28Lab2.asta")
            bundle.write(ROOT / "docs" / "reference" / "lab2" / "G28Lab2_Corrected.pdf", "Lab2_G28/G28Lab2.pdf")
            bundle.writestr("Lab2_G28/AI_REFERENCE_ONLY.txt", "AI-GENERATED REVIEW REFERENCE ONLY. NOT FOR LAB 1 OR LAB 2 SUBMISSION.\nGeneral course rules prohibit generated text/models in those submissions.\nOriginal submissions are preserved in docs/baseline of the Lab 3 repository.\n")
    evidence = {"python": platform.python_version(), "platform": platform.platform(), "pythonFunctionsDocumented": functions, "coverage": coverage, "pdfPages": counts, "baselineHashesVerified": True, "lab1BaselineHashVerified": True, "lab2GeneratedOutputsAreReviewOnly": True, "readmeAndIndexLocalLinksVerified": check_document_links(), "projectZipWhitelistVerified": whitelisted_count, "storyComparison": story_comparison, "developmentTranscriptMessagesVerified": transcript_messages, "documentRevisionDate": "2026-10-26", "unitTestsPassed": unit_count, "browserChecksPassed": browser_count, "threeAssistantChoicesAndSelectedFollowupVerified": three_choices_verified, "cleanInstallVerified": True, "examplePromptsAndReducedMotionVerified": True}
    (ROOT / "evidence" / "current" / "artifact-checks.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8", newline="\n")
    if "--build-project-zip" in sys.argv:
        build_project_zip()
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
