export const meta = {
  name: 'deep-explore-anger',
  description: '深度探索愤怒主题：多视角理解压抑的愤怒及其整合路径',
  phases: [
    { title: '多视角理解', detail: 'IFS、荣格、依恋、认知行为四个视角并行分析' },
    { title: '整合与洞察', detail: '综合四个视角，识别核心机制和突破点' },
    { title: '行为方案设计', detail: '设计3个可实践的小行动，评估风险和支持' },
    { title: '文档生成', detail: '生成会话记录、总结、更新地图和工具' },
  ],
}

// ==================== 阶段1：多视角理解（并行） ====================

phase('多视角理解')

const perspectives = await parallel([
  // 视角A：IFS内部家庭系统
  () => agent(
    `你是IFS（内部家庭系统）治疗师。

**背景资料**：
用户是36岁男性，压抑愤怒几十年。已识别的模式：
- 愤怒全部转向内部，变成自我攻击
- 核心信念："愤怒=变成父亲=不可原谅"
- 父亲两次出轨毁家，童年学到"表达情绪=把自己放第一位=伤害别人"
- 被父亲、前妻、朋友、前女友反复伤害，档案里全是"理解""分析"，没有愤怒

**你的任务**：
从IFS视角分析愤怒系统：
1. 愤怒作为流放者：被锁在哪里？承载什么伤口？
2. 哪些管理者在压制愤怒？它们的保护策略是什么？
3. 哪些救火员在转移愤怒？（如自我攻击、复合冲动）
4. Self如何接触这个流放的愤怒？
5. 愤怒的正当性在哪里？它想保护什么？

输出：500-800字的分析`,
    {
      label: 'IFS视角',
      phase: '多视角理解',
      schema: {
        type: 'object',
        properties: {
          anger_as_exile: { type: 'string', description: '愤怒作为流放者的状态' },
          managers_suppressing: { type: 'string', description: '压制愤怒的管理者' },
          firefighters_diverting: { type: 'string', description: '转移愤怒的救火员' },
          self_access_path: { type: 'string', description: 'Self接触愤怒的路径' },
          legitimacy: { type: 'string', description: '愤怒的正当性' },
        },
        required: ['anger_as_exile', 'managers_suppressing', 'firefighters_diverting', 'self_access_path', 'legitimacy'],
      }
    }
  ),

  // 视角B：荣格分析心理学
  () => agent(
    `你是荣格分析心理学专家。

**背景资料**：
用户压抑愤怒几十年，核心信念："愤怒=变成父亲"。已识别黑暗阴影：被压死的愤怒。

**你的任务**：
从荣格视角分析愤怒阴影：
1. 愤怒如何成为黑暗阴影？投射到哪里？
2. "愤怒=父亲"的人格面具vs阴影分裂
3. 压抑愤怒的心理代价（能量、创造力、真实性）
4. 整合愤怒阴影的过程（不是消除，是整合）
5. 愤怒与个体化的关系

输出：500-800字的分析`,
    {
      label: '荣格视角',
      phase: '多视角理解',
      schema: {
        type: 'object',
        properties: {
          shadow_formation: { type: 'string', description: '愤怒阴影的形成' },
          persona_split: { type: 'string', description: '人格面具与阴影的分裂' },
          psychological_cost: { type: 'string', description: '压抑的心理代价' },
          integration_process: { type: 'string', description: '整合路径' },
          individuation: { type: 'string', description: '与个体化的关系' },
        },
        required: ['shadow_formation', 'persona_split', 'psychological_cost', 'integration_process', 'individuation'],
      }
    }
  ),

  // 视角C：依恋理论
  () => agent(
    `你是依恋理论专家。

**背景资料**：
用户童年经历：7-8岁父亲出轨母亲离家，从未被无条件爱过。核心信念："我必须足够好才值得被爱"。压抑愤怒，因为"表达情绪=自私=伤害别人"。

**你的任务**：
从依恋视角分析愤怒压抑：
1. 不安全依恋模式如何导致愤怒压抑？
2. 愤怒与依恋需求的关系（愤怒是被拒绝时的自然反应）
3. "表达愤怒=失去连接"的恐惧从何而来？
4. 如何在安全的关系中学习表达愤怒？
5. 修复性依恋体验的可能性

输出：500-800字的分析`,
    {
      label: '依恋理论视角',
      phase: '多视角理解',
      schema: {
        type: 'object',
        properties: {
          attachment_pattern: { type: 'string', description: '依恋模式与愤怒压抑' },
          anger_attachment_link: { type: 'string', description: '愤怒与依恋需求' },
          fear_of_expression: { type: 'string', description: '表达愤怒的恐惧' },
          safe_expression: { type: 'string', description: '安全表达的学习' },
          corrective_experience: { type: 'string', description: '修复性体验' },
        },
        required: ['attachment_pattern', 'anger_attachment_link', 'fear_of_expression', 'safe_expression', 'corrective_experience'],
      }
    }
  ),

  // 视角D：认知行为视角
  () => agent(
    `你是认知行为治疗（CBT）专家。

**背景资料**：
用户核心信念："愤怒=变成父亲=不可原谅"。自动化思维："如果我愤怒，我就是自私的""表达情绪会伤害别人"。行为模式：压抑愤怒→自我攻击→付出过界。

**你的任务**：
从CBT视角分析愤怒压抑：
1. 核心信念的认知扭曲（全或无、情绪推理、灾难化）
2. 愤怒压抑的ABC模型（触发事件→信念→后果）
3. 功能失调的假设："如果我X，就会Y"
4. 认知重构的切入点（如何挑战"愤怒=父亲"）
5. 行为激活：小步骤表达愤怒的练习

输出：500-800字的分析`,
    {
      label: '认知行为视角',
      phase: '多视角理解',
      schema: {
        type: 'object',
        properties: {
          cognitive_distortions: { type: 'string', description: '认知扭曲类型' },
          abc_model: { type: 'string', description: 'ABC模型分析' },
          dysfunctional_assumptions: { type: 'string', description: '功能失调假设' },
          reframing: { type: 'string', description: '认知重构切入点' },
          behavioral_activation: { type: 'string', description: '行为激活练习' },
        },
        required: ['cognitive_distortions', 'abc_model', 'dysfunctional_assumptions', 'reframing', 'behavioral_activation'],
      }
    }
  ),
])

