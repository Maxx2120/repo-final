const API_URL = "";

// Auth Utils
function getToken() {
    return localStorage.getItem('token');
}

function setToken(token) {
    localStorage.setItem('token', token);
}

function removeToken() {
    localStorage.removeItem('token');
}

function checkAuth() {
    const token = getToken();
    const path = window.location.pathname;

    if (!token && path === '/dashboard') {
        window.location.href = '/login';
    } else if (token && (path === '/login' || path === '/signup' || path === '/')) {
        window.location.href = '/dashboard';
    }
}

// Check auth on load
document.addEventListener('DOMContentLoaded', checkAuth);

// UI Utils
function showToast(message) {
    const toast = document.getElementById('toast');
    if (toast) {
        toast.textContent = message;
        toast.style.display = 'block';
        setTimeout(() => {
            toast.style.display = 'none';
        }, 3000);
    }
}

// Auth Pages
const loginForm = document.getElementById('login-form');
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(loginForm);
        const data = Object.fromEntries(formData);

        try {
            const response = await fetch(`${API_URL}/auth/token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams(data)
            });

            if (response.ok) {
                const result = await response.json();
                setToken(result.access_token);
                window.location.href = '/dashboard';
            } else {
                const result = await response.json();
                showToast(result.detail || 'Login failed');
            }
        } catch (error) {
            showToast('An error occurred');
        }
    });
}

const signupForm = document.getElementById('signup-form');
if (signupForm) {
    signupForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(signupForm);
        const data = Object.fromEntries(formData);

        try {
            const response = await fetch(`${API_URL}/auth/signup`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                const result = await response.json();
                setToken(result.access_token);
                window.location.href = '/dashboard';
            } else {
                const result = await response.json();
                showToast(result.detail || 'Signup failed');
            }
        } catch (error) {
            showToast('An error occurred');
        }
    });
}

const forgotPasswordForm = document.getElementById('forgot-password-form');
if (forgotPasswordForm) {
    forgotPasswordForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(forgotPasswordForm);
        const data = Object.fromEntries(formData);

        try {
            const response = await fetch(`${API_URL}/otp/forgot-password`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                // Redirect to verify otp with email in query param or localStorage
                localStorage.setItem('reset_email', data.email);
                window.location.href = '/verify-otp';
            } else {
                const result = await response.json();
                showToast(result.detail || 'Failed to send OTP');
            }
        } catch (error) {
            showToast('An error occurred');
        }
    });
}

const verifyOtpForm = document.getElementById('verify-otp-form');
if (verifyOtpForm) {
    const emailInput = document.getElementById('email-verify');
    if (emailInput) {
        emailInput.value = localStorage.getItem('reset_email') || '';
    }

    verifyOtpForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(verifyOtpForm);
        const data = Object.fromEntries(formData);

        try {
            const response = await fetch(`${API_URL}/otp/verify`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                localStorage.setItem('reset_otp', data.otp);
                window.location.href = '/reset-password';
            } else {
                const result = await response.json();
                showToast(result.detail || 'Invalid OTP');
            }
        } catch (error) {
            showToast('An error occurred');
        }
    });
}

const resetPasswordForm = document.getElementById('reset-password-form');
if (resetPasswordForm) {
    const emailInput = document.getElementById('email-reset');
    const otpInput = document.getElementById('otp-reset');
    if (emailInput && otpInput) {
        emailInput.value = localStorage.getItem('reset_email') || '';
        otpInput.value = localStorage.getItem('reset_otp') || '';
    }

    resetPasswordForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(resetPasswordForm);
        const data = Object.fromEntries(formData);

        try {
            const response = await fetch(`${API_URL}/otp/reset-password`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                showToast('Password reset successfully');
                setTimeout(() => {
                    window.location.href = '/login';
                }, 2000);
            } else {
                const result = await response.json();
                showToast(result.detail || 'Reset failed');
            }
        } catch (error) {
            showToast('An error occurred');
        }
    });
}

// Dashboard Logic
function logout() {
    removeToken();
    window.location.href = '/login';
}

function showSection(sectionId) {
    document.querySelectorAll('.section').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));

    document.getElementById(`${sectionId}-section`).classList.add('active');

    // Highlight nav btn
    // Assuming buttons are in order or we can select by onclick
    // Simple way:
    // ... (omitted for brevity)

    if (sectionId === 'image') loadHistory('image');
    if (sectionId === 'video') loadHistory('video');
}

// Chat
async function sendMessage() {
    const input = document.getElementById('chat-input');
    const model = document.getElementById('chat-model').value;
    const message = input.value;

    if (!message) return;

    addMessageToChat('user', message);
    input.value = '';

    try {
        const response = await fetch(`${API_URL}/chat/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getToken()}`
            },
            body: JSON.stringify({ message, model })
        });

        if (response.ok) {
            const result = await response.json();
            addMessageToChat('assistant', result.response);
        } else {
            showToast('Failed to send message');
        }
    } catch (error) {
        showToast('An error occurred');
    }
}

function addMessageToChat(role, text) {
    const window = document.getElementById('chat-window');
    const div = document.createElement('div');
    div.className = `chat-message ${role}`;
    div.textContent = text;
    window.appendChild(div);
    window.scrollTop = window.scrollHeight;
}

// Image
async function generateImage() {
    const prompt = document.getElementById('image-prompt').value;
    if (!prompt) return;

    const loader = document.getElementById('image-loader');
    loader.classList.remove('hidden');

    try {
        const response = await fetch(`${API_URL}/image/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getToken()}`
            },
            body: JSON.stringify({ prompt })
        });

        if (response.ok) {
            const result = await response.json();
            const resultArea = document.getElementById('image-result');
            resultArea.innerHTML = `<img src="${result.image_url}" alt="${result.prompt}">`;
            loadHistory('image');
        } else {
            showToast('Image generation failed');
        }
    } catch (error) {
        showToast('An error occurred');
    } finally {
        loader.classList.add('hidden');
    }
}

// Video
async function processVideo() {
    const fileInput = document.getElementById('video-file');
    const prompt = document.getElementById('video-prompt').value;

    if (!fileInput.files[0] || !prompt) return;

    const loader = document.getElementById('video-loader');
    loader.classList.remove('hidden');

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('prompt', prompt);

    try {
        const response = await fetch(`${API_URL}/video/process`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getToken()}`
            },
            body: formData
        });

        if (response.ok) {
            const result = await response.json();
            const resultArea = document.getElementById('video-result');
            resultArea.innerHTML = `<video controls src="${result.output_url}"></video>`;
            loadHistory('video');
        } else {
            showToast('Video processing failed');
        }
    } catch (error) {
        showToast('An error occurred');
    } finally {
        loader.classList.add('hidden');
    }
}

async function loadHistory(type) {
    const container = document.getElementById(`${type}-history`);
    if (!container) return;

    try {
        const response = await fetch(`${API_URL}/${type}/history`, {
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        });

        if (response.ok) {
            const items = await response.json();
            container.innerHTML = '';
            items.forEach(item => {
                const div = document.createElement('div');
                div.className = 'history-item';
                if (type === 'image') {
                    div.innerHTML = `<img src="${item.image_path}" alt="${item.prompt}"><p>${item.prompt}</p>`;
                } else {
                    div.innerHTML = `<video controls src="${item.output_file}"></video><p>${item.command}</p>`;
                }
                container.appendChild(div);
            });
        }
    } catch (error) {
        console.error('Failed to load history', error);
    }
}

// Load chat history on load if in dashboard
if (window.location.pathname === '/dashboard') {
    // We can load chat history too
    // For now just basic
}
