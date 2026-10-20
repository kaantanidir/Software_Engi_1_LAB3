"""Validate coursework coverage/function comments and assemble the labeled Lab 2 review bundle."""

import ast
import hashlib
import json
from pathlib import Path
import platform
import re
import sys
from zipfile import ZipFile, ZIP_DEFLATED

from PIL import Image, ImageDraw
from pypdf import PdfReader
from coursework_data import LAB3, SOURCES

ROOT = Path(__file__).resolve().parents[1]


def check_document_links():
    """Purpose: validate navigation after documentation moves. Inputs: README/index files. Returns: checked local-link count."""
    count = 0
    for file in (ROOT / "README.md", ROOT / "docs" / "README.md"):
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
    for folder in (ROOT, ROOT / "smartbrew", ROOT / "tests", ROOT / "tools"):
        for file in folder.glob("*.py"):
            tree = ast.parse(file.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    doc = ast.get_docstring(node)
                    assert doc and "input" in doc.lower() and ("return" in doc.lower() or "output" in doc.lower() or "yield" in doc.lower()), f"Missing purpose/input/output: {file}:{node.lineno}"
                    functions += 1
    counts = {}
    for label, name in (("lab2", "G28Lab2_Corrected.pdf"), ("lab3", "G28Lab3_Report.pdf")):
        reader = PdfReader(ROOT / "output" / "pdf" / name)
        text = "\n".join(p.extract_text() for p in reader.pages)
        for header in ("Description", "Inputs", "Outputs", "Precondition", "Postcondition", "Importance", "Estimate", "How to demo"):
            assert header in text, f"Missing {header} in {name}"
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
    manifest = json.loads((ROOT / "docs" / "baseline" / "manifest.json").read_text())
    for name in ("G28Lab2.pdf", "G28Lab2.asta"):
        assert hashlib.sha256((ROOT / "docs" / "baseline" / name).read_bytes()).hexdigest() == manifest[name], "Baseline changed"
    lab1 = ROOT / "docs" / "baseline" / "lab1"
    manifest1 = json.loads((lab1 / "manifest.json").read_text())
    assert hashlib.sha256((lab1 / "G28Lab1.asta").read_bytes()).hexdigest() == manifest1["G28Lab1.asta"], "Lab 1 baseline changed"
    appendix = PdfReader(ROOT / "output" / "pdf" / "G28Lab3_AI_Appendix.pdf")
    appendix_text = "\n".join(page.extract_text() for page in appendix.pages)
    for phrase in ("GPT-6.1 Sol", "Task A", "Task B", "Task C", "do we need to", "personal reflection"):
        assert phrase in appendix_text, "Missing appendix content: " + phrase
    counts["aiAppendix"] = len(appendix.pages)
    if "--include-reference" in sys.argv:
        with ZipFile(ROOT / "output" / "G28Lab2_Corrected.zip", "w", ZIP_DEFLATED) as bundle:
            bundle.write(ROOT / "output" / "G28Lab2.asta", "Lab2_G28/G28Lab2.asta")
            bundle.write(ROOT / "output" / "pdf" / "G28Lab2_Corrected.pdf", "Lab2_G28/G28Lab2.pdf")
            bundle.writestr("Lab2_G28/AI_REFERENCE_ONLY.txt", "AI-GENERATED REVIEW REFERENCE ONLY. NOT FOR LAB 1 OR LAB 2 SUBMISSION.\nGeneral course rules prohibit generated text/models in those submissions.\nOriginal submissions are preserved in docs/baseline of the Lab 3 repository.\n")
    evidence = {"python": platform.python_version(), "platform": platform.platform(), "pythonFunctionsDocumented": functions, "coverage": coverage, "pdfPages": counts, "baselineHashesVerified": True, "lab1BaselineHashVerified": True, "lab2GeneratedOutputsAreReviewOnly": True, "readmeAndIndexLocalLinksVerified": check_document_links()}
    (ROOT / "evidence" / "artifact-checks.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
