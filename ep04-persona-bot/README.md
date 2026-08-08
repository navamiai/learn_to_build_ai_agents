# Episode 4 — Persona-Driven Q&A Bot

A framework-free AI agent that demonstrates the core ideas from Phase 1 of the
AI Agent Engineer series: the agent loop, temperature, token counting, system
prompts, few-shot examples, and chain-of-thought prompting — all in one file.

## What's in here

- **`persona_bot.py`** — the whole agent. One file, no framework.
- **`requirements.txt`** — `openai`, `anthropic`, `tiktoken`, `python-dotenv`.
- **`.env.example`** — copy to `.env` and add your API key.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# edit .env and add OPENAI_API_KEY or ANTHROPIC_API_KEY
```

## Run it

```bash
# Try it with no API key at all — proves the loop and prompt work first
python persona_bot.py --dry-run

# Focused, consistent answers (temperature 0)
python persona_bot.py --provider anthropic --temperature 0

# Looser, more exploratory answers (temperature 0.9)
python persona_bot.py --provider anthropic --temperature 0.9

# Turn on chain-of-thought for multi-step / trick questions
python persona_bot.py --provider anthropic --temperature 0 --cot
```

Swap `--provider anthropic` for `--provider openai` to use GPT models instead —
the agent loop and persona are identical either way, which is the whole point
of Episode 1's lesson: the loop doesn't care which model is on the other end.

## What each concept maps to in the code

| Episode | Concept | Where it lives |
|---|---|---|
| 1 | The agent loop | `run()` — perceive (`input()`) → think/act (`call_*`) → observe (`print`) → repeat |
| 2 | Temperature | `--temperature` flag, passed straight into the API call |
| 2 | Token counting | `count_tokens_openai()`, using `tiktoken` |
| 3 | System prompt / persona | `SYSTEM_PROMPT` — Kai's role, rules, and voice |
| 3 | Few-shot examples | The two `Q: / A:` pairs baked into `SYSTEM_PROMPT` |
| 3 | Chain-of-thought trigger | `COT_TRIGGER`, appended only when `--cot` is passed |

## Try this

1. Ask the same question at `--temperature 0` twice in a row, then at
   `--temperature 0.9` twice in a row. Compare how much the wording changes.
2. Ask a multi-step logic question with `--cot` off, then the exact same
   question with `--cot` on. Watch whether the answer changes.
3. Open `persona_bot.py` and rewrite `SYSTEM_PROMPT` with your own persona —
   notice how much the bot's "personality" shifts with zero changes to the
   loop itself.