log('四个视角的分析已完成')

// ==================== 阶段2：整合与洞察 ====================

phase('整合与洞察')

const integration = await agent(
  `你是整合式心理治疗师。

你刚刚收到了关于"愤怒压抑"主题的四个视角分析：

**IFS视角**：
${JSON.stringify(perspectives[0], null, 2)}

**荣格视角**：
${JSON.stringify(perspectives[1], null, 2)}

**依恋理论视角**：
${JSON.stringify(perspectives[2], null, 2)}

**认知行为视角**：
${JSON.stringify(perspectives[3], null, 2)}

**你的任务**：
整合四个视角，提炼核心洞察：

1. **共同发现**：四个视角都指向什么核心机制？
2. **互补视角**：不同视角如何相互补充、形成完整画面？
3. **关键突破点**：从"压抑愤怒"到"整合愤怒"，最关键的3个突破点是什么？
4. **风险评估**：整合愤怒的过程中需要注意什么？
5. **个性化路径**：基于用户的具体情况（36岁、债务压力、孤独、无稳定支持系统），最适合的切入点是什么？

输出：1000-1500字的整合报告`,
  {
    label: '整合分析',
    phase: '整合与洞察',
    schema: {
      type: 'object',
      properties: {
        common_findings: { type: 'string', description: '共同发现的核心机制' },
        complementary_views: { type: 'string', description: '互补视角的综合' },
        breakthrough_points: {
          type: 'array',
          items: { type: 'string' },
          description: '3个关键突破点',
          minItems: 3,
          maxItems: 3
        },
        risks: { type: 'string', description: '风险评估' },
        personalized_path: { type: 'string', description: '个性化路径建议' },
      },
      required: ['common_findings', 'complementary_views', 'breakthrough_points', 'risks', 'personalized_path'],
    }
  }
)

