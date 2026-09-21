# Phase 4 — 对话模拟训练系统 实施计划 v2.0

**创建时间**：2026-09-04  
**版本**：v2.0（根据用户反馈重新设计）  
**核心变更**：独立训练数据目录 + 虚拟来访者支持 + 全局规则遵循

---

## 🎯 用户明确需求

1. **训练数据独立存储（方案A）** — 即使原始档案删除/修改，训练记录不受影响
2. **督导评估使用Opus** — 质量优先，后期可升级更好模型
3. **虚拟来访者功能独立** — 针对特定课题修改案例后再次模拟是常见场景
4. **遵循全局CLAUDE规则** — 不编造数据、严格验证、遵循WORKFLOW

---

## 一、系统概述

### 核心理念
对话模拟训练系统是**独立的训练模块**，基于真实/虚拟来访者进行实战演练，训练记录与原始档案解耦。

### 四大核心功能

| 功能 | 说明 | 技术实现 |
|------|------|---------|
| **AI扮演来访者** | 基于人设生成一致的对话角色 | Claude Opus + 人设Prompt |
| **我扮演咨询师** | 用户实时输入咨询回应 | 三栏对话界面 + SSE流式输出 |
| **AI实时督导** | 对话过程中评估技术质量 | 异步评估 + 浮窗提示（Opus） |
| **录音回放与复盘** | 对话结束后生成完整报告 | 存储JSON + AI生成报告 |

---

## 二、数据结构设计（⭐ 核心变更）

### 2.1 独立目录结构

```
data/
  training_sessions/              # ⭐ 新增：独立训练数据目录
    session_20260904_001.json     # 训练记录1
    session_20260904_002.json     # 训练记录2
    ...
  
  training_personas/              # ⭐ 新增：虚拟来访者人设库
    persona_custom_001.json       # 自定义虚拟人设1
    persona_custom_002.json       # 自定义虚拟人设2
    ...
  
  visitors/                        # 已有：真实来访者档案
    V20260522001/
      profile.json
      visits/
        visit_001.json
```

**设计理由**：
1. ✅ 训练数据与真实档案完全解耦
2. ✅ 删除/修改真实档案不影响训练记录
3. ✅ 支持基于真实档案生成人设，也支持完全虚拟的人设
4. ✅ 未来可导出训练记录用于教学/分享

---

### 2.2 session JSON 数据结构

```json
{
  "session_id": "session_20260904_001",
  "created_at": "2026-09-04T23:00:00",
  "duration_seconds": 850,
  "approach": "存在主义",
  "model_used": "claude-opus-4-8",
  
  "persona_source": {
    "type": "real_visitor",           // 或 "virtual_custom"
    "visitor_id": "V20260522001",     // 如果是真实来访者
    "visit_id": "visit_001",          // 如果基于某次来访
    "persona_file": null              // 如果是虚拟人设，指向persona_custom_XXX.json
  },
  
  "visitor_persona": {
    "name": "李先生（匿名）",
    "age": 50,
    "gender": "男",
    "core_issues": ["妻子癌症去世", "本人确诊癌症", "存在性绝望"],
    "emotional_state": "抑郁、绝望、气若游丝",
    "key_phrases": ["活不下去了", "为什么这种事落在我头上", "我也想活呀"],
    "background_summary": "妻子去年癌症晚期去世，上个月本人确诊癌症...",
    "defense_mechanisms": ["否认", "隔离情感"],
    "expectations": {
      "explicit": "想知道怎么活下去",
      "implicit": "希望被理解、被陪伴"
    }
  },
  
  "dialogue": [
    {
      "seq": 1,
      "role": "counselor",
      "content": "李先生您好，今天想和我聊些什么呢？",
      "timestamp": "2026-09-04T23:00:15",
      "supervision_feedback": null
    },
    {
      "seq": 2,
      "role": "client",
      "content": "（叹气）我...我不知道该说什么...就是觉得活不下去了...",
      "timestamp": "2026-09-04T23:00:35"
    },
    {
      "seq": 3,
      "role": "counselor",
      "content": "听起来您感到非常绝望...",
      "timestamp": "2026-09-04T23:01:10",
      "supervision_feedback": {
        "technique_used": "简单反映",
        "quality_score": 6,
        "comment": "识别到情绪，但可以更深入共情具体感受",
        "better_example": "听起来您现在感到非常绝望...（停顿等待）能和我说说，'活不下去'这种感觉是什么样的吗？"
      }
    }
  ],
  
  "final_report": {
    "overall_score": 75,
    "total_turns": 18,
    "techniques_summary": [
      {"technique": "简单反映", "count": 5, "avg_score": 6.4},
      {"technique": "开放式提问", "count": 3, "avg_score": 7.2},
      {"technique": "深度共情", "count": 2, "avg_score": 8.0}
    ],
    "highlights": ["第7轮的存在性探索切入点准确", "第12轮共情到位，来访者明显放松"],
    "core_issues": ["过早给建议（第4轮）", "未追问'为什么'背后的存在意义"],
    "improvement_suggestions": {
      "P0": ["避免在前5轮给建议，先建立关系"],
      "P1": ["练习'空椅子技术'处理未竟事宜（妻子去世）"],
      "P2": ["丰富反映技术的词汇库，避免重复'听起来'"]
    },
    "next_training_focus": "存在主义技术：引导来访者探索'活'的意义，而非解决'怎么活'"
  },
  
  "cost_info": {
    "total_input_tokens": 28500,
    "total_output_tokens": 15200,
    "estimated_cost_usd": 1.56
  }
}
```

