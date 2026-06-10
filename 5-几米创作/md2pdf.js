// 复用脚本：将项目中的 Markdown 转为 PDF
// 用法: node md2pdf.js <markdown文件路径>
const fs = require('fs');
const path = require('path');

const mdPath = process.argv[2];
if (!mdPath) {
    console.error('用法: node md2pdf.js <markdown文件路径>');
    process.exit(1);
}

const absMdPath = path.resolve(mdPath);
const dir = path.dirname(absMdPath);
const baseName = path.basename(absMdPath, '.md');
const htmlPath = path.join(dir, baseName + '.html');
const pdfPath = path.join(dir, baseName + '.pdf');

const md = fs.readFileSync(absMdPath, 'utf-8');
let content = md.replace(/^---[\s\S]*?---\s*/, '');

function escapeHtml(text) {
    return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function convertInline(text) {
    text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
    text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/\*(.+?)\*/g, '<em>$1</em>');
    return text;
}

const lines = content.split('\n');
let html = '';
let inCodeBlock = false, codeBlockContent = '';
let inTable = false, tableRows = [];

function flushTable() {
    if (tableRows.length === 0) return '';
    let t = '<table>';
    tableRows.forEach((row, i) => {
        if (row.every(c => /^[-:]+$/.test(c.trim()))) return;
        const tag = i === 0 ? 'th' : 'td';
        t += '<tr>' + row.map(c => `<${tag}>${convertInline(c.trim())}</${tag}>`).join('') + '</tr>';
    });
    t += '</table>';
    tableRows = [];
    return t;
}

for (const line of lines) {
    if (line.startsWith('```')) {
        if (inCodeBlock) {
            html += `<pre><code>${escapeHtml(codeBlockContent)}</code></pre>\n`;
            codeBlockContent = '';
            inCodeBlock = false;
        } else { inCodeBlock = true; }
        continue;
    }
    if (inCodeBlock) { codeBlockContent += (codeBlockContent ? '\n' : '') + line; continue; }

    if (inTable && (!line.startsWith('|') || !line.trim().endsWith('|'))) {
        html += flushTable();
        inTable = false;
        tableRows = [];
    }

    if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
        inTable = true;
        tableRows.push(line.trim().split('|').slice(1, -1));
        continue;
    }

    if (line.startsWith('#### ')) html += `<h4>${convertInline(line.slice(5))}</h4>\n`;
    else if (line.startsWith('### ')) html += `<h3>${convertInline(line.slice(4))}</h3>\n`;
    else if (line.startsWith('## ')) html += `<h2>${convertInline(line.slice(3))}</h2>\n`;
    else if (line.startsWith('# ')) html += `<h1>${convertInline(line.slice(2))}</h1>\n`;
    else if (line.trim() === '---') html += '<hr>\n';
    else if (line.startsWith('> ')) html += `<blockquote>${convertInline(line.slice(2))}</blockquote>\n`;
    else if (line.trim() === '') html += '\n';
    else html += `<p>${convertInline(line)}</p>\n`;
}
if (inTable) html += flushTable();

const fullHtml = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>${baseName}</title>
<style>
  @media print { @page { size: A4; margin: 2cm; } body { -webkit-print-color-adjust: exact; print-color-adjust: exact; } }
  * { box-sizing: border-box; }
  body { font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans SC", sans-serif; font-size: 13pt; line-height: 1.9; color: #1F2937; max-width: 900px; margin: 0 auto; padding: 40px 50px; }
  h1 { font-size: 24pt; border-bottom: 3px solid #3B82F6; padding-bottom: 14px; margin: 44px 0 22px 0; color: #111827; page-break-before: avoid; }
  h2 { font-size: 17pt; color: #1E40AF; margin: 34px 0 16px 0; border-left: 5px solid #3B82F6; padding-left: 14px; page-break-before: avoid; }
  h3 { font-size: 14pt; color: #2563EB; margin: 26px 0 12px 0; page-break-before: avoid; }
  h4 { font-size: 12pt; color: #6B7280; margin: 20px 0 10px 0; page-break-before: avoid; }
  table { border-collapse: collapse; width: 100%; margin: 18px 0; font-size: 10.5pt; page-break-inside: avoid; }
  th { background: #DBEAFE; padding: 10px 14px; text-align: left; font-weight: 600; color: #1E3A5F; border: 1px solid #BFDBFE; }
  td { padding: 8px 14px; border: 1px solid #E5E7EB; vertical-align: top; }
  blockquote { border-left: 5px solid #3B82F6; padding: 16px 26px; margin: 20px 0; background: #EFF6FF; color: #374151; font-style: italic; border-radius: 0 6px 6px 0; }
  code { background: #F3F4F6; padding: 2px 7px; border-radius: 4px; font-size: 10.5pt; font-family: "Cascadia Code", "Consolas", "Courier New", monospace; border: 1px solid #E5E7EB; }
  pre { background: #1E293B; color: #E2E8F0; padding: 20px 24px; border-radius: 8px; overflow-x: auto; font-size: 10pt; line-height: 1.7; page-break-inside: avoid; }
  pre code { background: none; padding: 0; color: inherit; border: none; }
  hr { border: none; border-top: 2px solid #E5E7EB; margin: 38px 0; }
  strong { color: #1E40AF; }
  p { margin: 12px 0; }
  h1:first-child { margin-top: 0; }
</style>
</head>
<body>\n${html}\n</body>
</html>`;

fs.writeFileSync(htmlPath, fullHtml, 'utf-8');

// Use Chrome headless to generate PDF
const { execSync } = require('child_process');
const chromePath = 'C:/Program Files/Google/Chrome/Application/chrome.exe';

try {
    execSync(`"${chromePath}" --headless --disable-gpu --print-to-pdf="${pdfPath}" --no-margins "file:///${htmlPath.replace(/\\/g, '/')}"`, { timeout: 30000 });
    fs.unlinkSync(htmlPath); // 删除中间 HTML
    const stats = fs.statSync(pdfPath);
    console.log(`PDF 已生成: ${pdfPath} (${(stats.size / 1024).toFixed(0)} KB)`);
} catch (e) {
    console.error('PDF 生成失败:', e.message);
    console.log(`HTML 已保留: ${htmlPath} (可在浏览器中打开后 Ctrl+P 打印为 PDF)`);
}
