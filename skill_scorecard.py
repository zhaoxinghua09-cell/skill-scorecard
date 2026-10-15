#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
skill-scorecard — one command, zero dependencies: score any AI skill (SKILL.md / agent skill directory)
against the LGD machine-readability bar (Register · Verify · Gate).
Usage:
    python skill_scorecard.py <path-to-skill-or-SKILL.md>
Exit code: 0 = pass (>=60), 1 = fail (<60), 2 = error.
"""
import json, os, re, sys

WEIGHTS = {
    "registration": 20,   # frontmatter completeness (Register)
    "bilingual": 15,      # EN + ZH content
    "license": 15,        # LICENSE file + SPDX-recognizable
    "machine_readable": 15,  # AGENTS.md / llms.txt / .well-known index
    "hygiene": 10,        # banned placeholder wording
    "content": 15,        # description depth + structure
    "verification": 10,   # testable claims / verification section (Verify)
}
BANNED = ["placeholder", "占位", "priority claim", "placehold", "临时占"]

def locate_skill(path):
    """Resolve a path to (dir, skill_md)."""
    p = os.path.abspath(path)
    if os.path.isfile(p) and os.path.basename(p).lower() in ("skill.md", "claude.md", "agents.md"):
        return os.path.dirname(p), p
    if os.path.isdir(p):
        for cand in ("SKILL.md", "skill.md", "CLAUDE.md", "AGENTS.md"):
            fp = os.path.join(p, cand)
            if os.path.isfile(fp):
                return p, fp
    return None, None

def parse_frontmatter(text):
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    fm = {}
    for line in parts[1].splitlines():
        if ":" in line and not line.strip().startswith("#"):
            k, _, v = line.partition(":")
            fm[k.strip().lower()] = v.strip().strip('"\'')
    return fm

def score_skill(path):
    d, md = locate_skill(path)
    if not md:
        return {"error": f"no SKILL.md/AGENTS.md found at {path}"}, 2
    text = open(md, encoding="utf-8", errors="replace").read()
    fm = parse_frontmatter(text)
    scores, details = {}, {}

    # 1 registration
    need = ["name", "description", "license", "version"]
    got = [k for k in need if fm.get(k)]
    scores["registration"] = round(len(got) / len(need) * WEIGHTS["registration"])
    details["registration"] = f"frontmatter keys: {got} / {need}"

    # 2 bilingual (heuristic: presence of CJK + latin beyond frontmatter)
    body = text.split("---", 2)[-1]
    has_cjk = bool(re.search(r"[\u4e00-\u9fff]{2,}", body))
    has_en = bool(re.search(r"[A-Za-z]{4,}", body))
    scores["bilingual"] = round((has_en and has_cjk) / 1 * WEIGHTS["bilingual"]) if (has_en and has_cjk) else (WEIGHTS["bilingual"] * 0.5 if (has_en or has_cjk) else 0)
    details["bilingual"] = f"EN={'yes' if has_en else 'no'}, ZH={'yes' if has_cjk else 'no'}"

    # 3 license
    lic_file = os.path.exists(os.path.join(d, "LICENSE"))
    spdx = bool(re.search(r"apache-2\.0|mit|bsd-3|agpl|gpl", fm.get("license", "").lower()))
    lic_score = 0
    if lic_file: lic_score += 10
    if spdx: lic_score += 5
    scores["license"] = lic_score
    details["license"] = f"LICENSE file={'yes' if lic_file else 'no'}, frontmatter SPDX={'yes' if spdx else 'no'}"

    # 4 machine readable
    mr = 0
    for f in ("AGENTS.md", "llms.txt"):
        if os.path.exists(os.path.join(d, f)): mr += 5
    wk = os.path.exists(os.path.join(d, ".well-known", "agent-skills", "index.json"))
    if wk: mr += 5
    scores["machine_readable"] = mr
    details["machine_readable"] = f"AGENTS.md/llms.txt/.well-known-index = {mr}/15"

    # 5 hygiene
    low = text.lower()
    hits = [w for w in BANNED if w in low]
    scores["hygiene"] = WEIGHTS["hygiene"] if not hits else 0
    details["hygiene"] = "no banned wording" if not hits else f"banned: {hits}"

    # 6 content
    desc_len = len(fm.get("description", ""))
    sections = len(re.findall(r"^#{1,3} ", text, re.M))
    c = 0
    if desc_len >= 50: c += 7
    elif desc_len >= 20: c += 4
    if sections >= 3: c += 8
    elif sections >= 1: c += 4
    scores["content"] = min(c, WEIGHTS["content"])
    details["content"] = f"desc_len={desc_len}, sections={sections}"

    # 7 verification
    v = 0
    if re.search(r"verif|验证|test|测试", text, re.I): v += 6
    if re.search(r"evidence|证据|source|来源", text, re.I): v += 4
    scores["verification"] = v
    details["verification"] = f"verification/evidence mentions = {v}/10"

    total = sum(scores.values())
    verdict = "PASS" if total >= 60 else "FAIL"
    return {
        "skill": md,
        "total": total,
        "max": sum(WEIGHTS.values()),
        "verdict": verdict,
        "scores": scores,
        "details": details,
    }, 0 if verdict == "PASS" else 1

def main():
    if len(sys.argv) < 2:
        print("usage: python skill_scorecard.py <path>", file=sys.stderr)
        return 2
    res, code = score_skill(sys.argv[1])
    if "error" in res:
        print("ERROR:", res["error"], file=sys.stderr)
        return 2
    print(json.dumps(res, ensure_ascii=False, indent=2))
    print(f"\nVERDICT: {res['verdict']} ({res['total']}/{res['max']})")
    return code

if __name__ == "__main__":
    sys.exit(main())
