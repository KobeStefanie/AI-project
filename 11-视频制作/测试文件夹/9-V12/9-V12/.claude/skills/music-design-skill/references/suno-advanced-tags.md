# Suno 进阶 Meta-tag 大全

> SKILL.md 第七节的 Meta-tag 是基础版。本文是进阶版——当你想精确控制 Suno 输出时使用。
> 灵感参考 anthropic skill-creator 中的 songwriting skill（英文），针对中文项目和影视配乐需求调优。

---

## 一、结构标签（控制歌曲段落）

### 基础结构

| 标签 | 用途 | 备注 |
|------|------|------|
| `[Intro]` | 开场前奏（一般 4-8 小节） | 可不加，Suno 会自动加 |
| `[Verse]` `[Verse 1]` `[Verse 2]` | 主歌 | 写故事/铺陈的部分 |
| `[Pre-Chorus]` | 副歌前的过渡段 | 拉张力，常用于流行歌 |
| `[Chorus]` | 副歌（核心记忆点） | 反复出现，每次内容可微调 |
| `[Post-Chorus]` | 副歌后的延续段 | 让副歌余韵延长 |
| `[Hook]` | 钩子段 | 通常是单句或单乐句，记忆点强 |
| `[Bridge]` | 桥段（转折/视角切换） | 副歌前的"另一个世界" |
| `[Interlude]` | 间奏 | 有词或无词都行 |
| `[Instrumental]` | 纯演奏段 | 无人声 |
| `[Instrumental Break]` | 间奏休止 | 多用于现场感 |
| `[Guitar Solo]` `[Piano Solo]` `[Solo]` | 乐器独奏 | 指定乐器 |
| `[Breakdown]` | 简化段（拆解层次） | 电子/嘻哈常用 |
| `[Build-up]` | 累积段 | 准备 drop 或高潮 |
| `[Drop]` | 副歌爆发点 | EDM/电子 |
| `[Outro]` | 收尾 | 可加 [Soft Outro]、[Fade Out] |
| `[End]` | 强制结束 | 适用于戛然而止 |

### 影视配乐专用结构

| 标签 | 用途 |
|------|------|
| `[Climax]` | 情绪最高点 |
| `[Soft Outro]` | 情绪缓缓退去 |
| `[Sustained]` | 持续/拖长的尾音 |
| `[Silence]` | 静默（Suno 会留空 1-2 秒）|
| `[Tension Build]` | 紧张感累积 |
| `[Release]` | 紧张释放 |
| `[Cinematic Swell]` | 电影感渐强 |

---

## 二、人声表演标签

控制人声的演唱方式：

| 标签 | 含义 |
|------|------|
| `[Whispered]` | 耳语 |
| `[Spoken Word]` | 念白（不唱） |
| `[Sung]` | 演唱 |
| `[Belted]` | 大声、有力地唱 |
| `[Falsetto]` | 假声 |
| `[Head Voice]` | 头声 |
| `[Chest Voice]` | 胸声 |
| `[Powerful]` | 有力 |
| `[Soulful]` | 灵魂感 |
| `[Raspy]` | 沙哑 |
| `[Breathy]` | 气声 |
| `[Smooth]` | 平滑 |
| `[Gritty]` | 粗粝 |
| `[Staccato]` | 断奏 |
| `[Legato]` | 连奏 |
| `[Vibrato]` | 颤音 |
| `[Melismatic]` | 装饰音多 |
| `[Harmonies]` | 和声 |
| `[Choir]` | 合唱 |
| `[Harmonized Chorus]` | 副歌做和声化 |

---

## 三、动态/能量标签

控制段落的能量曲线：

| 标签 | 含义 |
|------|------|
| `[High Energy]` | 高能量 |
| `[Low Energy]` | 低能量 |
| `[Building Energy]` | 能量累积中 |
| `[Explosive]` | 爆发 |
| `[Emotional Climax]` | 情绪高潮 |
| `[Gradual swell]` | 缓慢渐强 |
| `[Orchestral swell]` | 管弦渐强 |
| `[Quiet arrangement]` | 安静的编配 |
| `[Falling tension]` | 张力下降 |
| `[Slow Down]` | 减速 |
| `[Speed Up]` | 加速 |

---

## 四、性别/音色

| 标签 | 含义 |
|------|------|
| `[Female Vocals]` | 女声 |
| `[Male Vocals]` | 男声 |
| `[Female Lead, Male Backing]` | 女主男和 |
| `[Duet]` | 男女对唱 |
| `[Children's Choir]` | 童声合唱 |
| `[Mixed Choir]` | 混声合唱 |

---

## 五、氛围标签

