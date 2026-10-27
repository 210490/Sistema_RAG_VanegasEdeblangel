document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email, password})
        });
        const data = await response.json();
        if (response.ok) {
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('categoria', data.categoria);
            if (data.categoria === 'Administrador') {
                window.location.href = '/admin';
            } else {
                window.location.href = '/chat';
            }
        } else {
            alert(data.detail || 'Error al iniciar sesión');
        }
    } catch (error) {
        alert('Error de conexión');
    }
});
