# AI Resume Parser — Episode 8 Project

An AI-powered resume parser that turns raw resume text into clean, validated
JSON — the same core architecture behind the AI parsing features in tools
like Greenhouse, Lever, and Workday.

This project combines the three concepts from Episodes 5, 6, and 7:

- **Episode 5 (API calls done right):** the Claude API call is wrapped in
  exponential-backoff retry logic for rate limits and transient errors —
  see `_call_with_backoff` in `parser.py`.
- **Episode 6 (Structured Outputs):** the output shape is a Pydantic model
  (`schemas.py`) passed straight into Claude's native Structured Outputs via
  `client.messages.parse(output_format=ParsedResume)`. If a response
  somehow still fails validation, we retry with the exact Pydantic error fed
  back to the model — not a vague "try again."
- **Episode 7 (System prompts & personas):** the parser's identity
  (`system_prompt.py`) is built to survive adversarial input — a resume that
  tries to prompt-inject its way to a fake "10/10 hire" verdict.

## What it extracts

For any resume (plain text or PDF), the parser returns:

- Name, email, LinkedIn
- Work experience (company, title, duration, bullet points)
- Skills, categorized into languages / frameworks / tools
- Education
- A strictly factual, 3-sentence candidate summary

## Project layout

```
ep08-resume-parser/
├── schemas.py              # Pydantic models (the output contract)
├── system_prompt.py        # The parser's persona + hard rules
├── parser.py                # API call + retry logic + validation retry
├── main.py                  # CLI entry point
├── requirements.txt
├── .env.example
└── samples/
    ├── clean_resume.txt         # A normal resume
    └── adversarial_resume.txt   # A resume that tries to prompt-inject the parser
```

## How to build it (setup)

1. Create a virtual environment and install dependencies:

   ```bash
   python -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and add your real Anthropic API key:

   ```bash
   cp .env.example .env
   ```

   Never commit `.env` — it should already be in your `.gitignore`.

## How to run it

```bash
python main.py samples/clean_resume.txt
python main.py samples/adversarial_resume.txt
```

Each run prints the parsed JSON to the terminal and saves it next to the
input file (e.g. `samples/clean_resume.json`).

Run the adversarial sample and check the `candidate_summary` field — it
should stay neutral and factual (junior developer, HTML/CSS, incomplete
coursework) instead of the fabricated "10/10, hire immediately, ex-Google
Senior Staff Engineer" the resume text tries to plant. That's the system
prompt from Episode 7 holding up under exactly the kind of pressure it was
designed for.

## Notes

- This project targets Claude's native Structured Outputs
  (`client.messages.parse`). The equivalent on OpenAI's side is
  `response_format` / Structured Outputs with a Pydantic model passed the
  same way — swap the client and the call shape stays conceptually
  identical.
- PDF support requires `pypdf` (already in `requirements.txt`). For scanned/
  image-only PDFs, you'd need OCR first — out of scope here.