| 标签 | 含义 |
|------|------|
| `[Melancholic]` | 忧郁 |
| `[Euphoric]` | 狂喜 |
| `[Nostalgic]` | 怀旧 |
| `[Aggressive]` | 激进 |
| `[Dreamy]` | 梦幻 |
| `[Intimate]` | 亲密 |
| `[Dark Atmosphere]` | 黑暗氛围 |
| `[Hopeful]` | 充满希望 |
| `[Bittersweet]` | 苦乐参半 |
| `[Ominous]` | 不祥 |
| `[Triumphant]` | 凯旋 |

---

## 六、音效/环境标签

| 标签 | 含义 |
|------|------|
| `[Vinyl Crackle]` | 黑胶噪点 |
| `[Rain]` | 雨声 |
| `[Applause]` | 掌声 |
| `[Static]` | 静电噪音 |
| `[Thunder]` | 雷声 |
| `[Wind]` | 风声 |
| `[Footsteps]` | 脚步声 |
| `[Heartbeat]` | 心跳声 |
| `[Clock Ticking]` | 钟表滴答 |
| `[Ambient Noise]` | 环境噪音 |

---

## 七、动态曲线设计：Energy Mapping

歌曲不是平的，是一条曲线。设计能量曲线能让 Suno 生成的歌"有起伏感"。

**典型流行歌曲能量曲线**（1-10 量化）：

| 段落 | 能量 |
|------|------|
| Intro | 2-3 |
| Verse 1 | 5-6 |
| Pre-Chorus | 7 |
| Chorus | 8-9 |
| Verse 2 | 6-7（比 V1 稍高） |
| Pre-Chorus | 7-8 |
| Chorus | 9 |
| Bridge | 4-5（拆解，为最终爆发蓄力） |
| Final Chorus | 9-10 |
| Outro | 5 → 2（缓缓退去）|

**最重要的动态范式：Whisper to Roar to Whisper**

开场用耳语般的低能量，渐渐推到全力咆哮，最后回到耳语收尾。这种"V 型"曲线最能打动人心。

**应用到 Style 描述**：

```
Style: melancholic indie-folk, intimate fingerpicked acoustic guitar, breathy female vocal,
60 BPM. Begins as a whispered confession over sparse guitar. Gradually adds layers—
strings entering in second verse, percussion in pre-chorus. Final chorus erupts with full
orchestra and belted vocals. Outro strips back to a lone piano and fading whisper.
```

这比 `Style: sad folk song` 强 10 倍——因为告诉了 Suno **能量怎么走**。

---

## 八、中文项目的特殊提示

### 8.1 中文 Suno 生成提示

Suno 对中文的支持在不断改善，但有些细节需要注意：

1. **多音字**：在歌词中遇到多音字（"得"/"的"/"地"），尽量按发音改写
   - 例：「我得（dé）到了」改成「我得（děi）到了」时，Suno 容易混淆。
   - 解决：在 Style 描述中加一句 `(use Mandarin pronunciation: 得 should be pronounced as "děi" in this context)`

2. **儿化音**：北方方言的儿化音（"小事儿"）Suno 可能直接生成成"小事 + 儿"两个音
   - 解决：在歌词里直接写连读音 "小事儿" → "小事er" 或保持原样让 Suno 自动处理（多数时候没问题）

3. **入声字**：粤语项目中的入声字
   - 解决：在 Style 中明确写 `Cantonese pronunciation` 或用拼音注释

### 8.2 中文 metatags 风格混合

可以中英文混用，但建议：
- 段落标签用英文（[Verse 1]、[Chorus]）—— 这是 Suno 的标准
- 演唱风格标签可以中英结合（如 [Whispered, 气声唱法]、[Belted, 高亢]）

### 8.3 中文项目的"金句位置"

中文歌的金句（钩子）通常出现在：
1. **副歌的第一句**（"我想念你"、"再见再见"）
2. **副歌的最后一句**（落点 / 情绪回落）
3. **Pre-Chorus 的最后一句**（拉张力到副歌）

设计歌词时，把最打动你的那句放在这些位置之一。

---

## 九、纯配乐（Instrumental）的进阶用法

纯配乐没有歌词，但仍可以用 metatags 控制结构：

```
[Intro - Sparse Piano]
[Theme Statement - Solo Cello]
[Build-up - Adding Strings]
[Climax - Full Orchestra]
[Variation - Solo Violin]
[Final Statement - Full Orchestra Forte]
[Outro - Piano Solo, Fading]
```

把音乐当成一个无言的故事讲——每段是叙事中的一段。

---

## 十、与 SKILL.md 主体的关系

- SKILL.md 第七节给出**基础 metatags**——日常使用就够
- 本文给出**进阶 metatags**——当需要精确控制时调用
- 实际产出时，**不要塞太多 tag**（每段 5-8 个是上限），太多会让 Suno 困惑

**一句话原则**：tag 服务于"动态弧线"，不为了显得专业而堆砌。
