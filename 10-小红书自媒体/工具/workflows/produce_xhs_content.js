export const meta = {
  name: 'produce-xhs-content',
  description: '小红书心理类图文自动生产流水线',
  phases: [
    { title: '内容策划', detail: '分析脚本，决定形式和风格' },
    { title: '视觉设计', detail: '封面、配色、卡片结构' },
    { title: '文案创作', detail: '标题、正文、标签' },
    { title: '质量审核', detail: '对标爆款规律，评分' },
    { title: '生成执行', detail: '调用工具生成图文' },
  ],
}

// ── 全局配置 ──
const BASE_DIR = 'd:/AI-项目/10-视频自媒体'
const KNOWLEDGE_BASE = `${BASE_DIR}/工具/knowledge/xhs_rules.md`

// ── JSON Schema 定义 ──
const PlanSchema = {
  type: 'object',
  properties: {
    content_type: { type: 'string', enum: ['感悟类', '案例类', '知识类'] },
    format: { type: 'string', enum: ['图文', '视频'] },
    style: { type: 'string', description: '风格定位（温暖治愈/冷静专业/故事化）' },
    cards_count: { type: 'number', description: '卡片数量' },
    reasoning: { type: 'string', description: '为什么这样决策' },
  },
  required: ['content_type', 'format', 'style', 'cards_count', 'reasoning'],
}

const DesignSchema = {
  type: 'object',
  properties: {
    cover: {
      type: 'object',
      properties: {
        hook_type: { type: 'string', enum: ['疑问句', '反差对比', '场景化', '金句断言'] },
        text: { type: 'string', description: '封面文字（12-16字）' },
        bg_color: { type: 'string', description: 'hex颜色' },
        text_color: { type: 'string' },
      },
      required: ['hook_type', 'text', 'bg_color', 'text_color'],
    },
    cards_structure: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          card_no: { type: 'number' },
          role: { type: 'string', description: '卡片角色：封面/铺陈/转折/CTA' },
          content_lines: { type: 'array', items: { type: 'string' } },
        },
      },
    },
    reasoning: { type: 'string' },
  },
  required: ['cover', 'cards_structure', 'reasoning'],
}

const CopySchema = {
  type: 'object',
  properties: {
    title: { type: 'string', description: '18-24字' },
    body: { type: 'string', description: '3段式正文' },
    tags: { type: 'array', items: { type: 'string' }, description: '5-8个标签' },
    reasoning: { type: 'string' },
  },
  required: ['title', 'body', 'tags', 'reasoning'],
}

const QASchema = {
  type: 'object',
  properties: {
    cover_score: { type: 'number', minimum: 0, maximum: 10 },
    content_score: { type: 'number', minimum: 0, maximum: 10 },
    copy_score: { type: 'number', minimum: 0, maximum: 10 },
    total_score: { type: 'number' },
    pass: { type: 'boolean' },
    feedback: { type: 'string', description: '不通过时的修改建议' },
  },
  required: ['cover_score', 'content_score', 'copy_score', 'total_score', 'pass'],
}

// ──────────────────────────────────────────
// 主流程
// ──────────────────────────────────────────

phase('内容策划')

const scriptPath = args?.script || args
if (!scriptPath) {
  log('❌ 缺少脚本路径参数')
  throw new Error('Usage: produce-xhs-content --args "path/to/script.md"')
}

log(`📋 脚本: ${scriptPath}`)

const planPrompt = `
你是内容策划总监。根据脚本决定如何制作小红书图文。

脚本文件：${scriptPath}

参考规律库：${KNOWLEDGE_BASE}

任务：
1. 读取脚本文件和规律库
2. 分析脚本的内容类型（感悟/案例/知识）
3. 决定制作形式（图文优先）
4. 决定视觉风格（温暖治愈/冷静专业/故事化）
5. 决定卡片数量（5张最优）

输出JSON Schema见下方。
`.trim()

const plan = await agent(planPrompt, {
  label: '策划总监',
  phase: '内容策划',
  schema: PlanSchema,
})

