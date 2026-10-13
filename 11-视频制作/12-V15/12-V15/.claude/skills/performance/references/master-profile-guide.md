---
name: master-profile-guide
description: 当你为核心角色建表演档案、或要把档案重写进某场戏时翻它。给母版块序、八条写作规则判据卡、眼活规范、声线边界、场景适配规则与标杆全文。
---

[定位]
    本卡是角色表演档案（master profile）的完整写法卡：母版块序、八条写作规则判据卡、眼活规范、声线边界、场景适配规则与标杆全文。为核心角色建档、或要把档案重写进某场戏时，翻开本卡。
    档案是"这个角色怎么演"的唯一真相源：写一次，登 assets/visual/character-prompts.md 该角色条目的「表演档案」段；使用方式是每场重写适配，永不整段粘贴。填空母版见 templates/master-profile-template.md。

[母版与块序 · 顺序固定]
    Character acting as {{NAME}}.（角色表演档案——某某。）
    体格即传记：年龄、体型、体格、体态——身体是履历的文件，职业、旧伤、自我认知都要能从中读出，如"当过拳手的厚脖子、中年后腰腹发福""为立威而过度矫正的坐姿"。
    一句话心理引擎：解释这具身体一切行为的内在驱动，一个从句说完，如"几十年的等待——等活儿、等回合、等麻烦——把耐心磨成了他的武器"。
    说话行为（Vocal profile）：音高音色、口音出身、语速与交付方式、情绪压力下声音怎么变——写的是戏剧行为，不是声线本体，边界见下文。
    习惯动作与 tic：招牌 tic + 触发器；压力 tic + 触发器；掩饰行为——他用什么动作藏住感受；默认面具 + 面具破裂的精确条件。
    步态（Walking style）：命名的步态——引号内造词，再拆解生物力学：重量、步幅、躯干与手臂、头。
    转变条款：However, when {{情绪触发器}}, {{transformation}}——体态、步态、脸怎么变。每份档案至少一条。
    唯一软化目标，可选：让这张脸真正柔软下来的那一个人、动物或物件。只给一个。
    长度：一段流水散文，无列表、无标题；密度对标 [标杆档案全文] 的 VIKTOR——删无可删，不为凑段注水。

[判据卡 · 八条写作规则]
    只写可观察行为
        怎么认：
            每个内在状态都配一个身体标记，摄影机拍得到。
        认错长什么样：
            「他很紧张」「他内心矛盾」——内心拍不到，模型只会给一张空脸。
        典型例子：
            反例「他很紧张」 → 正例「下唇微颤，一次沉重的吞咽，用嘴长吸一口气、再从抿紧的唇间短促吐出」。
    每个 tic 必带触发器
        怎么认：
            {{tic}} + {{何时/为何}} 成对出现。无触发器的 tic 是装饰，有触发器的是戏。
        认错长什么样：
            「他爱掰指节」——什么时候掰？为什么掰？没有答案就是贴纸。
        典型例子：
            正例「在无关紧要的寒暄里掰响指节——用来伪装从容」。
    步态要命名
        怎么认：
            引号内一个自造的名字锚住生物力学，再拆解：重量、步幅、躯干手臂、头。
        认错长什么样：
            「走路很有气势」——没有名字、没有力学，模型自由发挥。
        典型例子：
            「老拳手步」（"old boxer's walk"）——沉、滚动，步幅短而经济，双肩持平，双手松弛备战，从不赶路。
    面具 + 裂缝必有
        怎么认：
            默认面具（facade） + 让它塌掉的精确触发器，写成 However, when X 条款。同时演两个真相，是木偶与人的分界。
        认错长什么样：
            从头到尾一张脸，即无面具；或裂缝无条件随时裂——无面具的另一种写法。
        典型例子：
            不可一世的横步，被拒绝的一瞬塌成孩子式的驼背；训人的铁面，只在某一个人面前融成毫无防备的笑。
    唯一软化目标
        怎么认：
            只给一个人、动物或物件。一个即人性化，两个即稀释。
        认错长什么样：
            「他对家人和老朋友都很温柔」——软化面一宽，人物立刻变糊。
        典型例子：
            他的脸只为流浪狗真正柔软——他用大衣口袋里的东西喂它们。
    禁服装
        怎么认：
            档案在任何换装下都成立。服装住在资产与场景块里。
        认错长什么样：
            档案里写"总穿一件旧皮衣"——换装那集档案就作废。
    禁镜头、禁调色
        怎么认：
            档案只驱动脸、声音行为、动作；机位、景别、调色、光住在提示词别处。
        认错长什么样：
            档案里写"适合大特写""冷色调下更有味道"。
    体格即传记
        怎么认：
            年龄、体型、体态的每个选择都在讲前史——职业、旧伤、自我认知可从身体读出。
        认错长什么样：
            体格与履历打架——街头混混长着舞者的挺拔体态，却没有任何解释。
        典型例子：
            「因常年伏案而前倾的颈椎、握笔处的茧」——不用说他是老会计，身体已经说了。