---

### 2.3 虚拟人设 JSON 数据结构

```json
{
  "persona_id": "persona_custom_001",
  "created_at": "2026-09-05T10:00:00",
  "created_by": "user",
  "tags": ["青少年", "校园霸凌", "自杀意念"],
  
  "persona": {
    "name": "小雨（化名）",
    "age": 15,
    "gender": "女",
    "core_issues": ["校园霸凌", "自杀意念", "父母期待"],
    "emotional_state": "麻木、无望、回避",
    "key_phrases": ["都是我的错", "他们说的对", "我不想上学了"],
    "background_summary": "初三女生，成绩中等偏上，半年前开始遭受校园霸凌，父母不理解...",
    "defense_mechanisms": ["内化攻击", "自我贬低"],
    "expectations": {
      "explicit": "希望咨询师告诉她怎么办",
      "implicit": "希望有人相信她、站在她这边"
    }
  },
  
  "training_notes": "用于练习危机干预技术，重点评估自杀风险等级"
}
```

---

## 三、系统架构设计

### 3.1 数据流架构

```
[训练入口] → 选择来访者来源
    ├─ 真实来访者（从visitors/选择）
    │    ↓
    │  [生成人设] ← 读取visit_001.json
    │    ↓
    │  [保存到training_sessions/]
    │
    └─ 虚拟来访者
         ├─ 从人设库选择（training_personas/）
         └─ 手动创建新人设（表单输入）
              ↓
         [保存到training_personas/]
              ↓
[对话界面启动] → 用户输入 → AI来访者回应（SSE）
      ↓
[异步督导评估] → 浮窗提示（<3秒）
      ↓
[对话结束] → 生成最终报告（Opus）
      ↓
[保存session JSON] → training_sessions/
      ↓
[训练记录列表] → 查看历史 + 回放 + 报告
```

---

### 3.2 服务器端点设计

**服务器**: `src/simulation_training_api.py`  
**端口**: 8772  
**模型**: claude-opus-4-8（所有端点）

#### API端点列表

