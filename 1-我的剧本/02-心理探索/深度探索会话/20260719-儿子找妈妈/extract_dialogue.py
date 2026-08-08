import json
import sys

jsonl_file = "C:/Users/Administrator/.claude/projects/d--AI----1-----/4432330c-729e-4c4e-b475-cd3f204b6620.jsonl"
output_file = "d:/AI-项目/1-我的剧本/02-心理探索/深度探索会话/20260719-儿子找妈妈/完整对话记录-20260719.md"

dialogue = []
with open(jsonl_file, encoding='utf-8') as f:
    for line in f:
        msg = json.loads(line)
        t = msg.get('type')
        
        if t == 'user':
            content = msg.get('message', {}).get('content', '')
            if isinstance(content, str) and content.strip():
                if not content.startswith('<local-command'):
                    dialogue.append(('用户', content.strip()))
        
        elif t == 'assistant':
            msg_content = msg.get('message', {}).get('content', [])
            if isinstance(msg_content, list):
                texts = [item.get('text', '') for item in msg_content if item.get('type') == 'text']
                content = '\n'.join(texts).strip()
                if content and not content.startswith('...'):
                    dialogue.append(('治疗师', content))

# 找到今天对话的起点
start_idx = -1
for i, (role, content) in enumerate(dialogue):
    if '读取资料，开始新的深度探索' in content:
        start_idx = i
        break

if start_idx >= 0:
    dialogue = dialogue[start_idx:]

# 写入markdown
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("# 第七次深度自我探索对话记录（完整版）\n\n")
    f.write("**日期**：2026年7月19日\n")
    f.write("**主题**：儿子找妈妈的感觉 — Maternal需求首次识别\n")
    f.write(f"**消息数量**：{len(dialogue)}\n\n")
    f.write("---\n\n")
    f.write("## 对话开始\n\n")
    
    for role, content in dialogue:
        f.write(f"**{role}**：{content}\n\n")
        f.write("---\n\n")

sys.stdout.buffer.write(f"对话记录已导出: {len(dialogue)} 条消息\n".encode('utf-8'))
sys.stdout.buffer.write(f"文件: {output_file}\n".encode('utf-8'))
