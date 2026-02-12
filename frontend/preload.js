const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
    fetch: async (url, options) => {
        const response = await fetch(url, options);
        return await response.json();
    },
    restartBackend: () => ipcRenderer.send('restart-backend')
});
