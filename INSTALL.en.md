# Installation

> There is no stable release yet. These commands install the development version from `master`.

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

The repository includes `.cursor-plugin/plugin.json` and `openclaw.plugin.json`. Live installation smoke tests remain a required v1.0 gate. Use the Agent Skills copy path above if a platform installer does not yet accept the GitHub source.
