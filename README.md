# skill-scorecard

## One command. Zero dependencies. Grade any AI skill.

**一条命令、零依赖，给任意 AI 技能打分。**

```bash
python skill_scorecard.py /path/to/skill
# or point it at a single SKILL.md / AGENTS.md
```

Scores an AI skill (SKILL.md / agent skill directory) against a machine-readable quality bar derived from the Lifecycle Governance Doctrine (LGD) — Register · Verify · Gate. Think **OpenSSF Scorecard, but for AI skills**.

为 AI 技能（SKILL.md / agent 技能目录）按机器可读质量标尺打分，标尺源自全程治理论（LGD）三律——有籍·有证·有门禁。相当于 **AI 技能界的 OpenSSF Scorecard**。

## Why（为什么）

- 2026 年最大的抱怨之一：**"CI passes, but teams still cannot prove the agent actually worked."** 技能生态正在爆发（Anthropic Agent Skills、1000+ 技能清单、技能包管理器），但**没有质量门**——谁都能发布一个 SKILL.md，没人能判断它可信不可信。
- 2026 年最大的抱怨之一："CI 通过了，但团队无法证明 agent 真的干了活。"技能生态正在爆发，但缺少质量门——谁都能发技能，没人能判断它是否可信。
- skill-scorecard 给这个混沌加上一条可复现的机器标尺：**一条命令，7 个维度，0-100 分，fail-closed 退出码**（<60 直接 FAIL），可接入 CI。

## Scoring dimensions（评分维度，满分 100）

| # | Dimension | Weight | What it checks |
|---|---|---|---|
| 1 | Registration（有籍） | 20 | frontmatter completeness: name/description/license/version |
| 2 | Bilingual（双语） | 15 | EN + ZH content both present |
| 3 | License（许可） | 15 | LICENSE file + SPDX-recognizable frontmatter |
| 4 | Machine-readable（机器可读） | 15 | AGENTS.md / llms.txt / `.well-known/agent-skills/index.json` |
| 5 | Hygiene（措辞卫生） | 10 | no placeholder / priority-claim wording |
| 6 | Content（内容质量） | 15 | description depth + section structure |
| 7 | Verification（可验证性） | 10 | verification & evidence anchors present (Verify) |

| # | 维度 | 权重 | 检查项 |
|---|---|---|---|
| 1 | 有籍（注册） | 20 | frontmatter 完整：name/description/license/version |
| 2 | 双语 | 15 | 中英文内容均存在 |
| 3 | 许可 | 15 | LICENSE 文件 + frontmatter SPDX 可识别 |
| 4 | 机器可读 | 15 | AGENTS.md / llms.txt / `.well-known/agent-skills/index.json` |
| 5 | 措辞卫生 | 10 | 无占位/优先权宣称类措辞 |
| 6 | 内容质量 | 15 | 描述深度 + 结构完整 |
| 7 | 可验证性 | 10 | 含验证与证据锚点（有证） |

**Verdict**: `PASS` ≥ 60 / `FAIL` < 60 — exit code 0/1, CI-friendly, fail-closed by default.

**判定**：≥60 PASS（退出码 0）、<60 FAIL（退出码 1）——CI 友好，默认故障闭合。

## Example（示例）

```bash
$ python skill_scorecard.py ./my-skill
{
  "skill": ".../my-skill/AGENTS.md",
  "total": 80,
  "verdict": "PASS",
  "scores": { "registration": 20, "bilingual": 15, "license": 5, ... }
}
VERDICT: PASS (80/100)
```

A `placeholder`-laden skill scores ~7/100 and exits 1. 一个带占位措辞的技能约 7/100 分并以退出码 1 结束。

## Badge（评分徽章）

Generate a self-contained SVG badge and drop it in your README — the score becomes visible at a glance.

生成自包含 SVG 徽章放进 README——分数一眼可见。

```bash
python skill_scorecard.py ./my-skill --badge badge.svg
# then embed:  <img src="badge.svg" alt="skill score">
```

![skill score badge example](docs/example-badge.svg)

## GitHub Action（CI 集成）

Add `.github/workflows/scorecard.yml` (copy from this repo) — any SKILL.md/AGENTS.md scoring below 60 fails the build (**fail-closed**).

把 `.github/workflows/scorecard.yml` 复制进你的仓库（本仓自带）——任何低于 60 分的技能文件都会让构建失败（**故障闭合**）。

```yaml
# .github/workflows/scorecard.yml  (see this repo for full copy)
name: skill-scorecard
on: [push, pull_request]
jobs:
  score:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: python -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/zhaoxinghua09-cell/skill-scorecard/main/skill_scorecard.py','skill_scorecard.py')"
      - run: python skill_scorecard.py .   # <60 fails the build
```

## Roadmap（路线）

- [x] v0.1 — core scoring, 7 dimensions, JSON output, fail-closed exit codes
- [x] v0.3 — **SVG badge generation (`--badge`) + GitHub Action workflow**
- [ ] v0.2 — recursive scan of a skill directory tree; aggregate report
- [ ] v0.4 — plugin rules (custom dimension weights)

## License

Apache-2.0. Theory text carries its own attribution per LGD.
Apache-2.0；理论文本按 LGD 署名声明。

---

*Lifecycle Governance Doctrine (LGD) · SynomosAI initiative · Register · Verify · Gate.*
