# Տեղադրում

> Նախագիծը դեռ կայուն թողարկում չունի։ Ստորև հրամանները տեղադրում են `master` ճյուղի զարգացման տարբերակը։

## Agent Skills համատեղելի գործակալներ

Codex CLI-ի, Cursor-ի, Windsurf-ի, GitHub Copilot-ի և համատեղելի այլ գործակալների համար՝

```bash
npx skills add arm092/hy-text
```

Կամ ձեռքով պատճենեք `skills/hy-text`, `skills/hy-check` և `skills/hy-score` պանակները օգտատիրոջ `~/.agents/skills/` պանակ։ Նոր հմտությունները բեռնվում են նոր նստաշրջանում։

Windows PowerShell՝

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

## Cursor և OpenClaw

Պահոցը պարունակում է `.cursor-plugin/plugin.json` և `openclaw.plugin.json` մանիֆեստները։ Մինչև `v1.0.0` դրանց իրական տեղադրման smoke ստուգումները բաց թողարկման պարտադիր դարպաս են։ Եթե հարթակի տեղադրիչը դեռ չի ընդունում GitHub հասցեն, օգտագործեք վերևի Agent Skills պատճենումը։

[English](INSTALL.en.md)