| 端点 | 方法 | 功能 | 输入 | 输出 |
|------|------|------|------|------|
| `/health` | GET | 健康检查 | - | `{"status": "healthy"}` |
| `/api/generate_persona_from_visit` | POST | 从真实档案生成人设 | visitor_id, visit_id | persona JSON |
| `/api/save_custom_persona` | POST | 保存自定义虚拟人设 | persona数据 | persona_id |
| `/api/list_personas` | GET | 列出所有虚拟人设 | - | persona列表 |
| `/api/start_session` | POST | 开始训练会话 | persona, approach | session_id |
| `/api/chat_stream` | POST | 对话流式输出（AI来访者） | session_id, user_msg | SSE流 |
| `/api/supervise_turn` | POST | 异步督导评估 | session_id, turn_seq | supervision JSON |
| `/api/end_session` | POST | 结束会话并生成报告 | session_id | final_report JSON |
| `/api/list_sessions` | GET | 列出训练记录 | - | session列表 |
| `/api/get_session` | GET | 获取单次训练详情 | session_id | 完整session JSON |

---

## 四、AI Prompt 设计（⭐ 遵循全局规则）

### Prompt 1: 从真实档案生成人设

```
你是一位专业的心理咨询案例模拟专家。请根据以下真实接访记录，生成一个一致的来访者人设，用于对话模拟训练。

【真实接访记录】
逐字稿/对话内容：
{visit_data.dialogue}

咨询师复盘：
{visit_data.counselor_review}

来访者基本信息：
年龄：{visitor_profile.age}
性别：{visitor_profile.gender}
主诉：{visit_summary.complaint}

---

请输出JSON格式的人设（严格按此结构）：

{
  "name": "匿名称呼（如'李先生'）",
  "age": 数字,
  "gender": "男/女",
  "core_issues": ["核心问题1", "核心问题2", "核心问题3"],
  "emotional_state": "情绪状态描述（3-5个词）",
  "key_phrases": ["来访者典型语句1", "典型语句2", "典型语句3"],
  "background_summary": "背景概述（100字以内）",
  "defense_mechanisms": ["防御机制1", "防御机制2"],
  "expectations": {
    "explicit": "显性期待",
    "implicit": "隐性期待"
  }
}

【要求】
1. ⚠️ 严格基于真实记录，不编造不存在的信息
2. key_phrases必须来自真实逐字稿原文
3. 捕捉来访者的独特性（语言风格、情绪特征）
4. 为后续对话模拟提供一致性依据
5. 如果某项信息真实记录中没有，标注为null，不猜测

【验证】
输出前检查：
- [ ] core_issues是否有原文支持？
- [ ] key_phrases是否真实出现过？
- [ ] 是否编造了不存在的背景信息？
```

---

### Prompt 2: AI扮演来访者（对话中）

```
你正在扮演一位来访者，参与心理咨询对话模拟训练。

【来访者人设（严格遵循）】
{persona_json}

【对话历史】
{dialogue_history}

【咨询师刚才说】
{user_last_input}

---

请以来访者身份自然回应，注意：

1. **人设一致性**：
   - 保持情绪状态一致（{persona.emotional_state}）
   - 使用人设中的语言模式
   - 展现防御机制：{persona.defense_mechanisms}

2. **真实性**：
   - 根据咨询师的回应调整情绪（好的共情会让来访者更开放）
   - 不要刻意配合，模拟真实来访者的自然反应
   - 如果咨询师技术不当（过早给建议、打断），自然表现出抗拒或困惑

3. **回应长度**：
   - 50-150字，符合真实对话节奏
   - 不要一次性倾泻太多信息（除非咨询师引导得当）

4. **口语化表达**：
   - 用生活化语言，避免专业术语
   - 可以有停顿、重复、叹气等真实表现
   - 例："我...我也不知道该怎么说...就是觉得...（叹气）很难受"

【禁止】
- 不要主动"顿悟"（咨询没到那个阶段）
- 不要说"你这个问题问得很好"等不自然的话
- 不要展开人设中没有的新议题
- 不要突然变得积极乐观（除非咨询确实推进到那个阶段）

【输出格式】
直接输出来访者的话，不要加"来访者："等前缀。
```

---

### Prompt 3: 实时督导评估（单轮）

