# -*- coding: utf-8 -*-
"""V14 死引用精查（只读）
A1 skill 路径式引用：`<skill>/references/<x>.md` `<skill>/SKILL.md` 等，目标必须在磁盘上
A2 源库站名残留：引用了源库 3.0 的 skill 站名（V14 已合并掉的）
A3 运行期产物引用：只统计，不判错（这些是用户跑项目时生成的）
"""
import io, os, re

mds = []
for dp, dn, fn in os.walk("."):
    if "_v14升级工作台" in dp or "故事板" in dp:
        continue
    for f in fn:
        if f.endswith(".md"):
            mds.append(os.path.join(dp, f).replace("\\", "/"))
T = {p: io.open(p, encoding="utf-8").read() for p in mds}
HIST = ("CHANGELOG", "UPGRADE-LOG", "V14-FEATURE", "V13-FEATURE")
print(f"精查 {len(mds)} 个 md\n")

SKILLS = sorted(d for d in os.listdir(".claude/skills")
                if os.path.isdir(f".claude/skills/{d}"))
# 源库 3.0 的站名（V14 已合并/改名的）
SRC_STATIONS = ["character-design", "scene-design", "prop-design", "control-image",
                "director-grill", "script-write", "script-adapt", "script-breakdown",
                "motion-compile", "previz", "goal-creator", "film-reviewer",
                "review"]

print("=" * 66)
print("[A1] skill 内部路径引用（<skill>/{references,templates,examples}/x.md）")
print("=" * 66)
# 形如 foo/references/bar.md 或 foo/SKILL.md 或 references/bar.md
RX = re.compile(r"`?([a-z0-9_\-]+/)?((?:references|templates|examples)/[a-z0-9_\-.]+\.md|SKILL\.md)`?")
bad1 = []
for p, t in T.items():
    if any(h in p for h in HIST):
        continue
    owner = None
    m = re.match(r"\./\.claude/skills/([^/]+)/", p)
    if m:
        owner = m.group(1)
    for mm in RX.finditer(t):
        pre, tail = mm.group(1), mm.group(2)
        ref = (pre or "") + tail
        cands = []
        if pre:  # 带站名前缀
            st = pre.rstrip("/")
            cands.append(f".claude/skills/{st}/{tail}")
            cands.append(f".claude/{st}/{tail}")
        else:    # 无前缀 = 本站内
            if owner:
                cands.append(f".claude/skills/{owner}/{tail}")
            cands.append(f".claude/skills/{tail}")
        # 相对当前文件
        cands.append(os.path.normpath(os.path.join(os.path.dirname(p), ref)))
        if not any(os.path.exists(c) for c in cands):
            bad1.append((p, ref))
if not bad1:
    print("  OK 零死引用")
else:
    seen = set()
    for p, ref in bad1:
        k = (p, ref)
        if k in seen:
            continue
        seen.add(k)
        print(f"  X {p}\n      -> {ref}")

print()
print("=" * 66)
print("[A2] 源库 3.0 站名残留（V14 已合并的站，不该再作为指路目标）")
print("=" * 66)
for st in SRC_STATIONS:
    hits = []
    for p, t in T.items():
        if any(h in p for h in HIST):
            continue
        for i, line in enumerate(t.splitlines(), 1):
            # 只收「像路径 / 像指路」的用法
            if re.search(rf"{st}/(SKILL|references|templates|examples)", line) \
               or re.search(rf"(见|详见|归|回|派|调用|走)\s*`?{st}`?(?![\w\-])", line):
                hits.append((p, i, line.strip()[:100]))
    if hits:
        print(f"\n  ── {st}  ({len(hits)} 处)")
        for p, i, l in hits[:6]:
            print(f"     {p}:{i}")
            print(f"        {l}")
        if len(hits) > 6:
            print(f"     … 另 {len(hits)-6} 处")
if not any(True for st in SRC_STATIONS for p, t in T.items()
           if not any(h in p for h in HIST) and re.search(rf"{st}/(SKILL|references)", t)):
    print("  (无 path 式残留)")

print()
print("=" * 66)
print("[A4] 每个 skill 的 SKILL.md frontmatter 完整性")
print("=" * 66)
for s in SKILLS:
    if s == "_shared":
        continue
    fp = f".claude/skills/{s}/SKILL.md"
    if not os.path.exists(fp):
        print(f"  X {s}  无 SKILL.md")
        continue
    t = io.open(fp, encoding="utf-8").read()
    if not t.startswith("---"):
        print(f"  X {s}  无 frontmatter")
        continue
    fm = t.split("---")[1]
    miss = [k for k in ("name:", "description:") if k not in fm]
    nm = re.search(r"name:\s*(\S+)", fm)
    warn = ""
    if nm and nm.group(1) != s:
        warn = f"  ⚠ name({nm.group(1)}) != 目录名({s})"
    print(f"  {'X' if miss else 'OK'} {s}{'  缺 ' + str(miss) if miss else ''}{warn}")
