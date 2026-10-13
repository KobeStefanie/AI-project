# -*- coding: utf-8 -*-
"""V14 可用性审查（只读，不改任何文件）
查 selfcheck.py 覆盖不到的三类结构性 bug：
  A 死路径  —— md 里引用的库内文件，磁盘上不存在
  B 孤岛    —— skill 目录存在但无人调用（agent frontmatter / CLAUDE.md / 其他 skill 都没引）
  C 移植缺口 —— 源库 3.0 有、V14 没有的 skill/reference
"""
import io, os, re, sys

ROOT = "."
SRC = "../Seedance 分镜师 3.0"

mds = []
for dp, dn, fn in os.walk(ROOT):
    if "_v14升级工作台" in dp or "故事板" in dp or ".git" in dp:
        continue
    for f in fn:
        if f.endswith(".md"):
            mds.append(os.path.join(dp, f).replace("\\", "/"))
T = {p: io.open(p, encoding="utf-8").read() for p in mds}
HIST = ("CHANGELOG", "UPGRADE-LOG", "V14-FEATURE", "V13-FEATURE", "00-断点")
print(f"审查 {len(mds)} 个 md\n")

# ─────────────────────────────────────────────
# A 死路径：引用了磁盘上不存在的库内文件
# ─────────────────────────────────────────────
print("=" * 60)
print("[A] 死路径检测（引用的库内文件是否真实存在）")
print("=" * 60)

# 只收「看起来像库内相对路径」的引用；排除 outputs/ assets/ 这类运行期产物
RUNTIME = re.compile(r"^(outputs/|assets/|input/|script/|\.project-config|\.agent-state|project/)")
CAND = re.compile(r"`([A-Za-z0-9_\-./]+\.(?:md|py|json))`|\(([A-Za-z0-9_\-./]+\.md)\)")

def resolve(ref, frm):
    """尝试多种解析方式，任一命中即算存在"""
    cands = []
    d = os.path.dirname(frm)
    cands.append(os.path.normpath(os.path.join(d, ref)))          # 相对当前文件
    cands.append(os.path.normpath(os.path.join(ROOT, ref)))        # 相对库根
    cands.append(os.path.normpath(os.path.join(".claude/skills", ref)))  # 相对 skills 根
    cands.append(os.path.normpath(os.path.join(".claude", ref)))
    # 同名兜底：库内任何位置有同名文件即算可解析
    base = os.path.basename(ref)
    for c in cands:
        if os.path.exists(c):
            return True, c
    hits = [p for p in mds if p.endswith("/" + base)]
    if hits and ("/" not in ref or any(p.endswith(ref.lstrip("./")) for p in mds)):
        return True, hits[0] + " (同名)"
    return False, None

dead = {}
for p, t in T.items():
    if any(h in p for h in HIST):
        continue
    for m in CAND.finditer(t):
        ref = m.group(1) or m.group(2)
        if not ref or RUNTIME.match(ref):
            continue
        if ref.count("/") == 0 and not ref.endswith((".md", ".py")):
            continue
        ok, _ = resolve(ref, p)
        if not ok:
            dead.setdefault(ref, []).append(p)

if not dead:
    print("  OK 零死路径")
else:
    print(f"  发现 {len(dead)} 个无法解析的引用：")
    for ref, srcs in sorted(dead.items()):
        print(f"    ✗ {ref}")
        for s in sorted(set(srcs))[:3]:
            print(f"        被引于 {s}")

# ─────────────────────────────────────────────
# B 孤岛 skill：存在但无人调用
# ─────────────────────────────────────────────
print()
print("=" * 60)
print("[B] 孤岛检测（skill 是否被 agent/CLAUDE.md 调用）")
print("=" * 60)

skills = sorted(d for d in os.listdir(".claude/skills")
                if os.path.isdir(f".claude/skills/{d}"))
agent_txt = {}
for a in sorted(os.listdir(".claude/agents")):
    if a.endswith(".md"):
        agent_txt[a] = io.open(f".claude/agents/{a}", encoding="utf-8").read()
claude_md = T.get("./CLAUDE.md", "")

for s in skills:
    if s == "_shared":
        continue
    callers = []
    for a, at in agent_txt.items():
        m = re.search(r"^skills:\s*(.+)$", at, re.M)
        if m and s in m.group(1):
            callers.append(f"agent:{a}(frontmatter)")
        elif s in at:
            callers.append(f"agent:{a}(正文)")
    if s in claude_md:
        callers.append("CLAUDE.md")
    # 被别的 skill 引用
    others = [p for p, t in T.items() if f"/{s}/" in t or f"{s}/SKILL.md" in t
              or f"`{s}`" in t]
    others = [o for o in others if f"/skills/{s}/" not in o]
    if others:
        callers.append(f"其他skill×{len(others)}")
    has_fm = os.path.exists(f".claude/skills/{s}/SKILL.md")
    flag = "OK " if callers else "✗ 孤岛"
    print(f"  {flag} {s}"
          + ("" if has_fm else "  ⚠ 无 SKILL.md")
          + ("" if callers else "  ← 无人调用")
          + (f"   [{', '.join(callers[:3])}]" if callers else ""))

# agent frontmatter 声明的 skill 是否都存在（反向）
print("\n  -- agent frontmatter 反向核对 --")
for a, at in agent_txt.items():
    m = re.search(r"^skills:\s*(.+)$", at, re.M)
    if not m:
        print(f"  ⚠ {a} 无 skills: 字段")
        continue
    for s in [x.strip() for x in m.group(1).split(",") if x.strip()]:
        if not os.path.exists(f".claude/skills/{s}/SKILL.md"):
            print(f"  ✗ {a} -> {s}  (SKILL.md 不存在)")

# ─────────────────────────────────────────────
# C 移植缺口：源库 3.0 有、V14 没有
# ─────────────────────────────────────────────
print()
print("=" * 60)
print("[C] 移植完整性（源库 3.0 → V14）")
print("=" * 60)
if not os.path.isdir(SRC):
    print(f"  ⚠ 源库不可达: {SRC}")
else:
    src_files = []
    for dp, dn, fn in os.walk(SRC):
        for f in fn:
            if f.endswith(".md"):
                src_files.append(os.path.join(dp, f).replace("\\", "/"))
    print(f"  源库 3.0 共 {len(src_files)} 个 md，V14 共 {len(mds)} 个")
    v14_base = {os.path.basename(p) for p in mds}
    missing = [p for p in src_files if os.path.basename(p) not in v14_base]
    print(f"  V14 中找不到同名文件的源库文件：{len(missing)} 个")
    for p in sorted(missing):
        print(f"    · {p.replace(SRC + '/', '')}")