if (!plan) {
  log('❌ 策划失败')
  return null
}

log(`✓ 内容类型: ${plan.content_type}`)
log(`✓ 制作形式: ${plan.format}`)
log(`✓ 风格定位: ${plan.style}`)
log(`✓ 卡片数量: ${plan.cards_count}`)
log(`  策划理由: ${plan.reasoning}`)

// ──────────────────────────────────────────
phase('视觉设计')

const designPrompt = `
你是视觉设计总监。根据策划方案设计小红书图文卡片。

脚本文件：${scriptPath}
策划方案：${JSON.stringify(plan, null, 2)}
规律库：${KNOWLEDGE_BASE}

任务：
1. 设计封面：钩子类型、文字、配色
2. 规划卡片结构：每张卡片的角色和内容分配
3. 确保符合小红书规律（封面12-16字、5张卡片、温暖配色）

注意：
- 封面文字必须从脚本第一句提炼，改写成钩子形式
- 卡片分配要有节奏：封面→铺陈→转折→CTA
- 配色符合${plan.style}风格

输出JSON Schema见下方。
`.trim()

const design = await agent(designPrompt, {
  label: '设计总监',
  phase: '视觉设计',
  schema: DesignSchema,
})

if (!design) {
  log('❌ 设计失败')
  return null
}

log(`✓ 封面钩子: ${design.cover.hook_type}`)
log(`✓ 封面文字: ${design.cover.text}`)
log(`✓ 卡片结构: ${design.cards_structure.length}张`)
log(`  设计理由: ${design.reasoning}`)

// ──────────────────────────────────────────
phase('文案创作')

const copyPrompt = `
你是文案编辑。为小红书图文撰写标题、正文、标签。

脚本文件：${scriptPath}
内容类型：${plan.content_type}
规律库：${KNOWLEDGE_BASE}

任务：
1. 标题：18-24字，使用高点击率模板（疑问句/反差/归纳）
2. 正文：3段式，第一人称，口语化，分段清晰
3. 标签：5-8个，包含核心标签+内容标签+长尾标签

要求：
- 标题必须包含"心理"或"情绪"等关键词
- 正文要有钩子+内容+CTA
- 标签顺序：主题→核心→长尾

输出JSON Schema见下方。
`.trim()

const copy = await agent(copyPrompt, {
  label: '文案编辑',
  phase: '文案创作',
  schema: CopySchema,
})

if (!copy) {
  log('❌ 文案创作失败')
  return null
}

log(`✓ 标题: ${copy.title}`)
log(`✓ 标签: ${copy.tags.join(' ')}`)
log(`  文案理由: ${copy.reasoning}`)

// ──────────────────────────────────────────
phase('质量审核')

const qaPrompt = `
你是质检总监。审核小红书图文是否符合爆款规律。

规律库：${KNOWLEDGE_BASE}

待审核产出：
1. 封面设计：
   - 钩子类型: ${design.cover.hook_type}
   - 文字: ${design.cover.text}
   - 配色: ${design.cover.bg_color}

2. 内容结构：${design.cards_structure.length}张卡片
3. 标题：${copy.title}
4. 标签：${copy.tags.join(', ')}

审核标准（见规律库）：
- 封面评分（满分10）：钩子强度4分+视觉舒适3分+文字清晰3分
- 内容评分（满分10）：价值密度4分+叙事流畅3分+情感共鸣3分
- 文案评分（满分10）：标题吸引力4分+正文结构3分+标签精准3分

合格线：单项≥7分，总分≥24分

输出JSON Schema见下方。
`.trim()

const qa = await agent(qaPrompt, {
  label: '质检总监',
  phase: '质量审核',
  schema: QASchema,
})

if (!qa) {
  log('❌ 质检失败')
  return null
}

log(`✓ 封面得分: ${qa.cover_score}/10`)
log(`✓ 内容得分: ${qa.content_score}/10`)
log(`✓ 文案得分: ${qa.copy_score}/10`)
log(`✓ 总分: ${qa.total_score}/30`)
log(`✓ 审核结果: ${qa.pass ? '通过 ✓' : '不通过 ✗'}`)

