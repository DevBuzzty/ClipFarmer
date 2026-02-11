const analyzeBtn = document.getElementById('analyze-btn');
const urlInput = document.getElementById('vod-url');
const statusDiv = document.getElementById('status');
const clipContainer = document.getElementById('clip-container');
const saveSettingsBtn = document.getElementById('save-settings-btn');
const exportAllBtn = document.getElementById('export-all-btn');

const BACKEND_URL = 'http://localhost:5000';

// Tab switching logic
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById(btn.dataset.tab).classList.add('active');
    });
});

// Load settings on startup
window.addEventListener('DOMContentLoaded', async () => {
    try {
        const settings = await window.api.fetch(`${BACKEND_URL}/settings`, { method: 'GET' });
        if (settings) {
            document.getElementById('set-gemini-key').value = settings.GEMINI_API_KEY || '';
            document.getElementById('set-twitch-id').value = settings.TWITCH_CLIENT_ID || '';
            document.getElementById('set-twitch-secret').value = settings.TWITCH_CLIENT_SECRET || '';
            document.getElementById('set-youtube-json').value = settings.YOUTUBE_JSON_PATH || '';
            document.getElementById('set-tiktok-session').value = settings.TIKTOK_SESSION_ID || '';
            document.getElementById('set-gpu').checked = settings.USE_GPU || false;
            document.getElementById('set-whisper-model').value = settings.WHISPER_MODEL || 'base';
        }
    } catch (e) {
        console.error("Failed to load settings", e);
    }
});

saveSettingsBtn.addEventListener('click', async () => {
    const settings = {
        GEMINI_API_KEY: document.getElementById('set-gemini-key').value,
        TWITCH_CLIENT_ID: document.getElementById('set-twitch-id').value,
        TWITCH_CLIENT_SECRET: document.getElementById('set-twitch-secret').value,
        YOUTUBE_JSON_PATH: document.getElementById('set-youtube-json').value,
        TIKTOK_SESSION_ID: document.getElementById('set-tiktok-session').value,
        USE_GPU: document.getElementById('set-gpu').checked,
        WHISPER_MODEL: document.getElementById('set-whisper-model').value
    };

    try {
        const response = await window.api.fetch(`${BACKEND_URL}/settings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });
        if (response.success) {
            alert('Einstellungen erfolgreich gespeichert!');
        }
    } catch (e) {
        alert('Fehler beim Speichern: ' + e.message);
    }
});

analyzeBtn.addEventListener('click', async () => {
    const url = urlInput.value;
    if (!url) {
        alert('Bitte eine URL eingeben!');
        return;
    }

    statusDiv.textContent = 'Lade VOD herunter und transkribiere... (Dies kann dauern)';
    analyzeBtn.disabled = true;
    clipContainer.innerHTML = '';

    try {
        const response = await window.api.fetch(`${BACKEND_URL}/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });

        if (response.error) {
            statusDiv.textContent = `Fehler: ${response.error}`;
            analyzeBtn.disabled = false;
            return;
        }

        displayClips(response.clips, url);
        statusDiv.textContent = `${response.clips.length} Clips identifiziert.`;
        analyzeBtn.disabled = false;
        exportAllBtn.style.display = 'inline-block';

        // Store clips for batch export
        window.currentClips = response.clips;
    } catch (err) {
        statusDiv.textContent = `Netzwerkfehler: ${err.message}`;
        analyzeBtn.disabled = false;
    }
});

