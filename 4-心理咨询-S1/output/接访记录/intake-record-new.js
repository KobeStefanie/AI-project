// API配置
const CONFIG_API = 'http://localhost:8003';
const AUDIO_API = 'http://localhost:8004';
const TRANSCRIPT_API = 'http://localhost:8005';  // 旧的逐字稿API（保留兼容）
const SUPERVISION_API = 'http://localhost:8006';
const INTAKE_API = 'http://localhost:8768';  // 接访记录保存服务器
const RECORDING_API = 'http://localhost:8767';  // 录音管理服务器
const TRANSCRIPT_UPLOAD_API = 'http://localhost:8769';  // 新的逐字稿上传API（与来访档案统一）

// 全局变量
let tagsLibrary = null;
let selectedAudioFiles = [];
let selectedTranscriptFiles = [];
let selectedSupervisionFiles = [];
let keywords = [];
let currentCase = null;  // 当前加载的案例
let isFollowUpSession = false;  // 是否为后续会谈模式
let childrenList = [];  // 孩子信息列表
let psychTestsList = [];  // 心理测评列表

// 常用心理测评量表
const PSYCH_TESTS = [
    { name: 'SCL-90', fullName: '症状自评量表', description: '评估心理症状严重程度' },
    { name: 'SDS', fullName: '抑郁自评量表', description: '评估抑郁程度' },
    { name: 'SAS', fullName: '焦虑自评量表', description: '评估焦虑程度' },
    { name: 'PHQ-9', fullName: '患者健康问卷', description: '抑郁症筛查' },
    { name: 'GAD-7', fullName: '广泛性焦虑量表', description: '焦虑症筛查' },
    { name: 'MMPI', fullName: '明尼苏达多相人格测验', description: '人格特征评估' },
    { name: 'EPQ', fullName: '艾森克人格问卷', description: '人格维度评估' },
    { name: 'BDI', fullName: '贝克抑郁量表', description: '抑郁情绪评估' },
    { name: 'BAI', fullName: '贝克焦虑量表', description: '焦虑情绪评估' },
    { name: '16PF', fullName: '卡特尔16种人格因素问卷', description: '人格特质评估' },
    { name: 'HAMA', fullName: '汉密尔顿焦虑量表', description: '焦虑严重度评估' },
    { name: 'HAMD', fullName: '汉密尔顿抑郁量表', description: '抑郁严重度评估' },
    { name: 'BPRS', fullName: '简明精神病评定量表', description: '精神病性症状评估' },
    { name: 'PANSS', fullName: '阳性和阴性症状量表', description: '精神分裂症症状评估' },
    { name: 'YMRS', fullName: '杨氏躁狂评定量表', description: '躁狂症状评估' },
    { name: 'CGI', fullName: '临床总体印象量表', description: '疾病严重度评估' },
    { name: 'Y-BOCS', fullName: '耶鲁布朗强迫量表', description: '强迫症状评估' },
    { name: 'SCARED', fullName: '儿童焦虑相关情绪障碍筛查量表', description: '儿童焦虑筛查' },
    { name: 'CDI', fullName: '儿童抑郁量表', description: '儿童抑郁评估' },
    { name: 'CBCL', fullName: '儿童行为量表', description: '儿童行为问题评估' },
    { name: 'Conners', fullName: 'Conners父母量表', description: 'ADHD评估' },
    { name: 'WCST', fullName: '威斯康星卡片分类测验', description: '执行功能评估' },
    { name: 'TMT', fullName: '连线测验', description: '注意力和认知灵活性' },
    { name: 'WAIS', fullName: '韦氏成人智力量表', description: '智力评估' },
    { name: 'WISC', fullName: '韦氏儿童智力量表', description: '儿童智力评估' }
];

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', async () => {
    // 加载标签库
    await loadTagsLibrary();

    // 生成关系标签
    renderRelationTags();

    // 生成症状标签
    renderSymptomTags();

    // 生成使用技巧
    renderTechniques();

    // 设置今天日期
    document.getElementById('接访日期').valueAsDate = new Date();

    // 检查是否有草稿
    checkAndLoadDraft();

    // 绑定关键词输入事件
    document.getElementById('keywordInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            addKeyword();
        }
    });

    // 绑定文件上传事件
    setupFileUpload('audio', selectedAudioFiles);
    setupFileUpload('transcript', selectedTranscriptFiles);
    setupFileUpload('supervision', selectedSupervisionFiles);
    setupWordUpload();

    // 绑定标签变化事件
    document.addEventListener('change', (e) => {
        if (e.target.type === 'checkbox' && (e.target.dataset.category === 'relation' || e.target.dataset.category === 'symptom')) {
            updateSelectedTags();
        }
    });

    // 自动保存草稿（每30秒）- 暂时禁用，避免错误
    // setInterval(() => {
    //     autoSaveDraft();
    // }, 30000);
});

// 加载标签库
async function loadTagsLibrary() {
    try {
        const response = await fetch(`${CONFIG_API}/api/tags-library`);
        if (!response.ok) throw new Error('加载标签库失败');
        tagsLibrary = await response.json();
    } catch (error) {
        console.error('加载标签库失败:', error);
        alert('加载标签库失败，请确保配置服务器正在运行 (端口8003)');
    }
}

// 渲染关系标签（三级折叠，二级露出）
function renderRelationTags() {
    if (!tagsLibrary) return;

    const container = document.getElementById('relationTagsContainer');
    const relationTags = tagsLibrary.relation_tags;

    for (const [category, data] of Object.entries(relationTags)) {
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'tag-category';

        // 一级分类标题（始终显示）
        const categoryTitle = document.createElement('div');
        categoryTitle.className = 'tag-category-title';
        categoryTitle.innerHTML = `<span>${data.icon}</span><span>${category}</span>`;
        categoryDiv.appendChild(categoryTitle);

        // 二级分类（始终显示，但三级可折叠）
        for (const [subcategory, tags] of Object.entries(data.children)) {
            const subcategoryDiv = document.createElement('div');
            subcategoryDiv.className = 'tag-subcategory';

            // 三级选项（默认折叠）- 先创建
            const optionsDiv = document.createElement('div');
            optionsDiv.className = 'tag-options collapsed';

            // 二级标题（可点击折叠三级）
            const subcategoryTitle = document.createElement('div');
            subcategoryTitle.className = 'tag-subcategory-title collapsed';
            subcategoryTitle.innerHTML = `<i class="fa fa-chevron-down toggle-icon"></i><span>${subcategory}</span>`;
            subcategoryTitle.onclick = () => {
                subcategoryTitle.classList.toggle('collapsed');
                optionsDiv.classList.toggle('collapsed');
            };
            subcategoryDiv.appendChild(subcategoryTitle);

            tags.forEach(tag => {
                const checkboxDiv = document.createElement('div');
                checkboxDiv.className = 'tag-checkbox';

                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.id = `rel_${tag}`;
                checkbox.value = tag;
                checkbox.dataset.category = 'relation';

                const label = document.createElement('label');
                label.htmlFor = `rel_${tag}`;
                label.textContent = tag.split('-').pop();
                label.title = tag;

                checkboxDiv.appendChild(checkbox);
                checkboxDiv.appendChild(label);
                optionsDiv.appendChild(checkboxDiv);
            });

            subcategoryDiv.appendChild(optionsDiv);
            categoryDiv.appendChild(subcategoryDiv);
        }

        container.appendChild(categoryDiv);
    }
}

// 渲染症状标签（三级折叠，二级露出）
function renderSymptomTags() {
    if (!tagsLibrary) return;

    const container = document.getElementById('symptomTagsContainer');
    const symptomTags = tagsLibrary.symptom_tags;

    for (const [category, data] of Object.entries(symptomTags)) {
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'tag-category';

        // 一级分类标题（始终显示）
        const categoryTitle = document.createElement('div');
        categoryTitle.className = 'tag-category-title';
        categoryTitle.innerHTML = `<span>${data.icon}</span><span>${category}</span>`;
        categoryDiv.appendChild(categoryTitle);

        const children = data.children;

        if (Array.isArray(children)) {
            // 直接是标签数组（这种情况作为一个二级分类处理）
            const subcategoryDiv = document.createElement('div');
            subcategoryDiv.className = 'tag-subcategory';

            // 三级选项（默认折叠）- 先创建
            const optionsDiv = document.createElement('div');
            optionsDiv.className = 'tag-options collapsed';

            const subcategoryTitle = document.createElement('div');
            subcategoryTitle.className = 'tag-subcategory-title collapsed';
            subcategoryTitle.innerHTML = `<i class="fa fa-chevron-down toggle-icon"></i><span>全部</span>`;
            subcategoryTitle.onclick = () => {
                subcategoryTitle.classList.toggle('collapsed');
                optionsDiv.classList.toggle('collapsed');
            };
            subcategoryDiv.appendChild(subcategoryTitle);

            children.forEach(tag => {
                const checkboxDiv = document.createElement('div');
                checkboxDiv.className = 'tag-checkbox';

                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.id = `sym_${tag}`;
                checkbox.value = tag;
                checkbox.dataset.category = 'symptom';

                const label = document.createElement('label');
                label.htmlFor = `sym_${tag}`;
                label.textContent = tag.split('-').slice(1).join('-');
                label.title = tag;

                checkboxDiv.appendChild(checkbox);
                checkboxDiv.appendChild(label);
                optionsDiv.appendChild(checkboxDiv);
            });

            subcategoryDiv.appendChild(optionsDiv);
            categoryDiv.appendChild(subcategoryDiv);
        } else {
            // 有子分类（二级）
            for (const [subcategory, tags] of Object.entries(children)) {
                const subcategoryDiv = document.createElement('div');
                subcategoryDiv.className = 'tag-subcategory';

                // 三级选项（默认折叠）- 先创建
                const optionsDiv = document.createElement('div');
                optionsDiv.className = 'tag-options collapsed';

                const subcategoryTitle = document.createElement('div');
                subcategoryTitle.className = 'tag-subcategory-title collapsed';
                subcategoryTitle.innerHTML = `<i class="fa fa-chevron-down toggle-icon"></i><span>${subcategory}</span>`;
                subcategoryTitle.onclick = () => {
                    subcategoryTitle.classList.toggle('collapsed');
                    optionsDiv.classList.toggle('collapsed');
                };
                subcategoryDiv.appendChild(subcategoryTitle);

                tags.forEach(tag => {
                    const checkboxDiv = document.createElement('div');
                    checkboxDiv.className = 'tag-checkbox';

                    const checkbox = document.createElement('input');
                    checkbox.type = 'checkbox';
                    checkbox.id = `sym_${tag}`;
                    checkbox.value = tag;
                    checkbox.dataset.category = 'symptom';

                    const label = document.createElement('label');
                    label.htmlFor = `sym_${tag}`;
                    label.textContent = tag.split('-').slice(2).join('-');
                    label.title = tag;

                    checkboxDiv.appendChild(checkbox);
                    checkboxDiv.appendChild(label);
                    optionsDiv.appendChild(checkboxDiv);
                });

                subcategoryDiv.appendChild(optionsDiv);
                categoryDiv.appendChild(subcategoryDiv);
            }
        }

        container.appendChild(categoryDiv);
    }
}

