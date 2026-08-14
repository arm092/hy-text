# Installation

> There is no stable release yet. These commands install the development version from `master`.

## Installation verification boundary

The release smoke check installs six separate package layouts in isolated temporary homes: Agent Skills, Claude, Codex, Cursor, Gemini, and OpenClaw. It parses the installed manifests, verifies skill and asset paths, and rejects missing references or paths that escape the package root. It never writes to the real user profile.

```bash
python tools/smoke_install.py --root . --output install-smoke.json
```

This result verifies hermetic package installation. Local Claude, Codex, Cursor, Gemini, and OpenClaw executable availability is recorded separately in the `live_cli` field. `unavailable` means only that the optional executable is not present on that machine; it is never reported as a fabricated live-install success.

## Agent Skills compatible agents

For Codex CLI, Cursor, Windsurf, GitHub Copilot, and other compatible agents:

```bash
npx skills add arm092/hy-text
```

Alternatively, copy `skills/hy-text`, `skills/hy-check`, and `skills/hy-score` into the user-level `~/.agents/skills/` directory. Start a new session after installation.

Windows PowerShell:

```powershell
git clone https://github.com/arm092/hy-text.git
New-Item -ItemType Directory -Force "$env:USERPROFILE\.agents\skills" | Out-Null
Copy-Item -Recurse hy-text\skills\* "$env:USERPROFILE\.agents\skills"
```

## Claude Code

```text
/plugin marketplace add arm092/hy-text
/plugin install hy-text@hy-text
```

## Gemini CLI

```bash
gemini extensions install https://github.com/arm092/hy-text
```

## Cursor and OpenClaw

The repository includes `.cursor-plugin/plugin.json` and `openclaw.plugin.json`. Their package layouts pass the hermetic verification described above. This does not claim that an optional platform CLI is installed on the current machine. Use the Agent Skills copy path above if a platform installer does not yet accept the GitHub source.
