#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
skill-scorecard v0.4 — LGD Four-Angle AI Skill Scoring System
一条命令、零依赖，给任意 AI 技能做四角度成体系评分。

Angles（角度，对应 LGD 三律 + 基础设施）:
  REGISTERED  已注册度 (有籍)   identity / registry / namespace / attribution
  TRUSTWORTHY 可信度   (有证)   verification / evidence / reproducibility / citation
  SAFE        安全度   (有门禁) guardrails / least-privilege / fail-closed / threat scan
  MACHINE     机器可读度(基础设施) frontmatter / bilingual / license / index / hygiene / content

Total = weighted mean of the four angles; PASS >= 60, fail-closed exit code.
Usage:
  python skill_scorecard.py <path> [--angle reg|trust|safe|mach] [--badge out.svg] [--badges-dir dir/] [--json]
"""
import hashlib, json, os, re, sys

# ---------- constants ----------
PASS_BAR = 60
ANGLE_WEIGHTS = {"registered": 1, "trustworthy": 1, "safe": 1, "machine": 1}  # equal by default

BANNED = ["placeholder", "占位", "priority claim", "placehold", "临时占", "TODO: 占"]

# Threat patterns: category -> list of regexes (inspired by published agent-skill threat taxonomies)
THREATS = {
    "prompt_injection": [
        r"(?i)ignore (all )?(previous|prior|above) instructions",
        r"(?i)jailbreak|dan mode|system prompt override",
        r"[\u200b\u200c\u200d\u2060\u2062\u2063]",
    ],
    "hardcoded_secret": [
        r"(?i)(api[_-]?key|secret|token|password|passwd)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}",
        r"(?i)(ghp_|sk-|AKIA|gho_)[A-Za-z0-9_\-]{16,}",
        r"(?i)private[_ ]?key|BEGIN [A-Z ]*PRIVATE KEY",
    ],
    "destructive_command": [
        r"(?i)rm\s+-rf\s*/|rm\s+-rf\s+~\s*$",
        r"(?i)DROP TABLE|DROP DATABASE",
        r"(?i)mkfs|dd\s+if=.*of=/dev/",
        r"(?i)format\s+[c-z]:",
    ],
    "data_exfiltration": [
        r"(?i)curl\s+[^|]*\s+-d\s|curl\s+.*\|.*sh",
        r"(?i)~\/(\.ssh|\.aws|\.gnupg|\.git)",
        r"(?i)rev(erse)?[- ]?shell",
        r"(?i)\.aws\/credentials|credential file",
    ],
    "crypto_mining": [r"(?i)xmrig|coinhive|minerd|cpuminer|stratum\+tcp"],
    "privilege_escalation": [
        r"(?i)sudo\s+rm|chmod\s+777|chown\s+root",
        r"(?i)useradd\s+-o|passwd\s+-?\w*\s+root",
    ],
    "persistence": [
        r"(?i)crontab|@reboot|authorized_keys",
        r"(?i)\.bashrc|rc\.local|systemctl\s+enable",
    ],
    "obfuscation": [
        r"(?i)base64\s*-d\s*\||base64\s*--decode\s*\|",
        r"(?i)eval\(\$\(|compile\(.*exec\(|__import__\(['\"]os",
    ],
}

# ---------- utils ----------
def locate_skill(path):
    p = os.path.abspath(path)
    if os.path.isfile(p) and os.path.basename(p).lower() in ("skill.md", "claude.md", "agents.md"):
        return os.path.dirname(p), p
    if os.path.isdir(p):
        for cand in ("SKILL.md", "skill.md", "CLAUDE.md", "AGENTS.md", "README.md"):
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

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def has_any(text, patterns):
    for p in patterns:
        if re.search(p, text):
            return True
    return False

# ---------- angles ----------
def angle_registered(fm, text):
    """REGISTERED AI (有籍): identity, registry proof, namespace, attribution."""
    s, d = 0, []
    if fm.get("name"):
        s += 15; d.append("name")
    if re.search(r"doi|zenodo|10\.\d{4,}", text, re.I):
        s += 30; d.append("DOI/registry proof")
    if fm.get("namespace") or fm.get("type"):
        s += 20; d.append("namespace/type")
    if re.search(r"(?i)author|orcid|registered_by|by\s+\w", text):
        s += 20; d.append("attribution")
    if fm.get("version"):
        s += 15; d.append("version")
    return min(s, 100), d

def angle_trustworthy(text):
    """TRUSTWORTHY AI (有证): verification anchors, evidence, reproducibility, citation."""
    s, d = 0, []
    if re.search(r"(?i)verification|验证|查重|checked", text):
        s += 30; d.append("verification section")
    if re.search(r"(?i)evidence|prior-art|证据|来源|reference", text):
        s += 25; d.append("evidence anchors")
    if re.search(r"(?i)reproduc|test|benchmark|复现|测试|步骤\s*\d", text):
        s += 20; d.append("reproducibility")
    if re.search(r"(?i)doi|cite|引用|bibtex", text):
        s += 15; d.append("citation")
    if re.search(r"(?i)version|changelog|变更|历史", text):
        s += 10; d.append("versioning")
    return min(s, 100), d

def angle_safe(fm, text, d):
    """SAFE AI (有门禁): guardrails, least privilege, fail-closed, threat scan."""
    s, d2 = 0, []
    # guardrails present
    if has_any(text, [r"(?i)guardrail", r"(?i)必须.*不|禁止|never|must not|不允许", r"(?i)#\s*安全|safety"]):
        s += 25; d2.append("guardrails")
    # least privilege
    if not has_any(text, [r"(?i)sudo\s+(rm|chmod 777)", r"(?i)full (access|permission)"]):
        s += 15; d2.append("least-privilege")
    # fail-closed
    if has_any(text, [r"(?i)fail[- ]closed|default[- ]deny|默认拒绝|先拒绝|门禁"]):
        s += 15; d2.append("fail-closed")
    else:
        s += 5; d2.append("no fail-closed declaration")
    # threat scan (45 pts: 8 categories, -6 each hit)
    threat_hits = []
    for cat, pats in THREATS.items():
        if has_any(text, pats):
            threat_hits.append(cat)
    s += max(0, 45 - len(threat_hits) * 6)
    d2.append(f"threat scan: {'clean' if not threat_hits else 'HITS ' + ','.join(threat_hits)}")
    return min(s, 100), d2

def angle_machine(fm, text, d):
    """MACHINE-READABLE (基础设施): frontmatter/bilingual/license/index/hygiene/content."""
    body = text.split("---", 2)[-1] if text.startswith("---") else text
    s, d2 = 0, []
    need = ["name", "description", "license", "version"]
    got = [k for k in need if fm.get(k)]
    s += int(len(got) / len(need) * 20); d2.append(f"frontmatter {got}/{need}")
    has_cjk, has_en = bool(re.search(r"[\u4e00-\u9fff]{2,}", body)), bool(re.search(r"[A-Za-z]{4,}", body))
    if has_en and has_cjk:
        s += 15; d2.append("bilingual")
    elif has_en or has_cjk:
        s += 7.5; d2.append("single-language")
    lic_file = os.path.exists(os.path.join(d, "LICENSE"))
    spdx = bool(re.search(r"apache-2\.0|mit|bsd-3|agpl|gpl", fm.get("license", "").lower()))
    s += (10 if lic_file else 0) + (5 if spdx else 0); d2.append(f"LICENSE file={'y' if lic_file else 'n'}, SPDX={'y' if spdx else 'n'}")
    for f in ("AGENTS.md", "llms.txt"):
        if os.path.exists(os.path.join(d, f)): s += 5
    if os.path.exists(os.path.join(d, ".well-known", "agent-skills", "index.json")): s += 5
    d2.append("machine-readable")
    low = text.lower()
    hits = [w for w in BANNED if w in low]
    s += 10 if not hits else 0; d2.append("hygiene" if not hits else f"banned:{hits}")
    desc_len = len(fm.get("description", ""))
    sections = len(re.findall(r"^#{1,3} ", text, re.M))
    if desc_len >= 50: s += 7
    elif desc_len >= 20: s += 4
    s += min(8, sections * 2 if sections >= 3 else sections)
    d2.append(f"content(desc={desc_len},sections={sections})")
    if re.search(r"verif|验证|test|测试", text, re.I): s += 6
    if re.search(r"evidence|证据|source|来源", text, re.I): s += 4
    d2.append("verification")
    return round(min(s, 100)), d2

# ---------- badges ----------
def make_badge(label, total, verdict, with_shield=True):
    """Shield-seal style badge. label in {LGD, REG, TRUST, SAFE, MACH}."""
    vc = "#22d3ee" if verdict == "PASS" else "#f87171"
    score = f"{total:.0f}/100"
    fs = 12
    pad = 9
    icon_w = 26 if with_shield else 0
    wl = int(pad * 2 + icon_w + 4 + fs * 0.62 * len(label))
    wv = int(pad * 2 + fs * 0.62 * len(score))
    W = wl + wv
    H = 26
    icon = ('<path d="M12 2 L20 5 V11 C20 17 16.5 20.5 12 22 C7.5 20.5 4 17 4 11 V5 Z" '
            'fill="none" stroke="#38bdf8" stroke-width="1.6" stroke-linejoin="round"/>'
            '<path d="M9 11.5 L11.5 14 L15.5 9" fill="none" stroke="#38bdf8" stroke-width="1.8" '
            'stroke-linecap="round" stroke-linejoin="round"/>')
    label_e = esc(label)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{label_e}: {esc(score)}">
  <defs>
    <linearGradient id="sd" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#101827"/><stop offset="1" stop-color="#1e293b"/></linearGradient>
    <linearGradient id="se" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0891b2"/><stop offset="1" stop-color="{vc}"/></linearGradient>
  </defs>
  <g font-family="Segoe UI,Helvetica Neue,Arial,sans-serif">
    <rect width="{wl}" height="{H}" rx="5" fill="url(#sd)"/>
    <rect x="{wl}" width="{wv}" height="{H}" rx="5" fill="url(#se)"/>
    <rect width="{W}" height="{H}" rx="5" fill="none" stroke="rgba(255,255,255,.16)"/>
    {('<g transform="translate(8,' + str(H / 2 - 11) + ') scale(0.85)">' + icon + '</g>') if with_shield else ''}
    <text x="{pad * 2 + icon_w + 12}" y="{H * 0.72}" fill="#fff" font-size="12" font-weight="700" text-anchor="middle" letter-spacing=".5">{label_e}</text>
    <text x="{wl + wv / 2}" y="{H * 0.72}" fill="#fff" font-size="{fs}" font-weight="800" text-anchor="middle">{esc(score)}</text>
  </g>
</svg>'''

def make_verified_badge(total, verdict, sha8):
    """LGD VERIFIED badge — for skills that pass, embeds a verifiable content hash.
    NOT an official certification or endorsement; generated by LGD skill-scorecard static audit."""
    vc = "#16a34a"
    W, H = 182, 28
    fs = 12
    text = f"LGD VERIFIED {total}/100"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="LGD Verified {esc(str(total))}/100 (sha {esc(sha8)})">
  <defs>
    <linearGradient id="vd" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0f172a"/><stop offset="1" stop-color="#1e293b"/></linearGradient>
    <linearGradient id="ve" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#15803d"/><stop offset="1" stop-color="{vc}"/></linearGradient>
  </defs>
  <g font-family="Segoe UI,Helvetica Neue,Arial,sans-serif">
    <rect width="118" height="{H}" rx="5" fill="url(#vd)"/>
    <rect x="118" width="64" height="{H}" rx="5" fill="url(#ve)"/>
    <path d="M14 3 L22 5.6 V11 C22 16.4 19 19.6 14 21.4 C9 19.6 6 16.4 6 11 V5.6 Z" fill="none" stroke="#4ade80" stroke-width="1.5" stroke-linejoin="round"/>
    <path d="M11 11 L13.2 13.2 L17 9.2" fill="none" stroke="#4ade80" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>
    <text x="48" y="{H * 0.72}" fill="#fff" font-size="12" font-weight="700" text-anchor="middle" letter-spacing=".4">LGD VERIFIED</text>
    <text x="150" y="{H * 0.72}" fill="#fff" font-size="{fs}" font-weight="800" text-anchor="middle">{esc(str(total))}/100</text>
    <text x="6" y="{H + 12}" fill="#94a3b8" font-size="9">sha:{esc(sha8)} · static audit · not certification</text>
  </g>
</svg>'''

# ---------- scoring ----------
def score_skill(path):
    d, md = locate_skill(path)
    if not md:
        return {"error": f"no SKILL.md/AGENTS.md/CLAUDE.md found at {path}"}, 2
    text = open(md, encoding="utf-8", errors="replace").read()
    fm = parse_frontmatter(text)
    reg, reg_d = angle_registered(fm, text)
    tru, tru_d = angle_trustworthy(text)
    saf, saf_d = angle_safe(fm, text, d)
    mac, mac_d = angle_machine(fm, text, d)
    angles = {"registered": reg, "trustworthy": tru, "safe": saf, "machine": mac}
    total = round(sum(angles[a] * ANGLE_WEIGHTS[a] for a in angles) / sum(ANGLE_WEIGHTS.values()))
    verdict = "PASS" if total >= PASS_BAR else "FAIL"
    return {
        "skill": md,
        "sha256": hashlib.sha256(open(md, "rb").read()).hexdigest(),
        "total": total,
        "verdict": verdict,
        "bar": PASS_BAR,
        "angles": angles,
        "angle_details": {"registered": reg_d, "trustworthy": tru_d, "safe": saf_d, "machine": mac_d},
    }, 0 if verdict == "PASS" else 1

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    angle_opt = None
    badge_out = None
    badges_dir = None
    if "--angle" in sys.argv:
        i = sys.argv.index("--angle")
        if i + 1 < len(sys.argv):
            m = {"reg": "registered", "trust": "trustworthy", "safe": "safe", "mach": "machine"}.get(sys.argv[i + 1].lower())
            angle_opt = m or sys.argv[i + 1].lower()
    if "--badge" in sys.argv:
        i = sys.argv.index("--badge")
        if i + 1 < len(sys.argv):
            badge_out = sys.argv[i + 1]
    if "--badges-dir" in sys.argv:
        i = sys.argv.index("--badges-dir")
        if i + 1 < len(sys.argv):
            badges_dir = sys.argv[i + 1]
    if not args:
        print("usage: python skill_scorecard.py <path> [--angle reg|trust|safe|mach] [--badge out.svg] [--badges-dir dir/] [--json]", file=sys.stderr)
        return 2
    res, code = score_skill(args[0])
    if "error" in res:
        print("ERROR:", res["error"], file=sys.stderr)
        return 2
    if angle_opt:
        a = res["angles"].get(angle_opt)
        if a is None:
            print("unknown angle:", angle_opt, file=sys.stderr)
            return 2
        res = {"skill": res["skill"], "angle": angle_opt, "score": a,
               "verdict": "PASS" if a >= PASS_BAR else "FAIL", "details": res["angle_details"][angle_opt]}
    if "--json" in sys.argv:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        if "angles" in res:
            print(f"skill: {res['skill']}")
            for k, v in res["angles"].items():
                print(f"  {k:12s} {v:3d}/100  {'PASS' if v >= PASS_BAR else 'FAIL'}  {res['angle_details'][k]}")
            print(f"  TOTAL     {res['total']:3d}/100  {res['verdict']}  (bar={res['bar']})")
        else:
            print(json.dumps(res, ensure_ascii=False, indent=2))
            print(f"VERDICT: {res['verdict']} ({res['score']}/100)")
    if "--verified" in sys.argv:
        i = sys.argv.index("--verified")
        out = sys.argv[i + 1] if i + 1 < len(sys.argv) else "LGD_VERIFIED.svg"
        sha8 = res.get("sha256", "?" * 8)[:8]
        open(out, "w", encoding="utf-8").write(make_verified_badge(res["total"], res["verdict"], sha8))
        print(f"LGD VERIFIED badge written: {out} (sha256:{sha8}, total {res['total']}/100)")
    if badge_out:
        lbl = {"registered": "REG", "trustworthy": "TRUST", "safe": "SAFE", "machine": "MACH"}.get(angle_opt, "LGD")
        score_val = res["angles"][angle_opt] if (angle_opt and "angles" in res) else (res["score"] if "score" in res else res["total"])
        vd = "PASS" if score_val >= PASS_BAR else "FAIL"
        open(badge_out, "w", encoding="utf-8").write(make_badge(lbl, score_val, vd, with_shield=(angle_opt is None)))
        print(f"badge written: {badge_out}")
    if badges_dir:
        os.makedirs(badges_dir, exist_ok=True)
        for lbl, key in (("LGD", None), ("REG", "registered"), ("TRUST", "trustworthy"), ("SAFE", "safe"), ("MACH", "machine")):
            if key is None:
                sc, vd = res["total"], res["verdict"]
            else:
                sc, vd = res["angles"][key], "PASS" if res["angles"][key] >= PASS_BAR else "FAIL"
            open(os.path.join(badges_dir, lbl + ".svg"), "w", encoding="utf-8").write(
                make_badge(lbl, sc, vd, with_shield=(key is None)))
        print(f"badges written: {badges_dir}/LGD.svg REG.svg TRUST.svg SAFE.svg MACH.svg")
    return code

if __name__ == "__main__":
    sys.exit(main())