// 渲染使用技巧
function renderTechniques() {
    if (!tagsLibrary) return;

    const container = document.getElementById('techniquesContainer');
    const techniques = tagsLibrary.techniques;

    for (const [school, techList] of Object.entries(techniques)) {
        const schoolDiv = document.createElement('div');
        schoolDiv.className = 'tag-category';

        const schoolTitle = document.createElement('div');
        schoolTitle.className = 'tag-category-title';
        schoolTitle.textContent = school;
        schoolDiv.appendChild(schoolTitle);

        const optionsDiv = document.createElement('div');
        optionsDiv.className = 'tag-options';

        techList.forEach(tech => {
            const checkboxDiv = document.createElement('div');
            checkboxDiv.className = 'tag-checkbox';

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = `tech_${tech}`;
            checkbox.value = tech;
            checkbox.dataset.category = 'technique';

            const label = document.createElement('label');
            label.htmlFor = `tech_${tech}`;
            label.textContent = tech;

            checkboxDiv.appendChild(checkbox);
            checkboxDiv.appendChild(label);
            optionsDiv.appendChild(checkboxDiv);
        });

        schoolDiv.appendChild(optionsDiv);
        container.appendChild(schoolDiv);
    }
}

// 切换折叠状态
function toggleCollapse(header) {
    header.classList.toggle('collapsed');
    const content = header.nextElementSibling;
    if (content && content.classList.contains('collapsible-content')) {
        content.classList.toggle('collapsed');
    }
}

// 全部展开/收起关系标签
function toggleAllRelationTags() {
    const headers = document.querySelectorAll('#relationTagsContainer .tag-subcategory-title');
    const allCollapsed = Array.from(headers).every(h => h.classList.contains('collapsed'));

    headers.forEach(header => {
        const optionsDiv = header.nextElementSibling;
        if (allCollapsed) {
            header.classList.remove('collapsed');
            optionsDiv?.classList.remove('collapsed');
        } else {
            header.classList.add('collapsed');
            optionsDiv?.classList.add('collapsed');
        }
    });
}

// 全部展开/收起症状标签
function toggleAllSymptomTags() {
    const headers = document.querySelectorAll('#symptomTagsContainer .tag-subcategory-title');
    const allCollapsed = Array.from(headers).every(h => h.classList.contains('collapsed'));

    headers.forEach(header => {
        const optionsDiv = header.nextElementSibling;
        if (allCollapsed) {
            header.classList.remove('collapsed');
            optionsDiv?.classList.remove('collapsed');
        } else {
            header.classList.add('collapsed');
            optionsDiv?.classList.add('collapsed');
        }
    });
}

// 设置Word文档上传
function setupWordUpload() {
    const dropZone = document.getElementById('wordDropZone');
    const fileInput = document.getElementById('wordFileInput');
    const statusDiv = document.getElementById('wordImportStatus');

    // 点击上传区域选择文件
    dropZone.addEventListener('click', (e) => {
        if (e.target === dropZone || e.target.closest('.upload-zone')) {
            fileInput.click();
        }
    });

    // 文件选择变化
    fileInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (file) {
            await processWordFile(file, statusDiv);
        }
    });

    // 拖拽上传
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragging');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragging');
    });

    dropZone.addEventListener('drop', async (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragging');

        const file = e.dataTransfer.files[0];
        if (file && (file.name.endsWith('.doc') || file.name.endsWith('.docx'))) {
            await processWordFile(file, statusDiv);
        } else {
            alert('请上传Word文档（.doc或.docx格式）');
        }
    });
}

// 处理Word文件
async function processWordFile(file, statusDiv) {
    statusDiv.innerHTML = '<div class="text-blue-600"><i class="fa fa-spinner fa-spin"></i> 正在识别文档...</div>';

    try {
        console.log('[Word上传] 开始处理文件:', file.name);

        const formData = new FormData();
        formData.append('file', file);

        console.log('[Word上传] 发送请求到:', `${CONFIG_API}/api/word/parse`);
        const response = await fetch(`${CONFIG_API}/api/word/parse`, {
            method: 'POST',
            body: formData
        });

        console.log('[Word上传] 响应状态:', response.status, response.statusText);

        if (!response.ok) {
            throw new Error('文档解析失败: ' + response.status);
        }

        const data = await response.json();
        console.log('[Word上传] 解析后的数据:', JSON.stringify(data, null, 2));

        // 自动填充表单
        console.log('[Word上传] 开始填充表单...');
        fillFormFromWordData(data);
        console.log('[Word上传] 表单填充完成');

        statusDiv.innerHTML = '<div class="text-green-600"><i class="fa fa-check-circle"></i> 文档识别成功，已自动填充表单</div>';

        // 3秒后隐藏状态
        setTimeout(() => {
            statusDiv.innerHTML = '';
        }, 3000);

    } catch (error) {
        console.error('[Word上传] 处理失败:', error);
        statusDiv.innerHTML = '<div class="text-red-600"><i class="fa fa-times-circle"></i> 文档识别失败: ' + error.message + '</div>';
    }
}

