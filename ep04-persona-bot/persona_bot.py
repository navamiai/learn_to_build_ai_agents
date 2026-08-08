#!/usr/bin/env python3
"""
persona_bot.py
Episode 4 — "Build Your First AI Agent: A Persona-Driven Q&A Bot"

A minimal, framework-free AI agent that demonstrates:
  - Episode 1: The agent loop (input -> LLM call -> output -> repeat)
  - Episode 2: Temperature control + token counting with tiktoken
  - Episode 3: A persona system prompt, baked-in few-shot examples,
               and a chain-of-thought trigger phrase

Works with either OpenAI or Anthropic's API. Pick one with --provider,
or set PROVIDER in your .env file. Supports --dry-run so you can test
the whole loop before spending a single API credit.

Usage:
    python persona_bot.py --provider anthropic --temperature 0.9 --cot
    python persona_bot.py --provider openai --temperature 0 --dry-run
"""

import argparse
import os
import sys

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# THE PERSONA — this is the "soul" of the agent (Episode 3: system prompts)
# ---------------------------------------------------------------------------
PERSONA_NAME = "Kai"

SYSTEM_PROMPT = f"""You are {PERSONA_NAME}, a sharp, slightly sarcastic senior Python \
engineer. You've answered the same beginner questions hundreds of times, so you don't \
sugarcoat things — but you genuinely want the person you're talking to to actually \
understand the answer, not just copy-paste it.

Rules you always follow:
- Keep answers under 120 words unless the question truly needs more.
- If the question is ambiguous, ask ONE clarifying question instead of guessing.
- Never say "As an AI language model" or anything like it. You are {PERSONA_NAME}, full stop.
- Use a real code example whenever it helps, but keep it short.
- If you're not sure about something, say so directly instead of making it up.

Here are two examples of exactly how you respond:

Q: Why is my for loop only printing the last item in my list?
A: Classic. You're almost certainly printing outside the loop instead of inside it. \
Python doesn't care about your intentions, just your indentation. Check this:
```python
for item in my_list:
    print(item)   # inside the loop = correct
print(item)       # outside the loop = only the last value
```
Fix the indentation and you're done.

Q: What's the difference between a list and a tuple?
A: A list can change after you create it — add, remove, edit. A tuple can't; \
once it's made, it's locked. Use a list when the data will grow or shift. Use a \
tuple when it shouldn't — like coordinates, or a fixed record. That immutability \
is also what makes tuples hashable, so you can use them as dictionary keys. \
Lists, you can't.
"""

COT_TRIGGER = (
    "\n\nWhen a question involves multiple steps or could have a hidden trap, "
    "think through it step-by-step internally before giving your final answer. "
    "Show that reasoning briefly, then clearly state the final answer at the end."
)


def build_system_prompt(use_cot: bool) -> str:
    """Episode 3: toggling the chain-of-thought trigger phrase on/off."""
    return SYSTEM_PROMPT + COT_TRIGGER if use_cot else SYSTEM_PROMPT


def count_tokens_openai(text: str, model: str = "gpt-4o-mini") -> int:
    """Episode 2: token counting with tiktoken (OpenAI models).

    Falls back to -1 (skip) if tiktoken isn't installed, or if its encoding
    file can't be fetched (e.g. no network / first run behind a firewall).
    That failure should never take down the agent loop over a debug feature.
    """
    try:
        import tiktoken

        try:
            enc = tiktoken.encoding_for_model(model)
        except KeyError:
            enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return -1


# ---------------------------------------------------------------------------
# PROVIDER CALLS — the "Act" step of the agent loop
# ---------------------------------------------------------------------------
def call_openai(messages, temperature: float, model: str = "gpt-4o-mini") -> str:
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content


def call_anthropic(system: str, history, temperature: float, model: str = "claude-3-5-sonnet-latest") -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model=model,
        system=system,
        messages=history,
        max_tokens=500,
        temperature=temperature,
    )
    return response.content[0].text


def call_dry_run(user_input: str) -> str:
    """No API call at all — just proves the loop, the prompt assembly,
    and the CLI plumbing all work before you spend a single token."""
    return (
        f"[DRY RUN — no API call made]\n"
        f"{PERSONA_NAME} would now answer: \"{user_input}\"\n"
        f"System prompt length: {len(SYSTEM_PROMPT)} characters."
    )


# ---------------------------------------------------------------------------
# THE AGENT LOOP — Episode 1: perceive -> think -> act -> observe -> repeat
# ---------------------------------------------------------------------------
def run(provider: str, temperature: float, use_cot: bool, dry_run: bool) -> None:
    system_prompt = build_system_prompt(use_cot)

    print(f"\n{'=' * 60}")
    print(f"  {PERSONA_NAME} — Persona-Driven Q&A Bot")
    print(f"  provider={provider}  temperature={temperature}  cot={'on' if use_cot else 'off'}")
    print(f"{'=' * 60}")
    print("Type your question, or 'exit' to quit.\n")

    # For OpenAI: messages array includes the system role directly.
    # For Anthropic: system prompt is a separate top-level param,
    # so 'history' only holds user/assistant turns.
    openai_messages = [{"role": "system", "content": system_prompt}]
    anthropic_history = []

    while True:  # PERCEIVE
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSession ended.")
            break

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            print(f"{PERSONA_NAME}: See you next time.")
            break

        tokens_in = count_tokens_openai(system_prompt + user_input)
        if tokens_in != -1:
            print(f"[debug] prompt tokens (est.): {tokens_in}")

        try:  # THINK + ACT
            if dry_run:
                reply = call_dry_run(user_input)
            elif provider == "openai":
                openai_messages.append({"role": "user", "content": user_input})
                reply = call_openai(openai_messages, temperature)
                openai_messages.append({"role": "assistant", "content": reply})
            elif provider == "anthropic":
                anthropic_history.append({"role": "user", "content": user_input})
                reply = call_anthropic(system_prompt, anthropic_history, temperature)
                anthropic_history.append({"role": "assistant", "content": reply})
            else:
                raise ValueError(f"Unknown provider: {provider}")
        except KeyError as e:
            print(f"\n[error] Missing API key: {e}. Set it in your .env file, "
                  f"or run with --dry-run to test without one.\n")
            continue
        except Exception as e:
            print(f"\n[error] API call failed: {e}\n")
            continue

        print(f"\n{PERSONA_NAME}: {reply}\n")  # OBSERVE (and loop back to PERCEIVE)


def main():
    parser = argparse.ArgumentParser(description="Episode 4 — Persona-driven Q&A agent")
    parser.add_argument(
        "--provider",
        choices=["openai", "anthropic"],
        default=os.environ.get("PROVIDER", "anthropic"),
        help="Which API to call (default: value of PROVIDER in .env, or 'anthropic')",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="0 = focused and consistent, 1 = varied and exploratory (default: 0.7)",
    )
    parser.add_argument(
        "--cot",
        action="store_true",
        help="Turn on the chain-of-thought trigger phrase for multi-step questions",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test the loop and prompt assembly without calling any API",
    )
    args = parser.parse_args()

    if not args.dry_run and args.provider == "openai" and "OPENAI_API_KEY" not in os.environ:
        print("Missing OPENAI_API_KEY. Add it to your .env file or run with --dry-run.")
        sys.exit(1)
    if not args.dry_run and args.provider == "anthropic" and "ANTHROPIC_API_KEY" not in os.environ:
        print("Missing ANTHROPIC_API_KEY. Add it to your .env file or run with --dry-run.")
        sys.exit(1)

    run(args.provider, args.temperature, args.cot, args.dry_run)


if __name__ == "__main__":
    main()
