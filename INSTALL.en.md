# Installation

The commands below install the stable `v1.0.0` release.

## Installation verification boundary

The release smoke check installs six separate package layouts in isolated temporary homes: Agent Skills, Claude, Codex, Cursor, Gemini, and OpenClaw. It parses the installed manifests, verifies skill and asset paths, and rejects missing references or paths that escape the package root. It never writes to the real user profile.

```bash
python tools/smoke_install.py --root . --temp-root . --output install-smoke.json
```

`--temp-root` is required; this command explicitly selects the repository directory. The checker creates a unique temporary child below it and removes that child completely when the run finishes. To use another location, pass an existing temporary directory that you control. No user-profile location is selected by default.

This result verifies hermetic package installation. Local Claude, Codex, Cursor, Gemini, and OpenClaw executable availability is recorded separately in the `live_cli` field. `unavailable` means only that the optional executable is not present on that machine; it is never reported as a fabricated live-install success.

## Agent Skills compatible agents

For Codex CLI, Cursor, Windsurf, GitHub Copilot, and other compatible agents:

```bash
npx skills add "arm092/hy-text#v1.0.0"
```

Alternatively, copy `skills/hy-text`, `skills/hy-check`, and `skills/hy-score` into the user-level `~/.agents/skills/` directory. Start a new session after installation.

Windows PowerShell:

```powershell
git clone --branch v1.0.0 --depth 1 https://github.com/arm092/hy-text.git
New-Item -ItemType Directory -Force "$env:USERPROFILE\.agents\skills" | Out-Null
Copy-Item -Recurse hy-text\skills\* "$env:USERPROFILE\.agents\skills"
```

## Claude Code

```text
/plugin marketplace add arm092/hy-text@v1.0.0
/plugin install hy-text@hy-text
```

## Gemini CLI

```bash
gemini extensions install https://github.com/arm092/hy-text --ref v1.0.0
```

## Cursor and OpenClaw

The repository includes `.cursor-plugin/plugin.json` and `openclaw.plugin.json`. Their package layouts pass the hermetic verification described above. This does not claim that an optional platform CLI is installed on the current machine. Use the Agent Skills copy path above if a platform installer does not yet accept the GitHub source.
