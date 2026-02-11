const analyzeBtn = document.getElementById('analyze-btn');
const urlInput = document.getElementById('vod-url');
const statusDiv = document.getElementById('status');
const clipContainer = document.getElementById('clip-container');

const BACKEND_URL = 'http://localhost:5000';

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

        card.innerHTML = `
            <div class="rating">${clip.rating}/10</div>
            <div class="clip-info">
                <div class="clip-title">${clip.title}</div>
                <div class="clip-meta">${Math.floor(clip.start)}s - ${Math.floor(clip.end)}s | ${clip.description}</div>
            </div>
            <div class="actions">
                <button class="btn-secondary" onclick="window.open('${timestampUrl}')">Vorschau</button>
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
        } else {
            alert(`Fehler beim Export: ${response.error}`);
            statusDiv.textContent = 'Export fehlgeschlagen.';
        }
    } catch (err) {
        alert(`Netzwerkfehler: ${err.message}`);
    }
}
