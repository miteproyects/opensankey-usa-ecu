// SuperComp V4 - Frontend Logic with Manual CAPTCHA
document.addEventListener('DOMContentLoaded', () => {
    const yearSelect = document.getElementById('year-select');
    const rucInput = document.getElementById('ruc-input');
    const consultarBtn = document.getElementById('consultar-btn');
    const progressFill = document.getElementById('progress-fill');
    const statusContent = document.getElementById('status-content');
    const verHistorialBtn = document.getElementById('ver-historial');
    const historyModal = document.getElementById('history-modal');
    const closeModalBtn = document.getElementById('close-modal');
    const modalBackdrop = document.querySelector('.modal-backdrop');
    const historyList = document.getElementById('history-list');

    let isSubmitting = false;
    let currentRuc = null;
    let captchaCheckInterval = null;

    // Check if form is valid
    function checkFormValidity() {
        const year = yearSelect.value;
        const ruc = rucInput.value.trim();
        const isValid = ruc.length === 13 && year !== '';
        consultarBtn.disabled = !isValid || isSubmitting;
    }

    // Year select handling
    yearSelect.addEventListener('change', () => {
        checkFormValidity();
        hideStatus();
    });

    // RUC input handling
    rucInput.addEventListener('input', (e) => {
        // Only allow digits
        let value = e.target.value.replace(/\D/g, '');
        
        // Limit to 13 digits
        if (value.length > 13) {
            value = value.slice(0, 13);
        }
        
        e.target.value = value;
        
        // Update progress bar
        const progress = (value.length / 13) * 100;
        progressFill.style.width = `${progress}%`;
        
        // Update input styling
        updateInputState(value);
        
        // Check form validity
        checkFormValidity();
    });

    // Handle paste
    rucInput.addEventListener('paste', (e) => {
        e.preventDefault();
        const pasted = (e.clipboardData || window.clipboardData).getData('text');
        const cleaned = pasted.replace(/\D/g, '').slice(0, 13);
        
        rucInput.value = cleaned;
        rucInput.dispatchEvent(new Event('input'));
    });

    // Handle keypress (Enter to submit)
    rucInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !consultarBtn.disabled) {
            consultar();
        }
    });

    function updateInputState(value) {
        rucInput.classList.remove('valid', 'error');
        
        if (value.length === 13) {
            rucInput.classList.add('valid');
        }
    }

    // Button click
    consultarBtn.addEventListener('click', consultar);

    async function consultar() {
        const ruc = rucInput.value.trim();
        const year = yearSelect.value;
        currentRuc = ruc;
        
        // Validation
        if (ruc.length !== 13) {
            showStatus('El R.U.C. debe tener exactamente 13 dígitos.', 'error');
            rucInput.classList.add('error');
            setTimeout(() => rucInput.classList.remove('error'), 500);
            rucInput.focus();
            return;
        }

        if (!year) {
            showStatus('Por favor selecciona un año.', 'error');
            yearSelect.focus();
            return;
        }

        isSubmitting = true;
        consultarBtn.disabled = true;
        consultarBtn.classList.add('loading');
        hideStatus();

        try {
            // Step 1: Save locally
            const localResponse = await fetch('/consultar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ruc, year }),
            });
            const localData = await localResponse.json();

            if (!localData.success) {
                showStatus('Error al guardar.', 'error');
                isSubmitting = false;
                consultarBtn.classList.remove('loading');
                checkFormValidity();
                return;
            }

            // Step 2: Start Supercias automation
            fetch('/consultar-supercias', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ruc }),
            });

            // Show waiting for CAPTCHA message
            showStatus('Chrome abierto. Esperando CAPTCHA...', 'info');
            
            // Start checking for CAPTCHA availability
            startCaptchaCheck(ruc);
            
        } catch (error) {
            showStatus('Error de conexión.', 'error');
            checkFormValidity();
        }
    }

    function startCaptchaCheck(ruc) {
        // Clear any existing interval
        if (captchaCheckInterval) {
            clearInterval(captchaCheckInterval);
        }
        
        // Check every second if CAPTCHA is ready
        captchaCheckInterval = setInterval(async () => {
            try {
                const response = await fetch(`/captcha-status/${ruc}`);
                const data = await response.json();
                
                if (data.ready && data.status === 'waiting') {
                    clearInterval(captchaCheckInterval);
                    showCaptchaInput(ruc);
                }
            } catch (e) {
                console.error('Error checking captcha status:', e);
            }
        }, 1000);
    }

    function showCaptchaInput(ruc) {
        // Create CAPTCHA input UI
        const captchaHtml = `
            <div class="captcha-section">
                <p class="captcha-text">Por favor escribe el CAPTCHA que ves en Chrome:</p>
                <img src="/captcha-image/${ruc}" alt="CAPTCHA" class="captcha-img">
                <div class="captcha-input-group">
                    <input type="text" id="captcha-input" placeholder="Escribe el CAPTCHA..." maxlength="10" autocomplete="off">
                    <button id="captcha-submit" class="captcha-btn">Enviar</button>
                </div>
            </div>
        `;
        
        statusContent.innerHTML = captchaHtml;
        statusContent.className = 'status-content captcha';
        
        // Focus the captcha input
        setTimeout(() => {
            const captchaInput = document.getElementById('captcha-input');
            if (captchaInput) captchaInput.focus();
        }, 100);
        
        // Add event listeners
        const submitBtn = document.getElementById('captcha-submit');
        const captchaInput = document.getElementById('captcha-input');
        
        submitBtn.addEventListener('click', () => submitCaptcha(ruc, captchaInput.value));
        captchaInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                submitCaptcha(ruc, captchaInput.value);
            }
        });
    }

    async function submitCaptcha(ruc, code) {
        if (!code.trim()) {
            showStatus('Por favor escribe el CAPTCHA.', 'error');
            return;
        }
        
        try {
            const response = await fetch('/submit-captcha', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ruc, captcha: code.trim() }),
            });
            
            const data = await response.json();
            
            if (data.success) {
                showStatus('✅ CAPTCHA enviado. Procesando consulta...', 'success');
                
                // Reset form
                rucInput.value = '';
                progressFill.style.width = '0%';
                rucInput.classList.remove('valid');
                yearSelect.value = '';
                currentRuc = null;
                
                isSubmitting = false;
                consultarBtn.classList.remove('loading');
                checkFormValidity();
            } else {
                showStatus(`Error: ${data.message}`, 'error');
            }
        } catch (error) {
            showStatus('Error al enviar CAPTCHA.', 'error');
        }
    }

    function showStatus(message, type) {
        if (type === 'captcha') return; // Handled separately
        statusContent.textContent = message;
        statusContent.className = 'status-content ' + type;
    }

    function hideStatus() {
        statusContent.className = 'status-content hidden';
    }

    // History modal
    verHistorialBtn.addEventListener('click', async () => {
        await loadHistory();
        historyModal.classList.add('active');
    });

    closeModalBtn.addEventListener('click', closeModal);
    modalBackdrop.addEventListener('click', closeModal);

    function closeModal() {
        historyModal.classList.remove('active');
    }

    // Close modal on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && historyModal.classList.contains('active')) {
            closeModal();
        }
    });

    async function loadHistory() {
        try {
            const response = await fetch('/historial');
            const data = await response.json();

            historyList.innerHTML = '';

            if (data.success && data.files.length > 0) {
                data.files.forEach(filename => {
                    const li = document.createElement('li');
                    const match = filename.match(/RUC_(\d+)_(\d{4}|SUPERCIAS)_(.+?)\.txt/);
                    if (match) {
                        const ruc = match[1];
                        const type = match[2];
                        const timestamp = match[3].replace(/_/g, ' ');
                        const typeLabel = type === 'SUPERCIAS' ? 'Supercias' : `Año ${type}`;
                        li.innerHTML = `<span class="ruc">${ruc}</span><span class="year">${typeLabel}</span><span class="date">${timestamp}</span>`;
                    } else {
                        li.textContent = filename;
                    }
                    historyList.appendChild(li);
                });
            } else {
                const li = document.createElement('li');
                li.className = 'empty';
                li.textContent = 'No hay consultas registradas aún.';
                historyList.appendChild(li);
            }
        } catch (error) {
            historyList.innerHTML = '<li class="empty">Error al cargar el historial.</li>';
        }
    }

    // Focus year select on load
    yearSelect.focus();
});