function displayClips(clips, vodUrl) {
    clipContainer.innerHTML = '';

    // Sort by rating desc
    clips.sort((a, b) => b.rating - a.rating);

    clips.forEach((clip, index) => {
        const card = document.createElement('div');
        card.className = 'clip-card';

        const timestampUrl = `${vodUrl}?t=${Math.floor(clip.start)}s`;

        // Extract video ID from VOD URL
        const videoIdMatch = vodUrl.match(/videos\/(\d+)/);
        const videoId = videoIdMatch ? videoIdMatch[1] : null;
        const twitchClipUrl = videoId ? `https://www.twitch.tv/videos/${videoId}?t=${Math.floor(clip.start)}s` : '#';

        card.innerHTML = `
            <div class="rating">${clip.rating}/10</div>
            <div class="clip-info">
                <div class="clip-title">${clip.title}</div>
                <div class="clip-meta">${Math.floor(clip.start)}s - ${Math.floor(clip.end)}s | ${clip.description}</div>
                <div class="clip-seo" style="font-size: 0.8em; color: #666; margin-top: 5px;">
                    ${clip.hashtags ? clip.hashtags.join(' ') : ''}
                </div>
            </div>
            <div class="actions">
                <button class="btn-secondary" onclick="window.open('${timestampUrl}')">Vorschau</button>
                <button class="btn-secondary" onclick="window.open('${twitchClipUrl}')">Twitch Clip Link</button>
                <button onclick="exportClip(${index}, ${JSON.stringify(clip).replace(/"/g, '&quot;')})">Exportieren</button>
            </div>
        `;
        clipContainer.appendChild(card);
    });
}

async function exportClip(id, clipData) {
    statusDiv.textContent = `Exportiere Clip: ${clipData.title}...`;

    try {
        const response = await window.api.fetch(`${BACKEND_URL}/export`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ clip: clipData })
        });

        if (response.success) {
            alert(`Clip erfolgreich exportiert: ${response.path}`);
            statusDiv.textContent = 'Export abgeschlossen.';
            // Add upload buttons to the specific card
            const card = document.querySelectorAll('.clip-card')[id];
            const actions = card.querySelector('.actions');

            if (!actions.querySelector('.upload-group')) {
                const uploadGroup = document.createElement('div');
                uploadGroup.className = 'upload-group';
                uploadGroup.style.marginTop = '10px';
                uploadGroup.innerHTML = `
                    <button class="btn-yt" onclick="uploadClip('${response.path}', 'youtube', '${clipData.title.replace(/'/g, "\\'")}')">Shorts</button>
                    <button class="btn-tt" onclick="uploadClip('${response.path}', 'tiktok', '${clipData.title.replace(/'/g, "\\'")}')">TikTok</button>
                `;
                actions.appendChild(uploadGroup);
            }
        } else {
            alert(`Fehler beim Export: ${response.error}`);
            statusDiv.textContent = 'Export fehlgeschlagen.';
        }
    } catch (err) {
        alert(`Netzwerkfehler: ${err.message}`);
    }
}

exportAllBtn.addEventListener('click', async () => {
    if (!window.currentClips) return;

    statusDiv.textContent = 'Batch-Export gestartet...';
    exportAllBtn.disabled = true;

    for (let i = 0; i < window.currentClips.length; i++) {
        statusDiv.textContent = `Exportiere Clip ${i+1} von ${window.currentClips.length}...`;
        await exportClip(i, window.currentClips[i]);
    }

    statusDiv.textContent = 'Batch-Export abgeschlossen.';
    exportAllBtn.disabled = false;
});

async function uploadClip(path, platform, title) {
    statusDiv.textContent = `Lade auf ${platform} hoch...`;
    try {
        const response = await window.api.fetch(`${BACKEND_URL}/upload`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                platform,
                video_path: path,
                title: title,
                description: `#shorts #twitch #viral ${title}`,
                tags: ['twitch', 'clip', 'viral']
            })
        });

        if (response.success) {
            alert(`Erfolgreich auf ${platform} hochgeladen!`);
            statusDiv.textContent = `Upload auf ${platform} abgeschlossen.`;
        } else {
            alert(`Upload Fehler: ${response.error}`);
            statusDiv.textContent = `Upload auf ${platform} fehlgeschlagen.`;
        }
    } catch (err) {
        alert(`Netzwerkfehler: ${err.message}`);
    }
}
