# 🧠 RLM Plugin for Hermes Agent

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey)](.)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)
[![Hermes](https://img.shields.io/badge/Hermes-Agent-orange)](https://hermes-agent.nousresearch.com)

**Recursive Language Model** — deep recursive analysis instead of shallow RAG search.

---

## TL;DR

- **RLM vs RAG:** модель сама решает что читать, а не получает готовые куски от векторной БД
- **Любой OpenAI-совместимый API:** OpenAI, OpenRouter, Ollama, vLLM — что угодно
- **Кроссплатформенно:** Linux, macOS, Windows — один скрипт `python3 install.py`
- **Хранится в `~/.hermes/rlm/`:** постоянно, не чистится системой, переживает ребуты
- **Инструмент `rlm_complete`:** агент вызывает когда нужен глубокий анализ
- **Для:** больших документов, сравнения файлов, задач где нельзя ошибиться
- **Не для:** коротких файлов, простых фактов, механических задач

---

## What it does

| | RAG | RLM |
|---|---|---|
| **Who searches** | Vector DB (dumb) | The model itself (smart) |
| **How** | Embedding similarity | Document structure |
| **Completeness** | Top-K chunks — can miss critical info | Can read **everything** |
| **Complex tasks** | Fails on comparison, cross-analysis | Handles naturally |

RLM works like a human researcher: open document → scan structure → find relevant sections → compare → synthesize. The model decides what to read, in what order, where to go back, what to cross-check.

```
┌─────────────────────────────────────────────────┐
│                    RLM FLOW                      │
│                                                  │
│  User: "Compare liability clauses in 3 contracts"│
│                                                  │
│  RLM:                                           │
│    ├─ Read contract A → find "Responsibility"   │
│    ├─ Read contract B → find "Liability"         │
│    ├─ Read contract C → find "Penalties"         │
│    ├─ Cross-reference all three                  │
│    └─ Synthesize: "A has X, B has Y, C has Z"   │
│                                                  │
│  RAG would:                                      │
│    └─ Search "liability" → return chunks → miss  │
│       "penalties" section entirely               │
└─────────────────────────────────────────────────┘
```

**Use for:**
- Analyzing large documents (500+ lines)
- Comparing multiple files/contracts/specs
- Tasks where "missing one piece = disaster"
- Deep research with cross-references

**Don't use for:**
- Short files (<200 lines) — regular `read_file` is faster
- Simple facts — `web_search` is faster
- Mechanical tasks (git, deploy) — `terminal` is faster

---

## Quick Install

**Linux / macOS / Windows — one command:**

```bash
python3 install.py
```

Or directly from GitHub:

```bash
# Linux / macOS
curl -O https://raw.githubusercontent.com/defdis/rlm-hermes-plugin/main/install.py
python3 install.py

# Windows (PowerShell)
Invoke-WebRequest -Uri https://raw.githubusercontent.com/defdis/rlm-hermes-plugin/main/install.py -OutFile install.py
python install.py
```

The installer will:
1. Check Python 3.11+, git, and Hermes
2. Ask for your API credentials (any OpenAI-compatible endpoint)
3. Clone and install the RLM library
4. Create the Hermes plugin
5. Restart Hermes

**Cross-platform:** works on Linux, macOS, and Windows. No bash required.

---

## Requirements

- **Hermes Agent** (any version with plugin support)
- **Python 3.11+**
- **git**
- **Any OpenAI-compatible API** — OpenAI, OpenRouter, Ollama, vLLM, local models, etc.
- API key with sufficient token budget (RLM makes multiple iterations)

---

## Supported API Providers

| Provider | Base URL |
|---|---|
| OpenAI | `https://api.openai.com/v1` |
| OpenRouter | `https://openrouter.ai/api/v1` |
| Ollama (local) | `http://localhost:11434/v1` |
| vLLM | `http://your-server:8000/v1` |
| Any OpenAI-compatible | your endpoint |

---

## Manual Install

### 1. Install RLM library

```bash
# Linux / macOS
mkdir -p ~/.hermes/rlm
git clone https://github.com/alexzhang13/rlm.git ~/.hermes/rlm/repo
python3.12 -m venv ~/.hermes/rlm/.venv
~/.hermes/rlm/.venv/bin/pip install -e ~/.hermes/rlm/repo

# Windows
mkdir %USERPROFILE%\.hermes\rlm
git clone https://github.com/alexzhang13/rlm.git %USERPROFILE%\.hermes\rlm\repo
python -m venv %USERPROFILE%\.hermes\rlm\.venv
%USERPROFILE%\.hermes\rlm\.venv\Scripts\pip install -e %USERPROFILE%\.hermes\rlm\repo
```

### 2. Configure environment

Add to `~/.hermes/.env`:

```bash
RLM_OPENAI_BASE_URL=https://your-api-endpoint/v1
RLM_OPENAI_API_KEY=your_api_key_here
```

### 3. Create plugin

```bash
mkdir -p ~/.hermes/plugins/rlm
cp plugin/__init__.py ~/.hermes/plugins/rlm/__init__.py
```

### 4. Restart Hermes

```bash
hermes-ctl restart YOUR_USERNAME
```

---

## Verify

Ask your agent: **"Compare RAG and RLM in 3 bullet points."**

If it responds meaningfully — it works.

---

## How it works

The plugin registers a `rlm_complete` tool in Hermes. When called:

1. Hermes agent passes the task to RLM
2. RLM spawns a Python REPL environment
3. The model recursively explores: reads, asks sub-questions, cross-references
4. Returns a synthesized answer

---

## Notes

- RLM in local mode cannot read files directly — pass content in the prompt
- Each iteration consumes tokens — use regular tools for simple tasks
- `model_name` in `backend_kwargs` is required
- `result.response` (not `.answer`) contains the final answer
- Works with any OpenAI-compatible endpoint

---

## Uninstall

```bash
# Linux / macOS
rm -rf ~/.hermes/plugins/rlm/ ~/.hermes/rlm/

# Windows
rmdir /s %USERPROFILE%\.hermes\plugins\rlm
rmdir /s %USERPROFILE%\.hermes\rlm

# Remove RLM_OPENAI_* lines from ~/.hermes/.env
hermes-ctl restart YOUR_USERNAME
```

---

## Credits

- **RLM library:** [alexzhang13/rlm](https://github.com/alexzhang13/rlm) — Alex Zhang, Tim Kraska, Omar Khattab (MIT)
- **Hermes Agent:** [Nous Research](https://hermes-agent.nousresearch.com)
- **Plugin author:** [defdis](https://github.com/defdis)