// 从Word数据填充表单
function fillFormFromWordData(data) {
    // 判断是否为后续接访模式
    const isFollowUp = isFollowUpSession && currentCase;

    // 基本信息（后续接访时跳过静态字段）
    if (!isFollowUp && data.basic_info) {
        if (data.basic_info.代号) document.getElementById('代号').value = data.basic_info.代号;
        if (data.basic_info.性别) document.getElementById('性别').value = data.basic_info.性别;
        if (data.basic_info.年龄) document.getElementById('年龄').value = data.basic_info.年龄;
        if (data.basic_info.职业) document.getElementById('职业').value = data.basic_info.职业;
        if (data.basic_info.婚姻状况) document.getElementById('婚姻状况').value = data.basic_info.婚姻状况;
        if (data.basic_info.性取向) document.getElementById('性取向').value = data.basic_info.性取向;
        if (data.basic_info.宗教信仰) document.getElementById('宗教信仰').value = data.basic_info.宗教信仰;
        if (data.basic_info.来访者联系电话) document.getElementById('来访者联系电话').value = data.basic_info.来访者联系电话;
        if (data.basic_info.background) document.getElementById('背景信息').value = data.basic_info.background;
    }

    // 动态信息（后续接访时也可以更新）
    if (data.basic_info) {
        if (data.basic_info.紧急联系人) document.getElementById('紧急联系人').value = data.basic_info.紧急联系人;
        if (data.basic_info.紧急联系人关系) document.getElementById('紧急联系人关系').value = data.basic_info.紧急联系人关系;
        if (data.basic_info.紧急联系人电话) document.getElementById('紧急联系人电话').value = data.basic_info.紧急联系人电话;
        if (data.basic_info.用药情况) document.getElementById('用药情况').value = data.basic_info.用药情况;
        if (data.basic_info.来访备注) document.getElementById('来访备注').value = data.basic_info.来访备注;
    }

    // 接访信息（后续接访时只更新部分字段）
    if (data.session_info) {
        if (data.session_info.接访日期) document.getElementById('接访日期').value = data.session_info.接访日期;
        if (!isFollowUp && data.session_info.接访次数) document.getElementById('接访次数').value = data.session_info.接访次数;
        if (data.session_info.通话时长) document.getElementById('通话时长').value = data.session_info.通话时长;
        if (data.session_info.咨询渠道) document.getElementById('咨询渠道').value = data.session_info.咨询渠道;
        if (data.session_info.咨询师姓名) document.getElementById('咨询师姓名').value = data.session_info.咨询师姓名;
        if (data.session_info.案例状态) document.getElementById('案例状态').value = data.session_info.案例状态;
    }

    // 主诉和目标 - 优先使用AI分析后的核心诉求
    if (data.complaint_analysis && data.complaint_analysis.summarized_complaint) {
        const complaintField = document.getElementById('主诉');
        if (complaintField) {
            // 使用AI提炼后的核心诉求
            let complaintText = data.complaint_analysis.summarized_complaint;

            // 添加核心问题和情绪状态标注
            if (data.complaint_analysis.core_issue) {
                complaintText = `【核心问题】${data.complaint_analysis.core_issue}\n\n${complaintText}`;
            }
            if (data.complaint_analysis.emotional_state) {
                complaintText += `\n\n【情绪状态】${data.complaint_analysis.emotional_state}`;
            }

            complaintField.value = complaintText;
            console.log('[主诉] 已填充AI分析后的核心诉求:', data.complaint_analysis.core_issue);
        }
    } else if (data.complaint) {
        // 降级：没有AI分析时使用原始主诉
        const complaintField = document.getElementById('主诉');
        if (complaintField) {
            complaintField.value = data.complaint;
            console.log('[主诉] 已填充原始主诉内容');
        }
    }

    // 咨询目标（后续接访时跳过）
    if (!isFollowUp && data.咨询目标) {
        document.getElementById('咨询目标').value = data.咨询目标;
    }

    // 既往史（后续接访时跳过）
    if (!isFollowUp && data.既往史) {
        if (data.既往史.有既往咨询史) document.getElementById('有既往咨询史').checked = true;
        if (data.既往史.有精神科就诊史) document.getElementById('有精神科就诊史').checked = true;
        if (data.既往史.既往史详情) document.getElementById('既往史详情').value = data.既往史.既往史详情;
    }

    // 心理测评（后续接访时跳过）
    if (!isFollowUp && data.心理测评 && Array.isArray(data.心理测评)) {
        psychTestsList = data.心理测评;
        renderPsychTestsList();
    }

    // 家庭结构（后续接访时跳过）- 兼容family_structure和家庭结构两种格式
    const familyData = data.family_structure || data.家庭结构;
    if (!isFollowUp && familyData) {
        console.log('[家庭结构] 开始填充家庭结构:', familyData);
        if (familyData.父亲年龄) document.getElementById('父亲年龄').value = familyData.父亲年龄;
        if (familyData.父亲职业) document.getElementById('父亲职业').value = familyData.父亲职业;
        if (familyData.父亲身体情况) document.getElementById('父亲身体情况').value = familyData.父亲身体情况;
        if (familyData.母亲年龄) document.getElementById('母亲年龄').value = familyData.母亲年龄;
        if (familyData.母亲职业) document.getElementById('母亲职业').value = familyData.母亲职业;
        if (familyData.母亲身体情况) document.getElementById('母亲身体情况').value = familyData.母亲身体情况;
        if (familyData.父母关系) document.getElementById('父母关系').value = familyData.父母关系;
        if (familyData.兄弟姐妹) document.getElementById('兄弟姐妹').value = familyData.兄弟姐妹;
        if (familyData.配偶性别) document.getElementById('配偶性别').value = familyData.配偶性别;
        if (familyData.配偶年龄) document.getElementById('配偶年龄').value = familyData.配偶年龄;
        if (familyData.配偶职业) document.getElementById('配偶职业').value = familyData.配偶职业;
        if (familyData.配偶身体情况) document.getElementById('配偶身体情况').value = familyData.配偶身体情况;
        if (familyData.家庭备注) document.getElementById('家庭备注').value = familyData.家庭备注;
        console.log('[家庭结构] 家庭结构填充完成');

        // 加载孩子列表
        if (familyData.孩子列表 && Array.isArray(familyData.孩子列表)) {
            childrenList = familyData.孩子列表;
            renderChildrenList();
        }
    }

    // 咨询师复盘 - 填充Word原始对话内容
    if (data.dialogue) {
        const dialogueField = document.getElementById('dialogue');
        if (dialogueField) {
            dialogueField.value = data.dialogue;
            console.log('[咨询师复盘] 已填充对话内容，长度:', data.dialogue.length);

            // 同步到来访者档案的咨询师复盘
            // 在保存接访记录时，dialogue内容会同步到对应来访者档案
        } else {
            console.warn('[咨询师复盘] 未找到dialogue字段元素');
        }
    }

    // 咨询师小结
    if (data.counselor_reflection) {
        const reflectionField = document.getElementById('counselor_reflection') || document.getElementById('咨询师小结');
        if (reflectionField) {
            reflectionField.value = data.counselor_reflection;
            console.log('[咨询师小结] 已填充小结内容');
        }
    }

    // 关系标签
    if (data.tags && data.tags.relation) {
        data.tags.relation.forEach(tag => {
            const checkbox = document.querySelector(`input[value="${tag}"][data-category="relation"]`);
            if (checkbox) checkbox.checked = true;
        });
    }

    // 症状标签
    if (data.tags && data.tags.symptom) {
        data.tags.symptom.forEach(tag => {
            const checkbox = document.querySelector(`input[value="${tag}"][data-category="symptom"]`);
            if (checkbox) checkbox.checked = true;
        });
    }

    // 危机等级 - 支持大观学派A-Z 26级连续评估
    if (data.crisis_assessment && data.crisis_assessment.all_matched) {
        console.log('[危机等级] 开始处理危机等级（连续评估）:', data.crisis_assessment);

        // 1. 勾选所有匹配到的等级（连续评估的所有落脚点）
        const allMatched = data.crisis_assessment.all_matched; // 格式: ["L-L-敌意/报复", "E-E-痛苦绝望"]

        allMatched.forEach(matched => {
            // 提取等级代码（如 "L-L-敌意/报复" -> "L"）
            const levelCode = matched.split('-')[0];

            const checkbox = document.querySelector(`input.crisis-level-checkbox[value="${levelCode}"]`);
            console.log('[危机等级] 勾选匹配等级:', levelCode, checkbox);

            if (checkbox) {
                checkbox.checked = true;

                // 勾选所属的等级组
                const parentDiv = checkbox.closest('.border-2');
                if (parentDiv) {
                    const groupCheckbox = parentDiv.querySelector('input.crisis-class-checkbox');
                    if (groupCheckbox) {
                        groupCheckbox.checked = true;
                    }
                }
            }
        });

        // 2. 标记最终落脚点（最严重的等级）
        if (data.crisis_assessment.level) {
            const finalLevel = data.crisis_assessment.level;
            const finalCheckbox = document.querySelector(`input.crisis-level-checkbox[value="${finalLevel}"]`);

            if (finalCheckbox) {
                // 给最终落脚点添加特殊样式
                const label = finalCheckbox.closest('label');
                if (label) {
                    label.style.fontWeight = 'bold';
                    label.style.backgroundColor = '#fef3c7';
                    label.style.padding = '2px 6px';
                    label.style.borderRadius = '4px';
                    label.style.border = '2px solid #f59e0b';
                }
                console.log('[危机等级] 最终落脚点:', finalLevel);
            }
        }

        // 3. 填充评估依据
        if (data.crisis_assessment.evidence && data.crisis_assessment.evidence.length > 0) {
            const evidenceField = document.getElementById('危机评估备注') || document.getElementById('crisis_evidence') || document.getElementById('crisis_assessment_notes');
            console.log('[危机等级] 查找评估依据字段:', evidenceField);
            if (evidenceField) {
                const allMatchedText = data.crisis_assessment.all_matched.join('\n  · ');
                evidenceField.value = `【大观学派连续评估】\n\n` +
                    `最终落脚点：${data.crisis_assessment.level} - ${data.crisis_assessment.name} (${data.crisis_assessment.layer})\n\n` +
                    `连续评估过程（所有触及等级）：\n  · ${allMatchedText}\n\n` +
                    `证据关键词：${data.crisis_assessment.evidence.join('、')}`;
                console.log('[危机等级] 已填充评估依据:', evidenceField.value);
            }
        }
    }
    // 兼容旧格式
    else if (data.crisis_level) {
        console.log('[危机等级] 使用旧格式:', data.crisis_level);
        const radio = document.getElementById(`crisis_${data.crisis_level}`);
        if (radio) radio.checked = true;
    } else {
        console.log('[危机等级] 没有危机等级数据');
    }
    if (data.crisis_evidence) {
        const evidenceField = document.getElementById('crisis_evidence');
        if (evidenceField) evidenceField.value = data.crisis_evidence;
    }

    // 使用技巧
    if (data.techniques_used) {
        data.techniques_used.forEach(tech => {
            const checkbox = document.querySelector(`input[value="${tech}"][data-category="technique"]`);
            if (checkbox) checkbox.checked = true;
        });
    }

    // 督导信息
    if (data.督导信息) {
        if (data.督导信息.督导状态) document.getElementById('督导状态').value = data.督导信息.督导状态;
        if (data.督导信息.督导师姓名) document.getElementById('督导师姓名').value = data.督导信息.督导师姓名;
        if (data.督导信息.督导日期) document.getElementById('督导日期').value = data.督导信息.督导日期;
        if (data.督导信息.督导要点) document.getElementById('督导要点').value = data.督导信息.督导要点;
        if (data.督导信息.督导建议) document.getElementById('督导建议').value = data.督导信息.督导建议;
    }

    // 关键词
    if (data.keywords) {
        keywords = [...data.keywords];
        renderKeywords();
    }

    // 咨询师复盘（HTML中ID为'dialogue'）
    if (data.dialogue) {
        document.getElementById('dialogue').value = data.dialogue;
    }

    // 咨询师反思（如果有单独的字段）
    if (data.counselor_reflection) {
        const dialogueElem = document.getElementById('dialogue');
        if (dialogueElem && !dialogueElem.value) {
            dialogueElem.value = data.counselor_reflection;
        }
    }

    // 下一步计划
    if (data.next_session_plan) {
        document.getElementById('next_session_plan').value = data.next_session_plan;
    }

    // 更新已选标签显示
    updateSelectedTags();
}


// 更新已选标签显示
function updateSelectedTags() {
    const container = document.getElementById('selectedTagsDisplay');
    const section = document.getElementById('selectedTagsSection');

    const relationTags = Array.from(document.querySelectorAll('input[data-category="relation"]:checked'))
        .map(cb => ({ value: cb.value, type: 'relation' }));

    const symptomTags = Array.from(document.querySelectorAll('input[data-category="symptom"]:checked'))
        .map(cb => ({ value: cb.value, type: 'symptom' }));

    const allTags = [...relationTags, ...symptomTags];

    if (allTags.length === 0) {
        section.style.display = 'none';
        return;
    }

    section.style.display = 'block';
    container.innerHTML = '';

    allTags.forEach(tag => {
        const badge = document.createElement('span');
        badge.className = `selected-tag-badge ${tag.type}`;
        badge.innerHTML = `
            <span>${tag.value}</span>
            <i class="fa fa-check-circle"></i>
        `;
        container.appendChild(badge);
    });
}

// 检查是否需要显示前情概要
function checkPreviousSessions() {
    const sessionNum = document.getElementById('接访次数').value.trim();
    const section = document.getElementById('previousSummarySection');

    // 如果不是第1次，显示前情概要区域
    if (sessionNum && !sessionNum.includes('第1次') && !sessionNum.includes('1次')) {
        section.style.display = 'block';
    } else {
        section.style.display = 'none';
    }
}

// 加载前情概要
async function loadPreviousSummary() {
    const caseAlias = document.getElementById('代号').value.trim();
    const statusSpan = document.getElementById('previousSummaryStatus');
    const contentDiv = document.getElementById('previousSummaryContent');

    if (!caseAlias) {
        alert('请先填写案例代号');
        return;
    }

    statusSpan.textContent = '正在加载...';

    try {
        const response = await fetch(`${CONFIG_API}/api/cases/search?alias=${encodeURIComponent(caseAlias)}`);

        if (!response.ok) {
            throw new Error('未找到该案例的历史记录');
        }

        const cases = await response.json();

        if (!cases || cases.length === 0) {
            contentDiv.innerHTML = '<p class="text-gray-500 text-center">未找到该案例的历史记录</p>';
            statusSpan.textContent = '';
            return;
        }

        // 显示最近一次的概要
        const lastCase = cases[cases.length - 1];
        const summary = lastCase.analyses?.daguanpai?.ai_analysis?.summary || '暂无概要';

        contentDiv.innerHTML = `
            <div class="mb-3">
                <span class="text-sm font-medium text-gray-600">上次接访：</span>
                <span class="text-sm text-gray-800">${lastCase.session_info?.接访日期 || '未知'}</span>
                <span class="text-sm text-gray-600 ml-4">案例编号：</span>
                <span class="text-sm text-gray-800">${lastCase.case_id}</span>
            </div>
            <div class="text-sm text-gray-700 whitespace-pre-wrap">${summary}</div>
        `;

        statusSpan.textContent = '加载成功';

    } catch (error) {
        console.error('加载前情概要失败:', error);
        contentDiv.innerHTML = `<p class="text-red-500 text-center">${error.message}</p>`;
        statusSpan.textContent = '';
    }
}

// 添加关键词
function addKeyword() {
    const input = document.getElementById('keywordInput');
    const keyword = input.value.trim();

    if (keyword && !keywords.includes(keyword)) {
        keywords.push(keyword);
        renderKeywords();
        input.value = '';
    }
}

