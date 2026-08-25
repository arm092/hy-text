# Տեղադրում

Ստորև հրամանները տեղադրում են `v1.0.0` կայուն տարբերակը։

## Տեղադրման ստուգման սահմանը

Թողարկման smoke ստուգումը վեց առանձին փաթեթային դասավորություն է տեղադրում մեկուսացված ժամանակավոր պանակներում՝ Agent Skills, Claude, Codex, Cursor, Gemini և OpenClaw։ Այն կարդում է տեղադրված մանիֆեստները, ստուգում հմտությունների ու պատկերների ուղիները և մերժում բացակայող կամ փաթեթի արմատից դուրս եկող հղումները։ Ստուգումը երբեք չի գրում օգտատիրոջ իրական պրոֆիլում։

```bash
python tools/smoke_install.py --root . --temp-root . --output install-smoke.json
```

`--temp-root`-ը պարտադիր է․ հրամանում բացահայտ ընտրված է պահոցի պանակը։ Ստուգիչը դրա ներսում ստեղծում է եզակի ժամանակավոր ենթապանակ և ավարտվելիս ամբողջությամբ հեռացնում է այն։ Այլ տեղադրություն ընտրելու համար փոխանցեք գոյություն ունեցող, ձեզ պատկանող ժամանակավոր պանակի ուղին։ Որևէ օգտատիրոջ պրոֆիլ լռելյայն չի ընտրվում։

Այս արդյունքը հաստատում է փաթեթի հերմետիկ տեղադրումը։ Տեղական Claude, Codex, Cursor, Gemini կամ OpenClaw գործարկիչի առկայությունը գրանցվում է առանձին `live_cli` դաշտում։ `unavailable` արժեքը նշանակում է միայն, որ տվյալ գործարկիչը մեքենայում հասանելի չէ, ոչ թե որ իրական տեղադրումը կեղծ հաջողությամբ է փոխարինվել։

## Agent Skills համատեղելի գործակալներ

Codex CLI-ի, Cursor-ի, Windsurf-ի, GitHub Copilot-ի և համատեղելի այլ գործակալների համար՝

```bash
npx skills add "arm092/hy-text#v1.0.0"
```

Կամ ձեռքով պատճենեք `skills/hy-text`, `skills/hy-check` և `skills/hy-score` պանակները օգտատիրոջ `~/.agents/skills/` պանակ։ Նոր հմտությունները բեռնվում են նոր նստաշրջանում։

Windows PowerShell՝

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

## Cursor և OpenClaw

Պահոցը պարունակում է `.cursor-plugin/plugin.json` և `openclaw.plugin.json` մանիֆեստները։ Դրանց փաթեթային դասավորությունը անցնում է վերևում նկարագրված հերմետիկ ստուգումը։ Սա չի պնդում, որ տվյալ մեքենայում հարթակի ընտրովի CLI-ն տեղադրված է։ Եթե հարթակի տեղադրիչը դեռ չի ընդունում GitHub հասցեն, օգտագործեք վերևի Agent Skills պատճենումը։

[English](INSTALL.en.md)
