// API配置
const API_BASE = 'http://localhost:8007';

// 全局状态
let currentStep = 1;
let caseData = {
    case_id: '',
    temp_word_file: '',
    content: '',
    ai_analysis: {},
    basic_info: {},
    session_info: {},
    tags: { relation: [], symptom: [] },
    crisis_level: 'C',
    crisis_evidence: '',
    keywords: [],
    techniques_used: [],
    dialogue: '',
    audio_files: [],
    transcripts: [],
    supervision_files: []
};

let tagsLibrary = {};
let selectedWordFile = null;

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    loadTagsLibrary();
    setupFileUpload();
});

// 加载标签库
async function loadTagsLibrary() {
    try {
        const response = await fetch(`${API_BASE}/api/tags-library`);
        tagsLibrary = await response.json();
    } catch (error) {
        console.error('加载标签库失败:', error);
    }
}

// 设置文件上传
function setupFileUpload() {
    const uploadArea = document.getElementById('wordUploadArea');
    const fileInput = document.getElementById('wordFileInput');

    // 拖拽上传
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file && file.name.endsWith('.docx')) {
            handleWordFile(file);
        } else {
            alert('请上传.docx格式的Word文档');
        }
    });

    // 点击上传
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            handleWordFile(file);
        }
    });
}

// 处理Word文件
function handleWordFile(file) {
    selectedWordFile = file;
    document.getElementById('wordFileName').textContent = file.name;
    document.getElementById('wordFileSize').textContent = `(${(file.size / 1024).toFixed(2)} KB)`;
    document.getElementById('wordFileInfo').classList.remove('hidden');
}

// 开始分析
async function startAnalysis() {
    if (!selectedWordFile) {
        alert('请先选择Word文档');
        return;
    }

    goToStep(2);

    const formData = new FormData();
    formData.append('file', selectedWordFile);

    try {
        const response = await fetch(`${API_BASE}/api/upload-word`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();

        if (result.success) {
            caseData.case_id = result.case_id;
            caseData.temp_word_file = result.temp_word_file;
            caseData.content = result.content;
            caseData.dialogue = result.content;
            caseData.ai_analysis = result.ai_analysis;

            // 填充AI分析结果
            populateAIAnalysis(result.ai_analysis);

            // 进入核实步骤
            setTimeout(() => goToStep(3), 1000);
        } else {
            alert('分析失败: ' + (result.error || '未知错误'));
            goToStep(1);
        }
    } catch (error) {
        console.error('分析出错:', error);
        alert('分析失败: ' + error.message + '\n\n请确保后端服务器正在运行（端口8007）');
        goToStep(1);
    }
}

// 填充AI分析结果
function populateAIAnalysis(analysis) {
    document.getElementById('caseIdDisplay').textContent = caseData.case_id;

    // 填充标签
    const relationTags = analysis.relation_tags || [];
    const symptomTags = analysis.symptom_tags || [];

    displayTags('relationTagsArea', relationTags, 'relation');
    displayTags('symptomTagsArea', symptomTags, 'symptom');

    // 填充其他字段
    document.getElementById('input_crisis_level').value = analysis.crisis_level || 'C';
    document.getElementById('input_crisis_evidence').value = analysis.crisis_evidence || '';
    document.getElementById('input_keywords').value = (analysis.keywords || []).join(', ');
    document.getElementById('input_summary').value = analysis.summary || '';

    caseData.tags.relation = relationTags;
    caseData.tags.symptom = symptomTags;
    caseData.crisis_level = analysis.crisis_level || 'C';
    caseData.crisis_evidence = analysis.crisis_evidence || '';
    caseData.keywords = analysis.keywords || [];
}

// 显示标签
function displayTags(containerId, selectedTags, type) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';

    // 获取所有可选标签
    const library = type === 'relation' ? tagsLibrary.relation_tags : tagsLibrary.symptom_tags;
    const allTags = [];

    if (library) {
        Object.values(library).forEach(category => {
            if (category.children) {
                Object.values(category.children).forEach(tags => {
                    if (Array.isArray(tags)) {
                        allTags.push(...tags);
                    }
                });
            }
        });
    }

    // 显示已选标签和可选标签
    const uniqueTags = [...new Set([...selectedTags, ...allTags])];

    uniqueTags.forEach(tag => {
        const tagEl = document.createElement('span');
        tagEl.className = 'tag-item' + (selectedTags.includes(tag) ? ' selected' : '');
        tagEl.textContent = tag;
        tagEl.onclick = () => toggleTag(tag, type, tagEl);
        container.appendChild(tagEl);
    });
}

// 切换标签选择
function toggleTag(tag, type, element) {
    const isSelected = element.classList.contains('selected');

    if (isSelected) {
        element.classList.remove('selected');
        const index = caseData.tags[type].indexOf(tag);
        if (index > -1) {
            caseData.tags[type].splice(index, 1);
        }
    } else {
        element.classList.add('selected');
        if (!caseData.tags[type].includes(tag)) {
            caseData.tags[type].push(tag);
        }
    }
}

// 添加逐字稿
let transcriptCounter = 0;
function addTranscript() {
    transcriptCounter++;
    const container = document.getElementById('transcriptList');

    const transcriptDiv = document.createElement('div');
    transcriptDiv.className = 'border rounded p-4 bg-gray-50';
    transcriptDiv.innerHTML = `
        <div class="mb-3">
            <label class="block text-sm font-bold mb-1">标题</label>
            <input type="text" class="w-full border rounded px-3 py-2" id="transcript_title_${transcriptCounter}">
        </div>
        <div class="mb-3">
            <label class="block text-sm font-bold mb-1">内容</label>
            <textarea rows="4" class="w-full border rounded px-3 py-2" id="transcript_content_${transcriptCounter}"></textarea>
        </div>
        <button onclick="this.parentElement.remove()" class="text-red-500 hover:text-red-700">
            <i class="fa fa-trash mr-1"></i>删除
        </button>
    `;

    container.appendChild(transcriptDiv);
}

