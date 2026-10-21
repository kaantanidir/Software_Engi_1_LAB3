"""Validate coursework coverage/function comments and assemble the labeled Lab 2 review bundle."""

import ast
import hashlib
import json
from pathlib import Path
import platform
import re
import sys
from zipfile import ZipFile, ZIP_DEFLATED

from coursework_data import LAB3, SOURCES

ROOT = Path(__file__).resolve().parents[1]

FINAL_ZIP_WHITELIST = (
    ".gitattributes",
    ".gitignore",
    "README.md",
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
    "tools/start_local_ai.ps1",
    "tools/verify_artifacts.py",
    "docs/AI_CONVERSATION.md",
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
    "evidence/history/assistant-conversations-first-run.json",
    "evidence/history/assistant-conversations-second-run.json",
    "evidence/history/assistant-heldout-baseline.json",
    "evidence/history/assistant-heldout-postchange-first-run.json",
    "evidence/history/assistant-long-chat-wording-failure.json",
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
        ROOT / "docs" / "README.md",
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
    for phrase in ("GPT-6.1 Sol", "Task A", "Task B", "Task C", "do we need to", "personal reflection"):
        assert phrase in appendix_text, "Missing appendix content: " + phrase
    counts["aiAppendix"] = len(appendix.pages)
    if "--include-reference" in sys.argv:
        with ZipFile(ROOT / "docs" / "reference" / "lab2" / "G28Lab2_Corrected.zip", "w", ZIP_DEFLATED) as bundle:
            bundle.write(ROOT / "docs" / "reference" / "lab2" / "G28Lab2.asta", "Lab2_G28/G28Lab2.asta")
            bundle.write(ROOT / "docs" / "reference" / "lab2" / "G28Lab2_Corrected.pdf", "Lab2_G28/G28Lab2.pdf")
            bundle.writestr("Lab2_G28/AI_REFERENCE_ONLY.txt", "AI-GENERATED REVIEW REFERENCE ONLY. NOT FOR LAB 1 OR LAB 2 SUBMISSION.\nGeneral course rules prohibit generated text/models in those submissions.\nOriginal submissions are preserved in docs/baseline of the Lab 3 repository.\n")
    evidence = {"python": platform.python_version(), "platform": platform.platform(), "pythonFunctionsDocumented": functions, "coverage": coverage, "pdfPages": counts, "baselineHashesVerified": True, "lab1BaselineHashVerified": True, "lab2GeneratedOutputsAreReviewOnly": True, "readmeAndIndexLocalLinksVerified": check_document_links(), "projectZipWhitelistVerified": whitelisted_count}
    (ROOT / "evidence" / "current" / "artifact-checks.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8", newline="\n")
    if "--build-project-zip" in sys.argv:
        build_project_zip()
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
