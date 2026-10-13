---
name: image-edit-template
description: 当你要给一张已生成的资产图或控制图写编辑指令时套它。给手术式编辑、中文直用、纹理修复、delta 状态变体、改输入五档可填空母版与填写纪律。
---

# 图像编辑指令母版

## 使用说明

- 图像手术式编辑母版，出口 2 与出口 4 用，属图像规则集。按症状选一档母版填空，{{}} 内为填空位，按本图实情填，用不到的档整块删除。
- 填空原则：CHANGE 越小越干净，PRESERVE 越穷举越安全。一次一改；删除必配填补。
- 执行后与原图并排对照，逐条扫 PRESERVE 项验收。
- 版本注记：[vN · YYYY-MM-DD · 症状：{{一句}} · 出口：{{2 或 4}} · 改动：{{一句话，含旧值}}]。
- 状态变体另登记 assets/ 对应文件与 reference-index，编号 -vN、永不覆盖原版。

## 手术式编辑母版 · 英文骨架，编辑链通用

```
Edit the image: {{一句话目标}}.

CHANGE: {{唯一变化，精确到位置与目标状态；删除时含填补物}}.

PRESERVE EXACTLY:
- {{穷举清单，按本图实际内容逐项列：face 五官、clothing 服装、props 道具、positions 位置关系、wall & floor 墙面地面、camera angle 机位角度、all existing shadows 全部既有阴影}}
- Color grade, palette, contrast, grain, falloff

ONLY CHANGE: {{重申唯一变化}}.
100% identical otherwise.
```

Color grade 那一行即调色、色板、对比度、颗粒、光衰减，整行照抄、不删。

## 中文直用母版 · 生成侧不便用英文时

```
编辑这张图：{{一句话目标}}。
只改：{{唯一变化；删除时写明原位由什么自然填补}}。
以下必须逐项保持完全一致：{{五官、服装、道具、位置关系、背景结构、机位角度、全部既有阴影，逐项列}}；调色、色板、对比度、颗粒、光衰减全部不变。
重申：只改{{那一处}}，其余部分百分之百一致。
```

## 纹理修复母版 · 质感假、图成立

```
Edit the image: revive the sloppy AI textures only.
CHANGE: {{只列表面项，选本图需要的：skin pores 皮肤毛孔、fabric weave 织物织纹、surface dirt and wear 表面尘埃与磨损}}.
PRESERVE EXACTLY: composition, identity, facial features, lighting, color grade——即构图、身份、五官、光线、调色，全部锁死。
ONLY CHANGE: the listed surface textures. 100% identical otherwise.
```

本通道内不做任何点位编辑；改道具或删物体另开 「手术式编辑母版 · 英文骨架，编辑链通用」。

## delta 状态变体母版 · 新状态 = 编辑产物，不重跑底图

```
Edit the image: create the {{状态名：带伤/湿身/战损/夜版}} variant of {{char/scene/prop-NNN}}.
CHANGE: {{只列状态差异，如加左眉骨挫伤与领口血渍、打湿头发与肩部布料并加垂坠感}}.
PRESERVE EXACTLY: {{底图其余一切——五官、发型、服装未变部分、姿态、背景中灰底、光线}}; color grade, palette, contrast, grain.
ONLY CHANGE: the listed state differences. 100% identical otherwise.
```

执行后三步：1 与原版并排验证同一身份；2 登记 char/scene/prop-NNN-vN 进 assets/ 对应文件与 reference-index；3 原版保留不覆盖。

## 改输入母版 · 倒置与预摆姿态 · 出口 4

- 倒置图：无需编辑指令——把 char-NNN 的表或关键帧整体旋转 180° 存为新文件，登记 char-NNN-vN 倒置态。视频条改为引用该变体，prompt 放松为只钉锚点：只写关键位置锚 + 运动因果，不再满帧描述物理。
- 预摆姿态：用「手术式编辑母版 · 英文骨架，编辑链通用」把关键帧中人物改到目标姿态。

```
CHANGE: {{repose the figure to 目标姿态，如 mid-swing 挥拳中段、跪地撑臂，写清四肢位置与重心}}.
PRESERVE EXACTLY: 身份、服装、背景、光线、机位；调色行照抄。
```

产出作为该条的首帧或关键帧输入，以图定姿、以词定动。
