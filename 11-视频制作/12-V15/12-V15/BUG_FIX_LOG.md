# Bug 修复日志 — 《躲进世界的角落里》

> 新记录加在最上面。排查问题前先搜本文件有没有同类记录。
> 本项目的「Bug」包括：提示词/文档里的矛盾、断链、走样、模型雷（审核五类病），以及流程上的漏记、误报。
> 2026-10-10 补建，10-08、10-09 两天的记录根据 `feedback-to-upstream.md`、`review/art-direction-report.md`、`decisions.md`、PROJECT_STATUS 更新日志整理。

---

## ⚠️ 当前已知隐患（未修）

| 隐患 | 触发条件 / 后果 | 临时规避 | 计划修法 |
|---|---|---|---|
| scene-prompts.md L231 给分镜师的附注仍写衣柜里「背靠柜壁」（2026-10-10 导演报） | 与 ★表确认后的「背抵柜右侧壁、侧对镜头」不一致；下游照附注写会回到背对镜头 | 以镜头表 v2 和讲戏本为准 | 下次调服化道时顺手同步，不重出图 |
| 卧室图上「门缝暖光铺到他脚边（约 50cm）」与「退半步背碰书桌靠门桌腿」可能无法同时成立（2026-10-10 导演报） | 图中书桌靠门一端离门有一段距离（制片人看图目测，未量），两件事可能只能成立一件 | 已交分镜师编译时按图写站位 | 不成立 → 分镜师开 feedback #5，交用户裁决 |
| music-recommendations.md 有 2 处署名「待核实」，推荐片段秒数未试听 | 直接引用会出错 | 用前试听定位 | 用户选用某首时再核 |
| 人物一致性无兜底 | 一步出图，同一张脸要在 12 条里反复出现；出片后可能脸飘 | 每条都绑 `character-小宇.png` 当参考 | 脸飘 → 用户拍板切 dual（decisions.md L47） |
| `visual-style.md` L30 推论 A 文字残留 | 括号里仍写「门把手在他头顶、椅面到他胸口、桌沿齐他眼睛」；分镜师若照抄进提示词，会重新召唤人物、数字也和锚句对不上 | 分镜师以 v1.1 锚句数字为准，推论 A 只当原则读 | 待用户决定是否改成离地高度表述 |
| `visual-style.md` L48 写角色板「中灰底」，art-design-skill 规定白底 | 两把尺子不一致（资产审「上游观察」第 4 条）；人物板已出图，暂无实际影响 | 已出的图不动 | 是否已处理：待确认 |

---

## 2026-10-10 · 成片审 agent 卡死

**症状**：第一次派的成片审 agent 失败，报「no progress for 600s」，`review/` 下没有新报告。
**根本原因**：未确认。推测是一次读入的内容太多：video-prompts.md 79KB、镜头表 75KB、讲戏本 61KB，加上 skill 文件。
**修复方案**：重派时要求分段读取（每次不超过 150 行），能用脚本核对的就用脚本，并控制命令输出长度。
**验证步骤**：`ls outputs/ep01/review/`，看到 seedance-prompt-report.md 才算审完。
**下次先查什么**：派审核类 agent 前，先看对象文件有多大；超过 50KB 就在 prompt 里写明分段读取。

---

## 2026-10-10

### Bug：阶段四音乐中断，主文件引用了 4 个不存在的产物（✅ 已于 2026-10-10 13:24 修复）

**修复记录**：新开音乐总监实例（agentId a17cc3eb258fa27b4，原 id 为 null 无法 Resume）补齐 `lyrics-drafts.md`、`music-recommendations.md`、`【直接复制】/1–4`、feedback #3。制片人核验：`ls` 4 项均在；txt1 与 music-design.md L69–L95 逐字 diff 一致；4 个 txt 内 `**`/反引号 0 处；music-design.md 修改时间仍为 09:49，未被改动。

**症状**：`assets/music/music-design.md` 10-10 09:49 落盘，自检写「`lyrics-drafts.md`、`music-recommendations.md`、`【直接复制】/1–4` 均已落盘」「已写 feedback-to-upstream.md #3」，盘上全都没有。

