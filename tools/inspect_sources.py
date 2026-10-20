"""Preserve submission inputs and extract PDF text for an auditable comparison."""

import hashlib
import json
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from pypdf import PdfReader


def main():
    """Purpose: preserve supplied sources. Inputs: known source paths. Returns: None; writes copies/text/hashes."""
    root = Path(__file__).resolve().parents[1]
    baseline = root / "docs" / "baseline"
    baseline.mkdir(parents=True, exist_ok=True)
    archive = Path(r"C:/Users/HP/Desktop/VS UniStudies/Software Engi 1/Lab2_G28.zip")
    sources = {
        "feedback": Path(r"C:/Users/HP/Downloads/G28Lab2 (1).pdf"),
        "lecture2": Path(r"C:/Users/HP/Desktop/VS UniStudies/Software Engi 1/Lab Lecture Slides/Lecture-02-2026.pdf"),
        "lecture3": Path(r"C:/Users/HP/Desktop/VS UniStudies/Software Engi 1/Lab Lecture Slides/Lecture-03-2026.pdf"),
    }
    manifest = {"original_archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest()}
    with ZipFile(archive) as bundle:
        for name in ("G28Lab2.pdf", "G28Lab2.asta"):
            content = bundle.read("Lab2_G28/" + name)
            (baseline / name).write_bytes(content)
            manifest[name] = hashlib.sha256(content).hexdigest()
            if name.endswith(".pdf"):
                text = "\n\n".join(f"## Page {i}\n\n{p.extract_text()}" for i, p in enumerate(PdfReader(BytesIO(content)).pages, 1))
                (baseline / "submitted-task2b.md").write_text(text, encoding="utf-8")
    for label, path in sources.items():
        manifest[label] = {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        text = "\n\n".join(f"## Page {i}\n\n{p.extract_text()}" for i, p in enumerate(PdfReader(path).pages, 1))
        (baseline / f"{label}-text.md").write_text(text, encoding="utf-8")
    (baseline / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