// 渲染关键词标签
function renderKeywords() {
    const container = document.getElementById('keywordTags');
    container.innerHTML = '';

    keywords.forEach((keyword, index) => {
        const tag = document.createElement('span');
        tag.className = 'inline-flex items-center gap-2 px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm';
        tag.innerHTML = `
            ${keyword}
            <button onclick="removeKeyword(${index})" class="text-purple-600 hover:text-purple-800">
                <i class="fa fa-times"></i>
            </button>
        `;
        container.appendChild(tag);
    });
}

// 删除关键词
function removeKeyword(index) {
    keywords.splice(index, 1);
    renderKeywords();
}

// 设置文件上传
function setupFileUpload(type, fileArray) {
    const dropZone = document.getElementById(`${type}DropZone`);
    const fileInput = document.getElementById(`${type}FileInput`);
    const fileList = document.getElementById(`${type}FileList`);

    // 点击上传区域选择文件
    dropZone.addEventListener('click', (e) => {
        if (e.target === dropZone || e.target.closest('.upload-zone')) {
            fileInput.click();
        }
    });

    // 文件选择变化
    fileInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        files.forEach(file => {
            if (!fileArray.find(f => f.name === file.name && f.size === file.size)) {
                fileArray.push(file);
            }
        });
        renderFileList(type, fileArray, fileList);
    });

    // 拖拽上传
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragging');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragging');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragging');

        const files = Array.from(e.dataTransfer.files);
        files.forEach(file => {
            if (!fileArray.find(f => f.name === file.name && f.size === file.size)) {
                fileArray.push(file);
            }
        });
        renderFileList(type, fileArray, fileList);
    });
}

// 渲染文件列表
function renderFileList(type, fileArray, container) {
    container.innerHTML = '';

    fileArray.forEach((file, index) => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.innerHTML = `
            <div class="flex items-center gap-3">
                <i class="fa fa-file-o text-gray-500"></i>
                <div>
                    <div class="font-medium text-gray-800">${file.name}</div>
                    <div class="text-xs text-gray-500">${(file.size / 1024).toFixed(2)} KB</div>
                </div>
            </div>
            <button onclick="removeFile('${type}', ${index})" class="text-red-500 hover:text-red-700">
                <i class="fa fa-trash"></i>
            </button>
        `;
        container.appendChild(fileItem);
    });
}

// 删除文件
function removeFile(type, index) {
    if (type === 'audio') {
        selectedAudioFiles.splice(index, 1);
        renderFileList('audio', selectedAudioFiles, document.getElementById('audioFileList'));
    } else if (type === 'transcript') {
        selectedTranscriptFiles.splice(index, 1);
        renderFileList('transcript', selectedTranscriptFiles, document.getElementById('transcriptFileList'));
    } else if (type === 'supervision') {
        selectedSupervisionFiles.splice(index, 1);
        renderFileList('supervision', selectedSupervisionFiles, document.getElementById('supervisionFileList'));
    }
}

// 生成案例ID
function generateCaseId() {
    const today = new Date();
    const dateStr = today.toISOString().slice(0, 10).replace(/-/g, '');
    const randomNum = Math.floor(Math.random() * 900) + 100;
    return `C${dateStr}${randomNum}`;
}

// 收集表单数据
function collectFormData() {
    // 基本信息
    const basicInfo = {
        代号: document.getElementById('代号').value.trim(),
        性别: document.getElementById('性别').value,
        年龄: document.getElementById('年龄').value.trim(),
        职业: document.getElementById('职业').value.trim(),
        婚姻状况: document.getElementById('婚姻状况').value,
        性取向: document.getElementById('性取向').value,
        宗教信仰: document.getElementById('宗教信仰').value,
        来访者联系电话: document.getElementById('来访者联系电话').value.trim(),
        紧急联系人: document.getElementById('紧急联系人').value.trim(),
        紧急联系人关系: document.getElementById('紧急联系人关系').value.trim(),
        紧急联系人电话: document.getElementById('紧急联系人电话').value.trim(),
        用药情况: document.getElementById('用药情况').value.trim(),
        来访备注: document.getElementById('来访备注').value.trim(),
        background: document.getElementById('背景信息').value.trim()
    };

    // 接访信息
    const sessionInfo = {
        接访日期: document.getElementById('接访日期').value,
        接访次数: document.getElementById('接访次数').value.trim(),
        通话时长: document.getElementById('通话时长').value.trim(),
        咨询渠道: document.getElementById('咨询渠道').value,
        咨询师姓名: document.getElementById('咨询师姓名').value.trim(),
        案例状态: document.getElementById('案例状态').value
    };

    // 来访者主诉
    const 主诉 = document.getElementById('主诉').value.trim();

    // 咨询目标
    const 咨询目标 = document.getElementById('咨询目标').value.trim();

    // 生命危机评估
    const selectedLevels = Array.from(document.querySelectorAll('.crisis-level-checkbox:checked'))
        .map(cb => cb.value);

    const 危机评估 = {
        选中等级: selectedLevels,
        最终评级: document.getElementById('最终评级').value,
        危机评估备注: document.getElementById('危机评估备注').value.trim(),
        六变三托: {
            性情大变: document.getElementById('征兆_性情大变').checked,
            行为大变: document.getElementById('征兆_行为大变').checked,
            财务大变: document.getElementById('征兆_财务大变').checked,
            语言大变: document.getElementById('征兆_语言大变').checked,
            身体大变: document.getElementById('征兆_身体大变').checked,
            环境大变: document.getElementById('征兆_环境大变').checked,
            托人: document.getElementById('征兆_托人').checked,
            托事: document.getElementById('征兆_托事').checked,
            托物: document.getElementById('征兆_托物').checked
        }
    };

    // 既往史
    const 既往史 = {
        有既往咨询史: document.getElementById('有既往咨询史').checked,
        有精神科就诊史: document.getElementById('有精神科就诊史').checked,
        既往史详情: document.getElementById('既往史详情').value.trim()
    };

    // 心理测评
    const 心理测评 = psychTestsList;

    // 家庭结构
    const 家庭结构 = {
        父亲年龄: document.getElementById('父亲年龄').value.trim(),
        父亲职业: document.getElementById('父亲职业').value.trim(),
        父亲身体情况: document.getElementById('父亲身体情况').value.trim(),
        母亲年龄: document.getElementById('母亲年龄').value.trim(),
        母亲职业: document.getElementById('母亲职业').value.trim(),
        母亲身体情况: document.getElementById('母亲身体情况').value.trim(),
        父母关系: document.getElementById('父母关系').value,
        兄弟姐妹: document.getElementById('兄弟姐妹').value.trim(),
        配偶性别: document.getElementById('配偶性别').value,
        配偶年龄: document.getElementById('配偶年龄').value.trim(),
        配偶职业: document.getElementById('配偶职业').value.trim(),
        配偶身体情况: document.getElementById('配偶身体情况').value.trim(),
        孩子列表: childrenList,
        家庭备注: document.getElementById('家庭备注').value.trim()
    };

    // 关系标签
    const relationTags = Array.from(document.querySelectorAll('input[data-category="relation"]:checked'))
        .map(cb => cb.value);

    // 症状标签
    const symptomTags = Array.from(document.querySelectorAll('input[data-category="symptom"]:checked'))
        .map(cb => cb.value);

    // 使用技巧
    const techniquesUsed = Array.from(document.querySelectorAll('input[data-category="technique"]:checked'))
        .map(cb => cb.value);

    // 督导信息
    const 督导信息 = {
        督导状态: document.getElementById('督导状态').value,
        督导师姓名: document.getElementById('督导师姓名').value.trim(),
        督导日期: document.getElementById('督导日期').value,
        督导要点: document.getElementById('督导要点').value.trim(),
        督导建议: document.getElementById('督导建议').value.trim()
    };

    // 对话记录
    const dialogue = document.getElementById('dialogue').value.trim();

    // 咨询结果
    const consultationResult = document.getElementById('consultation_result').value.trim();

    // 布置任务
    const assignedTasks = document.getElementById('assigned_tasks').value.trim();

    // 下一步计划
    const nextStepPlan = document.getElementById('next_step_plan').value.trim();

    // 症状变化
    const symptomChanges = document.getElementById('symptom_changes').value.trim();

    // 咨询师反思
    const counselorReflection = document.getElementById('counselor_reflection').value.trim();

    // 下次接访建议
    const nextSessionPlan = document.getElementById('next_session_plan').value.trim();

    // 本次目标
    const 本次目标 = document.getElementById('本次目标')?.value.trim() || '';

    // 咨询进度
    const 咨询进度 = document.getElementById('咨询进度')?.value.trim() || '';

    return {
        basic_info: basicInfo,
        session_info: sessionInfo,
        主诉: 主诉,
        咨询目标: 咨询目标,
        本次目标: 本次目标,
        咨询进度: 咨询进度,
        危机评估: 危机评估,
        既往史: 既往史,
        心理测评: 心理测评,
        家庭结构: 家庭结构,
        tags: {
            relation: relationTags,
            symptom: symptomTags
        },
        techniques_used: techniquesUsed,
        督导信息: 督导信息,
        keywords: keywords,
        dialogue: dialogue,
        consultation_result: consultationResult,
        assigned_tasks: assignedTasks,
        next_step_plan: nextStepPlan,
        symptom_changes: symptomChanges,
        counselor_reflection: counselorReflection,
        next_session_plan: nextSessionPlan
    };
}

// 验证表单
function validateForm(data) {
    const errors = [];

    if (!data.basic_info.代号) {
        errors.push('请填写案例代号');
    }

    if (!data.basic_info.性别) {
        errors.push('请选择性别');
    }

    if (!data.basic_info.年龄) {
        errors.push('请填写年龄');
    }

    if (!data.session_info.接访日期) {
        errors.push('请选择接访日期');
    }

    if (!data.session_info.咨询师姓名 || data.session_info.咨询师姓名.trim() === '') {
        errors.push('请填写咨询师姓名');
    }

    if (!data.主诉) {
        errors.push('请填写来访者主诉');
    }

    if (!data.dialogue) {
        errors.push('请填写咨询师复盘');
    }

    // 危机评估：至少选择一个等级或填写最终评级
    if (data.危机评估.选中等级.length === 0 && !data.危机评估.最终评级) {
        errors.push('请至少选择一个危机等级或填写最终评级');
    }

    return errors;
}

