// 接访记录管理系统 - JavaScript

const AUDIO_API = 'http://localhost:8004';
const TRANSCRIPT_API = 'http://localhost:8005';
const SUPERVISION_API = 'http://localhost:8006';
const CASE_PROCESSOR_API = 'http://localhost:8007';

let currentCaseId = null;
let editingTranscriptId = null;
let selectedWordFile = null;
let tempWordFile = null;
let currentMode = 'new'; // 'new' or 'existing'

// ==================== 模式切换 ====================

function switchMode(mode) {
    currentMode = mode;

    // 更新按钮样式
    if (mode === 'new') {
        document.getElementById('btnNewCase').classList.remove('bg-gray-200', 'text-gray-700');
        document.getElementById('btnNewCase').classList.add('bg-blue-600', 'text-white');
        document.getElementById('btnExistingCase').classList.remove('bg-blue-600', 'text-white');
        document.getElementById('btnExistingCase').classList.add('bg-gray-200', 'text-gray-700');

        // 显示新建模式
        document.getElementById('existingCaseInput').classList.add('hidden');
        document.getElementById('caseInfo').classList.add('hidden');
        document.getElementById('mainContent').classList.remove('hidden');

        // 切换到案例创建Tab
        switchTab('create');
    } else {
        document.getElementById('btnExistingCase').classList.remove('bg-gray-200', 'text-gray-700');
        document.getElementById('btnExistingCase').classList.add('bg-blue-600', 'text-white');
        document.getElementById('btnNewCase').classList.remove('bg-blue-600', 'text-white');
        document.getElementById('btnNewCase').classList.add('bg-gray-200', 'text-gray-700');

        // 显示已有案例输入
        document.getElementById('existingCaseInput').classList.remove('hidden');
        document.getElementById('mainContent').classList.add('hidden');
    }
}

// ==================== Word文档处理 ====================

// 初始化Word上传
document.addEventListener('DOMContentLoaded', () => {
    const wordDropZone = document.getElementById('wordDropZone');
    const wordFileInput = document.getElementById('wordFileInput');

    if (wordDropZone && wordFileInput) {
        // 拖拽上传
        wordDropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            wordDropZone.classList.add('dragging');
        });

        wordDropZone.addEventListener('dragleave', () => {
            wordDropZone.classList.remove('dragging');
        });

        wordDropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            wordDropZone.classList.remove('dragging');
            const file = e.dataTransfer.files[0];
            if (file && file.name.endsWith('.docx')) {
                handleWordFile(file);
            } else {
                alert('请上传.docx格式的Word文档');
            }
        });

        // 点击上传
        wordFileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                handleWordFile(file);
            }
        });
    }
});

function handleWordFile(file) {
    selectedWordFile = file;
    document.getElementById('wordFileName').textContent = file.name;
    document.getElementById('wordFileSize').textContent = `(${(file.size / 1024).toFixed(2)} KB)`;
    document.getElementById('wordFileInfo').classList.remove('hidden');
    document.getElementById('wordDropZone').classList.add('hidden');
}

async function startWordAnalysis() {
    if (!selectedWordFile) {
        alert('请先选择Word文档');
        return;
    }

    // 显示分析中状态
    document.getElementById('wordFileInfo').classList.add('hidden');
    document.getElementById('wordAnalyzing').classList.remove('hidden');

    const formData = new FormData();
    formData.append('file', selectedWordFile);

    try {
        const response = await fetch(`${CASE_PROCESSOR_API}/api/upload-word`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();

        if (result.success) {
            // 保存临时数据
            currentCaseId = result.case_id;
            tempWordFile = result.temp_word_file;

            // 填充AI分析结果
            document.getElementById('newCaseId').textContent = result.case_id;
            document.getElementById('ai_crisis_level').value = result.ai_analysis.crisis_level || 'C';
            document.getElementById('ai_keywords').value = (result.ai_analysis.keywords || []).join(', ');
            document.getElementById('ai_summary').value = result.ai_analysis.summary || '';

            // 显示分析结果
            document.getElementById('wordAnalyzing').classList.add('hidden');
            document.getElementById('wordAnalysisResult').classList.remove('hidden');
        } else {
            throw new Error(result.error || '分析失败');
        }
    } catch (error) {
        console.error('分析出错:', error);
        alert('分析失败: ' + error.message + '\n\n请确保后端服务器正在运行（端口8007）');

        // 恢复初始状态
        document.getElementById('wordAnalyzing').classList.add('hidden');
        document.getElementById('wordFileInfo').classList.remove('hidden');
    }
}

async function saveNewCase() {
    if (!currentCaseId || !tempWordFile) {
        alert('请先完成Word文档分析');
        return;
    }

    // 收集数据
    const caseData = {
        case_id: currentCaseId,
        temp_word_file: tempWordFile,
        basic_info: {
            代号: document.getElementById('ai_代号').value,
            性别: document.getElementById('ai_性别').value,
            年龄: document.getElementById('ai_年龄').value,
            职业: document.getElementById('ai_职业').value
        },
        crisis_level: document.getElementById('ai_crisis_level').value,
        keywords: document.getElementById('ai_keywords').value.split(',').map(k => k.trim()).filter(k => k),
        ai_analysis: {
            summary: document.getElementById('ai_summary').value
        },
        tags: { relation: [], symptom: [] },
        transcripts: [],
        audio_files: [],
        supervision_files: []
    };

    try {
        const response = await fetch(`${CASE_PROCESSOR_API}/api/save-case`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(caseData)
        });

        const result = await response.json();

        if (result.success) {
            alert(`案例 ${currentCaseId} 保存成功！\n\n现在可以继续上传录音、逐字稿和督导资料。`);

            // 更新界面
            document.getElementById('currentCaseId').textContent = currentCaseId;
            document.getElementById('caseInfo').classList.remove('hidden');

            // 切换到录音上传Tab
            switchTab('audio');
        } else {
            alert('保存失败: ' + result.error);
        }
    } catch (error) {
        console.error('保存出错:', error);
        alert('保存失败: ' + error.message);
    }
}

