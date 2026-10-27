const questionInput = document.getElementById('questionInput');
const sendBtn = document.getElementById('sendBtn');
const chatMessages = document.getElementById('chatMessages');
const historyDiv = document.getElementById('history');

sendBtn.addEventListener('click', sendMessage);
questionInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

function logout() {
    localStorage.clear();
    window.location.href = '/login';
}

async function sendMessage() {
    const token = localStorage.getItem('token');
    if (!token) {
        alert('No autorizado');
        window.location.href = '/login';
        return;
    }
    
    const question = questionInput.value.trim();
    if (!question) return;
    
    // Mensaje usuario
    const userMsg = document.createElement('div');
    userMsg.className = 'bg-gray-200 p-4 rounded-lg max-w-3xl ml-auto';
    userMsg.innerHTML = `<p class="text-gray-800">${escapeHtml(question)}</p>`;
    chatMessages.appendChild(userMsg);
    
    questionInput.value = '';
    sendBtn.disabled = true;
    
    // Mensaje loading
    const loadingMsg = document.createElement('div');
    loadingMsg.className = 'bg-blue-100 p-4 rounded-lg max-w-3xl';
    loadingMsg.innerHTML = '<p class="text-gray-600">Pensando...</p>';
    chatMessages.appendChild(loadingMsg);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    try {
        const response = await fetch('/api/chat/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({question})
        });
        const data = await response.json();
        chatMessages.removeChild(loadingMsg);
        
        const botMsg = document.createElement('div');
        botMsg.className = 'bg-blue-100 p-4 rounded-lg max-w-3xl';
        let content = `<p class="text-gray-800 whitespace-pre-wrap">${escapeHtml(data.answer || data.detail)}</p>`;
        if (data.sources && data.sources.length > 0) {
            content += '<div class="mt-2 pt-2 border-t border-blue-300"><p class="text-xs text-gray-600 font-semibold">Fuentes:</p>';
            data.sources.forEach(src => {
                content += `<p class="text-xs text-gray-600">- ${src.source} (pág. ${src.page})</p>`;
            });
            content += '</div>';
        }
        botMsg.innerHTML = content;
        chatMessages.appendChild(botMsg);
        
        // Actualizar historial
        const histItem = document.createElement('div');
        histItem.className = 'p-2 hover:bg-gray-100 rounded cursor-pointer truncate';
        histItem.textContent = question;
        historyDiv.innerHTML = '';
        historyDiv.appendChild(histItem);
        
    } catch (error) {
        chatMessages.removeChild(loadingMsg);
        const errorMsg = document.createElement('div');
        errorMsg.className = 'bg-red-100 p-4 rounded-lg max-w-3xl';
        errorMsg.innerHTML = '<p class="text-red-800">Error de conexión</p>';
        chatMessages.appendChild(errorMsg);
    }
    
    sendBtn.disabled = false;
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
