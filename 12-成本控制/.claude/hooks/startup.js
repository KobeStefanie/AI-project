#!/usr/bin/env node
/**
 * 启动钩子：读取三大件并汇报项目状态
 *
 * 功能：
 * 1. 读取 PROJECT_STATUS.md - 了解当前进度、焦点、待办
 * 2. 读取 WORKFLOW.md - 了解当前工作流版本、标准流程
 * 3. 读取 CLAUDE.md - 了解项目原则、验证流程
 * 4. 自动汇报当前状态和下一步行动
 *
 * 触发：每次 Codex 会话启动时自动执行
 */

const fs = require('fs');
const path = require('path');

// 项目根目录
const PROJECT_ROOT = process.cwd();

// 三大件文件路径
const FILES = {
  PROJECT_STATUS: path.join(PROJECT_ROOT, 'PROJECT_STATUS.md'),
  WORKFLOW: path.join(PROJECT_ROOT, 'WORKFLOW.md'),
  CLAUDE: path.join(PROJECT_ROOT, 'CLAUDE.md')
};

/**
 * 读取文件内容
 */
function readFile(filePath) {
  try {
    if (!fs.existsSync(filePath)) {
      return null;
    }
    return fs.readFileSync(filePath, 'utf-8');
  } catch (error) {
    console.error(`❌ 读取文件失败: ${filePath}`);
    console.error(error.message);
    return null;
  }
}

/**
 * 从 PROJECT_STATUS.md 提取关键信息
 */
function parseProjectStatus(content) {
  if (!content) return null;

  const lines = content.split('\n');
  const info = {
    lastUpdate: '',
    currentStage: '',
    progress: '',
    mainTask: '',
    keyIndicators: [],
    blockingIssues: [],
    p0Tasks: [],
    p1Tasks: []
  };

  let inKeyIndicators = false;
  let inBlockingIssues = false;
  let inP0Tasks = false;
  let inP1Tasks = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();

    // 提取最后更新时间
    if (line.startsWith('**最后更新**:')) {
      info.lastUpdate = line.replace('**最后更新**:', '').trim();
    }

    // 提取当前阶段
    if (line.startsWith('**当前阶段**:')) {
      info.currentStage = line.replace('**当前阶段**:', '').trim();
    }

    // 提取项目进度
    if (line.startsWith('**项目进度**:')) {
      info.progress = line.replace('**项目进度**:', '').trim();
    }

    // 提取主线任务
    if (line.startsWith('**主线任务**:')) {
      info.mainTask = line.replace('**主线任务**:', '').trim();
    }

    // 提取阻塞问题
    if (line.startsWith('**阻塞问题**:')) {
      inBlockingIssues = true;
      continue;
    }

    if (inBlockingIssues) {
      if (line.startsWith('##') || line === '---') {
        inBlockingIssues = false;
      } else if (line.match(/^\d+\./)) {
        const issue = line.replace(/^\d+\.\s*/, '').trim();
        if (!issue.startsWith('✅')) {
          info.blockingIssues.push(issue);
        }
      }
    }

    // 提取关键指标（寻找表格）
    if (line.startsWith('## 📊 关键指标')) {
      inKeyIndicators = true;
      continue;
    }

    if (inKeyIndicators && line.startsWith('|') && !line.includes('---')) {
      const cells = line.split('|').map(c => c.trim()).filter(c => c);
      if (cells.length >= 4 && cells[0] !== '指标') {
        const indicator = `${cells[0]}: ${cells[2]} (${cells[3]})`;
        info.keyIndicators.push(indicator);
      }
      if (line.startsWith('##')) {
        inKeyIndicators = false;
      }
    }

    // 提取 P0 待办事项
    if (line.startsWith('### P0')) {
      inP0Tasks = true;
      inP1Tasks = false;
      continue;
    }

    // 提取 P1 待办事项
    if (line.startsWith('### P1')) {
      inP0Tasks = false;
      inP1Tasks = true;
      continue;
    }

    if (line.startsWith('### P2') || line.startsWith('##')) {
      inP0Tasks = false;
      inP1Tasks = false;
    }

    if (inP0Tasks && line.match(/^\d+\./)) {
      const task = line.replace(/^\d+\.\s*/, '').replace(/^\[\s*[x\s]\s*\]\s*/, '').trim();
      if (!line.includes('[x]')) {
        info.p0Tasks.push(task);
      }
    }

    if (inP1Tasks && line.match(/^\d+\./)) {
      const task = line.replace(/^\d+\.\s*/, '').replace(/^\[\s*[x\s]\s*\]\s*/, '').trim();
      if (!line.includes('[x]')) {
        info.p1Tasks.push(task);
      }
    }
  }

  return info;
}