```
你是一位资深心理咨询督导，正在实时评估学员的技术运用。

【流派】
{approach_name}

【来访者人设】
{persona_json}

【对话上下文（最近5轮）】
{recent_dialogue_history}

【学员刚才的回应】
{counselor_last_input}

【来访者的反应】
{client_response}

---

请评估这一轮咨询回应（基于{approach_name}流派视角）：

1. **识别技术**：学员用了什么技术？（从该流派的技术清单中识别）
2. **技术质量**：0-10分（7分及格）
3. **即时反馈**：1句话，30字以内，直接指出问题或肯定优点
4. **更好的说法**（可选）：如果质量<7分，给出具体的改进示例

【输出JSON格式】
{
  "technique_used": "技术名称（如：简单反映）",
  "quality_score": 数字（0-10）,
  "comment": "即时反馈（30字以内）",
  "better_example": "更好的说法示例（可选）"
}

【评分标准】
- 9-10分：技术运用精准，显著推进咨询进程
- 7-8分：技术正确，有效但可优化
- 5-6分：技术识别对，但执行不到位
- 3-4分：技术不当或时机不对
- 0-2分：严重错误（如：伤害性回应、违反伦理）

【要求】
- 基于该流派的理论框架评估
- 反馈具体、可操作，不泛泛而谈
- 不要长篇大论，保持实时性
- ⚠️ 不编造学员没用过的技术
```

---

### Prompt 4: 生成最终训练报告

```
你是一位资深心理咨询督导，正在为学员的模拟训练生成综合报告。

【训练信息】
流派: {approach_name}
来访者人设: {persona_json}
对话轮次: {total_turns}
总时长: {duration_seconds}秒

【完整对话逐字稿（含督导评估）】
{full_dialogue_with_supervision}

---

请生成训练报告（Markdown格式）：

# 一、总体评估（50字）
[综合表现概述，客观、具体]

# 二、技术使用统计

| 技术名称 | 使用次数 | 平均质量 | 典型示例（引用原文） |
|---------|---------|---------|---------------------|
| ...     | ...     | ...     | "第X轮：..." |

⚠️ 统计数据必须基于supervision_feedback，不编造

# 三、突出亮点（3-5点）

1. **第X轮 - 技术名称**：具体好在哪里（引用原文）
2. ...

# 四、核心问题（3-5点）

1. **第X轮 - 问题描述**：具体问题 + 为什么不当（引用原文）
2. ...

# 五、具体改进建议（按优先级）

### P0（必须改进）
1. **问题**：...  
   **改进方向**：...  
   **练习方法**：...

### P1（尽快优化）
2. ...

### P2（可选提升）
3. ...

# 六、下次训练方向

建议下次重点练习的场景/技术，基于本次训练暴露的薄弱环节。

---

【要求】
1. ⚠️ 所有数据基于真实对话记录，不编造
2. 引用原文时标注轮次（如"第3轮"）
3. 改进建议具体可操作，给出"更好的说法"示例
4. 技术统计必须与supervision_feedback一致
5. 如果某项无数据，标注"无"，不猜测

【验证清单】
- [ ] 技术统计是否与supervision_feedback一致？
- [ ] 典型示例是否真实引用了原文？
- [ ] 改进建议是否具体可操作？
- [ ] 是否编造了不存在的技术使用？
```

---

## 五、实施步骤（分阶段）

### 阶段1：后端API + 数据结构（3小时）

**任务**：
1. 创建 `src/simulation_training_api.py` (端口8772)
2. 创建目录 `data/training_sessions/` 和 `data/training_personas/`
3. 实现10个API端点（见3.2节）
4. 4套AI Prompt全部用真实案例测试质量
5. 更新 `start_all_servers.bat` 添加8772服务器

**验收标准**：
- [ ] `http://localhost:8772/health` 返回 `{"status": "healthy"}`
- [ ] `start_all_servers.bat` 已添加8772端口
- [ ] `/api/generate_persona_from_visit` 在V20260522001上测试，人设合理且不编造
- [ ] `/api/chat_stream` 能流式输出，10轮对话人设一致
- [ ] `/api/supervise_turn` 返回的技术识别准确（不是泛泛而谈）
- [ ] `/api/end_session` 生成的报告引用原文，不编造技术使用
- [ ] 所有Prompt遵循"不编造数据"原则，有验证清单

---

### 阶段2：前端对话界面（4小时）

