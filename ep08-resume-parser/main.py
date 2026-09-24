"""
CLI entry point for the AI Resume Parser.

Usage:
    python main.py samples/clean_resume.txt
    python main.py samples/adversarial_resume.txt

Reads a plain-text resume (PDF extraction hook included but optional — see
extract_text_from_pdf), sends it through parser.parse_resume(), prints the
resulting JSON, and saves it next to the input file as <name>.json.
"""

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from parser import parse_resume

load_dotenv()  # loads ANTHROPIC_API_KEY from a local .env — see Episode 5


def extract_text_from_pdf(path: Path) -> str:
    """
    Optional PDF support. Requires `pip install pypdf`.
    Kept separate and lazily imported so the plain-text path has zero
    extra dependencies.
    """
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def load_resume_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return extract_text_from_pdf(path)
    return path.read_text(encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python main.py <path-to-resume.txt-or-.pdf>")
        sys.exit(1)

    resume_path = Path(sys.argv[1])
    if not resume_path.exists():
        print(f"File not found: {resume_path}")
        sys.exit(1)

    print(f"Reading resume: {resume_path}")
    resume_text = load_resume_text(resume_path)

    print("Parsing with Claude (Structured Outputs)...")
    parsed = parse_resume(resume_text)

    result_json = parsed.model_dump_json(indent=2)
    print("\n--- Parsed Resume ---")
    print(result_json)

    out_path = resume_path.with_suffix(".json")
    out_path.write_text(result_json, encoding="utf-8")
    print(f"\nSaved to: {out_path}")


if __name__ == "__main__":
    main()
