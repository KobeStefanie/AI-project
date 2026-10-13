# -*- coding: utf-8 -*-
# 扫描退化/损坏的 md。结果写入 _v14升级工作台/scan-report.txt（不靠 stdout 传递）
import io, os, re, collections

out = []


def tables(L):
    res, cur, start = [], [], 0
    for i, x in enumerate(L):
        if x.strip().startswith('|'):
            if not cur:
                start = i + 1
            cur.append(x.strip())
        else:
            if len(cur) >= 3:
                res.append((start, cur))
            cur = []
    if len(cur) >= 3:
        res.append((start, cur))
    return res


files = []
for dp, dn, fn in os.walk('.'):
    if '_v14' in dp or '.git' in dp:
        continue
    for f in fn:
        if f.endswith('.md'):
            files.append(os.path.join(dp, f).replace('\\', '/'))

for p in sorted(files):
    try:
        t = io.open(p, encoding='utf-8').read()
    except Exception as e:
        out.append('READFAIL   %s  %s' % (p, e))
        continue
    L = t.splitlines()
    hits = []

    # 1) markdown 标题重复
    heads = [x.strip() for x in L if x.startswith('#')]
    for k, v in collections.Counter(heads).items():
        if v >= 2:
            ln = [i + 1 for i, x in enumerate(L) if x.strip() == k]
            hits.append('DUP-HEAD   %r x%d  行 %s' % (k[:50], v, ln))

    # 2) 方括号章节名重复（SKILL.md 风格）
    br = [x.strip() for x in L if re.match(r'^\[[^\]]{2,30}\]\s*$', x)]
    for k, v in collections.Counter(br).items():
        if v >= 2:
            ln = [i + 1 for i, x in enumerate(L) if x.strip() == k]
            hits.append('DUP-SEC    %r x%d  行 %s' % (k, v, ln))

    # 3) 同一非空行出现 >=5 次
    for k, v in collections.Counter(x.strip() for x in L if len(x.strip()) > 3).items():
        if v >= 5:
            hits.append('REP-LINE   %r x%d' % (k[:50], v))

    # 4) 占位符
    for m in set(re.findall(r'\{\{描述[^}]*\}\}', t)):
        hits.append('PLACEHLD   %s' % m)

    # 5) 连续分隔行
    for i in range(len(L) - 1):
        if re.match(r'^\|[\s\-|:]+\|$', L[i].strip()) and re.match(r'^\|[\s\-|:]+\|$', L[i + 1].strip()):
            hits.append('TBL-SEP2   行 %d' % (i + 1))

    # 6) 表内整行重复 / 首列重复
    for start, blk in tables(L):
        for k, v in collections.Counter(blk).items():
            if v >= 2 and not re.match(r'^\|[\s\-|:]+\|$', k):
                hits.append('TBL-DUPROW 表@行%d  %r' % (start, k[:60]))
        firsts = []
        for r in blk:
            if re.match(r'^\|[\s\-|:]+\|$', r):
                continue
            cells = [z.strip() for z in r.strip('|').split('|')]
            if cells:
                firsts.append(cells[0])
        for k, v in collections.Counter(x for x in firsts if x and not x.startswith('{{')).items():
            if v >= 2:
                hits.append('TBL-DUPKEY 表@行%d  首列 %r x%d' % (start, k[:30], v))

    # 7) 自指行（「见 [X]」出现在名为 X 的章节内部）
    for i, x in enumerate(L):
        m = re.search(r'见 \[([^\]]{2,20})\]', x)
        if m:
            tag = '[%s]' % m.group(1)
            for j in range(i, -1, -1):
                if re.match(r'^\[[^\]]{2,30}\]\s*$', L[j]):
                    if L[j].strip() == tag:
                        hits.append('SELF-REF   行 %d  %r' % (i + 1, x.strip()[:60]))
                    break

    if hits:
        out.append('=== %s' % p)
        out.extend('    ' + h for h in sorted(set(hits)))

io.open('_v14升级工作台/scan-report.txt', 'w', encoding='utf-8').write(
    ('扫描 %d 个 md\n\n' % len(files)) + ('\n'.join(out) if out else '未发现退化迹象') + '\n')
print('done')