// ==================== 案例加载 ====================

async function loadCase() {
    const caseId = document.getElementById('caseIdInput').value.trim();
    if (!caseId) {
        alert('请输入案例编号');
        return;
    }

    currentCaseId = caseId;
    document.getElementById('currentCaseId').textContent = caseId;
    document.getElementById('caseInfo').classList.remove('hidden');
    document.getElementById('mainContent').classList.remove('hidden');

    // 加载所有资料
    await refreshAllData();
}

async function refreshAllData() {
    await Promise.all([
        refreshAudioList(),
        refreshTranscriptList(),
        refreshSupervisionList(),
        loadAudioListForTranscript()
    ]);
    updateSummary();
}

// ==================== Tab切换 ====================

function switchTab(tabName) {
    // 切换按钮样式
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    // 切换内容
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`tab-${tabName}`).classList.add('active');

    // 如果切换到汇总，更新统计
    if (tabName === 'summary') {
        updateSummary();
    }
}

// ==================== 录音管理 ====================

// 拖拽上传 - 录音
const audioDropZone = document.getElementById('audioDropZone');
audioDropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    audioDropZone.classList.add('dragging');
});
audioDropZone.addEventListener('dragleave', () => {
    audioDropZone.classList.remove('dragging');
});
audioDropZone.addEventListener('drop', async (e) => {
    e.preventDefault();
    audioDropZone.classList.remove('dragging');
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('audio/')) {
        await uploadAudio(file);
    } else {
        alert('请上传音频文件');
    }
});

// 文件选择 - 录音
document.getElementById('audioFileInput').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (file) {
        await uploadAudio(file);
    }
});

async function uploadAudio(file) {
    if (!currentCaseId) {
        alert('请先选择案例');
        return;
    }

    const formData = new FormData();
    formData.append('case_id', currentCaseId);
    formData.append('audio_file', file);

    const progressDiv = document.getElementById('audioProgress');
    const progressBar = document.getElementById('audioProgressBar');
    const uploadStatus = document.getElementById('audioStatus');

    progressDiv.classList.remove('hidden');
    progressBar.style.width = '30%';
    uploadStatus.textContent = '上传中...';

    try {
        const response = await fetch(`${AUDIO_API}/api/audio/upload`, {
            method: 'POST',
            body: formData
        });

        progressBar.style.width = '100%';
        uploadStatus.textContent = '上传完成';

        if (response.ok) {
            setTimeout(() => {
                progressDiv.classList.add('hidden');
                alert('录音上传成功！');
                refreshAllData();
                document.getElementById('audioFileInput').value = '';
            }, 500);
        } else {
            throw new Error('上传失败');
        }
    } catch (error) {
        console.error('上传失败:', error);
        progressDiv.classList.add('hidden');
        alert('上传失败，请检查服务器是否启动');
    }
}

