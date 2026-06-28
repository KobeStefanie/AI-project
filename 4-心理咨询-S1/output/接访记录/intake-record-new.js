// API配置
const CONFIG_API = 'http://localhost:8003';
const AUDIO_API = 'http://localhost:8004';
const TRANSCRIPT_API = 'http://localhost:8005';
const SUPERVISION_API = 'http://localhost:8006';
const CASE_API = 'http://localhost:5001/api';

// 全局变量
let tagsLibrary = null;
let selectedAudioFiles = [];
let selectedTranscriptFiles = [];
let selectedSupervisionFiles = [];
let keywords = [];
let currentCase = null;  // 当前加载的案例
let isFollowUpSession = false;  // 是否为后续会谈模式

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

    // 自动保存草稿（每30秒）
    setInterval(() => {
        autoSaveDraft();
    }, 30000);
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
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${CONFIG_API}/api/word/parse`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('文档解析失败');
        }

        const data = await response.json();

        // 自动填充表单
        fillFormFromWordData(data);

        statusDiv.innerHTML = '<div class="text-green-600"><i class="fa fa-check-circle"></i> 文档识别成功，已自动填充表单</div>';

        // 3秒后隐藏状态
        setTimeout(() => {
            statusDiv.innerHTML = '';
        }, 3000);

    } catch (error) {
        console.error('Word文档处理失败:', error);
        statusDiv.innerHTML = '<div class="text-red-600"><i class="fa fa-times-circle"></i> 文档识别失败: ' + error.message + '</div>';
    }
}

// 从Word数据填充表单
function fillFormFromWordData(data) {
    // 基本信息
    if (data.basic_info) {
        if (data.basic_info.代号) document.getElementById('代号').value = data.basic_info.代号;
        if (data.basic_info.性别) document.getElementById('性别').value = data.basic_info.性别;
        if (data.basic_info.年龄) document.getElementById('年龄').value = data.basic_info.年龄;
        if (data.basic_info.职业) document.getElementById('职业').value = data.basic_info.职业;
        if (data.basic_info.婚姻状况) document.getElementById('婚姻状况').value = data.basic_info.婚姻状况;
        if (data.basic_info.性取向) document.getElementById('性取向').value = data.basic_info.性取向;
        if (data.basic_info.宗教信仰) document.getElementById('宗教信仰').value = data.basic_info.宗教信仰;
        if (data.basic_info.紧急联系人) document.getElementById('紧急联系人').value = data.basic_info.紧急联系人;
        if (data.basic_info.紧急联系电话) document.getElementById('紧急联系电话').value = data.basic_info.紧急联系电话;
        if (data.basic_info.用药情况) document.getElementById('用药情况').value = data.basic_info.用药情况;
        if (data.basic_info.来访备注) document.getElementById('来访备注').value = data.basic_info.来访备注;
    }

    // 接访信息
    if (data.session_info) {
        if (data.session_info.接访日期) document.getElementById('接访日期').value = data.session_info.接访日期;
        if (data.session_info.接访次数) document.getElementById('接访次数').value = data.session_info.接访次数;
        if (data.session_info.通话时长) document.getElementById('通话时长').value = data.session_info.通话时长;
        if (data.session_info.咨询渠道) document.getElementById('咨询渠道').value = data.session_info.咨询渠道;
        if (data.session_info.咨询师姓名) document.getElementById('咨询师姓名').value = data.session_info.咨询师姓名;
        if (data.session_info.案例状态) document.getElementById('案例状态').value = data.session_info.案例状态;
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

    // 家庭结构
    if (data.家庭结构) {
        if (data.家庭结构.父亲情况) document.getElementById('父亲情况').value = data.家庭结构.父亲情况;
        if (data.家庭结构.母亲情况) document.getElementById('母亲情况').value = data.家庭结构.母亲情况;
        if (data.家庭结构.父母关系) document.getElementById('父母关系').value = data.家庭结构.父母关系;
        if (data.家庭结构.兄弟姐妹) document.getElementById('兄弟姐妹').value = data.家庭结构.兄弟姐妹;
        if (data.家庭结构.配偶子女情况) document.getElementById('配偶子女情况').value = data.家庭结构.配偶子女情况;
    }

    // 对话记录
    if (data.dialogue) {
        document.getElementById('dialogue').value = data.dialogue;
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

    // 危机等级
    if (data.crisis_level) {
        const radio = document.getElementById(`crisis_${data.crisis_level}`);
        if (radio) radio.checked = true;
    }
    if (data.crisis_evidence) {
        document.getElementById('crisis_evidence').value = data.crisis_evidence;
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

    // 咨询师反思和建议
    if (data.counselor_reflection) {
        document.getElementById('counselor_reflection').value = data.counselor_reflection;
    }
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
        紧急联系人: document.getElementById('紧急联系人').value.trim(),
        紧急联系电话: document.getElementById('紧急联系电话').value.trim(),
        用药情况: document.getElementById('用药情况').value.trim(),
        来访备注: document.getElementById('来访备注').value.trim()
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

    // 家庭结构
    const 家庭结构 = {
        父亲情况: document.getElementById('父亲情况').value.trim(),
        母亲情况: document.getElementById('母亲情况').value.trim(),
        父母关系: document.getElementById('父母关系').value,
        兄弟姐妹: document.getElementById('兄弟姐妹').value.trim(),
        配偶子女情况: document.getElementById('配偶子女情况').value.trim()
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

    // 咨询师反思
    const counselorReflection = document.getElementById('counselor_reflection').value.trim();

    // 下次接访建议
    const nextSessionPlan = document.getElementById('next_session_plan').value.trim();

    return {
        basic_info: basicInfo,
        session_info: sessionInfo,
        主诉: 主诉,
        咨询目标: 咨询目标,
        危机评估: 危机评估,
        既往史: 既往史,
        家庭结构: 家庭结构,
        tags: {
            relation: relationTags,
            symptom: symptomTags
        },
        techniques_used: techniquesUsed,
        督导信息: 督导信息,
        keywords: keywords,
        dialogue: dialogue,
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

    if (!data.session_info.接访日期) {
        errors.push('请选择接访日期');
    }

    if (!data.主诉) {
        errors.push('请填写来访者主诉');
    }

    if (!data.dialogue) {
        errors.push('请填写对话记录');
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
    const caseData = {
        static_info: {
            代号: formData.basic_info.代号,
            性别: formData.basic_info.性别,
            年龄: formData.basic_info.年龄,
            出生日期: estimateBirthDate(formData.basic_info.年龄),
            职业: formData.basic_info.职业,
            婚姻状况: formData.basic_info.婚姻状况,
            性取向: formData.basic_info.性取向,
            宗教信仰: formData.basic_info.宗教信仰,
            主诉: formData.主诉,
            既往史: formData.既往史,
            家庭结构: formData.家庭结构
        },
        dynamic_info: {
            紧急联系人: formData.basic_info.紧急联系人,
            紧急联系电话: formData.basic_info.紧急联系电话,
            用药情况: formData.basic_info.用药情况,  // 后端会自动包装成 {current, history}
            咨询目标: formData.咨询目标,              // 后端会自动包装成 {current, history}
            来访备注: formData.basic_info.来访备注
        },
        session: {  // 注意：是单数 session，不是 sessions
            date: formData.session_info.接访日期,
            duration: formData.session_info.通话时长,
            channel: formData.session_info.咨询渠道,
            counselor: formData.session_info.咨询师姓名,
            dialogue: formData.dialogue,
            relation_tags: formData.tags.relation,
            symptom_tags: formData.tags.symptom,
            crisis_assessment: {
                level: formData.crisis_level,
                evidence: formData.crisis_evidence
            },
            techniques_used: formData.techniques_used,
            keywords: formData.keywords,
            counselor_reflection: formData.counselor_reflection,
            next_session_plan: formData.next_session_plan,
            summary: '',  // 后续由AI生成
            supervision: {
                status: formData.督导信息.督导状态,
                supervisor: formData.督导信息.督导师姓名,
                date: formData.督导信息.督导日期,
                key_points: formData.督导信息.督导要点,
                suggestions: formData.督导信息.督导建议
            }
        }
    };

    const response = await fetch(`${CASE_API}/cases`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(caseData)
    });

    const result = await response.json();
    if (!result.success) {
        throw new Error(result.error || '创建案例失败');
    }

    alert(`案例创建成功！\n案例代号：${result.case_id}`);
}

// 保存后续会谈
async function saveFollowUpSession(formData) {
    const caseId = currentCase.case_id;

    // 检测咨访目标是否变化
    const oldGoal = currentCase.dynamic_info.咨询目标?.current || '';
    const newGoal = formData.咨询目标;
    let goalChangeReason = null;

    if (newGoal !== oldGoal && newGoal.trim() !== '') {
        goalChangeReason = prompt('检测到咨询目标发生变化，请说明修改原因（必填）：\n\n旧目标：' + oldGoal + '\n新目标：' + newGoal);
        if (!goalChangeReason || goalChangeReason.trim() === '') {
            throw new Error('咨询目标修改原因为必填项');
        }
    }

    // 检测用药情况是否变化
    const oldMedication = currentCase.dynamic_info.用药情况?.current || '';
    const newMedication = formData.basic_info.用药情况;
    let medicationChangeReason = null;

    if (newMedication !== oldMedication && newMedication.trim() !== '') {
        medicationChangeReason = prompt('检测到用药情况发生变化，请说明修改原因（必填）：\n\n旧用药：' + oldMedication + '\n新用药：' + newMedication);
        if (!medicationChangeReason || medicationChangeReason.trim() === '') {
            throw new Error('用药情况修改原因为必填项');
        }
    }

    // 构建会谈数据
    const sessionData = {
        date: formData.session_info.接访日期,
        duration: formData.session_info.通话时长,
        channel: formData.session_info.咨询渠道,
        counselor: formData.session_info.咨询师姓名,
        dialogue: formData.dialogue,
        relation_tags: formData.tags.relation,
        symptom_tags: formData.tags.symptom,
        crisis_assessment: {
            level: formData.crisis_level,
            evidence: formData.crisis_evidence
        },
        techniques_used: formData.techniques_used,
        keywords: formData.keywords,
        counselor_reflection: formData.counselor_reflection,
        next_session_plan: formData.next_session_plan,
        summary: '',  // 后续由AI生成
        supervision: {
            status: formData.督导信息.督导状态,
            supervisor: formData.督导信息.督导师姓名,
            date: formData.督导信息.督导日期,
            key_points: formData.督导信息.督导要点,
            suggestions: formData.督导信息.督导建议
        },
        // 动态信息更新
        dynamic_updates: {
            紧急联系人: formData.basic_info.紧急联系人,
            紧急联系电话: formData.basic_info.紧急联系电话,
            来访备注: formData.basic_info.来访备注
        }
    };

    // 如果目标有变化，添加变更记录
    if (goalChangeReason) {
        sessionData.goal_change = {
            new_goal: newGoal,
            reason: goalChangeReason
        };
    }

    // 如果用药有变化，添加变更记录
    if (medicationChangeReason) {
        sessionData.medication_change = {
            new_medication: newMedication,
            reason: medicationChangeReason
        };
    }

    const response = await fetch(`${CASE_API}/cases/${caseId}/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sessionData)
    });

    const result = await response.json();
    if (!result.success) {
        throw new Error(result.error || '添加会谈记录失败');
    }

    const sessionNum = currentCase.sessions.length + 1;
    alert(`会谈记录保存成功！\n案例代号：${caseId}\n本次为第 ${sessionNum} 次会谈`);
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
    document.getElementById('紧急联系电话').value = '';
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

    // 清空家庭结构
    document.getElementById('父亲情况').value = '';
    document.getElementById('母亲情况').value = '';
    document.getElementById('父母关系').value = '';
    document.getElementById('兄弟姐妹').value = '';
    document.getElementById('配偶子女情况').value = '';

    // 清空标签选择
    document.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);

    // 重置危机等级
    document.getElementById('crisis_C').checked = true;
    document.getElementById('crisis_evidence').value = '';

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

    if (draft && timestamp) {
        const draftTime = new Date(timestamp);
        const now = new Date();
        const hoursDiff = (now - draftTime) / 1000 / 60 / 60;

        // 草稿在24小时内
        if (hoursDiff < 24) {
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
            }
        } else {
            // 清除过期草稿
            localStorage.removeItem('intake_draft');
            localStorage.removeItem('intake_draft_timestamp');
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
        const response = await fetch(`${CASE_API}/cases/${caseId}`);
        const result = await response.json();

        if (!result.success) {
            statusDiv.innerHTML = `<div class="text-red-600"><i class="fa fa-exclamation-circle"></i> ${result.error}</div>`;
            return;
        }

        currentCase = result.case;
        isFollowUpSession = true;

        // 显示成功信息
        const totalSessions = currentCase.sessions.length;
        const nextSession = totalSessions + 1;
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

    const 联系方式Elem = document.getElementById('联系方式');
    if (联系方式Elem) 联系方式Elem.value = staticInfo.联系方式 || '';

    // 2. 动态信息（可修改）
    const dynamicInfo = currentCase.dynamic_info;
    document.getElementById('紧急联系人').value = dynamicInfo.紧急联系人 || '';
    document.getElementById('紧急联系电话').value = dynamicInfo.紧急联系电话 || '';
    document.getElementById('用药情况').value = dynamicInfo.用药情况?.current || '';
    document.getElementById('来访备注').value = dynamicInfo.来访备注 || '';

    // 3. 主诉（只读显示）
    document.getElementById('主诉').value = staticInfo.主诉 || '';
    document.getElementById('主诉').readOnly = true;

    // 4. 咨询目标（显示当前值，可修改）
    document.getElementById('咨询目标').value = dynamicInfo.咨询目标?.current || '';

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
        Object.keys(staticInfo.家庭结构).forEach(key => {
            const elem = document.getElementById(key);
            if (elem) {
                elem.value = staticInfo.家庭结构[key] || '';
                elem.readOnly = true;
            }
        });
    }

    // 7. 接访信息（自动填充）
    const nextSessionNum = currentCase.sessions.length + 1;
    document.getElementById('接访次数').value = nextSessionNum;
    document.getElementById('接访日期').valueAsDate = new Date();

    // 8. 显示上次会谈概要
    if (currentCase.sessions.length > 0) {
        const lastSession = currentCase.sessions[currentCase.sessions.length - 1];
        showPreviousSummary(lastSession);
    }

    // 9. 隐藏Word导入区域
    document.getElementById('wordImportSection').style.display = 'none';

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

