import io,os,re
mds=[]
for dp,dn,fn in os.walk("."):
    if "故事板" in dp or "_v14升级工作台" in dp: continue
    for f in fn:
        if f.endswith(".md"): mds.append(os.path.join(dp,f).replace("\\","/"))
T={p:io.open(p,encoding='utf-8').read() for p in mds}
SKIP=("CHANGELOG","UPGRADE-LOG","V14-FEATURE","V13-FEATURE")
print("扫描",len(mds),"个 md")
print("\n[1] 源库路径残留（应零）")
for k in ("00-bible","01-script/","02-breakdown","03-shots","04-assets","05-control-prompts","06-motion-prompts","07-continuity","film-reviewer","废才"):
    h=[p for p in mds if not any(s in p for s in SKIP) and k in T[p]]
    print(f"  {'X' if h else 'OK'} {k}: {h[:3] if h else '零'}")
print("\n[2] v13 旧口径（应零，examples 带头注的除外）")
for k in ("三块散文","均分≥8","评分制放行","02-seedance"):
    h=[p for p in mds if not any(s in p for s in SKIP) and k in T[p]]
    print(f"  {'X' if h else 'OK'} {k}: {h[:3] if h else '零'}")
print("\n[3] agent skills 可达")
for p in [q for q in mds if "/agents/" in q]:
    m=re.search(r"^skills:\s*(.+)$",T[p],re.M)
    if m:
        for s in [x.strip() for x in m.group(1).split(",")]:
            if not os.path.exists(f".claude/skills/{s}/SKILL.md"): print("  X",os.path.basename(p),"->",s)
print("  (无输出=全绿)")
print("\n[4] 跨文件章节引用")
S={p:set(re.findall(r"^\[([^\]]+?)\]",t,re.M)) for p,t in T.items()}
bad=0
for p,t in T.items():
    if any(s in p for s in SKIP): continue
    for m in re.finditer(r"([A-Za-z0-9_\-\.]+\.md)\s*(?:的\s*)?\[([^\]]{2,30})\]",t):
        c=[q for q in mds if q.endswith("/"+m.group(1)) or q=="./"+m.group(1)]
        if c and not any(m.group(2) in S[x] for x in c): print(f"  X {p}: {m.group(1)} 无 [{m.group(2)}]"); bad+=1
cl=S.get("./CLAUDE.md",set())
for p,t in T.items():
    if any(s in p for s in SKIP): continue
    for m in re.finditer(r"CLAUDE\.md\s*(?:的\s*)?\[([^\]]{2,30})\]",t):
        if m.group(1) not in cl: print(f"  X {p}: CLAUDE.md 无 [{m.group(1)}]"); bad+=1
print("  OK 全部命中" if not bad else f"  {bad} 处断链")
print("\n[5] 缺口关键词在位")
K=[("assets/reference-index.template.md",["声线锁","短串"]),
   (".claude/skills/art-design-skill/SKILL.md",["纯正向","七维","声线锁"]),
   (".claude/skills/_shared/user-messages.md",["retake` 收案"]),
   (".claude/ARCHITECTURE.md",["02-shot-table","continuity-ledger","visual-style"]),
   (".claude/templates/file-index.template.md",["shot-table"]),
   ("CHANGELOG.md",["v14.0"]),("README.md",["v14"]),("USAGE.md",["v14"])]
for f,ks in K:
    if not os.path.exists(f): print("  X 缺文件",f); continue
    t=io.open(f,encoding='utf-8').read()
    miss=[k for k in ks if k not in t]
    print(f"  {'OK' if not miss else 'X'} {f} {miss if miss else ''}")
print(f"\n[6] V14-FEATURE-SUMMARY 存在: {os.path.exists('V14-FEATURE-SUMMARY.md')} / V13 已删: {not os.path.exists('V13-FEATURE-SUMMARY.md')}")
print("[7] CLAUDE.md 行数:", len(T['./CLAUDE.md'].splitlines()))
print("\n[8] 编号体系产地（G15 裁决后应转 OK）")
ri=io.open("assets/reference-index.template.md",encoding='utf-8').read()
has_col=("项目编号" in ri) or ("char-NNN" in ri)
print(f"  {'OK' if has_col else 'X'} reference-index.template 有编号列/编号格式: {has_col}"
      + ("" if has_col else "  ← 约 20 处消费方要求 char-NNN，索引母版无产地（见清单 G15，待用户裁决 A/B）"))
print("\n[9] 服化道模板 vs 三文件契约（G17）")
tp=".claude/skills/art-design-skill/templates/art-design-template.md"
t9=io.open(tp,encoding='utf-8').read()
for k in ("prop-prompts.md","char-001","scene-001","prop-001"):
    print(f"  {'OK' if k in t9 else 'X'} 模板含 {k}: {k in t9}"
          + ("" if k in t9 else "  ← SKILL.md 要求写三个文件/标题带编号，模板缺（见清单 G17）"))