**任务**：
1. 创建 `output/对话模拟训练/index.html`（训练入口）
2. 创建 `output/对话模拟训练/session.html`（对话界面，三栏布局）
3. 实现来访者选择（真实/虚拟）
4. 实现虚拟人设创建表单
5. 实现对话区（SSE流式输出）
6. 实现实时督导浮窗（可隐藏/显示）
7. 连接后端API，测试对话流畅性
8. 添加成本监控显示（已消耗tokens）

**验收标准**：
- [ ] 入口页面有"返回主页"链接
- [ ] 入口页面检查8772服务器状态，未启动时提示
- [ ] 可从真实来访者列表选择（读取visitors/）
- [ ] 可从虚拟人设库选择（读取training_personas/）
- [ ] 可手动创建新虚拟人设（表单完整，含所有字段）
- [ ] 对话界面三栏布局清晰（档案 | 对话 | 督导）
- [ ] 用户输入 → AI来访者立即流式回应（<2秒首字）
- [ ] 督导提示在对话后3秒内显示
- [ ] 督导浮窗可一键隐藏/显示
- [ ] 对话历史自动滚动到最新
- [ ] 页面右上角实时显示"已消耗XXX tokens，约$X.XX"
- [ ] 错误提示清晰（API调用失败时有明确反馈）
- [ ] 兼容移动端（Tailwind响应式布局）

---

### 阶段3：训练记录管理与回放（2小时）

**任务**：
1. 对话结束后调用 `/api/end_session` 生成报告
2. 自动保存 `session_XXX.json` 到 `training_sessions/`
3. 创建训练记录列表页（`output/对话模拟训练/history.html`）
4. 创建单次训练详情页（`output/对话模拟训练/session_detail.html`）
5. 实现"回放"功能（按时间戳逐条显示）
6. 实现报告导出为PDF

**验收标准**：
- [ ] 对话结束后自动生成完整报告（<30秒）
- [ ] session JSON保存到 `data/training_sessions/`
- [ ] 训练记录列表显示：时间、来访者、流派、总分、时长
- [ ] 可按时间/流派/来访者筛选
- [ ] 详情页包含：逐字稿、督导反馈、最终报告、技术统计
- [ ] 回放功能可按2秒/轮速度播放对话过程
- [ ] 回放时督导提示同步显示
- [ ] 报告支持一键导出为PDF（遵循全局PDF规则）
- [ ] PDF包含页码、清晰排版

---

### 阶段4：流派切换与优化（1小时）

**任务**：
1. 支持8个流派选择（精神动力学/大观/CBT/人本/存在/IFS/拉康/荣格）
2. 不同流派使用不同督导Prompt（从 `data/config/prompts/` 加载）
3. 流派配置联动（与现有流派管理系统一致）
4. 添加"暂停训练"功能（中途保存进度）
5. 添加"继续上次训练"功能

**验收标准**：
- [ ] 训练开始前可选择流派
- [ ] 不同流派的督导反馈体现流派特色
- [ ] 流派配置变更时，训练系统自动同步
- [ ] 可中途暂停训练，下次继续
- [ ] 暂停的训练会话在列表中标注"进行中"
- [ ] 继续训练时对话历史完整恢复

---

## 六、技术细节

### 6.1 实时督导的实现（异步评估）

```python
# 伪代码示例
@app.route('/api/supervise_turn', methods=['POST'])
async def supervise_turn():
    # 1. 接收参数
    session_id = request.json['session_id']
    turn_seq = request.json['turn_seq']
    
    # 2. 读取session数据
    session = load_session(session_id)
    recent_history = session['dialogue'][-5:]  # 最近5轮
    
    # 3. 构建督导Prompt
    prompt = build_supervision_prompt(
        approach=session['approach'],
        persona=session['visitor_persona'],
        recent_history=recent_history
    )
    
    # 4. 调用Opus评估
    result = await claude_api.call(prompt, model='claude-opus-4-8')
    
    # 5. 解析JSON结果
    supervision = json.loads(result)
    
    # 6. 保存到session
    session['dialogue'][turn_seq-1]['supervision_feedback'] = supervision
    save_session(session)
    
    return jsonify(supervision)
```

