---
name: ugc-texture
description: 当本片片型是 UGC/vlog/生活流/带货短视频、要在恒定层写媒介质感块、或要把"拍出来像真人随手拍"写进提示词时翻它。媒介质感六字段公式、flip-camera/手机/DV 词库块、反摆拍表演词、UGC 声音配方与收尾。
---

> 📌 **V14 适配说明**（本卡移植自 Seedance 分镜师 3.0，术语与数字按下表换算）：
> - **条 = Cut**（一条提示词 = 一个生成单元）；**场 ≈ P0X 剧情点**；「镜头N」= Cut 内分镜，含义不变
> - 文中出现的 **Seedance 2.5 / 单条 30s / 4–30s** 均为源库历史数字：V14 一律以 `.project-config.json.video_model_config` 的 `primary_model / min_seconds / max_seconds` 为准，换模型只改配置
> - 镜头表 = `outputs/<集数>/02-shot-table.md`；视频提示词 = `outputs/<集数>/video-prompts.md`；资产索引 = `assets/reference-index.md`；风格基准 = `assets/story/visual-style.md`（缺失时读 `creative-brief.md` 的全片视觉风格基准段）
> - 调用者：分镜师编 UGC/vlog 片型媒介质感块时。UGC/vlog 属延展片型，主场是精品微电影与 MV。

[定位]
    UGC 质感不是"降低质量"，是另一套精确的媒介语言：抖动、裁切、对焦犹豫都是要显式写出的正向指令。片型 = UGC/vlog 时，媒介质感块进恒定层 F1 第 3 段，替代电影级视觉语言的位置；全局尾缀加 UGC 附加项：无商业广告感、无平台尾页。
    UGC 条默认 A 轨 + 松档——时间戳分段 + 镜头自由度边界声明——详 dual-track.md。

[媒介质感六字段公式]
    媒介质感块 = 拍摄设备或影像媒介 + 构图特征 + 摄影机运动质感 + 光线条件 + 成像纹理 + 真实程度。
    六字段一句不缺，各给具体词——写"手机拍摄的真实感"只占一个字段、没用，要写满六个维度。

[词库块 · 按设备挑一块，双语保留、可整块入恒定层]
    翻盖机/late-2000s 家用机块：
        中文块，可整块抄：极生涩的手持翻盖机画面：重度晃动、自然重新取景、局部裁脸、对焦犹豫、曝光偏移、暖调褪色、轻微数字噪点、家庭录像式的真实瑕疵。
        英文原句：Extremely raw handheld flip-camera footage with heavy camera shake, natural reframing, partial face crops, focus hunting, exposure shifts, warm faded colors, mild digital noise, and authentic home-video imperfections.
    手机随手拍块：
        中文块，可整块抄：写实手机画面：轻微倾斜、自然晃动、窗边自然光、轻微颗粒。
        英文原句：Photorealistic phone footage with slight tilt, natural shake, window light, subtle film grain.
    朋友跟拍 vlog 块：
        中文块，可整块抄：镜头像一台真实的私人 vlog 相机而非商业制作：自然手持、随意取景、不完美的人手运镜、真实日常氛围；由朋友跟拍主角。
        英文原句：The camera feels like a real personal vlog camera, not a commercial production. Natural handheld movement, casual framing, imperfect human camera motion, authentic everyday atmosphere. Filmed by a friend following the main character.
    DV/家庭录像块：轻微磁带噪点、偶发白平衡漂移、变焦时的马达顿挫、日期角标位置留空不渲染文字。
    观察式纪录片块：长镜观察、变焦代替走位、构图迟半拍跟上事件、无摆位痕迹。
    认错长什么样：
        UGC 条里混进电影级词——"电影感构图、35mm、浅景深、轨道缓推"——质感立刻崩回广告片；或反过来把 UGC 抖动块带进正片条。两套媒介语言互斥，恒定层只装一套。

[反摆拍表演词 · 写进分镜正文]
    - 总声明："No scripted acting."（无剧本式表演。）人物自然行动、与环境真实互动，像真的在拍 vlog。
    - 对白方式：自然口语、对当下事件即时反应、非背诵式台词、非广告式表演；台词短、可以笑场、可以说半句。
    - 行为质感：整理头发、看手机、对镜头笑再移开视线、被环境吸引注意力——允许"无戏剧目的"的真实小动作。
    - 人物数量锁："She is the only person in the video."（她是视频中唯一的人物。）单人 vlog 必带，防乱入。

[UGC 声音配方]
    - 环境声穷举正向声明，列 6–10 个具体声源、越具体越稳：鸟叫、棕榈叶沙沙、砍椰子声、脚步、微风、远处笑声、洗衣机收尾的嗡鸣、湿布料声、衣夹咔嗒。
    - 人物反应声：呼吸、笑声、叹气、自言自语。
    - BGM 指令：通常「无任何背景音乐」（Natural ambience only. No background music.）——UGC 的真实感一半靠环境声裸奔。
    - 对白语言指定：自然规范的{{语种}}口语；例外句单列，如"除 'Good enough.' 一句为英文外，其余为自然韩语口语"。

[UGC 收尾配方]
    自然结束录制感：转回镜头、挥手、说告别句，"before naturally ending the recording"（随后自然结束录制）；或动作收尾——挂完最后一件衣服、安静欣赏成果。
    禁止：戏剧化定格、切黑、任何像"片尾"的东西——尾缀带 无平台尾页、无账号界面、无商业广告感。

[典型例子 · 30s 旅行 vlog 的段落骨架，供对标]
    [0-5秒] 清晨出门：背小包出公寓，看一眼手机，对镜头笑，边走边整理头发；镜头从背后跟拍、轻微晃动。晨光、安静街区。
    [5-12秒] 城市漫步：穿过本地街巷，买杯饮料，对镜头随口说两句，自然地笑；镜头贴近，抓即兴瞬间。
    [12-20秒] 抵达海边：城市街景渐变为海滨小镇，海风吹动头发，看到海露出兴奋表情；捡一枚贝壳。
    [20-27秒] 海滩下午：和朋友汇合，聊天、大笑、玩水；镜头在人之间自然移动，她回头对镜头笑。
    [27-30秒] 结尾时刻：金色黄昏，她坐在海边举着饮料看日落；镜头缓缓后移，露出海滩与平静的傍晚。
    收尾负向串，尾缀 + 质感锁：无商业电影感、无戏剧性摆拍、无人工转场、无字幕、无 Logo、无换脸。