// 跳转步骤
function goToStep(step) {
    // 收集当前步骤数据
    if (currentStep === 3) {
        collectStep3Data();
    } else if (currentStep === 4) {
        collectStep4Data();
    }

    // 隐藏所有内容
    for (let i = 1; i <= 5; i++) {
        document.getElementById(`content-step${i}`).classList.add('hidden');
        document.getElementById(`step${i}`).classList.remove('active', 'completed');
    }

    // 显示目标步骤
    currentStep = step;
    document.getElementById(`content-step${step}`).classList.remove('hidden');
    document.getElementById(`step${step}`).classList.add('active');

    // 标记已完成步骤
    for (let i = 1; i < step; i++) {
        document.getElementById(`step${i}`).classList.add('completed');
    }

    // 如果是第5步，显示摘要
    if (step === 5) {
        displayFinalSummary();
    }
}

// 收集步骤3数据
function collectStep3Data() {
    caseData.basic_info = {
        代号: document.getElementById('input_代号').value,
        性别: document.getElementById('input_性别').value,
        年龄: document.getElementById('input_年龄').value,
        职业: document.getElementById('input_职业').value,
        婚姻状况: document.getElementById('input_婚姻状况').value
    };

    caseData.session_info = {
        接访日期: document.getElementById('input_接访日期').value,
        接访次数: document.getElementById('input_接访次数').value,
        通话时长: document.getElementById('input_通话时长').value,
        咨询渠道: document.getElementById('input_咨询渠道').value
    };

    caseData.crisis_level = document.getElementById('input_crisis_level').value;
    caseData.crisis_evidence = document.getElementById('input_crisis_evidence').value;

    const keywordsText = document.getElementById('input_keywords').value;
    caseData.keywords = keywordsText.split(',').map(k => k.trim()).filter(k => k);

    caseData.ai_analysis.summary = document.getElementById('input_summary').value;
}

// 收集步骤4数据
function collectStep4Data() {
    // 录音文件
    const audioInput = document.getElementById('audioFileInput');
    caseData.audio_files = Array.from(audioInput.files).map(f => ({
        filename: f.name,
        file: f
    }));

    // 逐字稿
    caseData.transcripts = [];
    for (let i = 1; i <= transcriptCounter; i++) {
        const titleEl = document.getElementById(`transcript_title_${i}`);
        const contentEl = document.getElementById(`transcript_content_${i}`);

        if (titleEl && contentEl) {
            const title = titleEl.value.trim();
            const content = contentEl.value.trim();

            if (title && content) {
                caseData.transcripts.push({
                    id: `T${String(i).padStart(3, '0')}`,
                    title: title,
                    content: content,
                    created_at: new Date().toISOString()
                });
            }
        }
    }

    // 督导资料
    const supervisionInput = document.getElementById('supervisionFileInput');
    caseData.supervision_files = Array.from(supervisionInput.files).map(f => ({
        filename: f.name,
        file: f
    }));
}

// 显示最终摘要
function displayFinalSummary() {
    const summary = document.getElementById('finalSummary');
    summary.innerHTML = `
        <p><strong>案例编号:</strong> ${caseData.case_id}</p>
        <p><strong>代号:</strong> ${caseData.basic_info.代号 || '未填写'}</p>
        <p><strong>关系标签:</strong> ${caseData.tags.relation.join(', ') || '无'}</p>
        <p><strong>精神症状:</strong> ${caseData.tags.symptom.join(', ') || '无'}</p>
        <p><strong>危机等级:</strong> ${caseData.crisis_level}</p>
        <p><strong>关键词:</strong> ${caseData.keywords.join(', ') || '无'}</p>
        <p><strong>录音文件:</strong> ${caseData.audio_files.length} 个</p>
        <p><strong>逐字稿:</strong> ${caseData.transcripts.length} 个</p>
        <p><strong>督导资料:</strong> ${caseData.supervision_files.length} 个</p>
    `;
}

// 保存案例
async function saveCase() {
    try {
        const saveButton = event.target;
        saveButton.disabled = true;
        saveButton.innerHTML = '<i class="fa fa-spinner fa-spin mr-2"></i>保存中...';

        const response = await fetch(`${API_BASE}/api/save-case`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(caseData)
        });

        const result = await response.json();

        if (result.success) {
            // 显示成功页面
            document.getElementById('content-step5').classList.add('hidden');
            document.getElementById('content-success').classList.remove('hidden');
            document.getElementById('successCaseId').textContent = result.case_id;

            // 标记所有步骤完成
            for (let i = 1; i <= 5; i++) {
                document.getElementById(`step${i}`).classList.remove('active');
                document.getElementById(`step${i}`).classList.add('completed');
            }
        } else {
            alert('保存失败: ' + result.error);
            saveButton.disabled = false;
            saveButton.innerHTML = '<i class="fa fa-save mr-2"></i>保存案例';
        }
    } catch (error) {
        console.error('保存出错:', error);
        alert('保存失败，请重试');
        event.target.disabled = false;
        event.target.innerHTML = '<i class="fa fa-save mr-2"></i>保存案例';
    }
}