print("\n[10] 音频轨编号口径（G18：audio 不进条头）")
ad=io.open(".claude/skills/art-design-skill/SKILL.md",encoding='utf-8').read()
c1="不进条头" in ri
m10=re.search(r"\*\*发号规则\*\*：([^。]*)。",ad)
c2=bool(m10) and "audio" not in m10.group(1)
print(f"  {'OK' if c1 else 'X'} 索引母版声明音频不进条头: {c1}")
print(f"  {'OK' if c2 else 'X'} 服化道发号规则(首句)不含 audio: {c2}"
      + ("" if c2 else "  ← 服化道不产音频却发音频号，与 asset-binding.md 两套地址段冲突（见清单 G18）"))

# ── 以下三项由 G16 三条施工（P1-2 / 秒数 config 驱动 / v13 场号）固化为回归判据 ──

print("\n[11] v13 场号形态残留（s0N-cM 应零；v14 地址一律 epNN-P0X-CutM）")
rx11=re.compile(r"s\d{1,2}-c\d{1,2}")
h11=[(p,m.group(0)) for p,t in T.items() if not any(s in p for s in SKIP)
     for m in [rx11.search(t)] if m]
print("  OK 零残留" if not h11 else "  X "+str(h11[:5]))

print("\n[12] 秒数 config 驱动（含生成时长语境 30s 的文件应引 video_model_config）")
# 判据只针对「生成/单条时长上限」语境；开场30秒、平台主流时长30s 等叙事/运营数字不在内
RX12=re.compile(r"(单条|每条|底片|延长|可延|生成时长|时长上限|上限)[^。\n]{0,14}?(30\s*s|30\s*秒)"
                r"|4[–\-—]30\s*s")
OK12=re.compile(r"video_model_config|max_seconds")
warn=[]
for p,t in T.items():
    if any(s in p for s in SKIP): continue
    if RX12.search(t) and not OK12.search(t):
        warn.append((p,[l.strip()[:70] for l in t.splitlines() if RX12.search(l)][:2]))
if not warn: print("  OK 全部已 config 驱动")
else:
    print(f"  ! {len(warn)} 个文件写死秒数且无 config 引用（warn，非零容忍——逐条判语境）")
    for p,ls in warn: print(f"     {p}\n       {ls}")

print("\n[13] 平台图片 tag 口径统一（应零 @图N，全库统一 @图片N）")
rx13=re.compile(r"@图(?!片)")
h13=[(p,len(rx13.findall(t))) for p,t in T.items() if rx13.search(t)]
print("  OK 零残留" if not h13 else "  X "+str(h13[:8]))
bad13=[(p,len(re.findall(r"@图片片|@视频片|@音频片",t))) for p,t in T.items()
       if re.search(r"@图片片|@视频片|@音频片",t)]
print("  OK 无替换误伤" if not bad13 else "  X 误伤 "+str(bad13[:5]))

print("\n[14] 源库站名映射兜底（含旧站名的文件，本站入口须有映射块）")
# 背景：UPGRADE-LOG:91 决策「不做全库重命名，改为入口 SKILL.md 各加一行映射」，
# 且「入口映射对本卡的 references / templates 一并生效」。故判据是【站级】不是文件级：
# 本文件自身有映射，或其所属 skill 的入口 SKILL.md 有映射，即算兜底。
# 词边界必需：无 (?![\w\-]) 会把 director-index.md 误判成 director-grill。
ST14=["motion-compile","character-design","scene-design","prop-design",
      "control-image","director-grill","script-breakdown"]
RXH14=re.compile("(?:"+"|".join(ST14)+r")(?![\w\-])")
RXOK14=re.compile(r"源库站名|站名映射|别去调|不是一个真实存在|不要真的去调|V14 无独立")
def _cov14(p):
    if RXOK14.search(T[p]): return True
    m=re.match(r"\./\.claude/skills/([^/]+)/",p)
    if m:
        e="./.claude/skills/%s/SKILL.md"%m.group(1)
        if e in T and RXOK14.search(T[e]): return True
    return False
miss14=[(p,sorted(set(RXH14.findall(t)))) for p,t in T.items()
        if not any(s in p for s in SKIP) and RXH14.search(t) and not _cov14(p)]
if not miss14: print("  OK 全部有映射兜底")
else:
    print(f"  X {len(miss14)} 个文件含旧站名且无映射兜底（agent 会指向不存在的站）")
    for p,s in miss14: print(f"     {p}  {s}")

