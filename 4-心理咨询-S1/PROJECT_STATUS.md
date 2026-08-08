# PROJECT_STATUS.md — 心理咨询案例管理系统

**最后更新**：2026-07-23 18:00  
**当前阶段**：Phase 3A 完成并测试中，P0阻塞已解决  
**项目进度**：40%

---

## 🎯 当前焦点

**主线任务**：三大目标系统逐步落地
1. 来访者档案记录并分析（AI自动多流派分析）✅ 已上线
2. 帮我成为心理咨询师（AI督导反馈）⏳ Phase 3C待开发
3. 对话模拟飞速提升实战水平 ⏳ Phase 4待开发

**当前焦点**：AI分析API服务器已启动运行，正在进行真实案例测试

**已解决的P0阻塞**：
- ✅ AI分析API服务器stdout冲突问题已修复
- ✅ 数据路径兼容性已修复（支持旧格式data/cases/processed/）
- ✅ start_all_servers.bat已更新包含8771服务器
- ✅ API Key自动配置（CatKing AI默认配置）

---

## 📊 关键指标

| 指标 | 当前值 | 目标 |
|------|--------|------|
| 来访者档案数 | 4个（旧路径）| 持续增加 |
| 已完成AI流派分析数 | 0 | 每个来访者6个流派 |
| 支持的流派数 | 6个（大观/CBT/精分/人本/存在/IFS）| 6个 |
| 运行中服务器 | 12个（8771未启动）| 13个 |
| 对话模拟功能 | 未开始 | Phase 4完成 |

---

## ✅ 已完成的里程碑

### 基础架构（v1.0-v2.0）
- [x] 来访者为中心的数据结构设计
- [x] 12个微服务器（接访记录/录音/逐字稿/流派配置等）
- [x] 多流派Tab界面（5+1流派 → 现扩展为6个含IFS）
- [x] Word文档上传解析
- [x] 流派配置自动联动HTML重新生成
- [x] 来访者库双视图（卡片+列表）
- [x] 流派对比视图
- [x] 逐字稿上传（多格式）

### AI分析引擎 Phase 3A（2026-07-23完成）
- [x] 6个流派AI分析Prompt模板（深度定制）
  - 大观学派：基于PPT原版，含SOR/危机等级A-Z/六变三托
  - CBT：认知三角/11种认知扭曲/苏格拉底式提问
  - 精神动力学：防御机制/客体关系/移情反移情
  - 人本主义：Rogers三核心/Maslow需求层次
  - 存在主义：Yalom四大终极关怀/Frankl意义疗法
  - IFS：内在部分识别/真我8C能量/卸负担
- [x] AI分析核心服务 `ai_analysis_service.py`（支持Claude Opus 4.8）
- [x] AI分析API服务器 `ai_analysis_api.py`（端口8771）
- [x] 前端集成：来访者详情页添加"🤖 生成AI分析"按钮
- [x] CatKing AI接口测试成功（base_url已配置）
- [x] IFS新流派配置文件 `data/config/approaches/ifs.json`

---

## 🔄 进行中的工作

### 待测试（P0 - 今天）
- [ ] 启动8771 AI分析API服务器
- [ ] 打开真实案例详情页，点击"🤖 生成AI分析"测试
- [ ] 评估AI分析质量，决定是否需要调整Prompt

---

## ⚠️ 已识别的风险

### P0（阻断性）
- **AI分析服务器未启动**：8771端口未运行，前端按钮无法工作
  - 解决方案：`set ANTHROPIC_API_KEY=sk-d285... && python src/ai_analysis_api.py`
- **来访者数据路径问题**：`data/visitors/` 目录为空，案例数据在 `data/cases/processed/` 旧路径
  - AI分析服务从 `data/visitors/` 读取，需要确认实际数据位置

### P1（重要）
- `start_all_servers.bat` 未包含8771服务器，每次需手动启动
- 对话模拟系统（Phase 4）是提升水平的核心功能，尚未开始

### P2（次要）
- `output/来访者库/downloads/` 与 `output/案例库/downloads/` 文件重复（历史遗留）
- `generate_visit_details_v2.py` 与v1功能差异，保留备用

---

## 📝 待办事项

### P0（立即执行）
1. 启动AI分析API服务器（8771），进行真实案例测试
2. 确认来访者数据路径，修复数据读取问题
3. 更新 `start_all_servers.bat` 加入8771服务器

### P1（本周完成）
4. 评估AI分析Prompt质量，根据反馈调整
5. 开发Phase 3C：AI督导系统（督导Tab界面）
6. 更新 README.md 反映Phase 3A新功能

### P2（有空再做）
7. Phase 4：对话模拟系统（来访者AI角色扮演）
8. Phase 5：技能树可视化
9. 解决downloads目录重复问题

---

## 🗂️ 核心资产位置

| 资产 | 路径 |
|------|------|
| AI分析服务 | `src/ai_analysis_service.py` |
| AI分析API服务器 | `src/ai_analysis_api.py` （端口8771）|
| 6个流派Prompt模板 | `data/config/prompts/*.md` |
| 流派配置文件 | `data/config/approaches/*.json`（6个已启用）|
| 来访者详情页生成器 | `src/generate_visit_details.py` |
| 大观学派手册 | `大观-危机干预技术/大观危机干预技术手册.md` |
| 案例数据（旧路径） | `data/cases/processed/*.json` |
| 来访者输出页面 | `output/来访者库/` |
| 启动脚本 | `start_all_servers.bat` |

---

## 📅 更新日志（最近5条）

### 2026-07-23
- Phase 3A完成：AI分析引擎全部开发完毕
- 新增6个流派Prompt模板（大观基于PPT深度定制）
- 前端集成：详情页添加AI分析按钮
- IFS新流派加入系统（含配置文件和Prompt）
- CatKing AI接口测试成功，首次AI分析输出6533 tokens

### 2026-07-05
- 代码审查与优化完成（8个不一致项修复）
- 服务器列表更新（12个服务器，含正确端口）
- temp_1/temp_2流派禁用，补充name_short字段
