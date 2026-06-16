#!/usr/bin/env python3
"""
RLM Plugin Installer for Hermes Agent
Cross-platform: Linux, macOS, Windows
Requires: Python 3.11+, git, Hermes Agent installed
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path


# ─── Colors (Windows-safe) ───────────────────────────────────────────────────
def green(s):  return f"\033[0;32m{s}\033[0m" if os.name != "nt" else s
def red(s):    return f"\033[0;31m{s}\033[0m" if os.name != "nt" else s
def yellow(s): return f"\033[1;33m{s}\033[0m" if os.name != "nt" else s
def cyan(s):   return f"\033[0;36m{s}\033[0m" if os.name != "nt" else s


def banner():
    print()
    print(cyan("╔══════════════════════════════════════════════════════════╗"))
    print(cyan("║     RLM Plugin Installer for Hermes Agent                ║"))
    print(cyan("║     Recursive Language Model — deep analysis             ║"))
    print(cyan("╚══════════════════════════════════════════════════════════╝"))
    print()


def find_python():
    """Find Python 3.11+ on any OS."""
    for name in ["python3.12", "python3.11", "python3.13", "python3", "python"]:
        exe = shutil.which(name)
        if exe:
            try:
                ver = subprocess.check_output(
                    [exe, "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
                    text=True, stderr=subprocess.DEVNULL
                ).strip()
                major, minor = map(int, ver.split("."))
                if major >= 3 and minor >= 11:
                    return exe
            except Exception:
                continue
    return None


def find_hermes_home():
    """Find Hermes home directory."""
    home = os.environ.get("HERMES_HOME", "")
    if home:
        return Path(home)

    # Default locations
    if os.name == "nt":  # Windows
        candidates = [
            Path(os.environ.get("USERPROFILE", "")) / ".hermes",
            Path(os.environ.get("HOMEDRIVE", "") + os.environ.get("HOMEPATH", "")) / ".hermes",
        ]
    else:  # Linux/macOS
        candidates = [
            Path.home() / ".hermes",
        ]

    for c in candidates:
        if (c / "config.yaml").exists():
            return c
    return None


def run(cmd, **kwargs):
    """Run a command, print output on failure."""
    try:
        return subprocess.run(cmd, check=True, capture_output=True, text=True, **kwargs)
    except subprocess.CalledProcessError as e:
        print(red(f"Command failed: {' '.join(cmd)}"))
        print(e.stderr)
        raise


def main():
    banner()

    # ─── Check Python ────────────────────────────────────────────────────────
    python = find_python()
    if not python:
        print(red("ERROR: Python 3.11+ required."))
        print("  Ubuntu/Debian: sudo apt install python3.12 python3.12-venv")
        print("  macOS:         brew install python@3.12")
        print("  Windows:       winget install Python.Python.3.12")
        sys.exit(1)
    print(green("✓") + f" Python: {python}")

    # ─── Check git ───────────────────────────────────────────────────────────
    if not shutil.which("git"):
        print(red("ERROR: git not found. Install git first."))
        print("  https://git-scm.com/downloads")
        sys.exit(1)
    print(green("✓") + " git found")

    # ─── Check Hermes ────────────────────────────────────────────────────────
    hermes_home = find_hermes_home()
    if not hermes_home:
        print(red("ERROR: Hermes Agent not found."))
        print("  Install: https://hermes-agent.nousresearch.com")
        sys.exit(1)
    print(green("✓") + f" Hermes: {hermes_home}")

    # ─── API Credentials ─────────────────────────────────────────────────────
    print()
    print(yellow("API Configuration"))
    print("RLM needs any OpenAI-compatible API endpoint.")
    print()
    print("Examples:")
    print("  OpenAI:      https://api.openai.com/v1")
    print("  OpenRouter:  https://openrouter.ai/api/v1")
    print("  Ollama:      http://localhost:11434/v1")
    print("  vLLM:        http://your-server:8000/v1")
    print()

    base_url = input("API Base URL: ").strip()
    api_key = input("API Key: ").strip()
    model = input("Model name [gpt-4o]: ").strip() or "gpt-4o"

    # ─── Install paths (inside Hermes home — survives reboots) ────────────────
    rlm_dir = hermes_home / "rlm"
    rlm_repo = rlm_dir / "repo"
    rlm_venv = rlm_dir / ".venv"

    # ─── Install RLM library ─────────────────────────────────────────────────
    print()
    print(cyan("Installing RLM library..."))

    if not rlm_repo.exists():
        run(["git", "clone", "https://github.com/alexzhang13/rlm.git", str(rlm_repo)])

    # Create venv
    run([python, "-m", "venv", str(rlm_venv)])

    # pip executable (cross-platform)
    if os.name == "nt":
        pip = str(rlm_venv / "Scripts" / "pip.exe")
    else:
        pip = str(rlm_venv / "bin" / "pip")

    run([pip, "install", "-q", "-e", str(rlm_repo)])
    print(green("✓") + " RLM library installed")

    # ─── Configure environment ───────────────────────────────────────────────
    print()
    print(cyan("Configuring environment..."))

    env_file = hermes_home / ".env"

    # Read existing, remove old RLM lines
    lines = []
    if env_file.exists():
        lines = [l for l in env_file.read_text().splitlines()
                 if not l.startswith("RLM_OPENAI_")]

    lines.append(f"RLM_OPENAI_BASE_URL={base_url}")
    lines.append(f"RLM_OPENAI_API_KEY={api_key}")
    env_file.write_text("\n".join(lines) + "\n")
    print(green("✓") + " Environment configured")

    # ─── Install plugin ──────────────────────────────────────────────────────
    print()
    print(cyan("Installing Hermes plugin..."))

    plugin_dir = hermes_home / "plugins" / "rlm"
    plugin_dir.mkdir(parents=True, exist_ok=True)

    # Find plugin source (next to this script)
    script_dir = Path(__file__).parent.resolve()
    plugin_src = script_dir / "plugin" / "__init__.py"

    if not plugin_src.exists():
        print(red("ERROR: plugin/__init__.py not found."))
        print("Run this script from the repo root directory.")
        sys.exit(1)

    shutil.copy(plugin_src, plugin_dir / "__init__.py")
    print(green("✓") + " Plugin installed")

    # ─── Restart Hermes ──────────────────────────────────────────────────────
    print()
    print(cyan("Restarting Hermes..."))

    hermes_ctl = shutil.which("hermes-ctl")
    if hermes_ctl:
        # Try to detect username
        config = hermes_home / "config.yaml"
        username = None
        if config.exists():
            for line in config.read_text().splitlines():
                if line.strip().startswith("name:"):
                    username = line.split(":", 1)[1].strip().strip('"').strip("'")
                    break
        if username:
            try:
                subprocess.run([hermes_ctl, "restart", username], timeout=30)
                print(green("✓") + " Hermes restarted")
            except Exception:
                print(yellow("⚠") + f" Restart manually: hermes-ctl restart {username}")
        else:
            print(yellow("⚠") + " Restart manually: hermes-ctl restart YOUR_USERNAME")
    else:
        print(yellow("⚠") + " hermes-ctl not found. Restart Hermes manually.")

    # ─── Done ────────────────────────────────────────────────────────────────
    print()
    print(green("╔══════════════════════════════════════════════════════════╗"))
    print(green("║     RLM Plugin installed successfully!                  ║"))
    print(green("╚══════════════════════════════════════════════════════════╝"))
    print()
    print("Verify: ask your Hermes agent 'Compare RAG and RLM in 3 bullet points'")
    print()
    print("Uninstall:")
    if os.name == "nt":
        print(f"  rmdir /s {plugin_dir}")
        print(f"  rmdir /s {rlm_venv.parent}")
        print(f"  rmdir /s {rlm_repo}")
    else:
        print(f"  rm -rf {plugin_dir} {rlm_venv.parent} {rlm_repo}")
    print(f"  # Remove RLM_OPENAI_* lines from {env_file}")
    print()


if __name__ == "__main__":
    main()
