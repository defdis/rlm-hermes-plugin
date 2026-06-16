"""
RLM Plugin for Hermes — Recursive Language Model.

Provides rlm_complete: recursive task solving where the model
reads files, explores sub-questions, and cross-references on its own.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def _get_rlm_paths():
    """Resolve RLM venv and repo paths from Hermes home."""
    hermes_home = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
    rlm_dir = hermes_home / "rlm"
    rlm_venv = rlm_dir / ".venv"
    rlm_repo = rlm_dir / "repo"

    # Python executable (cross-platform)
    if os.name == "nt":
        rlm_python = rlm_venv / "Scripts" / "python.exe"
    else:
        rlm_python = rlm_venv / "bin" / "python"

    return rlm_venv, rlm_repo, str(rlm_python)


RLM_VENV, RLM_REPO, RLM_PYTHON = _get_rlm_paths()


def _call_rlm(prompt: str, root_prompt: str | None = None, model: str = "deepseek-v4-pro", max_iterations: int = 10, timeout: int = 180) -> dict:
    """Call RLM completion via subprocess."""
    base_url = os.environ.get("RLM_OPENAI_BASE_URL", "")
    api_key = os.environ.get("RLM_OPENAI_API_KEY", "")

    if not base_url or not api_key:
        return {"success": False, "error": "RLM_OPENAI_BASE_URL and RLM_OPENAI_API_KEY must be set"}

    # Escape prompt for safe embedding in Python string
    prompt_escaped = prompt.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    root_escaped = (root_prompt or "").replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")

    script = f'''
import json, sys
sys.path.insert(0, "{RLM_REPO}")
from rlm import RLM

rlm = RLM(
    backend="openai",
    backend_kwargs={{"base_url": "{base_url}", "api_key": "{api_key}", "model_name": "{model}"}},
    max_iterations={max_iterations},
    max_timeout={timeout},
    verbose=False,
)

result = rlm.completion(
    prompt="{prompt_escaped}",
    root_prompt="{root_escaped}" if "{root_escaped}" else None,
)
# result is RLMChatCompletion — extract response
answer = result.response if hasattr(result, "response") else str(result)
print(json.dumps({{"answer": answer}}, ensure_ascii=False))
'''

    try:
        proc = subprocess.run(
            [RLM_PYTHON, "-c", script],
            capture_output=True, text=True, timeout=timeout + 30,
            env={**os.environ, "PYTHONPATH": str(RLM_REPO)},
        )
        if proc.returncode != 0:
            return {"success": False, "error": proc.stderr.strip() or "RLM failed"}
        return {"success": True, "result": json.loads(proc.stdout.strip())}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"RLM timed out after {timeout}s"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def register(ctx):
    ctx.register_tool(
        name="rlm_complete",
        toolset="rlm",
        schema={
            "name": "rlm_complete",
            "description": "Solve a complex task using Recursive Language Model. Unlike RAG (which returns top-K chunks), RLM recursively explores the problem: reads files, spawns sub-questions, cross-references, and synthesizes a complete answer. Use for: analyzing large documents, comparing multiple files, complex research questions, legal/contract analysis, or any task where missing one piece would change the answer. The prompt should describe the task and mention any file paths to read.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Full task description. Include file paths to read, questions to answer, comparison dimensions. E.g. 'Read /path/to/contract.pdf and extract all liability clauses. Compare them with standard Russian civil code requirements.'"
                    },
                    "root_prompt": {
                        "type": "string",
                        "description": "Optional short question that the root LM sees directly. E.g. 'What are the key liability differences?'"
                    },
                    "model": {
                        "type": "string",
                        "description": "Model for RLM. Default: deepseek-v4-pro.",
                        "default": "deepseek-v4-pro"
                    },
                    "max_iterations": {
                        "type": "integer",
                        "description": "Max recursive iterations. Higher = deeper analysis but slower. Default 10.",
                        "default": 10
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Max seconds. Default 180.",
                        "default": 180
                    }
                },
                "required": ["prompt"]
            },
        },
        handler=lambda params, **kw: json.dumps(_call_rlm(
            prompt=params.get("prompt"),
            root_prompt=params.get("root_prompt"),
            model=params.get("model", "deepseek-v4-pro"),
            max_iterations=params.get("max_iterations", 10),
            timeout=params.get("timeout", 180),
        )),
        description="Recursive task solving — reads files, spawns sub-questions, cross-references. For complex analysis where completeness matters.",
    )

    def on_tool_call(**kwargs):
        tool_name = kwargs.get("tool_name", "")
        if tool_name == "rlm_complete":
            print(f"[rlm] rlm_complete called", file=sys.stderr)

    ctx.register_hook("post_tool_call", on_tool_call)
