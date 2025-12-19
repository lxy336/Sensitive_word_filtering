// 全局变量
let currentAudioFile = null;
let isRecording = false;
let recordingTimer = null;
let recordingStartTime = null;
let recordingDuration = 0; // 录音总时长（秒）
let mediaRecorder = null;
let audioChunks = [];
let sensitiveWords = ['小狼', '开心', '快乐'];
let currentResults = null;

// DOM 元素
let uploadArea, audioFileInput, fileInfo, fileName, removeFileBtn;
let recordBtn, recordTime, recordDuration, customDurationInput, customDuration;
let sensitiveWordInput, wordTags, processBtn, processStatus, resultsSection;
let loadingOverlay, progressFill, progressText, loadingText;

// 初始化DOM元素引用
function initializeDOMElements() {
    uploadArea = document.getElementById('uploadArea');
    audioFileInput = document.getElementById('audioFile');
    fileInfo = document.getElementById('fileInfo');
    fileName = document.getElementById('fileName');
    removeFileBtn = document.getElementById('removeFile');
    recordBtn = document.getElementById('recordBtn');
    recordTime = document.getElementById('recordTime');
    recordDuration = document.getElementById('recordDuration');
    customDurationInput = document.getElementById('customDurationInput');
    customDuration = document.getElementById('customDuration');
    sensitiveWordInput = document.getElementById('sensitiveWordInput');
    wordTags = document.getElementById('wordTags');
    processBtn = document.getElementById('processBtn');
    processStatus = document.getElementById('processStatus');
    resultsSection = document.getElementById('resultsSection');
    loadingOverlay = document.getElementById('loadingOverlay');
    progressFill = document.getElementById('progressFill');
    progressText = document.getElementById('progressText');
    loadingText = document.getElementById('loadingText');
}

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeDOMElements();
    initializeEventListeners();
    updateSensitiveWordTags();
});

// 输入方式选择函数
function selectUploadMethod() {
    document.getElementById('inputMethodSelection').style.display = 'none';
    document.getElementById('uploadSection').style.display = 'block';
    document.getElementById('recordingSection').style.display = 'none';
}

function selectRecordMethod() {
    document.getElementById('inputMethodSelection').style.display = 'none';
    document.getElementById('uploadSection').style.display = 'none';
    document.getElementById('recordingSection').style.display = 'block';
}

function backToMethodSelection() {
    document.getElementById('inputMethodSelection').style.display = 'block';
    document.getElementById('uploadSection').style.display = 'none';
    document.getElementById('recordingSection').style.display = 'none';

    // 清理当前选择的文件或录音
    if (currentAudioFile) {
        removeFile();
    }
    if (isRecording) {
        stopRecording();
    }
}

// 初始化事件监听器
function initializeEventListeners() {
    // 输入方式选择
    document.getElementById('uploadOption').addEventListener('click', selectUploadMethod);
    document.getElementById('recordOption').addEventListener('click', selectRecordMethod);
    document.getElementById('backFromUpload').addEventListener('click', backToMethodSelection);
    document.getElementById('backFromRecord').addEventListener('click', backToMethodSelection);

    // 文件上传
    uploadArea.addEventListener('click', () => audioFileInput.click());
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('drop', handleDrop);
    audioFileInput.addEventListener('change', handleFileSelect);
    removeFileBtn.addEventListener('click', removeFile);

    // 录音功能
    recordBtn.addEventListener('click', toggleRecording);
    recordDuration.addEventListener('change', handleDurationChange);

    // 敏感词输入
    sensitiveWordInput.addEventListener('keypress', handleSensitiveWordInput);

    // 处理按钮
    processBtn.addEventListener('click', startProcessing);

    // 下载按钮
    document.getElementById('downloadTxt').addEventListener('click', downloadTxtResult);
}

// 文件拖拽处理
function handleDragOver(e) {
    e.preventDefault();
    uploadArea.style.borderColor = '#357abd';
    uploadArea.style.background = '#f0f8ff';
}

function handleDrop(e) {
    e.preventDefault();
    uploadArea.style.borderColor = '#4a90e2';
    uploadArea.style.background = '#f8fbff';
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

// 文件选择处理
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
}