// 上传文件到服务器
async function uploadFiles(caseId) {
    const results = {
        audio: [],
        transcript: [],
        supervision: []
    };

    // 上传录音
    for (const file of selectedAudioFiles) {
        try {
            const formData = new FormData();
            formData.append('audio', file);
            formData.append('case_id', caseId);

            const response = await fetch(`${AUDIO_API}/api/upload`, {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                results.audio.push(result.filename);
            }
        } catch (error) {
            console.error('录音上传失败:', file.name, error);
        }
    }

    // 上传逐字稿
    for (const file of selectedTranscriptFiles) {
        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('case_id', caseId);

            const response = await fetch(`${TRANSCRIPT_API}/api/upload`, {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                results.transcript.push(result.filename);
            }
        } catch (error) {
            console.error('逐字稿上传失败:', file.name, error);
        }
    }

    // 上传督导资料
    for (const file of selectedSupervisionFiles) {
        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('case_id', caseId);
            formData.append('title', file.name);

            const response = await fetch(`${SUPERVISION_API}/api/upload`, {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                results.supervision.push(result.filename);
            }
        } catch (error) {
            console.error('督导资料上传失败:', file.name, error);
        }
    }

    return results;
}

// 保存案例
async function saveCase() {
    // 收集数据
    const formData = collectFormData();

    // 验证
    const errors = validateForm(formData);
    if (errors.length > 0) {
        alert('请完善以下信息:\n' + errors.join('\n'));
        return;
    }

    // 显示保存中状态
    const saveBtn = event.target;
    const originalText = saveBtn.innerHTML;
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> 正在保存...';

    try {
        if (isFollowUpSession && currentCase) {
            // 后续会谈模式：添加新的会谈记录
            await saveFollowUpSession(formData);
        } else {
            // 首次接访模式：创建新案例
            await saveNewCase(formData);
        }

        // 清除草稿
        localStorage.removeItem('intake_draft');
        localStorage.removeItem('intake_draft_timestamp');

        // 提供下一步操作选项
        const nextAction = confirm('保存成功！\n\n点击【确定】继续录入新案例\n点击【取消】留在当前页面查看');
        if (nextAction) {
            resetForm();
            currentCase = null;
            isFollowUpSession = false;
            document.getElementById('wordImportSection').style.display = 'block';
        }

    } catch (error) {
        console.error('保存失败:', error);
        alert('保存失败：' + error.message);
    } finally {
        saveBtn.disabled = false;
        saveBtn.innerHTML = originalText;
    }
}

// 保存新案例（首次接访）
async function saveNewCase(formData) {
    // 调用新的接访记录保存API
    const response = await fetch(`${INTAKE_API}/save_new_case`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
    });

    const result = await response.json();
    if (!result.success) {
        throw new Error(result.error || '创建案例失败');
    }

    const visitorId = result.visitor_id;
    const visitId = result.visit_id;

    // 上传录音文件
    if (selectedAudioFiles.length > 0) {
        console.log(`开始上传 ${selectedAudioFiles.length} 个录音文件...`);
        for (const file of selectedAudioFiles) {
            try {
                const formData = new FormData();
                formData.append('file', file);
                formData.append('visitor_id', visitorId);
                formData.append('visit_id', visitId);
                formData.append('description', `接访记录上传 - ${file.name}`);

                const uploadResponse = await fetch(`${RECORDING_API}/upload`, {
                    method: 'POST',
                    body: formData
                });

                const uploadResult = await uploadResponse.json();
                if (uploadResult.success) {
                    console.log(`✓ 录音上传成功: ${file.name}`);
                } else {
                    console.error(`✗ 录音上传失败: ${file.name}`, uploadResult.error);
                }
            } catch (error) {
                console.error('录音上传失败:', file.name, error);
            }
        }
    }

    alert(`案例创建成功！\n来访者ID：${visitorId}\n来访ID：${visitId}`);
}

// 保存后续会谈
async function saveFollowUpSession(formData) {
    const visitorId = currentCase.case_id;

    // 检测用药情况是否变化（包括新增、修改、停药）
    const oldMedication = currentCase.dynamic_info.用药情况?.current || '';
    const newMedication = formData.basic_info.用药情况;

    if (newMedication !== oldMedication && (newMedication.trim() !== '' || oldMedication.trim() !== '')) {
        const changeType = !oldMedication ? '新增用药' : !newMedication ? '停止用药' : '修改用药';
        const medicationChangeReason = prompt(`检测到用药情况发生变化（${changeType}），请说明原因（必填）：\n\n旧用药：${oldMedication || '无'}\n新用药：${newMedication || '无'}`);
        if (!medicationChangeReason || medicationChangeReason.trim() === '') {
            throw new Error('用药情况修改原因为必填项');
        }
        // 将变更原因添加到来访备注中
        formData.basic_info.来访备注 = (formData.basic_info.来访备注 || '') + `\n[${changeType}] ${medicationChangeReason}`;
    }

    // 构建后续会谈数据（匹配后端API格式）
    const followUpData = {
        visitor_id: visitorId,
        session_info: formData.session_info,
        主诉: formData.主诉,
        本次目标: formData.本次目标,
        咨询进度: formData.咨询进度,
        危机评估: formData.危机评估,
        tags: formData.tags,
        techniques_used: formData.techniques_used,
        keywords: formData.keywords,
        dialogue: formData.dialogue,
        consultation_result: formData.consultation_result,
        assigned_tasks: formData.assigned_tasks,
        next_step_plan: formData.next_step_plan,
        symptom_changes: formData.symptom_changes,
        counselor_reflection: formData.counselor_reflection,
        next_session_plan: formData.next_session_plan,
        督导信息: formData.督导信息,
        basic_info: formData.basic_info  // 包含动态信息更新
    };

    // 调用后续会谈保存API
    const response = await fetch(`${INTAKE_API}/save_follow_up`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(followUpData)
    });

    const result = await response.json();
    if (!result.success) {
        throw new Error(result.error || '保存后续会谈失败');
    }

    const visitId = result.visit_id;
    const visitNumber = result.visit_number;

    // 上传录音文件
    if (selectedAudioFiles.length > 0) {
        console.log(`开始上传 ${selectedAudioFiles.length} 个录音文件...`);
        for (const file of selectedAudioFiles) {
            try {
                const formData = new FormData();
                formData.append('file', file);
                formData.append('visitor_id', visitorId);
                formData.append('visit_id', visitId);
                formData.append('description', `第${visitNumber}次接访 - ${file.name}`);

                const uploadResponse = await fetch(`${RECORDING_API}/upload`, {
                    method: 'POST',
                    body: formData
                });

                const uploadResult = await uploadResponse.json();
                if (uploadResult.success) {
                    console.log(`✓ 录音上传成功: ${file.name}`);
                } else {
                    console.error(`✗ 录音上传失败: ${file.name}`, uploadResult.error);
                }
            } catch (error) {
                console.error('录音上传失败:', file.name, error);
            }
        }
    }

    // 上传逐字稿文件（使用新的8769端口API）
    if (selectedTranscriptFiles.length > 0) {
        console.log(`开始上传 ${selectedTranscriptFiles.length} 个逐字稿文件...`);
        for (const file of selectedTranscriptFiles) {
            try {
                const formData = new FormData();
                formData.append('file', file);
                formData.append('visitor_id', visitorId);
                formData.append('visit_id', visitId);
                formData.append('description', `第${visitNumber}次接访 - ${file.name}`);

                const uploadResponse = await fetch(`${TRANSCRIPT_UPLOAD_API}/upload`, {
                    method: 'POST',
                    body: formData
                });

                const uploadResult = await uploadResponse.json();
                if (uploadResult.success) {
                    console.log(`✓ 逐字稿上传成功: ${file.name}`);
                } else {
                    console.error(`✗ 逐字稿上传失败: ${file.name}`, uploadResult.error);
                }
            } catch (error) {
                console.error('逐字稿上传失败:', file.name, error);
            }
        }
    }

    alert(`后续会谈保存成功！\n来访者ID：${visitorId}\n来访ID：${visitId}\n本次为第 ${visitNumber} 次会谈`);
}

// 估算出生日期（根据年龄）
function estimateBirthDate(age) {
    if (!age || age === '') return '';
    const currentYear = new Date().getFullYear();
    const birthYear = currentYear - parseInt(age);
    return `${birthYear}-06-01`;  // 默认6月1日
}

// 重置表单
function resetForm() {
    // 清空基本信息
    document.getElementById('代号').value = '';
    document.getElementById('性别').value = '';
    document.getElementById('年龄').value = '';
    document.getElementById('职业').value = '';
    document.getElementById('婚姻状况').value = '';
    document.getElementById('性取向').value = '';
    document.getElementById('宗教信仰').value = '';
    document.getElementById('紧急联系人').value = '';
    document.getElementById('紧急联系人关系').value = '';
    document.getElementById('紧急联系人电话').value = '';
    document.getElementById('用药情况').value = '';
    document.getElementById('来访备注').value = '';
    document.getElementById('接访日期').valueAsDate = new Date();
    document.getElementById('接访次数').value = '';
    document.getElementById('通话时长').value = '';
    document.getElementById('咨询渠道').value = '';
    document.getElementById('咨询师姓名').value = '';
    document.getElementById('案例状态').value = '进行中';

    // 清空主诉和目标
    document.getElementById('主诉').value = '';
    document.getElementById('咨询目标').value = '';

    // 清空既往史
    document.getElementById('有既往咨询史').checked = false;
    document.getElementById('有精神科就诊史').checked = false;
    document.getElementById('既往史详情').value = '';

    // 清空心理测评
    psychTestsList = [];
    renderPsychTestsList();

    // 清空家庭结构
    document.getElementById('父亲年龄').value = '';
    document.getElementById('父亲职业').value = '';
    document.getElementById('父亲身体情况').value = '';
    document.getElementById('母亲年龄').value = '';
    document.getElementById('母亲职业').value = '';
    document.getElementById('母亲身体情况').value = '';
    document.getElementById('父母关系').value = '';
    document.getElementById('兄弟姐妹').value = '';
    document.getElementById('配偶性别').value = '';
    document.getElementById('配偶年龄').value = '';
    document.getElementById('配偶职业').value = '';
    document.getElementById('配偶身体情况').value = '';
    document.getElementById('家庭备注').value = '';

    // 清空孩子列表
    childrenList = [];
    renderChildrenList();

    // 清空标签选择
    document.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);

    // 重置危机评级
    document.getElementById('最终评级').value = '';
    document.getElementById('危机评估备注').value = '';

    // 清空关键词
    keywords = [];
    renderKeywords();

    // 清空督导信息
    document.getElementById('督导状态').value = '未督导';
    document.getElementById('督导师姓名').value = '';
    document.getElementById('督导日期').value = '';
    document.getElementById('督导要点').value = '';
    document.getElementById('督导建议').value = '';

    // 清空对话和反思
    document.getElementById('dialogue').value = '';
    document.getElementById('counselor_reflection').value = '';
    document.getElementById('next_session_plan').value = '';

    // 清空文件
    selectedAudioFiles = [];
    selectedTranscriptFiles = [];
    selectedSupervisionFiles = [];
    document.getElementById('audioFileList').innerHTML = '';
    document.getElementById('transcriptFileList').innerHTML = '';
    document.getElementById('supervisionFileList').innerHTML = '';

    // 隐藏已选标签和前情概要
    document.getElementById('selectedTagsSection').style.display = 'none';
    document.getElementById('previousSummarySection').style.display = 'none';

    // 清除草稿
    localStorage.removeItem('intake_draft');
    localStorage.removeItem('intake_draft_timestamp');

    // 滚动到顶部
    window.scrollTo(0, 0);
}