async function refreshAudioList() {
    if (!currentCaseId) return;

    try {
        const response = await fetch(`${AUDIO_API}/api/audio/list?case_id=${currentCaseId}`);
        const audioList = await response.json();

        const container = document.getElementById('audioList');

        if (audioList.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-400">
                    <i class="fa fa-file-audio-o text-4xl mb-3"></i>
                    <p>暂无录音文件</p>
                </div>
            `;
            return;
        }

        container.innerHTML = audioList.map(audio => `
            <div class="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition">
                <div class="flex items-center justify-between">
                    <div class="flex-1">
                        <div class="flex items-center gap-3 mb-2">
                            <i class="fa fa-file-audio-o text-blue-600 text-xl"></i>
                            <span class="font-medium text-gray-800">${audio.filename}</span>
                        </div>
                        <div class="text-sm text-gray-500 ml-8">
                            <span><i class="fa fa-calendar"></i> ${formatDateTime(audio.uploaded_at)}</span>
                            <span class="ml-4"><i class="fa fa-hdd-o"></i> ${formatFileSize(audio.size)}</span>
                        </div>
                    </div>
                    <div class="flex items-center gap-2">
                        <button
                            onclick="playAudio('${audio.filename}')"
                            class="px-3 py-2 bg-green-100 text-green-700 rounded hover:bg-green-200 transition">
                            <i class="fa fa-play"></i> 播放
                        </button>
                        <button
                            onclick="deleteAudio('${audio.filename}')"
                            class="px-3 py-2 bg-red-100 text-red-700 rounded hover:bg-red-200 transition">
                            <i class="fa fa-trash"></i>
                        </button>
                    </div>
                </div>
                <audio id="player-${audio.filename}" class="w-full mt-3 hidden" controls>
                    <source src="${AUDIO_API}${audio.url}" type="audio/mpeg">
                </audio>
            </div>
        `).join('');
    } catch (error) {
        console.error('加载录音列表失败:', error);
    }
}

function playAudio(filename) {
    const player = document.getElementById(`player-${filename}`);
    if (player.classList.contains('hidden')) {
        document.querySelectorAll('audio').forEach(audio => {
            audio.pause();
            audio.classList.add('hidden');
        });
        player.classList.remove('hidden');
        player.play();
    } else {
        player.classList.add('hidden');
        player.pause();
    }
}

async function deleteAudio(filename) {
    if (!confirm(`确定要删除录音 "${filename}" 吗？`)) return;

    try {
        const response = await fetch(`${AUDIO_API}/api/audio/delete`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ case_id: currentCaseId, filename })
        });

        if (response.ok) {
            alert('删除成功');
            refreshAllData();
        }
    } catch (error) {
        console.error('删除失败:', error);
        alert('删除失败');
    }
}

// ==================== 逐字稿管理 ====================

async function loadAudioListForTranscript() {
    try {
        const response = await fetch(`${AUDIO_API}/api/audio/list?case_id=${currentCaseId}`);
        const audioList = await response.json();

        const select = document.getElementById('transcriptAudioSelect');
        select.innerHTML = '<option value="">无关联录音</option>';

        audioList.forEach(audio => {
            const option = document.createElement('option');
            option.value = audio.filename;
            option.textContent = audio.filename;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('加载录音列表失败:', error);
    }
}

async function saveTranscript() {
    if (!currentCaseId) {
        alert('请先选择案例');
        return;
    }

    const content = document.getElementById('transcriptContent').value.trim();
    if (!content) {
        alert('请输入逐字稿内容');
        return;
    }

    const audioFilename = document.getElementById('transcriptAudioSelect').value;

    try {
        const response = await fetch(`${TRANSCRIPT_API}/api/transcript`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                case_id: currentCaseId,
                content: content,
                audio_filename: audioFilename,
                timestamps: []
            })
        });

        if (response.ok) {
            alert('保存成功！');
            clearTranscriptForm();
            refreshAllData();
        } else {
            alert('保存失败');
        }
    } catch (error) {
        console.error('保存失败:', error);
        alert('保存失败，请检查服务器');
    }
}

function clearTranscriptForm() {
    document.getElementById('transcriptContent').value = '';
    document.getElementById('transcriptAudioSelect').value = '';
}

async function refreshTranscriptList() {
    if (!currentCaseId) return;

    try {
        const response = await fetch(`${TRANSCRIPT_API}/api/transcript?case_id=${currentCaseId}`);
        const transcripts = await response.json();

        const container = document.getElementById('transcriptList');

        if (transcripts.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-400">
                    <i class="fa fa-file-text-o text-4xl mb-3"></i>
                    <p>暂无逐字稿</p>
                </div>
            `;
            return;
        }

        container.innerHTML = transcripts.map(transcript => {
            const preview = transcript.content.substring(0, 150) + (transcript.content.length > 150 ? '...' : '');
            const audioInfo = transcript.audio_filename
                ? `<span class="text-xs text-blue-600"><i class="fa fa-link"></i> ${transcript.audio_filename}</span>`
                : '';

            return `
                <div class="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition">
                    <div class="flex items-start justify-between mb-3">
                        <div class="flex-1">
                            <div class="flex items-center gap-2 mb-1">
                                <span class="text-sm font-mono text-gray-600">${transcript.id}</span>
                                ${audioInfo}
                            </div>
                            <div class="text-xs text-gray-500">
                                ${formatDateTime(transcript.created_at)}
                            </div>
                        </div>
                        <div class="flex items-center gap-2">
                            <button
                                onclick='openEditModal("${transcript.id}", ${JSON.stringify(transcript.content)})'
                                class="px-3 py-1 bg-blue-100 text-blue-700 text-sm rounded hover:bg-blue-200 transition">
                                <i class="fa fa-edit"></i> 编辑
                            </button>
                            <button
                                onclick="deleteTranscript('${transcript.id}')"
                                class="px-3 py-1 bg-red-100 text-red-700 text-sm rounded hover:bg-red-200 transition">
                                <i class="fa fa-trash"></i>
                            </button>
                        </div>
                    </div>
                    <div class="bg-gray-100 rounded p-3 font-mono text-xs text-gray-700 whitespace-pre-wrap">${preview}</div>
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('加载逐字稿失败:', error);
    }
}

function openEditModal(transcriptId, content) {
    editingTranscriptId = transcriptId;
    document.getElementById('editTranscriptContent').value = content;
    document.getElementById('editModal').classList.remove('hidden');
}

function closeEditModal() {
    editingTranscriptId = null;
    document.getElementById('editModal').classList.add('hidden');
}

async function updateTranscript() {
    if (!editingTranscriptId) return;

    const content = document.getElementById('editTranscriptContent').value.trim();
    if (!content) {
        alert('逐字稿内容不能为空');
        return;
    }

    try {
        const response = await fetch(`${TRANSCRIPT_API}/api/transcript`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                case_id: currentCaseId,
                transcript_id: editingTranscriptId,
                content: content,
                timestamps: []
            })
        });

        if (response.ok) {
            alert('更新成功！');
            closeEditModal();
            refreshAllData();
        }
    } catch (error) {
        console.error('更新失败:', error);
        alert('更新失败');
    }
}

async function deleteTranscript(transcriptId) {
    if (!confirm('确定要删除这条逐字稿吗？')) return;

    try {
        const response = await fetch(`${TRANSCRIPT_API}/api/transcript`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                case_id: currentCaseId,
                transcript_id: transcriptId
            })
        });

        if (response.ok) {
            alert('删除成功');
            refreshAllData();
        }
    } catch (error) {
        console.error('删除失败:', error);
        alert('删除失败');
    }
}

// ==================== 督导资料管理 ====================

// 拖拽上传 - 督导资料
const supervisionDropZone = document.getElementById('supervisionDropZone');
supervisionDropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    supervisionDropZone.classList.add('dragging');
});
supervisionDropZone.addEventListener('dragleave', () => {
    supervisionDropZone.classList.remove('dragging');
});
supervisionDropZone.addEventListener('drop', async (e) => {
    e.preventDefault();
    supervisionDropZone.classList.remove('dragging');
    const file = e.dataTransfer.files[0];
    if (file) {
        await uploadSupervision(file);
    }
});

// 文件选择 - 督导资料
document.getElementById('supervisionFileInput').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (file) {
        await uploadSupervision(file);
    }
});

async function uploadSupervision(file) {
    if (!currentCaseId) {
        alert('请先选择案例');
        return;
    }

    const title = document.getElementById('supervisionTitle').value.trim() || file.name;
    const note = document.getElementById('supervisionNote').value.trim();

    const formData = new FormData();
    formData.append('case_id', currentCaseId);
    formData.append('title', title);
    formData.append('note', note);
    formData.append('supervision_file', file);

    const progressDiv = document.getElementById('supervisionProgress');
    const progressBar = document.getElementById('supervisionProgressBar');
    const uploadStatus = document.getElementById('supervisionStatus');

    progressDiv.classList.remove('hidden');
    progressBar.style.width = '30%';
    uploadStatus.textContent = '上传中...';

    try {
        const response = await fetch(`${SUPERVISION_API}/api/supervision/upload`, {
            method: 'POST',
            body: formData
        });

        progressBar.style.width = '100%';
        uploadStatus.textContent = '上传完成';

        if (response.ok) {
            setTimeout(() => {
                progressDiv.classList.add('hidden');
                alert('督导资料上传成功！');
                clearSupervisionForm();
                refreshAllData();
            }, 500);
        } else {
            throw new Error('上传失败');
        }
    } catch (error) {
        console.error('上传失败:', error);
        progressDiv.classList.add('hidden');
        alert('上传失败，请检查服务器');
    }
}

function clearSupervisionForm() {
    document.getElementById('supervisionTitle').value = '';
    document.getElementById('supervisionNote').value = '';
    document.getElementById('supervisionFileInput').value = '';
}

async function refreshSupervisionList() {
    if (!currentCaseId) return;

    try {
        const response = await fetch(`${SUPERVISION_API}/api/supervision/list?case_id=${currentCaseId}`);
        const supervisionList = await response.json();

        const container = document.getElementById('supervisionList');

        if (supervisionList.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-400">
                    <i class="fa fa-file-text-o text-4xl mb-3"></i>
                    <p>暂无督导资料</p>
                </div>
            `;
            return;
        }

        container.innerHTML = supervisionList.map(supervision => {
            const fileIcon = getFileIcon(supervision.filename);
            const note = supervision.note ? `<p class="text-xs text-gray-500 mt-1">${supervision.note}</p>` : '';

            return `
                <div class="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition">
                    <div class="flex items-center justify-between">
                        <div class="flex-1">
                            <div class="flex items-center gap-3 mb-2">
                                <i class="fa ${fileIcon} text-amber-600 text-xl"></i>
                                <div>
                                    <p class="font-medium text-gray-800">${supervision.title}</p>
                                    <p class="text-xs text-gray-500">${supervision.filename}</p>
                                    ${note}
                                </div>
                            </div>
                            <div class="text-sm text-gray-500 ml-8">
                                <span><i class="fa fa-calendar"></i> ${formatDateTime(supervision.uploaded_at)}</span>
                                <span class="ml-4"><i class="fa fa-hdd-o"></i> ${formatFileSize(supervision.size)}</span>
                            </div>
                        </div>
                        <div class="flex items-center gap-2">
                            <a
                                href="${SUPERVISION_API}${supervision.url}"
                                target="_blank"
                                class="px-3 py-2 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition">
                                <i class="fa fa-download"></i>
                            </a>
                            <button
                                onclick="deleteSupervision('${supervision.filename}')"
                                class="px-3 py-2 bg-red-100 text-red-700 rounded hover:bg-red-200 transition">
                                <i class="fa fa-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('加载督导资料失败:', error);
    }
}

async function deleteSupervision(filename) {
    if (!confirm(`确定要删除督导资料 "${filename}" 吗？`)) return;

    try {
        const response = await fetch(`${SUPERVISION_API}/api/supervision/delete`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ case_id: currentCaseId, filename })
        });

        if (response.ok) {
            alert('删除成功');
            refreshAllData();
        }
    } catch (error) {
        console.error('删除失败:', error);
        alert('删除失败');
    }
}

// ==================== 资料汇总 ====================

async function updateSummary() {
    if (!currentCaseId) return;

    try {
        const [audioRes, transcriptRes, supervisionRes] = await Promise.all([
            fetch(`${AUDIO_API}/api/audio/list?case_id=${currentCaseId}`),
            fetch(`${TRANSCRIPT_API}/api/transcript?case_id=${currentCaseId}`),
            fetch(`${SUPERVISION_API}/api/supervision/list?case_id=${currentCaseId}`)
        ]);

        const audioList = await audioRes.json();
        const transcriptList = await transcriptRes.json();
        const supervisionList = await supervisionRes.json();

        document.getElementById('summaryAudioCount').textContent = audioList.length;
        document.getElementById('summaryTranscriptCount').textContent = transcriptList.length;
        document.getElementById('summarySupervisionCount').textContent = supervisionList.length;
    } catch (error) {
        console.error('更新汇总失败:', error);
    }
}

async function regenerateCaseLibrary() {
    if (confirm('确定要重新生成案例库吗？这将更新所有案例的HTML页面。')) {
        alert('请在服务器端执行：python src/generate_case_library.py');
    }
}

// ==================== 工具函数 ====================

function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const icons = {
        'txt': 'fa-file-text-o',
        'md': 'fa-file-code-o',
        'pdf': 'fa-file-pdf-o',
        'doc': 'fa-file-word-o',
        'docx': 'fa-file-word-o',
        'jpg': 'fa-file-image-o',
        'jpeg': 'fa-file-image-o',
        'png': 'fa-file-image-o'
    };
    return icons[ext] || 'fa-file-o';
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function formatDateTime(isoString) {
    const date = new Date(isoString);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}