/**
 * 从 WORKFLOW.md 提取关键信息
 */
function parseWorkflow(content) {
  if (!content) return null;

  const lines = content.split('\n');
  const info = {
    currentVersion: '',
    lastUpdate: ''
  };

  for (const line of lines) {
    if (line.startsWith('**当前工作流版本**:')) {
      info.currentVersion = line.replace('**当前工作流版本**:', '').trim();
    }
    if (line.startsWith('**最后更新**:')) {
      info.lastUpdate = line.replace('**最后更新**:', '').trim();
    }
  }

  return info;
}

/**
 * 生成汇报输出
 */
function generateReport(projectStatus, workflow) {
  const today = new Date().toISOString().split('T')[0].replace(/-/g, '/');

  console.log('\n## 📍 当前状态（' + today + '）\n');

  if (projectStatus) {
    console.log('**项目进度**: ' + projectStatus.progress);
    console.log('**当前阶段**: ' + projectStatus.currentStage);
    console.log('**最后更新**: ' + projectStatus.lastUpdate);
    console.log();

    if (projectStatus.mainTask) {
      console.log('**主线任务**:');
      console.log('- ' + projectStatus.mainTask);
      console.log();
    }

    if (projectStatus.blockingIssues.length > 0) {
      console.log('**阻塞问题**:');
      projectStatus.blockingIssues.slice(0, 3).forEach((issue, i) => {
        console.log(`${i + 1}. ${issue}`);
      });
      console.log();
    }

    if (projectStatus.keyIndicators.length > 0) {
      console.log('**关键指标**:');
      projectStatus.keyIndicators.slice(0, 5).forEach(indicator => {
        console.log('- ' + indicator);
      });
      console.log();
    }
  }

  if (workflow) {
    console.log('**当前工作流**: ' + workflow.currentVersion);
    console.log();
  }

  console.log('---\n');
  console.log('## ⚡ 下一步行动（按优先级）\n');

  if (projectStatus) {
    if (projectStatus.p0Tasks.length > 0) {
      console.log('### P0（立即执行）');
      projectStatus.p0Tasks.slice(0, 3).forEach((task, i) => {
        console.log(`${i + 1}. ${task}`);
      });
      console.log();
    }

    if (projectStatus.p1Tasks.length > 0) {
      console.log('### P1（本周内）');
      projectStatus.p1Tasks.slice(0, 3).forEach((task, i) => {
        console.log(`${i + 1}. ${task}`);
      });
      console.log();
    }
  }

  console.log('---\n');
}

/**
 * 主函数
 */
function main() {
  console.log('🚀 正在读取三大件...\n');

  // 读取三大件
  const projectStatusContent = readFile(FILES.PROJECT_STATUS);
  const workflowContent = readFile(FILES.WORKFLOW);
  const claudeContent = readFile(FILES.CLAUDE);

  // 检查是否成功读取
  const filesRead = [];
  if (projectStatusContent) filesRead.push('PROJECT_STATUS.md');
  if (workflowContent) filesRead.push('WORKFLOW.md');
  if (claudeContent) filesRead.push('CLAUDE.md');

  if (filesRead.length === 0) {
    console.log('⚠️  未找到三大件文件，跳过状态汇报');
    return;
  }

  console.log('✅ 已读取: ' + filesRead.join(', ') + '\n');

  // 解析内容
  const projectStatus = parseProjectStatus(projectStatusContent);
  const workflow = parseWorkflow(workflowContent);

  // 生成汇报
  generateReport(projectStatus, workflow);

  console.log('💡 提示: 三大件已加载到上下文中，可以直接开始工作\n');
}

// 执行
main();
