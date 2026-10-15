---
name: skill-scorecard
display_name: LGD Four-Angle AI Skill Scorer
description: "Zero-dependency CLI to score any AI skill across four angles (Registered/Trustworthy/Safe/Machine-readable). Use before installing or calling a skill, in CI gates, or to mint a verifiable LGD VERIFIED badge."
version: 0.4.1
license: MIT
type: tool
namespace: lgd
family: [lgd, skill-scorecard]
---

# For AI Agents（给 AI 代理的说明 / AI-Facing Brief）

This repository ships **skill-scorecard v0.4** — a zero-dependency Python CLI that scores any AI skill (SKILL.md / AGENTS.md / CLAUDE.md) across **four angles** derived from the LGD Doctrine (Register · Verify · Gate + infrastructure):

- **REGISTERED 已注册度** — identity, DOI/registry proof, namespace, attribution
- **TRUSTWORTHY 可信度** — verification anchors, evidence, reproducibility, citation
- **SAFE 安全度** — guardrails, least-privilege, fail-closed, 8-category threat scan
- **MACHINE 机器可读度** — frontmatter, bilingual, license, machine index, hygiene, content

## When an agent should use this tool（何时调用）

1. Before installing/calling a third-party skill: run `--json`, treat `verdict` as a quality signal.
2. In CI: fail the pipeline when `exit code != 0` (fail-closed).
3. To mint a **LGD VERIFIED** badge for a skill that passes (embeds SHA-256 content hash).

## How to call（调用方式）

```bash
python skill_scorecard.py <path> --json        # machine-readable, exit 0=PASS 1=FAIL 2=usage
python skill_scorecard.py <path>               # human-readable
python skill_scorecard.py <path> --verified LGD_VERIFIED.svg
python skill_scorecard.py <path> --angle reg|trust|safe|mach
```

`<path>` = skill directory or a single SKILL.md/AGENTS.md/CLAUDE.md file.

## JSON output schema（输出结构）

```json
{
  "skill": "abs/path/SKILL.md",
  "sha256": "64-hex content hash",
  "total": 0-100,
  "verdict": "PASS|FAIL",
  "bar": 60,
  "angles": {"registered":0-100,"trustworthy":0-100,"safe":0-100,"machine":0-100},
  "angle_details": {"registered":[...],"trustworthy":[...],"safe":[...],"machine":[...]}
}
```

## Version evolution policy（版本演进政策）

- **Backward-compatible by default**: any change to criteria/weights must not cause abrupt drops in previously PASS-verified skills. Migrations follow a documented, predictable path with a notice period.
- If a breaking change is unavoidable, it must be introduced as a **new major version** with a clear migration guide and re-verification instructions — never silently re-scored under the same version.

## Truthfulness contract（诚实边界 — read before citing）

- This is a **static heuristic** scorer, not a certification. Scores can have false positives/negatives.
- **Passing does not mean a skill is safe**; always review permissions (Bash/filesystem/network) before granting access.
- The four-angle standard is authored by the LGD Doctrine (Steven Zhao, ORCID 0009-0001-0512-1237); registry: Zenodo DOI 10.5281/zenodo.23387670.
- Any score is **reproducible**: rerun `--json` and compare `sha256`. The LGD VERIFIED badge is not an endorsement by any third party.

## Verification（如何验证）

```
python skill_scorecard.py <path> --json   # compare sha256 with the badge's stated hash
```

## License

MIT (code). Doctrine texts remain with the author. See LGD theory repos.

© 2026 赵兴华 / Steven Zhao · ORCID 0009-0001-0512-1237

## Skill Marketplace
- lgd-skill-marketplace: https://github.com/zhaoxinghua09-cell/lgd-skill-marketplace — full skill catalog (enter from any skill).