[眼活规范 · 写进每份档案，逐场重表达；死眼是 AI 表演头号破绽]
    微跳视 + 具名注视目标：视线永远有对象，在目标间扫动、停驻、弹回，绝不锁死一点。
    眨眼率与质感随状态：紧张连眨、掌控慢眨、失神一眨后散焦。
    活的 catchlights：眼睛读作湿润、受光、活着。
    受控的静止是选择："Controlled stillness is chosen, never dead."（受控的静止是选出来的，不是死掉的。）近乎不眨的捕食者式平静，要写成罕见、缓慢、蓄意的眨——一个决定，不是一次冻结；目光仍带意图地缓慢移动。
    眼先于头：视线先到目标，头随后才转；话没出口，想法已先在眼睛里可读。
    眼活随变拍走：眨眼率、注视稳定度、目光温度随节拍一起变。

[声线边界]
    档案内的"说话行为"写戏剧变化：何时变慢、何时更轻、压力下声音在哪里破。
    声线锁是另一样东西：声音本体的书面条件——音区、音色、语速、口音、语气，由 character-design 登记在 assets/reference-index.md，由 motion-compile 的声音四要素逐字引用。"Voice is locked … never modify it per scene."（表演逐场重写；声线永不适配。）声线锁改一个同义词都是漂移风险。
    两者必须相合：档案说"越严肃越轻"，声线锁就不能写"急了会吼"。冲突时以声线锁为准，回改档案。

[场景适配规则 · 档案是"他是谁"，每场把它重写成"他此刻在做什么"]
    只写在场者：不在画面里的角色没有段落。
    恒定核不动：身份、说话行为、招牌 tic、眼活、情绪贯穿线每场一致——这是跨镜头"认得出同一个人在演"的锚，永不与档案矛盾。
    按本场重表达：按本场的坐/站/跑/躲姿态、动作与节拍、情绪状态、时段，选取、强调、改写或按下档案里的具体行为。
    转移不删除：本场做不了的行为转移进可行通道——踱步者坐上沙发，同一股神经能量转入微晃、甩腕、撕纸。能量恒定，出口改变。
    一段流水散文：无列表、无标题、无"参数"式行；以该角色的可视特征代称开头，如"眉骨带旧疤的老司机坐在驾驶座上……"，让模型把表演绑到正确的人身上；@编号只在成品条的【参考资产绑定】段出现一次，重复 @tag 是平台拒绝启动的头号原因，重场对白戏每条必中。

