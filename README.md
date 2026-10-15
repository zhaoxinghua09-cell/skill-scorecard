# skill-scorecard · LGD Four-Angle AI Skill Scoring

> One command, zero dependencies — score any AI skill across four angles: **Registered AI · Trustworthy AI · Safe AI · Machine-Readable**.
> 一条命令、零依赖——从四个角度给任意 AI 技能成体系评分：**已注册 · 可信 · 安全 · 机器可读**。

[![LGD](docs/badges/LGD.svg)](https://github.com/zhaoxinghua09-cell/skill-scorecard)
[![REG](docs/badges/REG.svg)](https://github.com/zhaoxinghua09-cell/skill-scorecard)
[![TRUST](docs/badges/TRUST.svg)](https://github.com/zhaoxinghua09-cell/skill-scorecard)
[![SAFE](docs/badges/SAFE.svg)](https://github.com/zhaoxinghua09-cell/skill-scorecard)
[![MACH](docs/badges/MACH.svg)](https://github.com/zhaoxinghua09-cell/skill-scorecard)

## Why / 为什么

The AI skill ecosystem is exploding — and most skills are untested, unregistered, and ungoverned. `skill-scorecard` turns the **LGD Doctrine** (Register · Verify · Gate) into an executable scoring system, so any skill can be rated on a four-angle system rather than a single ad-hoc dimension.

AI 技能生态正在爆发——大多数技能未经测试、未经注册、缺乏治理。`skill-scorecard` 把 **LGD 全程治理论**（有籍 Register · 有证 Verify · 有门禁 Gate）变成可执行的评分体系，让任何技能都能按四个角度成体系评分，而不是单维度临时打分。

## The four angles / 四角度

| Angle 角度 | Law 对应律 | What it scores 打分内容 |
|---|---|---|
| **REGISTERED** 已注册度 | Register 有籍 | identity, DOI/registry proof, namespace, attribution 身份标识、注册存证、命名规范、责任署名 |
| **TRUSTWORTHY** 可信度 | Verify 有证 | verification anchors, evidence, reproducibility, citation 验证锚点、证据链、可复现性、引用溯源 |
| **SAFE** 安全度 | Gate 有门禁 | guardrails, least-privilege, fail-closed, 8-category threat scan 行为护栏、权限最小化、fail-closed、8 类威胁模式扫描 |
| **MACHINE** 机器可读度 | Infrastructure 基础设施 | frontmatter, bilingual, license, machine-readable index, hygiene, content 元数据、双语、许可、机器索引、措辞卫生、内容 |

Total = weighted mean of the four angles. **PASS ≥ 60**, fail-closed exit code for CI.
总评 = 四角度加权平均。**PASS ≥ 60**，CI 故障闭合退出码。

Threat scan covers: prompt injection, hardcoded secrets, destructive commands, data exfiltration, crypto mining, privilege escalation, persistence, obfuscation.
威胁扫描覆盖：提示注入、硬编码密钥、破坏性命令、数据外泄、挖矿、提权、持久化、混淆。

## Usage / 用法

```bash
# score a skill directory or a single SKILL.md/AGENTS.md/CLAUDE.md
# 给技能目录或单个技能文件评分
python skill_scorecard.py path/to/skill

# one angle only / 只看某个角度
python skill_scorecard.py path/to/skill --angle reg|trust|safe|mach

# main badge + angle badges / 主徽章 + 角度徽章组
python skill_scorecard.py path/to/skill --badge lgd.svg
python skill_scorecard.py path/to/skill --badges-dir badges/

# machine-readable JSON / 机器可读 JSON
python skill_scorecard.py path/to/skill --json
```

### CI gate / CI 门禁

```yaml
- run: python skill_scorecard.py . || exit 1   # fail-closed
```

## Dogfooding / 自用实证

- **18 repositories** already carry LGD badges (17 terminology repos + lgd-guardrails).
  **18 个仓库**已挂载 LGD 徽章（17 术语仓 + lgd-guardrails）。
- Self-audit story: **34 → 76/90** after fixing machine-readable gaps — the scorer is honest, and the fixes are real.
  自评改进故事：**34 → 76/90** 分（修复机器可读缺口后）——评分器不徇私，改进是真实的。

## LGD VERIFIED badge / 认证徽章

Pass a skill and mint your own verifiable **LGD VERIFIED** badge — it embeds a SHA-256 content hash; static audit, **NOT a certification or endorsement**:
技能达标即可生成可验证的 **LGD VERIFIED** 认证徽章——内含 SHA-256 内容哈希；静态评测，**非官方认证、非背书**：

```bash
python skill_scorecard.py path/to/skill --verified LGD_VERIFIED.svg
```

High scorers may display the badge in their README. Anyone can verify: rerun `--json` and compare `sha256`.
高分技能可自行在 README 中展示徽章。任何人均可验证：重跑 `--json` 比对 `sha256`。

## License / 许可

MIT (code) · Theory texts (LGD Doctrine) remain with the author. See LGD theory repos for the doctrine.
MIT（代码）· 理论文本（LGD 全程治理论）版权归作者所有，理论详见 LGD 理论仓。

© 2026 赵兴华 / Steven Zhao · ORCID 0009-0001-0512-1237