**时序图**：
```
用户输入 → AI来访者立即回应（优先级高）
             ↓ (不等待)
      后台异步调用督导API（2-3秒）
             ↓
      督导反馈以"浮窗"形式出现
      （用户可选择查看或隐藏）
```

---

### 6.2 成本监控实现

```javascript
// 前端实时显示token消耗
let totalTokens = 0;

function updateCostDisplay(inputTokens, outputTokens) {
    totalTokens += inputTokens + outputTokens;
    
    // Opus定价：$15/1M input, $75/1M output
    const inputCost = (inputTokens / 1000000) * 15;
    const outputCost = (outputTokens / 1000000) * 75;
    const totalCost = inputCost + outputCost;
    
    document.getElementById('cost-display').innerText = 
        `已消耗 ${totalTokens.toLocaleString()} tokens，约 $${totalCost.toFixed(3)}`;
}
```

---

### 6.3 虚拟人设创建表单

```html
<form id="create-persona-form">
    <input type="text" name="name" placeholder="匿名称呼（如：小雨）" required>
    <input type="number" name="age" placeholder="年龄" required>
    <select name="gender" required>
        <option value="男">男</option>
        <option value="女">女</option>
    </select>
    
    <textarea name="core_issues" placeholder="核心问题（每行一个）" rows="3" required></textarea>
    <input type="text" name="emotional_state" placeholder="情绪状态（如：麻木、无望）" required>
    <textarea name="key_phrases" placeholder="典型语句（每行一个）" rows="3" required></textarea>
    <textarea name="background_summary" placeholder="背景概述（100字以内）" rows="3" required></textarea>
    <textarea name="defense_mechanisms" placeholder="防御机制（每行一个）" rows="2"></textarea>
    
    <input type="text" name="explicit_expectation" placeholder="显性期待" required>
    <input type="text" name="implicit_expectation" placeholder="隐性期待">
    
    <input type="text" name="tags" placeholder="标签（逗号分隔，如：青少年,校园霸凌）">
    <textarea name="training_notes" placeholder="训练备注（可选）" rows="2"></textarea>
    
    <button type="submit">保存虚拟人设</button>
</form>
```

---

## 七、风险与应对

### 风险1：AI来访者不够真实

**应对**：
- ✅ 基于真实逐字稿生成人设，不编造
- ✅ Prompt中强调"不刻意配合"、"模拟真实抗拒"
- ✅ 阶段1验收时用多个案例测试一致性
- ✅ 用户反馈机制：可标注"AI表现不真实"并记录

### 风险2：督导评估质量不稳定

**应对**：
- ✅ 使用Opus保证质量
- ✅ Prompt包含验证清单，要求不编造
- ✅ 阶段1测试时人工检查督导质量
- ✅ 保存每次督导的原始Prompt和结果，便于调试

### 风险3：训练数据与真实档案失去关联

**应对**：
- ✅ session JSON保留 `persona_source` 字段记录来源
- ✅ 即使原始档案删除，训练记录中有完整人设快照
- ✅ 训练记录列表显示"来源：V20260522001 - visit_001"
- ✅ 点击来源时检查档案是否存在，不存在则提示"原始档案已删除/修改"

### 风险4：用户"作弊"（看着真实逐字稿模拟）

**应对**：
- ✅ 训练界面不显示真实逐字稿
- ✅ 只显示来访者人设和核心问题
- ✅ 报告中强调"模拟训练"，不是复刻真实咨询
- ✅ 鼓励用户用虚拟人设训练（无"标准答案"）

---

## 八、成本估算

### 单次训练成本（20轮对话，全Opus）

| 项目 | Tokens | 单价 | 成本 |
|------|--------|------|------|
| 人设生成 | 2000 in + 1000 out | $15/1M in, $75/1M out | $0.105 |
| 对话20轮（AI来访者） | 20 × (1500 in + 300 out) | 同上 | $0.90 |
| 督导评估20轮（Opus） | 20 × (1000 in + 200 out) | 同上 | $0.60 |
| 最终报告生成 | 3000 in + 2000 out | 同上 | $0.195 |
| **总计** | | | **$1.80** |

