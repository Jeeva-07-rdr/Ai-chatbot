document.addEventListener('DOMContentLoaded', () => {
    // Helper to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    // Global Toast Function
    window.showToast = function(message) {
        const toastEl = document.getElementById('dummyToast');
        const toastBody = document.getElementById('dummyToastBody');
        if (toastEl && toastBody) {
            toastBody.textContent = message;
            const toast = new bootstrap.Toast(toastEl);
            toast.show();
        }
    };

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[title]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        if (!tooltipTriggerEl.hasAttribute('data-bs-toggle')) {
            tooltipTriggerEl.setAttribute('data-bs-toggle', 'tooltip');
            tooltipTriggerEl.setAttribute('data-bs-placement', 'top');
        }
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            trigger: 'hover'
        });
    });

    // Auto-resize textarea
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
            if (this.value === '') {
                this.style.height = '44px';
            }
        });
    }

    // --- Profile & Preference Auto-Save Handlers ---

    // 1. Submit Profile Form
    const profileForm = document.getElementById('profileForm');
    if (profileForm) {
        profileForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const formData = new FormData(profileForm);
            
            fetch('/settings/profile/save/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken
                },
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    window.showToast("Profile details updated successfully.");
                } else {
                    window.showToast("Error updating profile.");
                }
            })
            .catch(() => window.showToast("Network error."));
        });
    }

    // 2. Auto-save Preferences Form on Input Change
    const preferencesForm = document.getElementById('preferencesForm');
    if (preferencesForm) {
        const autoSaveFields = preferencesForm.querySelectorAll('select, input[type="range"], input[type="checkbox"], input[type="radio"]');
        autoSaveFields.forEach(field => {
            field.addEventListener('change', () => {
                const formData = new FormData(preferencesForm);
                
                // If it is the theme radio option, sync it immediately
                if (field.name === 'theme-options') {
                    const themeVal = field.id === 'themeDark' ? 'dark' : 'light';
                    formData.set('theme', themeVal);
                }

                fetch('/settings/preferences/save/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrftoken
                    },
                    body: formData
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        window.showToast("Preferences saved.");
                        // If theme was changed, update HTML dataset
                        if (field.name === 'theme-options' || field.id === 'themeLight' || field.id === 'themeDark') {
                            const newTheme = document.getElementById('themeDark').checked ? 'dark' : 'light';
                            document.documentElement.setAttribute('data-bs-theme', newTheme);
                        }
                    }
                });
            });
        });
    }

    // --- Notifications Polling Engine ---
    const notificationList = document.getElementById('notificationList');
    const notificationBadge = document.getElementById('notificationBadge');
    
    function pollNotifications() {
        if (!notificationList) return;
        
        fetch('/notifications/poll/')
        .then(res => res.json())
        .then(data => {
            const count = data.unread_count;
            if (count > 0 && notificationBadge) {
                notificationBadge.textContent = count;
                notificationBadge.style.display = 'block';
            }
            
            // Clear standard "No new notifications"
            const noNotifEl = document.getElementById('noNotifications');
            if (noNotifEl && data.notifications.length > 0) {
                noNotifEl.remove();
            }
            
            // Append
            data.notifications.forEach(notif => {
                // Check if already in list
                if (!document.getElementById(`notif-${notif.id}`)) {
                    const li = document.createElement('li');
                    li.id = `notif-${notif.id}`;
                    li.className = 'py-2 px-3 border-bottom text-dark';
                    li.setAttribute('data-bs-theme', 'dark');
                    li.style.color = 'var(--text-main)';
                    li.innerHTML = `
                        <div class="d-flex align-items-start gap-2">
                            <i class="bi bi-info-circle-fill text-primary"></i>
                            <div class="text-xs" style="color: var(--text-main);">${notif.text}</div>
                        </div>
                    `;
                    notificationList.appendChild(li);
                }
            });
        });
    }

    // Start poll
    pollNotifications();

    // Clear alerts click handler
    const clearNotificationsBtn = document.getElementById('clearNotifications');
    if (clearNotificationsBtn) {
        clearNotificationsBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (notificationBadge) {
                notificationBadge.style.display = 'none';
            }
            // Clear elements
            if (notificationList) {
                const items = notificationList.querySelectorAll('li:not(.dropdown-header)');
                items.forEach(item => item.remove());
                const emptyLi = document.createElement('li');
                emptyLi.id = 'noNotifications';
                emptyLi.className = 'text-center py-3 text-muted';
                emptyLi.textContent = 'No new notifications';
                notificationList.appendChild(emptyLi);
            }
            window.showToast("All notifications cleared.");
        });
    }

    // --- Message Copy Code Snippet Action helper ---
    document.addEventListener('click', (e) => {
        const copyBtn = e.target.closest('[title="Copy"]');
        if (copyBtn) {
            e.preventDefault();
            // Get content block
            const messageWrapper = copyBtn.closest('.message-content-box');
            if (messageWrapper) {
                const msgText = messageWrapper.querySelector('.message-text');
                if (msgText) {
                    navigator.clipboard.writeText(msgText.textContent.trim())
                    .then(() => window.showToast("Message copied to clipboard."))
                    .catch(() => window.showToast("Unable to copy."));
                }
            }
        }
    });

    // --- Dynamic AI Model Options Loading ---
    const providerSelect = document.getElementById('id_ai_provider');
    const modelSelect = document.getElementById('id_ai_model');
    
    function updateModelsList(provider, selectedModel = null) {
        if (!modelSelect) return;
        modelSelect.innerHTML = '<option value="">Loading models...</option>';
        
        fetch(`/settings/models/?provider=${provider}`)
        .then(res => res.json())
        .then(data => {
            modelSelect.innerHTML = '';
            let hasSelected = false;
            
            if (data.models && data.models.length > 0) {
                data.models.forEach((model, idx) => {
                    const option = document.createElement('option');
                    option.value = model;
                    option.textContent = model;
                    // If matched or if it is the first element and no model was pre-matched
                    if (selectedModel && model === selectedModel) {
                        option.selected = true;
                        hasSelected = true;
                    }
                    modelSelect.appendChild(option);
                });
                
                // If the pre-matched model was not found in the list, default to the first one
                if (!hasSelected && modelSelect.options.length > 0) {
                    modelSelect.options[0].selected = true;
                }
                
                // Automatically save the default model to the database if this was triggered by a provider switch
                if (!selectedModel || !hasSelected) {
                    modelSelect.dispatchEvent(new Event('change'));
                }
            } else {
                const option = document.createElement('option');
                option.value = '';
                option.textContent = 'No models found';
                modelSelect.appendChild(option);
                modelSelect.dispatchEvent(new Event('change'));
            }
        })
        .catch(() => {
            modelSelect.innerHTML = '<option value="">Error loading models</option>';
        });
    }
    
    if (providerSelect && modelSelect) {
        const initialModel = modelSelect.getAttribute('data-selected-model');
        updateModelsList(providerSelect.value, initialModel);
        
        providerSelect.addEventListener('change', () => {
            updateModelsList(providerSelect.value);
        });
    }
});