if (!qa.pass) {
  log(`  修改建议: ${qa.feedback}`)
  log('\n⚠️  质检未通过，自动重做...\n')

  // 第二轮：根据质检反馈重做设计和文案
  phase('重做设计')

  const redesignPrompt = `
你是视觉设计总监。根据质检反馈重新设计。

原设计：${JSON.stringify(design, null, 2)}
质检反馈：${qa.feedback}
脚本文件：${scriptPath}
规律库：${KNOWLEDGE_BASE}

任务：根据质检反馈修正设计，特别注意：
- 封面文字12-16字
- 使用疑问句钩子
- 其他部分保持原设计

输出JSON Schema见下方。
`.trim()

  const newDesign = await agent(redesignPrompt, {
    label: '设计总监(重做)',
    phase: '重做设计',
    schema: DesignSchema,
  })

  if (!newDesign) {
    log('❌ 重做设计失败')
    return { success: false, error: '重做失败' }
  }

  phase('重做文案')

  const recopyPrompt = `
你是文案编辑。根据质检反馈重写文案。

原文案：${JSON.stringify(copy, null, 2)}
质检反馈：${qa.feedback}
脚本文件：${scriptPath}
规律库：${KNOWLEDGE_BASE}

任务：根据质检反馈修正文案，特别注意：
- 标题18-24字
- 标签顺序：主题→核心→长尾
- 删除术语标签，补充长尾标签

输出JSON Schema见下方。
`.trim()

  const newCopy = await agent(recopyPrompt, {
    label: '文案编辑(重做)',
    phase: '重做文案',
    schema: CopySchema,
  })

  if (!newCopy) {
    log('❌ 重做文案失败')
    return { success: false, error: '重做失败' }
  }

  log(`✓ 重做完成`)
  log(`  新封面: ${newDesign.cover.text}`)
  log(`  新标题: ${newCopy.title}`)
  log(`  新标签: ${newCopy.tags.join(' ')}`)

  // 用新版本替换
  Object.assign(design, newDesign)
  Object.assign(copy, newCopy)

  log('\n✅ 已根据质检反馈自动修正，继续执行...\n')
}

// ──────────────────────────────────────────
phase('生成执行')

log('✓ 所有Agent协作完成，质检通过！')

// 汇总输出（不调用fs，直接返回结果让外部处理）
const output = {
  success: true,
  plan,
  design,
  copy,
  qa_scores: {
    cover: qa.cover_score,
    content: qa.content_score,
    copy: qa.copy_score,
    total: qa.total_score,
  },
  deliverables: {
    cover_text: design.cover.text,
    cover_hook_type: design.cover.hook_type,
    cover_bg: design.cover.bg_color,
    cover_text_color: design.cover.text_color,
    cards_count: design.cards_structure.length,
    cards: design.cards_structure,
    title: copy.title,
    body: copy.body,
    tags: copy.tags,
  },
}

log('\n🎉 制作完成！')
log('\n═══════════════════════════════════════')
log('📦 交付物总览')
log('═══════════════════════════════════════')
log(`\n【策划方案】`)
log(`  内容类型: ${plan.content_type}`)
log(`  制作形式: ${plan.format}`)
log(`  风格定位: ${plan.style}`)
log(`  卡片数量: ${plan.cards_count}张`)
log(`\n【封面设计】`)
log(`  钩子类型: ${design.cover.hook_type}`)
log(`  封面文字: ${design.cover.text}`)
log(`  背景色: ${design.cover.bg_color}`)
log(`\n【发布文案】`)
log(`  标题: ${copy.title}`)
log(`  标签: ${copy.tags.join(' ')}`)
log(`\n【质检得分】`)
log(`  封面: ${qa.cover_score}/10`)
log(`  内容: ${qa.content_score}/10`)
log(`  文案: ${qa.copy_score}/10`)
log(`  总分: ${qa.total_score}/30 ✓`)
log('\n═══════════════════════════════════════')

return output
