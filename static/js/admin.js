const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const fileList = document.getElementById('fileList');
const uploadBtn = document.getElementById('uploadBtn');
const statusDiv = document.getElementById('status');
let selectedFiles = [];

dropzone.addEventListener('click', () => fileInput.click());

dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('border-blue-500');
});

dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('border-blue-500');
});

dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('border-blue-500');
    selectedFiles = Array.from(e.dataTransfer.files);
    updateFileList();
});

fileInput.addEventListener('change', (e) => {
    selectedFiles = Array.from(e.target.files);
    updateFileList();
});

function updateFileList() {
    fileList.innerHTML = '';
    selectedFiles.forEach(file => {
        const div = document.createElement('div');
        div.className = 'flex items-center justify-between bg-gray-100 p-2 rounded';
        div.innerHTML = `<span class="text-sm text-gray-700">${file.name}</span><span class="text-xs text-gray-500">${(file.size/1024).toFixed(1)} KB</span>`;
        fileList.appendChild(div);
    });
    uploadBtn.disabled = selectedFiles.length === 0;
}

uploadBtn.addEventListener('click', async () => {
    const token = localStorage.getItem('token');
    if (!token) {
        alert('No autorizado');
        window.location.href = '/login';
        return;
    }
    
    const formData = new FormData();
    selectedFiles.forEach(file => {
        formData.append('files', file);
    });
    
    uploadBtn.disabled = true;
    statusDiv.innerHTML = '<p class="text-blue-600">Cargando y procesando documentos...</p>';
    
    try {
        const response = await fetch('/api/admin/upload', {
            method: 'POST',
            headers: {'Authorization': `Bearer ${token}`},
            body: formData
        });
        const data = await response.json();
        if (response.ok) {
            statusDiv.innerHTML = `<p class="text-green-600">${data.message}</p>`;
            selectedFiles = [];
            fileList.innerHTML = '';
            fileInput.value = '';
        } else {
            statusDiv.innerHTML = `<p class="text-red-600">${data.detail}</p>`;
        }
    } catch (error) {
        statusDiv.innerHTML = '<p class="text-red-600">Error de conexión</p>';
    }
    uploadBtn.disabled = selectedFiles.length === 0;
});

function logout() {
    localStorage.clear();
    window.location.href = '/login';
}
