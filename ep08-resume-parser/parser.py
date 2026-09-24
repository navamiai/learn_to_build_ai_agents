"""
Core parsing logic — where Episodes 5, 6, and 7 actually come together.

Episode 5: the API call itself is wrapped in retry logic with exponential
backoff, because rate limits (HTTP 429) and transient network errors are
never a matter of "if", only "when".

Episode 6: we don't ask the model to "please return JSON" and hope. We pass
our Pydantic model straight in as `output_format` to Claude's native
Structured Outputs (`client.messages.parse`), and if the response somehow
still fails validation, we retry ONCE with the exact Pydantic error fed back
to the model — not a vague "try again".

Episode 7: the system prompt (system_prompt.py) is the identity that has to
survive contact with an adversarial resume. This file just calls it — it
doesn't duplicate any of that logic here.
"""

import os
import random
import time

import anthropic
from pydantic import ValidationError

from schemas import ParsedResume
from system_prompt import RESUME_PARSER_SYSTEM_PROMPT

MODEL = "claude-opus-5"
MAX_API_RETRIES = 4          # Episode 5: rate limits / transient errors
MAX_VALIDATION_RETRIES = 2   # Episode 6: schema-correction retries


def _call_with_backoff(client: anthropic.Anthropic, **kwargs):
    """
    Episode 5's exponential backoff pattern, spelled out by hand so you can
    see exactly what the SDK is doing for you automatically most of the time.
    """
    for attempt in range(MAX_API_RETRIES):
        try:
            return client.messages.parse(**kwargs)
        except anthropic.RateLimitError:
            if attempt == MAX_API_RETRIES - 1:
                raise
            wait = (2 ** attempt) + random.uniform(0, 1)  # backoff + jitter
            print(f"[rate limited] retrying in {wait:.1f}s...")
            time.sleep(wait)
        except anthropic.APIConnectionError:
            if attempt == MAX_API_RETRIES - 1:
                raise
            wait = (2 ** attempt) + random.uniform(0, 1)
            print(f"[connection error] retrying in {wait:.1f}s...")
            time.sleep(wait)


def parse_resume(resume_text: str) -> ParsedResume:
    """
    Send raw resume text to Claude and get back a validated ParsedResume.

    Raises RuntimeError if the model still can't produce a valid schema
    after MAX_VALIDATION_RETRIES corrective retries — we fail loudly here,
    on purpose (see Episode 6, Scene 7: never fail silently into a broken
    record).
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    messages = [
        {
            "role": "user",
            "content": f"<resume>\n{resume_text}\n</resume>",
        }
    ]

    last_error: Exception | None = None

    for attempt in range(MAX_VALIDATION_RETRIES + 1):
        response = _call_with_backoff(
            client,
            model=MODEL,
            max_tokens=2048,
            system=RESUME_PARSER_SYSTEM_PROMPT,
            messages=messages,
            output_format=ParsedResume,
        )

        try:
            # response.parsed_output is already a validated ParsedResume
            # instance when client.messages.parse succeeds — this explicit
            # re-validation is a defensive belt-and-suspenders step for the
            # rare case a provider/model path hands back a raw dict instead.
            parsed = response.parsed_output
            if not isinstance(parsed, ParsedResume):
                parsed = ParsedResume.model_validate(parsed)
            return parsed

        except ValidationError as e:
            last_error = e
            if attempt == MAX_VALIDATION_RETRIES:
                break

            print(f"[schema mismatch] attempt {attempt + 1}, retrying with correction...")
            # Feed the EXACT validation error back — this is the difference
            # between "try again" and "here's precisely what to fix".
            messages.append({"role": "assistant", "content": str(response.content)})
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Your last response did not match the required schema. "
                        f"Validation error:\n{e}\n\n"
                        "Please re-extract the resume and return output that "
                        "matches the schema exactly."
                    ),
                }
            )

    raise RuntimeError(
        f"Failed to get a schema-valid resume after "
        f"{MAX_VALIDATION_RETRIES + 1} attempts. Last error: {last_error}"
    )
