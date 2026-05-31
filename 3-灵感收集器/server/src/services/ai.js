import Anthropic from '@anthropic-ai/sdk';

const DEFAULT_MODEL = process.env.AI_MODEL || 'claude-sonnet-4-6';

function hasAnthropic() {
  return Boolean(process.env.ANTHROPIC_API_KEY);
}

function client() {
  if (!hasAnthropic()) return null;
  return new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });
}

export async function analyzeInspiration(note) {
  const fallback = localAnalyze(note);
  const anthropic = client();
  if (!anthropic) return fallback;

  try {
    const message = await anthropic.messages.create({
      model: DEFAULT_MODEL,
      max_tokens: 1200,
      system: '你是一个中文灵感整理助手。只输出 JSON，不要输出 Markdown。JSON 字段：summary,tags,keywords,mood,expanded。mood 只能是 excited/calm/low/confused/anxious/inspired/determined 之一。',
      messages: [
        {
          role: 'user',
          content: `请整理这条灵感：\n内容：${note.content || ''}\n转写：${note.transcript || ''}\n上下文：${note.context || ''}`
        }
      ]
    });
    const text = message.content?.find(block => block.type === 'text')?.text || '{}';
    const parsed = JSON.parse(text);
    return {
      ...fallback,
      ...parsed,
      tags: Array.isArray(parsed.tags) ? parsed.tags.slice(0, 8) : fallback.tags,
      keywords: Array.isArray(parsed.keywords) ? parsed.keywords.slice(0, 12) : fallback.keywords
    };
  } catch (error) {
    return { ...fallback, aiError: error.message };
  }
}

export async function transcribeMedia(asset) {
  if (!asset || asset.type !== 'audio') return '';
  // v1 不接 Whisper；后续可在这里接入后备转写服务。
  return '';
}

function localAnalyze(note) {
  const text = `${note.content || ''} ${note.transcript || ''}`.trim();
  const words = extractKeywords(text);
  return {
    summary: note.summary || summarize(text),
    tags: words.slice(0, 5),
    keywords: words.slice(0, 10),
    mood: note.mood || inferMood(text),
    expanded: note.expanded || expandText(text),
    aiError: null
  };
}

function summarize(text) {
  if (!text) return '等待补充内容';
  return text.length > 80 ? `${text.slice(0, 80)}…` : text;
}

function extractKeywords(text) {
  return [...new Set(text
    .replace(/[，。！？、；：,.!?;:()（）\[\]【】"']/g, ' ')
    .split(/\s+/)
    .map(item => item.trim())
    .filter(item => item.length >= 2)
  )].slice(0, 12);
}

function inferMood(text) {
  if (/开心|兴奋|想做|太棒|灵感/.test(text)) return 'excited';
  if (/焦虑|担心|害怕/.test(text)) return 'anxious';
  if (/困惑|不确定|迷茫/.test(text)) return 'confused';
  if (/坚持|完成|推进/.test(text)) return 'determined';
  return 'inspired';
}

function expandText(text) {
  if (!text) return '';
  return `可以进一步拆解为：\n1. 核心想法：${summarize(text)}\n2. 下一步：补充触发场景、目标用户/用途、最小可执行动作。\n3. 关联：寻找相似主题或已有素材。`;
}