**根本原因**：会话在音乐总监写完主文件后中断（推测，具体中断原因待确认）；自检是写主文件时一并写的，写的是「打算落盘」不是「已落盘」。PROJECT_STATUS 也没记这次开工。

**修复方案**：待做。Resume 音乐总监补齐 4 项，制片人 `ls` 逐个核过再交用户。

**影响文件**：
- `assets/music/music-design.md` L5、L6、L19、L127、L132–L133
- 缺：`assets/music/lyrics-drafts.md`、`assets/music/music-recommendations.md`、`assets/music/【直接复制】/1–4`、`outputs/ep01/feedback-to-upstream.md` #3

**验证步骤**：`ls assets/music/ "assets/music/【直接复制】/"`；`grep -n "^## #3" outputs/ep01/feedback-to-upstream.md`

**下次先查**：agent 自检里的「已落盘」不算数，制片人自己 `ls`。

### Bug：PROJECT_STATUS.md 状态过时，和 decisions.md 冲突

**症状**：新会话读 PROJECT_STATUS.md，顶部写「等用户点头资产确认」「等用户重抽卧室 4 张」，Claude 照此汇报「P0 = 用户重抽卧室」。

**根本原因**：10-09 收尾时只往更新日志追加了「卧室 4 张重抽验收通过」，没回头改「当前阶段 / 当前焦点 / 等用户动作 / 待办」四块。实际 `decisions.md` L33 已记 ★资产确认，`assets/visual/images/` 下卧室 4 张是 10-09 19:31–19:33 重抽入库的。

**修复方案**：重写 PROJECT_STATUS 顶部各块；文件头加规则「判进度以 decisions 确认记录 + 盘上产物为准」；WORKFLOW.md 启动流程第 2 步加交叉核对。

**影响文件**：
- `PROJECT_STATUS.md`（L3–L14、待办、日志）
- `WORKFLOW.md`（Claude 工作指引 · 每次启动时）

**验证步骤**：
1. 启动时对比 `decisions.md` 确认记录最后一行和 PROJECT_STATUS「当前阶段」是否一致
2. 按 CLAUDE.md L153–L160 的路由规则核盘上产物，结论应和 PROJECT_STATUS 一致

**排查弯路**：只读 PROJECT_STATUS 就汇报。下次先查 decisions.md 确认记录和盘上产物。

---

## 2026-10-09

### Bug：资产审误报「已过审」，报告未落盘

**症状**：状态里写资产审已过，但 `outputs/ep01/review/art-direction-report.md` 不存在。

**根本原因**：判「审核完成」时没按 CLAUDE.md L160 核盘（审核完成 = 产物在 + review 报告在且 PASS）。具体是哪个环节漏写报告：待确认。

**修复方案**：派 reviewer fresh 实例补审，PASS（blocking 0 / major 4 / minor 7，全部已修）。

**影响文件**：`outputs/ep01/review/art-direction-report.md`

**验证步骤**：说「已过审」之前，先确认 `outputs/ep01/review/` 下对应报告文件存在且判定为 PASS。

### Bug：卧室门把手 160cm，无任何上游出处

**症状**：卧室板写门把手离地 160，只比 150cm 的他头顶高 10cm，尺度错位几乎看不出（资产审 major #2）。

**根本原因**：服化道写数字时没回剧本核对。剧本和讲戏本的依据是「他只到门把手的一半高」「远到不像是给人用的」。

**修复方案**：用户拍板门把手 300cm，门按比例约 6m×2.7m，站姿机位 138cm（decisions.md L31）。

**影响文件**：`assets/visual/scene-prompts.md` 卧室板、`assets/visual/【直接复制】/2–5`、`assets/reference-index.md`、`assets/story/visual-style.md` v1.1 锚句

**验证步骤**：卧室图里门把手应远在画面上方，桌沿压在画框水平中线（10-09 已验收）。

**教训**：改一个数不是改一个数。160→300 连带门尺寸、机位、竖幅装框距离，改任何数字都要查连带项。

### Bug：光中板机位 120cm，和 Cut6 起的坐姿机位对不上

**症状**：光中板覆盖 Cut3–Cut7，但讲戏本 Cut6 起机位降到坐姿高度；Cut8 起点用 120 板、终点用 70 板，在「镜头运动 = 0」的片子里等于暗示一次降机位运镜（资产审 major #1）。