// 处理文件
function handleFile(file) {
    // 检查文件类型
    const allowedTypes = ['audio/mp3', 'audio/wav', 'audio/m4a', 'audio/mpeg'];
    if (!allowedTypes.includes(file.type) && !file.name.match(/\.(mp3|wav|m4a)$/i)) {
        alert('请选择支持的音频格式：MP3, WAV, M4A');
        return;
    }

    currentAudioFile = file;
    fileName.textContent = file.name;
    uploadArea.style.display = 'none';
    fileInfo.style.display = 'flex';
    
    // 启用处理按钮
    processBtn.disabled = false;
}

// 移除文件
function removeFile() {
    currentAudioFile = null;
    audioFileInput.value = '';
    uploadArea.style.display = 'block';
    fileInfo.style.display = 'none';
    processBtn.disabled = true;
}

// 处理录音时长选择变化
function handleDurationChange() {
    if (recordDuration.value === 'custom') {
        customDurationInput.style.display = 'block';
    } else {
        customDurationInput.style.display = 'none';
    }
}

// 切换录音状态
async function toggleRecording() {
    if (!isRecording) {
        await startRecording();
    } else {
        stopRecording();
    }
}

// 开始录音
async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            const audioFile = new File([audioBlob], `recording_${Date.now()}.wav`, { type: 'audio/wav' });
            handleFile(audioFile);
        };

        mediaRecorder.start();
        isRecording = true;
        recordingStartTime = Date.now();
        
        // 更新UI
        recordBtn.innerHTML = '<i class="fas fa-stop"></i><span>停止录音</span>';
        recordBtn.classList.add('recording');
        
        // 开始计时
        recordingTimer = setInterval(updateRecordingTime, 100);
        
        // 自动停止录音
        const durationValue = recordDuration.value;
        let duration;

        if (durationValue === 'custom') {
            // 使用自定义时长
            duration = parseInt(customDuration.value) || 30; // 默认30秒
            if (duration < 1) duration = 1;
            if (duration > 300) duration = 300; // 最大5分钟
        } else {
            // 使用预设时长
            duration = parseInt(durationValue);
        }

        // 保存录音总时长
        recordingDuration = duration;

        // 设置自动停止定时器
        setTimeout(() => {
            if (isRecording) {
                stopRecording();
                console.log(`录音自动停止，时长: ${duration}秒`);
            }
        }, duration * 1000);
        
    } catch (error) {
        console.error('录音失败:', error);
        alert('无法访问麦克风，请检查权限设置');
    }
}

// 停止录音
function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
        
        isRecording = false;
        clearInterval(recordingTimer);
        
        // 重置UI
        recordBtn.innerHTML = '<i class="fas fa-microphone"></i><span>开始录音</span>';
        recordBtn.classList.remove('recording');
        recordTime.textContent = '00:00';
    }
}