**结论**：单次20轮对话模拟训练成本约 $1.8，可接受。

**成本优化建议**：
- 如果未来有更便宜的高质量模型，可切换
- 督导评估如果切换到Sonnet：成本降至 $0.60（总计$1.20）
- 用户可选择"仅最终报告"模式（不要实时督导，成本降至$1.20）

---

## 九、时间表

| 阶段 | 任务 | 预计时间 | 累计时间 |
|------|------|---------|---------|
| 阶段1 | 后端API + 数据结构 | 3小时 | 3小时 |
| 阶段2 | 前端对话界面 | 4小时 | 7小时 |
| 阶段3 | 训练记录管理与回放 | 2小时 | 9小时 |
| 阶段4 | 流派切换与优化 | 1小时 | 10小时 |
| **总计** | | **10小时** | |

**备注**：
- 假设每天投入2小时，预计5天完成
- 如遇问题，预留1-2天缓冲时间

---

## 十、验收标准（Phase 4 完成标志）

### 功能验收

- [ ] AI能基于真实档案生成一致的来访者人设（不编造数据）
- [ ] 用户可手动创建虚拟来访者人设并保存
- [ ] 用户可与AI来访者进行20轮以上流畅对话
- [ ] AI实时督导反馈在对话后3秒内显示（可隐藏）
- [ ] 对话结束后自动生成完整训练报告
- [ ] 训练记录列表可查看所有历史模拟对话
- [ ] 训练详情页包含逐字稿、督导反馈、最终报告
- [ ] 支持8个流派切换，督导反馈体现流派特色
- [ ] 训练数据与真实档案完全解耦（删除档案不影响训练记录）
- [ ] 前端实时显示token消耗和成本

### 质量验收

- [ ] AI来访者回应符合人设，情绪一致
- [ ] 督导反馈具体可操作，不是泛泛而谈
- [ ] 督导反馈不编造不存在的技术使用
- [ ] 最终报告包含技术统计、亮点、问题、改进建议
- [ ] 最终报告引用原文，不编造对话内容
- [ ] 界面布局清晰，操作流畅，无明显卡顿
- [ ] 单次训练成本在 $2 以内

### 文档验收

- [ ] `WORKFLOW.md` 更新了需求3（对话模拟训练）
- [ ] `PROJECT_STATUS.md` 更新进度为 Phase 4 完成（85%）
- [ ] `CLAUDE.md` 补充了训练系统的工作原则
- [ ] `start_all_servers.bat` 添加了8772服务器

---

## 十一、后续优化方向（Phase 5+）

1. **真实语音录音** — 集成Web Audio API，录制用户声音
2. **多人督导** — 邀请真人督导点评训练对话
3. **技能树可视化** — 统计用户在不同技术上的掌握程度
4. **难度分级** — 简单/中等/困难案例，逐步提升
5. **流派融合训练** — 同一个案例，尝试不同流派处理
6. **虚拟人设库共享** — 导出/导入人设，与其他咨询师分享

---

## 十二、关键变更总结（v2.0 vs v1.0）

| 方面 | v1.0 | v2.0（当前） |
|------|------|-------------|
| 数据结构 | visitors子目录 | **独立training_sessions目录** |
| 虚拟人设 | 不支持 | **training_personas独立管理** |
| 数据解耦 | 依赖真实档案 | **完全解耦，删除档案不影响训练** |
| 督导模型 | 未指定 | **明确使用Opus** |
| 成本监控 | 无 | **前端实时显示tokens和成本** |
| 全局规则 | 未强调 | **明确遵循不编造数据原则** |
| Prompt验证 | 无 | **每个Prompt含验证清单** |
| 启动脚本 | 未明确 | **阶段1必须更新start_all_servers.bat** |

---

**创建者**：Claude (Opus 4.8)  
**审阅者**：用户  
**状态**：待审批  
**版本**：v2.0（重新设计版）