**根本原因**：按光档拆板时没对照讲戏本的机位变化。

**修复方案**：新增「光中 · 坐」板（机位 70cm），覆盖 Cut6、Cut7 和 Cut8 起点；站姿机位统一为 138cm。资产图从 3 张扩到 7 张（decisions.md L32）。

**影响文件**：`assets/visual/scene-prompts.md`、`【直接复制】/4-卧室-光中-坐.txt`、`reference-index.md`、`decisions.md` L32

**验证步骤**：`scene-儿童卧室内-光中-坐.png` 机位 70 平视，桌面成头顶上方一条边。

### Bug：空场景板里有「人」，并且锚句光档词和光档板互斥

**症状**：
1. 空场板换算句写了「一个一百五十公分高的人」「比那个人的头顶还高」（资产审 major #3）
2. 场域锚句里有「他」：「桌沿齐他眼睛」「垂到他头顶以上」
3. 锚句「唯一的暖光是…细缝」和光近板「这道缝宽」打架；「暖光只剩柜门缝里那一条竖线」和光关闭板「暖色面积为零」打架（feedback-to-upstream #2）

**根本原因**：生图模型对提到的人有很强的出画倾向；锚句要求逐字嵌入，服化道不能改，光档词就跟着进了所有板，同一条提示词里互相矛盾，模型取平均。

**修复方案**：正文去掉所有「那个人」，改成纯离地高度；`visual-style.md` 升 v1.1，锚句去人称、去光档，光宽交给各光档板自己写（decisions.md L34）。

**影响文件**：`assets/story/visual-style.md` L52–L53、L115；`assets/visual/scene-prompts.md` 6 张场景板；`【直接复制】/2–7`

**验证步骤**：`grep -n "他\|那个人" assets/visual/【直接复制】/[2-7]*.txt` 应无召唤人物的表述；重抽的卧室 4 张空场无人（10-09 已验收）。

### Bug：人物板「规避版」txt 未登记，删掉了外观锁定项

**症状**：`【直接复制】/1-小宇人物板-规避版.txt` 在 character-prompts.md 无源段，reference-index、changelog 都没登记；删了眉/眼/唇/下颌/发尾锁定项（资产审 major #4）。

**根本原因**：为绕平台拦截临时写了备用版，没走登记，也没守「锁定项不得替换」（visual-style L62）。

**修复方案**：用户拍板用原版，规避版已删（decisions.md L35）。

**影响文件**：`assets/visual/【直接复制】/`（现为 7 个 txt，无规避版）

**验证步骤**：`【直接复制】/` 下只有一个人物板 txt；`character-小宇.png` 只有一张。

### Bug：眉疤文字写右眉，出图在左眉

**症状**：文字设定是「右眉尾」，出图的疤在他的左眉（画面右侧）。

**根本原因**：文字和出图左右不一致；「他的左」和「画面左」容易混。

**修复方案**：以出图为准，全项目改左眉（visual-style / profiles / character-prompts / 讲戏本 / 角色开发 / PROJECT_STATUS），visual-style L114 勘误。

**影响文件**：`assets/story/visual-style.md` L114 等

**验证步骤**：`grep -rn "右眉" assets/ outputs/ script/` 应无残留。

**建议**：以后写左右，同时标「他的左 / 画面右」。

---

## 2026-10-08

### Bug：讲戏本 prop-NNN 编号错位三位 + 死引用 prop-007

**症状**：P01 行的道具编号比权威表整体错位三位（排名纸 002→005、手机 005→006、纸箱 006→007），`prop-007` 在权威表中不存在（feedback-to-upstream #1）。

**根本原因**：导演写 P01 行时按出现顺序顺手编号，没回表核对。

**修复方案**：采纳建议 1，L44、L314 两行三处对回权威表；表头加「编号性质说明」块，写明 prop-NNN 是讲戏本内部记号、不是 reference-index 项目编号。

**影响文件**：`outputs/ep01/01-director-analysis.md` L44、L314、关键道具清单表头

**验证步骤**：全文 12 处 `prop-NNN` 逐个对权威表；`grep -n "prop-007" outputs/ep01/01-director-analysis.md` 应为 0 处。