// 自动保存草稿
function autoSaveDraft() {
    try {
        const formData = collectFormData();
        // 只在有内容时保存
        if (formData.basic_info.代号 || formData.主诉 || formData.dialogue) {
            localStorage.setItem('intake_draft', JSON.stringify(formData));
            localStorage.setItem('intake_draft_timestamp', new Date().toISOString());
            localStorage.removeItem('intake_draft_ignored'); // 清除忽略标记
            console.log('草稿已自动保存');
        }
    } catch (error) {
        console.error('自动保存草稿失败:', error);
    }
}

// 手动保存草稿
function saveDraft() {
    try {
        const formData = collectFormData();
        localStorage.setItem('intake_draft', JSON.stringify(formData));
        localStorage.setItem('intake_draft_timestamp', new Date().toISOString());
        localStorage.removeItem('intake_draft_ignored'); // 清除忽略标记
        alert('草稿已保存！');
    } catch (error) {
        console.error('保存草稿失败:', error);
        alert('保存草稿失败：' + error.message);
    }
}

// 检查并加载草稿
function checkAndLoadDraft() {
    const draft = localStorage.getItem('intake_draft');
    const timestamp = localStorage.getItem('intake_draft_timestamp');
    const draftIgnored = localStorage.getItem('intake_draft_ignored');

    if (draft && timestamp) {
        const draftTime = new Date(timestamp);
        const now = new Date();
        const hoursDiff = (now - draftTime) / 1000 / 60 / 60;

        // 草稿在24小时内，且未被忽略
        if (hoursDiff < 24 && draftIgnored !== timestamp) {
            const loadDraft = confirm(`发现 ${Math.floor(hoursDiff)} 小时前保存的草稿\n\n是否恢复？`);
            if (loadDraft) {
                try {
                    const formData = JSON.parse(draft);
                    fillFormFromData(formData);
                    alert('草稿已恢复！');
                } catch (error) {
                    console.error('加载草稿失败:', error);
                    alert('加载草稿失败：' + error.message);
                }
            } else {
                // 点击取消，记录此草稿已被忽略，不再提示
                localStorage.setItem('intake_draft_ignored', timestamp);
            }
        } else if (hoursDiff >= 24) {
            // 清除过期草稿
            localStorage.removeItem('intake_draft');
            localStorage.removeItem('intake_draft_timestamp');
            localStorage.removeItem('intake_draft_ignored');
        }
    }
}

// 从数据填充表单（用于草稿恢复）
function fillFormFromData(data) {
    // 基本信息
    if (data.basic_info) {
        Object.keys(data.basic_info).forEach(key => {
            const elem = document.getElementById(key);
            if (elem && data.basic_info[key]) {
                elem.value = data.basic_info[key];
            }
        });
    }

    // 接访信息
    if (data.session_info) {
        Object.keys(data.session_info).forEach(key => {
            const elem = document.getElementById(key);
            if (elem && data.session_info[key]) {
                elem.value = data.session_info[key];
            }
        });
    }

    // 主诉和目标
    if (data.主诉) document.getElementById('主诉').value = data.主诉;
    if (data.咨询目标) document.getElementById('咨询目标').value = data.咨询目标;

    // 既往史
    if (data.既往史) {
        if (data.既往史.有既往咨询史) document.getElementById('有既往咨询史').checked = true;
        if (data.既往史.有精神科就诊史) document.getElementById('有精神科就诊史').checked = true;
        if (data.既往史.既往史详情) document.getElementById('既往史详情').value = data.既往史.既往史详情;
    }

    // 心理测评
    if (data.心理测评 && Array.isArray(data.心理测评)) {
        psychTestsList = data.心理测评;
        renderPsychTestsList();
    }

    // 家庭结构
    if (data.家庭结构) {
        Object.keys(data.家庭结构).forEach(key => {
            const elem = document.getElementById(key);
            if (elem && data.家庭结构[key]) {
                elem.value = data.家庭结构[key];
            }
        });
    }

    // 标签
    if (data.tags) {
        if (data.tags.relation) {
            data.tags.relation.forEach(tag => {
                const checkbox = document.querySelector(`input[value="${tag}"][data-category="relation"]`);
                if (checkbox) checkbox.checked = true;
            });
        }
        if (data.tags.symptom) {
            data.tags.symptom.forEach(tag => {
                const checkbox = document.querySelector(`input[value="${tag}"][data-category="symptom"]`);
                if (checkbox) checkbox.checked = true;
            });
        }
    }

    // 危机等级
    if (data.crisis_level) {
        const radio = document.getElementById(`crisis_${data.crisis_level}`);
        if (radio) radio.checked = true;
    }
    if (data.crisis_evidence) document.getElementById('crisis_evidence').value = data.crisis_evidence;

    // 使用技巧
    if (data.techniques_used) {
        data.techniques_used.forEach(tech => {
            const checkbox = document.querySelector(`input[value="${tech}"][data-category="technique"]`);
            if (checkbox) checkbox.checked = true;
        });
    }

    // 督导信息
    if (data.督导信息) {
        Object.keys(data.督导信息).forEach(key => {
            const elem = document.getElementById(key);
            if (elem && data.督导信息[key]) {
                elem.value = data.督导信息[key];
            }
        });
    }

    // 关键词
    if (data.keywords) {
        keywords = [...data.keywords];
        renderKeywords();
    }

    // 对话和反思
    if (data.dialogue) document.getElementById('dialogue').value = data.dialogue;
    if (data.counselor_reflection) document.getElementById('counselor_reflection').value = data.counselor_reflection;
    if (data.next_session_plan) document.getElementById('next_session_plan').value = data.next_session_plan;

    // 更新已选标签显示
    updateSelectedTags();
}

// ==================== 案例管理功能 ====================

// 加载案例（后续会谈模式）
async function loadCase() {
    const caseId = document.getElementById('caseIdInput').value.trim();
    const statusDiv = document.getElementById('caseLoadStatus');

    if (!caseId) {
        statusDiv.innerHTML = '<div class="text-red-600"><i class="fa fa-exclamation-circle"></i> 请输入案例代号</div>';
        return;
    }

    statusDiv.innerHTML = '<div class="text-blue-600"><i class="fa fa-spinner fa-spin"></i> 正在加载案例...</div>';

    try {
        const response = await fetch(`http://localhost:8768/api/load_case/${caseId}`);
        const result = await response.json();

        if (!result.success) {
            statusDiv.innerHTML = `<div class="text-red-600"><i class="fa fa-exclamation-circle"></i> ${result.error}</div>`;
            return;
        }

        currentCase = {
            case_id: result.case_id,
            static_info: result.static_info,
            dynamic_info: result.dynamic_info,
            total_sessions: result.total_sessions,
            next_session: result.next_session
        };
        isFollowUpSession = true;

        // 显示成功信息
        const totalSessions = result.total_sessions;
        const nextSession = result.next_session;
        statusDiv.innerHTML = `
            <div class="bg-green-50 border border-green-200 rounded-lg p-4">
                <div class="flex items-start gap-3">
                    <i class="fa fa-check-circle text-green-600 text-xl"></i>
                    <div class="flex-1">
                        <p class="font-semibold text-green-800 mb-1">案例加载成功</p>
                        <p class="text-sm text-green-700">
                            代号：${currentCase.static_info.代号} |
                            性别：${currentCase.static_info.性别} |
                            年龄：${currentCase.static_info.年龄}岁 |
                            已完成 ${totalSessions} 次会谈
                        </p>
                        <p class="text-sm text-green-700 mt-1">
                            <strong>本次为第 ${nextSession} 次会谈</strong>
                        </p>
                    </div>
                </div>
            </div>
        `;

        // 填充表单（后续会谈模式）
        fillFormForFollowUp();

    } catch (error) {
        console.error('加载案例失败:', error);
        statusDiv.innerHTML = '<div class="text-red-600"><i class="fa fa-exclamation-circle"></i> 无法连接到服务器，请确保后端服务已启动</div>';
    }
}

