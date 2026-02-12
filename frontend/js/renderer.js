const BACKEND_URL = 'http://127.0.0.1:5001';

const navBtns = document.querySelectorAll('.nav-btn');
const views = document.querySelectorAll('.view');
const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');
const restartBtn = document.getElementById('restart-btn');

const vodUrlInput = document.getElementById('vod-url');
const analyzeBtn = document.getElementById('analyze-btn');
const progressContainer = document.getElementById('progress-container');
const progressBarFill = document.getElementById('progress-bar-fill');
const progressStatus = document.getElementById('progress-status');
const progressPercent = document.getElementById('progress-percent');
const clipGrid = document.getElementById('clip-grid');
const exportAllBtn = document.getElementById('export-all-btn');

const settingsFields = {
    GEMINI_API_KEY: document.getElementById('set-gemini-key'),
    WHISPER_MODEL: document.getElementById('set-whisper-model'),
    LAYOUT: document.getElementById('set-layout'),
    USE_GPU: document.getElementById('set-gpu'),
    CAPTIONS: document.getElementById('set-captions')
};

// Tab Switching
navBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        navBtns.forEach(b => b.classList.remove('active'));
        views.forEach(v => v.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById(btn.dataset.view).classList.add('active');
    });
});

// Server Health Check
async function checkHealth() {
    try {
        const data = await window.api.fetch(`${BACKEND_URL}/health`);
        if (data && data.status === 'healthy') {
            statusDot.className = 'status-dot status-online';
            statusText.textContent = 'Server Online';
            restartBtn.style.display = 'none';
        } else throw new Error();
    } catch (e) {
        statusDot.className = 'status-dot status-offline';
        statusText.textContent = 'Server Offline';
        restartBtn.style.display = 'inline-block';
    }
}

restartBtn.addEventListener('click', () => {
    window.api.restartBackend();
});

setInterval(checkHealth, 5000);
checkHealth();

// Load & Save Settings
async function loadSettings() {
    try {
        const config = await window.api.fetch(`${BACKEND_URL}/settings`);
        if (config) {
            settingsFields.GEMINI_API_KEY.value = config.GEMINI_API_KEY || '';
            settingsFields.WHISPER_MODEL.value = config.WHISPER_MODEL || 'base';
            settingsFields.LAYOUT.value = config.LAYOUT || 'stack';
            settingsFields.USE_GPU.checked = config.USE_GPU || false;
            settingsFields.CAPTIONS.checked = config.CAPTIONS !== undefined ? config.CAPTIONS : true;
        }
    } catch (e) { console.error("Settings load error", e); }
}

document.getElementById('save-settings-btn').addEventListener('click', async () => {
    const data = {
        GEMINI_API_KEY: settingsFields.GEMINI_API_KEY.value,
        WHISPER_MODEL: settingsFields.WHISPER_MODEL.value,
        LAYOUT: settingsFields.LAYOUT.value,
        USE_GPU: settingsFields.USE_GPU.checked,
        CAPTIONS: settingsFields.CAPTIONS.checked
    };
    try {
        await window.api.fetch(`${BACKEND_URL}/settings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        alert("Einstellungen gespeichert!");
    } catch (e) { alert("Fehler beim Speichern!"); }
});

loadSettings();

// Task Polling
async function pollTask(taskId, onUpdate) {
    return new Promise((resolve, reject) => {
        const interval = setInterval(async () => {
            try {
                const task = await window.api.fetch(`${BACKEND_URL}/status/${taskId}`);
                if (onUpdate) onUpdate(task);
                if (task.status === 'completed') {
                    clearInterval(interval);
                    resolve(task.result);
                } else if (task.status === 'failed') {
                    clearInterval(interval);
                    reject(new Error(task.error));
                }
            } catch (e) {
                clearInterval(interval);
                reject(e);
            }
        }, 1000);
    });
}

// Analyze Workflow
analyzeBtn.addEventListener('click', async () => {
    const url = vodUrlInput.value;
    if (!url) return alert("URL eingeben!");

    analyzeBtn.disabled = true;
    progressContainer.style.display = 'block';
    clipGrid.innerHTML = '';

    try {
        const { task_id } = await window.api.fetch(`${BACKEND_URL}/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });

        const result = await pollTask(task_id, (task) => {
            progressStatus.textContent = translateStatus(task.status);
            progressPercent.textContent = `${task.progress}%`;
            progressBarFill.style.width = `${task.progress}%`;
        });

        displayClips(result.clips);
    } catch (e) {
        progressStatus.textContent = `Fehler: ${e.message}`;
        analyzeBtn.disabled = false;
    }
});

function translateStatus(s) {
    const map = {
        'downloading': 'Lädt VOD herunter...',
        'transcribing': 'KI Transkription...',
        'audio_analysis': 'Audio-Heatmap wird erstellt...',
        'ai_search': 'KI sucht virale Momente...',
        'detecting_layout': 'Facecam wird lokalisiert...'
    };
    return map[s] || s;
}

function displayClips(clips) {
    analyzeBtn.disabled = false;
    exportAllBtn.style.display = 'block';
    clipGrid.innerHTML = '';

    clips.forEach((clip, i) => {
        const el = document.createElement('div');
        el.className = 'clip-card';
        el.innerHTML = `
            <div class="clip-header">
                <span class="rating-tag">Viral: ${clip.rating}/10</span>
                <span style="font-size: 11px; color: var(--text-dim);">${Math.floor(clip.start)}s - ${Math.floor(clip.end)}s</span>
            </div>
            <div class="clip-body">
                <div style="font-weight: 700; margin-bottom: 5px;">${clip.title}</div>
                <div style="font-size: 12px; color: var(--text-dim); margin-bottom: 15px;">${clip.description}</div>
                <div style="display: flex; gap: 8px;">
                    <button class="outline-btn" style="flex: 1; font-size: 11px;" onclick="window.open('${clip.twitch_url}', '_blank')">Link</button>
                    <button class="primary-btn" style="flex: 2; font-size: 12px;" onclick="exportClip(${i}, ${JSON.stringify(clip).replace(/"/g, '&quot;')})">Exportieren</button>
                </div>
            </div>
        `;
        clipGrid.appendChild(el);
    });
}

window.exportClip = async (index, clipData) => {
    const card = clipGrid.children[index];
    const btn = card.querySelector('.primary-btn');
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = "Verarbeitung...";

    try {
        const { task_id } = await window.api.fetch(`${BACKEND_URL}/export`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ clip: clipData })
        });

        const res = await pollTask(task_id, (task) => {
            btn.textContent = `Export: ${task.progress}%`;
        });

        btn.textContent = "Fertig!";
        btn.style.background = "#00ff88";
        console.log("Saved to:", res.path);
    } catch (e) {
        btn.disabled = false;
        btn.textContent = "Fehler!";
        alert(e.message);
    }
};
