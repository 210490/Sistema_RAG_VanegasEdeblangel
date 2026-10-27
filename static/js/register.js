document.getElementById('registerForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const userData = {
        nombre: document.getElementById('nombre').value,
        apellidos: document.getElementById('apellidos').value,
        cedula: document.getElementById('cedula').value,
        email: document.getElementById('email').value,
        telefono: document.getElementById('telefono').value,
        password: document.getElementById('password').value,
        categoria: document.getElementById('categoria').value
    };
    
    try {
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(userData)
        });
        const data = await response.json();
        if (response.ok) {
            alert('Usuario registrado exitosamente');
            window.location.href = '/login';
        } else {
            alert(data.detail || 'Error al registrar');
        }
    } catch (error) {
        alert('Error de conexión');
    }
});