log('整合分析已完成')

// ==================== 阶段3：行为方案设计 ====================

phase('行为方案设计')

const action_plan = await agent(
  `你是实践导向的心理治疗师。

**整合洞察**：
${JSON.stringify(integration, null, 2)}

**用户现状**：
- 36岁，在贵阳，债务43.6万，现金5.6万
- 孤独，无稳定支持系统
- 可用资源：弹钢琴、AI对话、可能的贵阳督导老师
- 已有工具：救火员手册、情绪日记

**你的任务**：
设计3个可实践的行为实验，帮助用户从"压抑愤怒"走向"整合愤怒"。

**要求**：
1. 从最小、最安全的开始（阶梯式）
2. 每个实验包含：具体行为、预期恐惧、观察重点、风险控制
3. 考虑用户的实际资源和限制
4. 不要求立即"释放"愤怒，而是"接触"和"观察"

输出：3个行为实验方案`,
  {
    label: '行为方案',
    phase: '行为方案设计',
    schema: {
      type: 'object',
      properties: {
        experiments: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              name: { type: 'string', description: '实验名称' },
              specific_behavior: { type: 'string', description: '具体行为（越具体越好）' },
              expected_fear: { type: 'string', description: '预期的恐惧' },
              observation_focus: { type: 'string', description: '观察重点' },
              risk_control: { type: 'string', description: '风险控制措施' },
              timeline: { type: 'string', description: '建议时间线' },
            },
            required: ['name', 'specific_behavior', 'expected_fear', 'observation_focus', 'risk_control', 'timeline'],
          },
          minItems: 3,
          maxItems: 3,
        },
        support_resources: { type: 'string', description: '支持资源建议' },
        warning_signs: { type: 'string', description: '需要暂停的警告信号' },
      },
      required: ['experiments', 'support_resources', 'warning_signs'],
    }
  }
)

log('行为方案已完成')

// ==================== 阶段4：文档生成 ====================

phase('文档生成')

const documentation = await agent(
  `你是文档整理专家。

**探索主题**：愤怒的深度探索与整合

**四个视角分析**：
- IFS: ${JSON.stringify(perspectives[0], null, 2)}
- 荣格: ${JSON.stringify(perspectives[1], null, 2)}
- 依恋: ${JSON.stringify(perspectives[2], null, 2)}
- 认知行为: ${JSON.stringify(perspectives[3], null, 2)}

**整合洞察**：
${JSON.stringify(integration, null, 2)}

**行为方案**：
${JSON.stringify(action_plan, null, 2)}

**你的任务**：
生成探索会话总结文档（markdown格式）。

**文档结构**：
# 愤怒的深度探索 - {日期}

## 探索背景
（简述为什么探索这个主题）

## 四个视角的发现
### IFS视角
### 荣格视角
### 依恋理论视角
### 认知行为视角

## 核心洞察
（整合分析的核心发现，3-5条）

## 关键突破点
（3个突破点）

## 行为实验方案
（3个实验的详细说明）

## 风险提示与支持资源

## 更新内容
- 自我认知地图更新：XXX
- 工具箱更新：XXX
- 下次探索方向：XXX

输出：完整的markdown文档`,
  {
    label: '文档生成',
    phase: '文档生成',
  }
)

log('文档生成已完成')

// ==================== 返回结果 ====================

return {
  summary: '愤怒深度探索已完成',
  perspectives: {
    ifs: perspectives[0],
    jung: perspectives[1],
    attachment: perspectives[2],
    cbt: perspectives[3],
  },
  integration,
  action_plan,
  documentation,
  next_steps: [
    '阅读生成的探索总结文档',
    '更新自我认知地图',
    '选择第一个行为实验开始尝试',
    '使用行为实验记录工具追踪过程',
  ],
}