// 填充表单（后续会谈模式）
function fillFormForFollowUp() {
    // 1. 基本信息（设为只读）
    const staticInfo = currentCase.static_info;
    document.getElementById('代号').value = staticInfo.代号;
    document.getElementById('代号').readOnly = true;
    document.getElementById('性别').value = staticInfo.性别 || '';
    document.getElementById('性别').disabled = true;
    document.getElementById('年龄').value = staticInfo.年龄 || '';

    const birthDateElem = document.getElementById('出生日期');
    if (birthDateElem) {
        birthDateElem.value = staticInfo.出生日期 || '';
        birthDateElem.readOnly = true;
    }

    document.getElementById('职业').value = staticInfo.职业 || '';
    document.getElementById('婚姻状况').value = staticInfo.婚姻状况 || '';

    const 性取向Elem = document.getElementById('性取向');
    if (性取向Elem) 性取向Elem.value = staticInfo.性取向 || '';

    const 宗教信仰Elem = document.getElementById('宗教信仰');
    if (宗教信仰Elem) 宗教信仰Elem.value = staticInfo.宗教信仰 || '';

    const 来访者联系电话Elem = document.getElementById('来访者联系电话');
    if (来访者联系电话Elem) {
        来访者联系电话Elem.value = staticInfo.联系方式 || '';
        来访者联系电话Elem.readOnly = true;
        来访者联系电话Elem.style.backgroundColor = '#f3f4f6';
    }

    // 背景信息（后续接访只读，从档案读取）
    const backgroundElem = document.getElementById('背景信息');
    if (backgroundElem) {
        backgroundElem.value = staticInfo.background || '';
        backgroundElem.readOnly = true;
        backgroundElem.style.backgroundColor = '#f3f4f6';
        backgroundElem.style.cursor = 'not-allowed';
        const backgroundHint = document.getElementById('background-readonly-hint');
        if (backgroundHint) backgroundHint.style.display = 'inline';
    }

    // 2. 动态信息（可修改）
    const dynamicInfo = currentCase.dynamic_info;
    document.getElementById('紧急联系人').value = dynamicInfo.紧急联系人 || '';
    document.getElementById('紧急联系人关系').value = dynamicInfo.紧急联系人关系 || '';
    document.getElementById('紧急联系人电话').value = dynamicInfo.紧急联系人电话 || '';
    document.getElementById('用药情况').value = dynamicInfo.用药情况?.current || '';
    document.getElementById('来访备注').value = dynamicInfo.来访备注 || '';

    // 3. 主诉（不加载，每次接访重新填写）
    document.getElementById('主诉').value = '';
    document.getElementById('主诉').placeholder = '请描述来访者本次会谈的主诉内容...';

    // 4. 整体咨询目标（后续接访只读，从档案读取）
    const counselingGoalElem = document.getElementById('咨询目标');
    if (counselingGoalElem) {
        counselingGoalElem.value = staticInfo.counseling_goal || '';
        counselingGoalElem.readOnly = true;
        counselingGoalElem.style.backgroundColor = '#f3f4f6';
        counselingGoalElem.style.cursor = 'not-allowed';
        const counselingGoalHint = document.getElementById('counseling-goal-readonly-hint');
        if (counselingGoalHint) counselingGoalHint.style.display = 'inline';
    }

    // 5. 既往史（只读）
    if (staticInfo.既往史) {
        document.getElementById('有既往咨询史').checked = staticInfo.既往史.有既往咨询史 || false;
        document.getElementById('有既往咨询史').disabled = true;
        document.getElementById('有精神科就诊史').checked = staticInfo.既往史.有精神科就诊史 || false;
        document.getElementById('有精神科就诊史').disabled = true;
        document.getElementById('既往史详情').value = staticInfo.既往史.既往史详情 || '';
        document.getElementById('既往史详情').readOnly = true;
    }

    // 6. 家庭结构（只读）
    if (staticInfo.家庭结构) {
        const familyMapping = {
            'father_age': '父亲年龄',
            'father_occupation': '父亲职业',
            'father_health': '父亲身体情况',
            'mother_age': '母亲年龄',
            'mother_occupation': '母亲职业',
            'mother_health': '母亲身体情况',
            'parents_relationship': '父母关系',
            'siblings': '兄弟姐妹',
            'spouse_gender': '配偶性别',
            'spouse_age': '配偶年龄',
            'spouse_occupation': '配偶职业',
            'spouse_health': '配偶身体情况',
            'family_notes': '家庭备注'
        };

        Object.keys(familyMapping).forEach(enKey => {
            const cnKey = familyMapping[enKey];
            const elem = document.getElementById(cnKey);
            if (elem && staticInfo.家庭结构[enKey] !== undefined) {
                elem.value = staticInfo.家庭结构[enKey] || '';
                elem.readOnly = true;
                elem.style.backgroundColor = '#f3f4f6';
            }
        });

        // 处理孩子列表
        if (staticInfo.家庭结构.children && Array.isArray(staticInfo.家庭结构.children)) {
            childrenList = staticInfo.家庭结构.children;
            renderChildrenList();
            // 孩子列表在后续接访时也设为只读
            const addChildBtn = document.querySelector('button[onclick="addChild()"]');
            if (addChildBtn) addChildBtn.style.display = 'none';
        }
    }

    // 7. 接访信息（自动填充）
    const totalSessions = currentCase.total_sessions || 0;
    const nextSessionNum = totalSessions + 1;
    document.getElementById('接访次数').value = `第${nextSessionNum}次`;
    document.getElementById('接访日期').valueAsDate = new Date();

    // 8. Word上传区域（保留，用于后续接访的AI分析）
    // 不隐藏，允许上传Word进行本次会谈的AI分析

    // 10. 滚动到接访信息区域
    setTimeout(() => {
        const targetSection = Array.from(document.querySelectorAll('h2')).find(h2 => h2.textContent.includes('接访信息'));
        if (targetSection) {
            targetSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }, 500);
}

// 显示上次会谈概要
function showPreviousSummary(lastSession) {
    const summaryHtml = `
        <div class="section-box bg-yellow-50 border-2 border-yellow-300">
            <h2 class="section-title text-yellow-800">
                <i class="fa fa-history text-yellow-600"></i> 上次会谈概要（第${lastSession.session_number}次，${lastSession.date}）
            </h2>
            <div class="bg-white rounded-lg p-4">
                <p class="text-gray-700 whitespace-pre-wrap">${lastSession.summary || '暂无概要'}</p>
            </div>
        </div>
    `;

    // 在接访信息前插入
    const allH2 = Array.from(document.querySelectorAll('h2'));
    const 接访信息H2 = allH2.find(h2 => h2.textContent.includes('接访信息'));
    if (接访信息H2) {
        const 接访信息Section = 接访信息H2.closest('.section-box');
        接访信息Section.insertAdjacentHTML('beforebegin', summaryHtml);
    }
}

// 危机评估信息字典
const CRISIS_INFO = {
    // 第一等：轻度危机 - 生活事件失控（A-G）
    'A': { level: '轻度危机', class: '第一等', phrase: '不想活了', cognition: '千错万错都是别人的错 - 无法控制环境', intervention: '30分钟结案 | A-F六阶段求助等级技术' },
    'B': { level: '轻度危机', class: '第一等', phrase: '不想活了', cognition: '千错万错都是别人的错 - 无法控制环境', intervention: '30分钟结案 | A-F六阶段求助等级技术' },
    'C': { level: '轻度危机', class: '第一等', phrase: '不想活了', cognition: '千错万错都是别人的错 - 无法控制环境', intervention: '30分钟结案 | A-F六阶段求助等级技术' },
    'D': { level: '轻度危机', class: '第一等', phrase: '不想活了', cognition: '千错万错都是别人的错 - 无法控制环境', intervention: '30分钟结案 | A-F六阶段求助等级技术' },
    'E': { level: '轻度危机', class: '第一等', phrase: '不想活了', cognition: '千错万错都是别人的错 - 无法控制环境', intervention: '30分钟结案 | A-F六阶段求助等级技术' },
    'F': { level: '轻度危机', class: '第一等', phrase: '不想活了', cognition: '千错万错都是别人的错 - 无法控制环境', intervention: '30分钟结案 | A-F六阶段求助等级技术' },
    'G': { level: '轻度危机', class: '第一等', phrase: '不想活了', cognition: '千错万错都是别人的错 - 无法控制环境', intervention: '30分钟结案 | A-F六阶段求助等级技术' },

    // 第二等：轻度危机 - 人际冲突挫败（H-J）
    'H': { level: '轻度危机', class: '第二等', phrase: '不想活了', cognition: '泛化负向观 - 批评否定世界、他人、自己', intervention: '30分钟结案 | A-F六阶段求助等级技术' },
    'I': { level: '轻度危机', class: '第二等', phrase: '不想活了', cognition: '泛化负向观 - 批评否定世界、他人、自己', intervention: '30分钟结案 | A-F六阶段求助等级技术' },
    'J': { level: '轻度危机', class: '第二等', phrase: '不想活了', cognition: '泛化负向观 - 批评否定世界、他人、自己', intervention: '30分钟结案 | A-F六阶段求助等级技术' },

    // 第三等：中度危机 - 异常动机困扰（K-O）
    'K': { level: '中度危机', class: '第三等', phrase: '死了算了', cognition: '千错万错都是自己的错 - 异常动机（无前置事件）', intervention: '30分钟结案 | A-F六阶段求助等级技术' },
    'L': { level: '中度危机', class: '第三等', phrase: '死了算了', cognition: '千错万错都是自己的错 - 异常动机（无前置事件）', intervention: '30分钟结案 | A-F六阶段求助等级技术' },
    'M': { level: '中度危机', class: '第三等', phrase: '死了算了', cognition: '千错万错都是自己的错 - 异常动机（无前置事件）', intervention: '30分钟结案 | A-F六阶段求助等级技术' },
    'N': { level: '中度危机', class: '第三等', phrase: '死了算了', cognition: '千错万错都是自己的错 - 异常动机（无前置事件）', intervention: '30分钟结案 | A-F六阶段求助等级技术' },
    'O': { level: '中度危机', class: '第三等', phrase: '死了算了', cognition: '千错万错都是自己的错 - 异常动机（无前置事件）', intervention: '30分钟结案 | A-F六阶段求助等级技术' },

    // 第四等：中度危机 - 异常情绪困扰（P-R）
    'P': { level: '中度危机', class: '第四等', phrase: '死了算了', cognition: '千错万错都是自己的错 - 异常情绪（无前置事件）', intervention: '30分钟结案 | A-F六阶段求助等级技术' },
    'Q1': { level: '中度危机', class: '第四等', phrase: '死了算了', cognition: '不快乐 - 活不下去（被动型）', intervention: '30分钟结案 | A-F六阶段求助等级技术' },
    'Q2': { level: '中度危机', class: '第四等', phrase: '死了算了', cognition: '活不下去', intervention: '30分钟结案 | A-F六阶段求助等级技术' },
    'R1': { level: '中度危机', class: '第四等', phrase: '死了算了', cognition: '太痛苦了 - 常常想去死（主动型）', intervention: '30分钟结案 | A-F六阶段求助等级技术' },
    'R2': { level: '中度危机', class: '第四等', phrase: '死了算了', cognition: '死了算了 - 常常想去死（主动型）', intervention: '30分钟结案 | A-F六阶段求助等级技术' },

    // 第五等：重度危机 - 已启动自杀方程式（S-U）
    'S1': { level: '重度危机', class: '第五等', phrase: '我要自杀', cognition: '没有能力继续活下去 - 自杀动机（过去）', intervention: '60分钟结案 | 搬楼层技术' },
    'S2': { level: '重度危机', class: '第五等', phrase: '我要自杀', cognition: '没有能力继续活下去 - 自杀动机（现在）', intervention: '60分钟结案 | 搬楼层技术' },
    'S3': { level: '重度危机', class: '第五等', phrase: '我要自杀', cognition: '没有能力继续活下去 - 自杀动机（未来）', intervention: '60分钟结案 | 搬楼层技术' },
    'T': { level: '重度危机', class: '第五等', phrase: '我要自杀', cognition: '没有能力继续活下去 - 自杀意念（无前置事件）', intervention: '60分钟结案 | 搬楼层技术' },
    'U': { level: '重度危机', class: '第五等', phrase: '我要自杀', cognition: '没有能力继续活下去 - 目的性自杀', intervention: '60分钟结案 | 搬楼层技术' },

    // 第六等：重度危机 - 准备进入自杀程序（V-W）
    'V1': { level: '重度危机', class: '第六等', phrase: '我要自杀', cognition: '准备进入自杀程序 - 有自伤经验', intervention: '60分钟结案 | 搬楼层技术 | 需立即找人陪伴，避免独处' },
    'V2': { level: '重度危机', class: '第六等', phrase: '我要自杀', cognition: '准备进入自杀程序 - 无法制止自杀的处境', intervention: '60分钟结案 | 搬楼层技术 | 需立即找人陪伴，避免独处' },
    'W1': { level: '重度危机', class: '第六等', phrase: '我要自杀', cognition: '准备进入自杀程序 - 自杀安排', intervention: '60分钟结案 | 搬楼层技术 | 需立即找人陪伴，避免独处' },
    'W2': { level: '重度危机', class: '第六等', phrase: '我要自杀', cognition: '准备进入自杀程序 - 临终安排', intervention: '60分钟结案 | 搬楼层技术 | 需立即找人陪伴，避免独处' },

    // 第七等：急迫危机 - 已进入自杀程序（X-Z）
    'X': { level: '⛔ 急迫危机', class: '第七等', phrase: '⛔ 非死不可', cognition: '⛔ 没有能力阻止自己 - 立刻去死', intervention: '⛔ 不限时！救下来才能挂断 | NOPQ急迫危机技术 | 立即报警' },
    'Y': { level: '⛔ 急迫危机', class: '第七等', phrase: '⛔ 非死不可', cognition: '⛔ 没有能力阻止自己 - 病发失控', intervention: '⛔ 不限时！救下来才能挂断 | NOPQ急迫危机技术 | 立即报警' },
    'Z': { level: '⛔ 急迫危机', class: '第七等', phrase: '⛔ 非死不可', cognition: '⛔ 没有能力阻止自己 - 正在执行自杀', intervention: '⛔ 不限时！救下来才能挂断 | NOPQ急迫危机技术 | 立即报警' }
};

// 切换危机等级明细显示/隐藏
// 更新系统建议评级（仅供参考，不自动填充）
function updateSuggestedRating() {
    const selectedLevels = Array.from(document.querySelectorAll('.crisis-level-checkbox:checked'))
        .map(cb => cb.value);

    const suggestedBox = document.getElementById('suggestedRatingBox');
    const suggestedDisplay = document.getElementById('suggestedRatingDisplay');

    if (selectedLevels.length === 0) {
        suggestedBox.style.display = 'none';
        return;
    }

    // 按字母顺序排序，找到最低（最严重）的等级
    selectedLevels.sort();
    const lowestLevel = selectedLevels[selectedLevels.length - 1];

    // 特殊处理Q1/Q2和R1/R2，按层级分组找最严重
    let finalLevel = lowestLevel;
    if (selectedLevels.some(l => l.startsWith('Z') || l.startsWith('Y') || l.startsWith('X'))) {
        finalLevel = selectedLevels.filter(l => l.startsWith('Z') || l.startsWith('Y') || l.startsWith('X')).sort().pop();
    } else if (selectedLevels.some(l => l.startsWith('W') || l.startsWith('V'))) {
        finalLevel = selectedLevels.filter(l => l.startsWith('W') || l.startsWith('V')).sort().pop();
    } else if (selectedLevels.some(l => l.startsWith('U') || l.startsWith('T') || l.startsWith('S'))) {
        finalLevel = selectedLevels.filter(l => l.startsWith('U') || l.startsWith('T') || l.startsWith('S')).sort().pop();
    } else if (selectedLevels.some(l => l.startsWith('R') || l.startsWith('Q') || l.startsWith('P'))) {
        finalLevel = selectedLevels.filter(l => l.startsWith('R') || l.startsWith('Q') || l.startsWith('P')).sort().pop();
    } else if (selectedLevels.some(l => l.startsWith('O') || l.startsWith('N') || l.startsWith('M') || l.startsWith('L') || l.startsWith('K'))) {
        finalLevel = selectedLevels.filter(l => l.startsWith('O') || l.startsWith('N') || l.startsWith('M') || l.startsWith('L') || l.startsWith('K')).sort().pop();
    }

    const info = CRISIS_INFO[finalLevel];
    if (!info) {
        suggestedBox.style.display = 'none';
        return;
    }

    // 显示建议评级
    suggestedDisplay.innerHTML = `
        <div class="font-bold text-red-700">${finalLevel}</div>
        <div class="text-xs text-gray-600 mt-1">危机层级：${info.level}</div>
        <div class="text-xs text-gray-600">脱口语：${info.phrase}</div>
        <div class="text-xs text-gray-500 mt-1">已选：${selectedLevels.join(', ')}</div>
    `;

    suggestedBox.style.display = 'block';
}

// ==================== 孩子信息管理 ====================

function addChild() {
    const child = {
        id: Date.now(),
        gender: '',
        age: '',
        health: '',
        education: '',
        occupation: ''
    };
    childrenList.push(child);
    console.log('添加孩子后，当前孩子数量：', childrenList.length);
    renderChildrenList();
}

function removeChild(childId) {
    childrenList = childrenList.filter(c => c.id !== childId);
    renderChildrenList();
}

function updateChild(childId, field, value) {
    const child = childrenList.find(c => c.id === childId);
    if (child) {
        child[field] = value;
    }
}

function renderChildrenList() {
    const container = document.getElementById('childrenList');
    const noChildrenText = document.getElementById('noChildrenText');

    if (childrenList.length === 0) {
        noChildrenText.style.display = 'block';
        return;
    }

    noChildrenText.style.display = 'none';

    container.innerHTML = childrenList.map((child, index) => `
        <div class="border border-gray-300 rounded-lg p-3 bg-gray-50">
            <div class="flex justify-between items-center mb-2">
                <span class="text-sm font-medium text-gray-700">孩子 ${index + 1}</span>
                <button type="button" onclick="removeChild(${child.id})" class="text-red-600 hover:text-red-800 text-sm">
                    <i class="fa fa-trash"></i> 删除
                </button>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-5 gap-2">
                <div>
                    <label class="block text-xs font-medium text-gray-600 mb-1">性别</label>
                    <select onchange="updateChild(${child.id}, 'gender', this.value)"
                            class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-pink-500">
                        <option value="" ${child.gender === '' ? 'selected' : ''}>未知</option>
                        <option value="男" ${child.gender === '男' ? 'selected' : ''}>男</option>
                        <option value="女" ${child.gender === '女' ? 'selected' : ''}>女</option>
                    </select>
                </div>
                <div>
                    <label class="block text-xs font-medium text-gray-600 mb-1">年龄</label>
                    <input type="text" value="${child.age}"
                           onchange="updateChild(${child.id}, 'age', this.value)"
                           placeholder="例如：2岁"
                           class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-pink-500">
                </div>
                <div>
                    <label class="block text-xs font-medium text-gray-600 mb-1">身体情况</label>
                    <input type="text" value="${child.health}"
                           onchange="updateChild(${child.id}, 'health', this.value)"
                           placeholder="例如：健康"
                           class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-pink-500">
                </div>
                <div>
                    <label class="block text-xs font-medium text-gray-600 mb-1">在读情况</label>
                    <input type="text" value="${child.education}"
                           onchange="updateChild(${child.id}, 'education', this.value)"
                           placeholder="例如：幼儿园"
                           class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-pink-500">
                </div>
                <div>
                    <label class="block text-xs font-medium text-gray-600 mb-1">职业</label>
                    <input type="text" value="${child.occupation}"
                           onchange="updateChild(${child.id}, 'occupation', this.value)"
                           placeholder="例如：学生"
                           class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-pink-500">
                </div>
            </div>
        </div>
    `).join('');
}

// ==================== 心理测评管理 ====================

function addPsychTest() {
    const test = {
        id: Date.now(),
        name: '',
        date: '',
        score: '',
        result: '',
        interpretation: ''
    };
    psychTestsList.push(test);
    renderPsychTestsList();
}

function removePsychTest(testId) {
    psychTestsList = psychTestsList.filter(t => t.id !== testId);
    renderPsychTestsList();
}

function updatePsychTest(testId, field, value) {
    const test = psychTestsList.find(t => t.id === testId);
    if (test) {
        test[field] = value;
    }
}

function renderPsychTestsList() {
    const container = document.getElementById('psychTestsList');
    const noPsychTestsText = document.getElementById('noPsychTestsText');

    if (psychTestsList.length === 0) {
        noPsychTestsText.style.display = 'block';
        return;
    }

    noPsychTestsText.style.display = 'none';

    container.innerHTML = psychTestsList.map((test, index) => `
        <div class="border border-indigo-300 rounded-lg p-4 bg-indigo-50">
            <div class="flex justify-between items-center mb-3">
                <span class="text-sm font-semibold text-indigo-700">测评 ${index + 1}</span>
                <button type="button" onclick="removePsychTest(${test.id})" class="text-red-600 hover:text-red-800 text-sm">
                    <i class="fa fa-trash"></i> 删除
                </button>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
                <div>
                    <label class="block text-xs font-medium text-gray-700 mb-1">量表名称</label>
                    <select onchange="updatePsychTest(${test.id}, 'name', this.value)"
                            class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-indigo-500">
                        <option value="">选择量表</option>
                        ${PSYCH_TESTS.map(pt => `
                            <option value="${pt.name}" ${test.name === pt.name ? 'selected' : ''}>
                                ${pt.name} - ${pt.fullName}
                            </option>
                        `).join('')}
                    </select>
                </div>
                <div>
                    <label class="block text-xs font-medium text-gray-700 mb-1">测评日期</label>
                    <input type="date" value="${test.date}"
                           onchange="updatePsychTest(${test.id}, 'date', this.value)"
                           class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-indigo-500">
                </div>
                <div>
                    <label class="block text-xs font-medium text-gray-700 mb-1">得分/结果</label>
                    <input type="text" value="${test.score}"
                           onchange="updatePsychTest(${test.id}, 'score', this.value)"
                           placeholder="例如：总分72分"
                           class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-indigo-500">
                </div>
                <div>
                    <label class="block text-xs font-medium text-gray-700 mb-1">评估结果</label>
                    <input type="text" value="${test.result}"
                           onchange="updatePsychTest(${test.id}, 'result', this.value)"
                           placeholder="例如：轻度抑郁"
                           class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-indigo-500">
                </div>
            </div>
            <div>
                <label class="block text-xs font-medium text-gray-700 mb-1">结果解读</label>
                <textarea value="${test.interpretation}"
                          onchange="updatePsychTest(${test.id}, 'interpretation', this.value)"
                          rows="2"
                          placeholder="测评结果的详细解读和说明..."
                          class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-indigo-500">${test.interpretation}</textarea>
            </div>
        </div>
    `).join('');
}

