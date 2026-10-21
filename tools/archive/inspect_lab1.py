"""Preserve and inspect the supplied Lab 1 baseline without changing its model."""

import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

from pypdf import PdfReader


def main():
    """Purpose: preserve Lab 1 evidence. Inputs: supplied archive/feedback paths. Returns: None; writes copies/hash/text."""
    root = Path(__file__).resolve().parents[2]
    target = root / "docs" / "baseline" / "lab1"
    target.mkdir(parents=True, exist_ok=True)
    archive = Path(r"C:/Users/HP/Downloads/G28Lab1.zip")
    feedback = Path(r"C:/Users/HP/Downloads/G28Lab1.pdf")
    with ZipFile(archive) as bundle:
        models = [entry for entry in bundle.infolist() if entry.filename.lower().endswith(".asta")]
        if len(models) != 1:
            raise ValueError("Expected exactly one submitted Astah project.")
        content = bundle.read(models[0])
        (target / "G28Lab1.asta").write_bytes(content)
    extracted = "\n\n".join(f"## Page {i}\n\n{p.extract_text()}" for i, p in enumerate(PdfReader(feedback).pages, 1))
    (target / "feedback-text.md").write_text(extracted, encoding="utf-8")
    manifest = {
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "G28Lab1.asta": hashlib.sha256(content).hexdigest(),
        "feedback_pdf_sha256": hashlib.sha256(feedback.read_bytes()).hexdigest(),
        "feedback_pdf_path": str(feedback),
    }
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