// 更新录音时间
function updateRecordingTime() {
    if (isRecording && recordingStartTime) {
        const elapsed = Date.now() - recordingStartTime;
        const elapsedSeconds = Math.floor(elapsed / 1000);

        // 计算剩余时间
        const remainingSeconds = Math.max(0, recordingDuration - elapsedSeconds);
        const minutes = Math.floor(remainingSeconds / 60);
        const seconds = remainingSeconds % 60;

        // 显示剩余时间
        if (remainingSeconds > 0) {
            recordTime.textContent = `剩余 ${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        } else {
            recordTime.textContent = '00:00';
        }

        // 如果时间到了，自动停止（双重保险）
        if (remainingSeconds <= 0 && isRecording) {
            stopRecording();
        }
    }
}

// 处理敏感词输入
function handleSensitiveWordInput(e) {
    if (e.key === 'Enter') {
        const word = e.target.value.trim();
        if (word && !sensitiveWords.includes(word)) {
            sensitiveWords.push(word);
            updateSensitiveWordTags();
            e.target.value = '';
        }
    }
}

// 更新敏感词标签
function updateSensitiveWordTags() {
    wordTags.innerHTML = '';
    sensitiveWords.forEach((word, index) => {
        const tag = document.createElement('span');
        tag.className = 'word-tag';
        tag.innerHTML = `${word} <i class="fas fa-times" onclick="removeSensitiveWord(${index})"></i>`;
        wordTags.appendChild(tag);
    });
}

// 移除敏感词
function removeSensitiveWord(index) {
    sensitiveWords.splice(index, 1);
    updateSensitiveWordTags();
}

// 开始处理
async function startProcessing() {
    if (!currentAudioFile) {
        alert('请先选择音频文件或录音');
        return;
    }

    // 显示加载界面
    showLoading();

    // 获取选中的过滤方法
    const filterMethod = document.querySelector('input[name="filterMethod"]:checked').value;

    try {
        // 检查是否有后端API
        const apiAvailable = await checkApiAvailability();

        if (apiAvailable) {
            // 使用真实API处理
            await processWithApi(filterMethod);
        } else {
            // 使用模拟处理
            await simulateProcessing(filterMethod);
        }

        // 隐藏加载界面
        hideLoading();

        // 显示结果
        displayResults();

    } catch (error) {
        console.error('处理失败:', error);
        hideLoading();
        alert('处理失败，请重试');
    }
}

// 检查API可用性
async function checkApiAvailability() {
    try {
        const response = await fetch('/api/health');
        return response.ok;
    } catch (error) {
        console.log('API不可用，使用模拟模式');
        return false;
    }
}

// 使用API处理
async function processWithApi(filterMethod) {
    try {
        // 1. 上传文件
        updateProcessStatus('preprocessing', 'processing');
        await updateProgress(0, 10, '正在上传音频文件...');

        const formData = new FormData();
        formData.append('audio', currentAudioFile);

        const uploadResponse = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        if (!uploadResponse.ok) {
            throw new Error('文件上传失败');
        }

        const uploadResult = await uploadResponse.json();
        updateProcessStatus('preprocessing', 'completed');

        // 2. 加载Whisper模型
        updateProcessStatus('recognition', 'processing');
        await updateProgress(10, 25, '🤖 加载 Whisper base 模型...');
        await new Promise(resolve => setTimeout(resolve, 1000)); // 模拟加载时间

        // 3. 语音识别和过滤
        await updateProgress(25, 40, '🎵 开始转录音频（集成敏感词过滤）...');
        await new Promise(resolve => setTimeout(resolve, 500));

        await updateProgress(40, 70, '🔄 正在进行语音识别...');
        await new Promise(resolve => setTimeout(resolve, 1000));

        // 4. 发送处理请求
        await updateProgress(70, 80, '🛡️ 正在应用敏感词过滤...');

        const processResponse = await fetch('/api/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                audio_file: uploadResult.filename,
                sensitive_words: sensitiveWords,
                filter_method: filterMethod
            })
        });

        if (!processResponse.ok) {
            const errorData = await processResponse.json();
            throw new Error(errorData.error || '音频处理失败');
        }

        const processResult = await processResponse.json();

        // 5. 处理完成
        updateProcessStatus('recognition', 'completed');
        updateProcessStatus('filtering', 'completed');
        await updateProgress(80, 95, '✅ 转录完成，正在生成结果...');
        await new Promise(resolve => setTimeout(resolve, 500));

        await updateProgress(95, 100, '🎉 处理完成！');

        // 转换结果格式
        currentResults = {
            audioFile: processResult.audio_file,
            language: processResult.language,
            duration: processResult.duration,
            processTime: processResult.process_time,
            realTimeFactor: processResult.real_time_factor,
            filterMethod: processResult.filter_method,
            originalText: processResult.original_text,
            simplifiedText: processResult.simplified_text,
            filteredText: processResult.filtered_text,
            segments: processResult.segments.map(seg => ({
                start: seg.start,
                end: seg.end,
                original: seg.original,
                simplified: seg.simplified,
                filtered: seg.filtered
            })),
            stats: processResult.stats,
            resultFile: processResult.result_file
        };

    } catch (error) {
        console.error('API处理失败:', error);
        throw error;
    }
}

// 显示加载界面
function showLoading() {
    loadingOverlay.style.display = 'flex';
    processStatus.style.display = 'block';

    // 重置进度条
    progressFill.style.width = '0%';
    progressText.textContent = '0%';
    loadingText.textContent = '正在准备处理...';

    // 更新状态
    updateProcessStatus('preprocessing', 'completed');
    updateProcessStatus('recognition', 'processing');
    updateProcessStatus('filtering', 'waiting');
}

// 隐藏加载界面
function hideLoading() {
    loadingOverlay.style.display = 'none';
}

// 更新处理状态
function updateProcessStatus(step, status) {
    const statusItems = document.querySelectorAll('.status-item');
    const stepMap = { preprocessing: 0, recognition: 1, filtering: 2 };
    const item = statusItems[stepMap[step]];
    
    if (!item) return;
    
    const icon = item.querySelector('.status-icon');
    icon.className = 'status-icon fas ';
    
    switch (status) {
        case 'completed':
            icon.classList.add('fa-check');
            break;
        case 'processing':
            icon.classList.add('fa-spinner', 'fa-spin');
            break;
        case 'waiting':
            icon.classList.add('fa-clock');
            break;
    }
}

// 模拟处理过程
async function simulateProcessing(filterMethod) {
    // 模拟音频预处理
    await updateProgress(0, 30, '正在预处理音频文件...');
    
    // 模拟语音识别
    updateProcessStatus('recognition', 'processing');
    await updateProgress(30, 70, '正在进行语音识别...');
    
    // 模拟敏感词过滤
    updateProcessStatus('recognition', 'completed');
    updateProcessStatus('filtering', 'processing');
    await updateProgress(70, 100, '正在过滤敏感词...');
    
    // 完成处理
    updateProcessStatus('filtering', 'completed');
    
    // 生成模拟结果
    generateMockResults(filterMethod);
}

// 更新进度条
function updateProgress(start, end, text) {
    return new Promise((resolve) => {
        loadingText.textContent = text;
        let current = start;
        const interval = setInterval(() => {
            current += 2;

            // 确保进度不超过目标值和100%
            const actualProgress = Math.min(current, end, 100);
            progressFill.style.width = `${actualProgress}%`;
            progressText.textContent = `${actualProgress}%`;

            if (current >= end) {
                clearInterval(interval);
                setTimeout(resolve, 500);
            }
        }, 100);
    });
}

// 生成模拟结果
function generateMockResults(filterMethod) {
    const originalText = "今天天气真好，小狼很开心，我们一起去玩吧，感觉很快乐。";
    const filteredText = originalText.replace(/小狼/g, '***').replace(/开心/g, '***').replace(/快乐/g, '***');
    
    currentResults = {
        audioFile: currentAudioFile.name,
        language: 'zh',
        duration: '00:04',
        processTime: '2.3秒',
        realTimeFactor: '1.7x',
        filterMethod: filterMethod,
        originalText: originalText,
        simplifiedText: originalText, // 模拟数据中简体转换结果与原文相同
        filteredText: filteredText,
        segments: [
            {
                start: 0.0,
                end: 2.5,
                original: "今天天气真好，小狼很开心",
                simplified: "今天天气真好，小狼很开心",
                filtered: "今天天气真好，***很***"
            },
            {
                start: 2.5,
                end: 4.0,
                original: "我们一起去玩吧，感觉很快乐",
                simplified: "我们一起去玩吧，感觉很快乐",
                filtered: "我们一起去玩吧，感觉很***"
            }
        ]
    };
}

// 显示结果
function displayResults() {
    if (!currentResults) return;
    
    // 显示结果区域
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth' });
    
    // 填充基本信息
    document.getElementById('audioFileName').textContent = currentResults.audioFile;
    document.getElementById('detectedLanguage').textContent = currentResults.language === 'zh' ? '中文' : currentResults.language;
    document.getElementById('audioDuration').textContent = currentResults.duration;
    document.getElementById('processTime').textContent = currentResults.processTime;
    document.getElementById('realTimeFactor').textContent = currentResults.realTimeFactor;
    document.getElementById('filterMethodUsed').textContent = getFilterMethodName(currentResults.filterMethod);
    
    // 填充文本结果
    document.getElementById('simplifiedText').textContent = currentResults.simplifiedText || currentResults.originalText;
    document.getElementById('filteredText').textContent = currentResults.filteredText;
    
    // 填充分段详情
    displaySegments();
}

// 获取过滤方法名称
function getFilterMethodName(method) {
    const names = {
        'DFA': 'DFA (确定有限自动机)',
        'aho_corasick': 'Aho-Corasick (AC自动机)',
        'trie_tree': 'Trie Tree (字典树)',
        'replace': 'Replace (字符串替换)',
        'regular_expression': 'Regular Expression (正则表达式)'
    };
    return names[method] || method;
}

// 显示分段详情
function displaySegments() {
    const container = document.getElementById('segmentsContainer');
    container.innerHTML = '';
    
    currentResults.segments.forEach((segment, index) => {
        const segmentDiv = document.createElement('div');
        segmentDiv.className = 'segment-item';
        
        segmentDiv.innerHTML = `
            <div class="segment-header">
                <span>分段 ${index + 1}</span>
                <span>[${segment.start.toFixed(2)}s - ${segment.end.toFixed(2)}s]</span>
            </div>
            <div class="segment-content">
                <div class="segment-text segment-original">
                    <strong>原始文本:</strong> ${highlightSensitiveWords(segment.original)}
                </div>
                <div class="segment-text segment-simplified">
                    <strong>简体转换:</strong> ${highlightSensitiveWords(segment.simplified || segment.original)}
                </div>
                <div class="segment-text segment-filtered">
                    <strong>过滤结果:</strong> ${segment.filtered}
                </div>
            </div>
        `;
        
        container.appendChild(segmentDiv);
    });
}

// 高亮敏感词
function highlightSensitiveWords(text) {
    let highlightedText = text;
    sensitiveWords.forEach(word => {
        const regex = new RegExp(word, 'g');
        highlightedText = highlightedText.replace(regex, `<span class="sensitive-highlight">${word}</span>`);
    });
    return highlightedText;
}

// 下载文本结果
async function downloadTxtResult() {
    if (!currentResults) return;

    // 如果有API结果文件，直接下载
    if (currentResults.resultFile) {
        try {
            const filename = currentResults.resultFile.replace('.json', '.txt');
            const response = await fetch(`/api/download/txt/${filename}`);
            if (response.ok) {
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                return;
            }
        } catch (error) {
            console.log('API下载失败，使用本地生成');
        }
    }

    // 本地生成文本文件
    const content = `Whisper 集成敏感词过滤测试结果
${'='.repeat(50)}

处理时间: ${new Date().toLocaleString()}
音频文件: ${currentResults.audioFile}
敏感词: ${JSON.stringify(sensitiveWords)}
识别语言: ${currentResults.language === 'zh' ? 'zh' : currentResults.language}
简体字转换: 启用
过滤方法: ${getFilterMethodName(currentResults.filterMethod)}

简体字转换结果:
${'-'.repeat(30)}
${currentResults.simplifiedText || currentResults.originalText}

敏感词过滤结果:
${'-'.repeat(30)}
${currentResults.filteredText}

分段详情对比:
${'-'.repeat(30)}
${currentResults.segments.map((seg, i) =>
    `分段 ${i + 1}: [${seg.start.toFixed(2)}s - ${seg.end.toFixed(2)}s]
  原始文本: ${seg.original}
  简体转换: ${seg.simplified || seg.original}
  过滤结果: ${seg.filtered}`
).join('\n\n')}

统计信息:
${'-'.repeat(30)}
音频时长: ${currentResults.duration} 秒
处理时间: ${currentResults.processTime}
实时倍数: ${currentResults.realTimeFactor}
分段数量: ${currentResults.segments.length}
过滤方法: ${getFilterMethodName(currentResults.filterMethod)}
`;

    downloadFile(content, `语音过滤结果_${Date.now()}.txt`, 'text/plain');
}





// 下载文件
function downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}