[标杆档案全文 · 英文原文 + 逐块解析]
    下面这段原样保留，作直接套用的密度标尺——写到它这个量级。
    英文原句：Character acting as VIKTOR. Early 60s male, a retired night-shift taxi driver and former amateur boxer; heavy, thick-necked build gone soft at the middle, with a flat-nosed face and old scar tissue over both eyebrows; sits and stands with a low, grounded center of gravity, weight always on the whole foot. Runs on a single engine: decades of waiting — for fares, for rounds, for trouble — have made patience his weapon. Vocal profile: low, hoarse, unhurried baritone with a working-class rasp, short sentences delivered flat and economical, dropping to a slower, quieter register the more serious things get — he never speeds up. Key physical habits and tics: rolls an old coin across his knuckles when sizing a situation up; a slow, audible nose-breath before he says no; when lying is happening in front of him, he goes completely still and lets a long silence do the pressing; his default face is a heavy-lidded, bored mask that conceals total attention. Eye life: sleepy, hooded eyes with slow deliberate blinks and constant quiet scanning — mirrors, hands, exits — the gaze settling on a speaker a beat before his head turns; catchlights low but alive. Walking style: a heavy, rolling "old boxer's walk," short economical steps, shoulders level, hands loose and ready, never hurrying. However, when someone raises a hand near him, the sleepy mask vanishes in a half-second: the chin drops, the hands rise halfway, the feet find their old stance — then he catches himself and folds it away, embarrassed. His face only truly softens for stray dogs, which he feeds from his coat pocket.
    逐块解析：
        体格即传记：夜班车 + 业余拳击两段履历全写在身体上——厚脖子、塌鼻梁、眉骨疤、低重心、全脚掌落地。
        心理引擎一句话："几十年的等待把耐心磨成了武器"——后面每个 tic 都由它解释。
        说话行为：越严肃越慢越轻、从不加速——给了压力下的声音方向，与声线锁一致。
        tic 全带触发器：硬币过指节 = 打量局面时；可闻的鼻息 = 说"不"之前；彻底静止 + 长 silence = 面前有人说谎时；面具 = 重眼皮的无聊相，藏着全部注意力。
        步态命名："老拳手步" + 力学拆解：沉、滚动、步幅短、肩平、手松弛备战。
        转变条款：有人在他附近抬手 → 半秒内面具消失、下颌收、双手半抬、脚找回旧站位——然后他自己收住、有点难堪。裂缝裂完还自己合上，一条条款演出两个真相。
        软化目标唯一：流浪狗。一个。
    场景适配标杆——夜间出租车内，后座年轻乘客在为车费撒谎：
        下面这段示范中文散文形态：以可视特征代称开头，全段不出现 @编号。
        中文块，可整块抄：眉骨带旧疤的老司机沉沉地坐在驾驶座里，不回头，从后视镜里看乘客——低垂的眼皮下，视线在镜子、对方的手、门锁之间缓慢安静地扫动，眨眼罕见而蓄意，目光先落在镜中人身上、头过了一拍才微微偏转。那枚旧硬币在椅背旁的指节间不紧不慢地走；随着乘客的说辞越编越漏，硬币在指节中段停住——他让沉默压上去，用鼻子缓慢地、可闻地吸了一口气，然后用低哑的男中音开口，比刚才更平、更轻，从不加速。直到那孩子声音发颤，昏昏欲睡的面具才松动一分：一次长长的呼气、一次缓慢的眨眼、硬币重新滚动——耐心暂且选择了仁慈。
        解析——为什么这么改写：开头是可视特征代称不是 @编号，@ 只在【参考资产绑定】段出现一次；步态无关、人在坐姿 → 步态的能量转入静止与硬币；tic 全部保住触发器——硬币 = 打量、硬币停 = 打断动作做标点、鼻息 = 拒绝、静止 + 沉默 = 对说谎者施压；眼活服从档案但重新锁靶到后视镜、手、门锁；变拍可见——硬币停 → 沉默 → 更轻的嗓音 → 松动；说话行为未违档案；声线锁一字未动——它由声音四要素逐字引用。

[落盘与登记]
    落盘：assets/visual/character-prompts.md 该角色条目下「表演档案」段——档案与出图提示词同条目不同段，互不混写：出图段走图像规则集，档案段属视频侧素材。
    登记：assets/reference-index.md 该角色行加指针，如"表演档案：见 character-prompts.md @char-NNN 表演档案段"。
    建档时机：character-design 建核心角色时同步建；后续集新核心角色登场时同步补。边角角色不建档，用五支柱现场推。
    变体与档案：char-NNN-vN 这类角色状态变体不另建档案——档案写的是人，不是状态；跨场损耗与落幅情绪记 assets/continuity-ledger.md，由下一场的场景适配段承接。
