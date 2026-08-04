document.addEventListener('DOMContentLoaded', () => {
    console.log('%c[UMI] App initialized', 'color: #2563EB; font-weight: bold;');
    const welcomeScreen = document.getElementById('welcome-screen');
    const chatContainer = document.getElementById('chat-container');
    const chatMessages = document.getElementById('chatMessages');
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    const typingIndicator = document.getElementById('typingIndicator');
    const suggestionCards = document.querySelectorAll('.suggestion-card');
    const newChatBtn = document.querySelector('.new-chat-btn');
    const sidebarSearch = document.getElementById('sidebarSearch');

    // Configure marked.js to use highlight.js
    if (typeof marked !== 'undefined') {
        marked.setOptions({
            highlight: function (code, lang) {
                if (lang && hljs.getLanguage(lang)) {
                    return hljs.highlight(code, { language: lang }).value;
                }
                return hljs.highlightAuto(code).value;
            }
        });
    }

    // Render markdown on load
    document.querySelectorAll('.markdown-body').forEach(el => {
        if (el.hasAttribute('data-raw-content')) {
            const rawContent = el.getAttribute('data-raw-content');
            const decodedContent = document.createElement('textarea');
            decodedContent.innerHTML = rawContent;
            if (typeof marked !== 'undefined') {
                el.innerHTML = marked.parse(decodedContent.value);
            }
        }
    });

    // Helper for CSRF Token
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

    // Handle New Chat Button
    if (newChatBtn) {
        newChatBtn.addEventListener('click', (e) => {
            e.preventDefault();
            console.log('[UMI] New chat created');
            window.location.href = '/chat/new/';
        });
    }

    // Scroll to bottom on load if messages exist
    scrollToBottom();

    // Suggestion Cards click handler
    suggestionCards.forEach(card => {
        card.addEventListener('click', () => {
            const title = card.querySelector('h6').innerText;
            handleSendMessageFlow(title);
        });
    });

    // Global variable for active controller to allow aborting
    window.activeAbortController = null;

    // Send Button click handler
    if (sendBtn && chatInput) {
        sendBtn.addEventListener('click', () => {
            // Check if generating: if yes, cancel active stream!
            if (sendBtn.getAttribute('data-generating') === 'true') {
                if (window.activeAbortController) {
                    window.activeAbortController.abort();
                    window.showToast("Response generation stopped.");
                }
                return;
            }
            
            const message = chatInput.value.trim();
            if (message) {
                chatInput.value = '';
                chatInput.style.height = '44px';
                handleSendMessageFlow(message);
            }
        });
        
        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendBtn.click();
            }
        });
    }

    // Dynamic Code Block Copy Button Generator
    function addCopyButtonsToCodeBlocks(container = document) {
        container.querySelectorAll('.markdown-body pre').forEach(pre => {
            if (pre.querySelector('.copy-code-btn') || pre.classList.contains('has-copy-btn')) return;
            pre.classList.add('has-copy-btn');
            pre.style.position = 'relative';
            
            const button = document.createElement('button');
            button.className = 'copy-code-btn btn btn-sm btn-outline-secondary position-absolute top-0 end-0 m-2 rounded';
            button.style.zIndex = '10';
            button.style.padding = '0.2rem 0.4rem';
            button.style.fontSize = '0.72rem';
            button.style.border = '1px solid var(--border-color)';
            button.style.backgroundColor = 'var(--card-bg)';
            button.style.color = 'var(--text-main)';
            button.innerHTML = '<i class="bi bi-clipboard me-1"></i>Copy';
            
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const code = pre.querySelector('code');
                if (code) {
                    navigator.clipboard.writeText(code.innerText.trim())
                    .then(() => {
                        button.innerHTML = '<i class="bi bi-check-lg me-1"></i>Copied!';
                        setTimeout(() => {
                            button.innerHTML = '<i class="bi bi-clipboard me-1"></i>Copy';
                        }, 2000);
                    });
                }
            });
            pre.appendChild(button);
        });
    }

    // Add Copy buttons to any pre-existing code blocks on load
    addCopyButtonsToCodeBlocks();

    // Toggle generating status indicator on sendBtn
    function setGeneratingState(isGenerating) {
        if (!sendBtn) return;
        if (isGenerating) {
            sendBtn.innerHTML = '<i class="bi bi-stop-fill fs-5 text-white"></i>';
            sendBtn.title = "Stop Generating";
            sendBtn.setAttribute('data-generating', 'true');
            sendBtn.style.backgroundColor = 'var(--bs-danger)';
            sendBtn.style.borderColor = 'var(--bs-danger)';
            sendBtn.disabled = false;
            if (chatInput) chatInput.disabled = true;
        } else {
            sendBtn.innerHTML = '<i class="bi bi-arrow-up-short fs-3"></i>';
            sendBtn.title = "Send Message";
            sendBtn.removeAttribute('data-generating');
            sendBtn.style.backgroundColor = '';
            sendBtn.style.borderColor = '';
            if (chatInput) {
                chatInput.disabled = false;
                chatInput.focus();
            }
        }
    }

    // Send flow with support for editMessageId
    function handleSendMessageFlow(text, editMessageId = null) {
        // Extract chat UUID from URL path e.g. /chat/3938840c-c016-4533-8d64-daf776ef85a3/
        const pathParts = window.location.pathname.split('/').filter(Boolean);
        let chatUUID = null;
        if (pathParts.length >= 2 && pathParts[0] === 'chat' && pathParts[1] !== 'new') {
            chatUUID = pathParts[1];
        }

        if (!chatUUID) {
            sessionStorage.setItem('pending_message', text);
            fetch('/chat/new/', { method: 'GET' })
            .then(response => {
                if (response.redirected || response.url) {
                    window.location.href = response.url;
                } else {
                    window.location.href = '/chat/new/';
                }
            })
            .catch(err => {
                console.error('[UMI] New chat redirect failed:', err);
                window.location.href = '/chat/new/';
            });
            return;
        }

        // Ensure welcome screen is hidden and chat container is visible
        const welcomeScreen = document.getElementById('welcome-screen');
        const chatContainer = document.getElementById('chat-container');
        if (welcomeScreen) {
            welcomeScreen.classList.add('d-none');
            welcomeScreen.classList.remove('d-flex');
        }
        if (chatContainer) {
            chatContainer.classList.remove('d-none');
            chatContainer.classList.add('d-flex');
        }

        setGeneratingState(true);
        console.log(`[UMI] Sending message... (edit: ${editMessageId || 'no'})`);
        const sendStartTime = performance.now();
        window.streamingTextBuffer = ""; // Reset streaming rendering buffer

        if (editMessageId) {
            // Find edited message in DOM and remove all subsequent messages
            const userWrapper = document.querySelector(`.message-wrapper[data-message-id="${editMessageId}"]`);
            if (userWrapper) {
                // Update DOM text
                const textNode = userWrapper.querySelector('.message-text');
                if (textNode) {
                    textNode.innerText = text;
                    textNode.removeAttribute('data-raw-content');
                }
                // Wipe subsequent siblings
                let nextNode = userWrapper.nextElementSibling;
                while (nextNode && nextNode !== typingIndicator) {
                    const temp = nextNode.nextElementSibling;
                    nextNode.remove();
                    nextNode = temp;
                }
            }
        } else {
            // Add normal user message to DOM
            addUserMessageHTML(text);
        }

        if (typingIndicator) {
            typingIndicator.classList.remove('d-none');
            scrollToBottom();
        }

        // Initialize active AbortController
        window.activeAbortController = new AbortController();
        const signal = window.activeAbortController.signal;

        // Create empty placeholder AI bubble
        const time = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        const placeholderId = 'streaming-ai-' + Date.now();
        const aiPlaceholderHTML = `
        <div class="message-wrapper d-flex w-100 justify-content-start slide-in mb-4" id="${placeholderId}">
            <div class="message-avatar me-3 flex-shrink-0 mt-1 d-flex flex-column align-items-center">
                <div class="avatar-circle ai-avatar d-flex align-items-center justify-content-center shadow-sm" style="border: none; background-color: transparent;">
                    <img src="/static/images/logo.png?v=2.0" alt="UMI" class="wave-float" style="width: 28px; height: 28px; object-fit: contain;">
                </div>
                <span class="ultra-small fw-semibold mt-1" style="color: var(--text-muted); font-size: 0.65rem;">UMI</span>
            </div>
            <div class="message-content-box d-flex flex-column align-items-start w-100 max-w-75">
                <div class="message-bubble ai-card w-100">
                    <div class="message-text markdown-body" style="white-space: pre-wrap;"></div>
                </div>
                <div class="message-meta mt-1 d-flex align-items-center gap-2 text-muted ultra-small">
                    <span class="timestamp fw-medium" style="font-size: 0.72rem;">${time}</span>
                    <span class="generation-time text-xs opacity-75 ms-2" id="${placeholderId}-duration"></span>
                </div>
            </div>
        </div>`;
        
        const aiNode = createNodeFromHTML(aiPlaceholderHTML);
        chatMessages.insertBefore(aiNode, typingIndicator);
        const aiTextContainer = aiNode.querySelector('.message-text');

        const currentAttachments = [...uploadedFileIds];
        uploadedFileIds = [];
        if (filePreviewArea) {
            filePreviewArea.innerHTML = '';
            filePreviewArea.classList.add('d-none');
            filePreviewArea.classList.remove('d-flex');
        }

        const currentCsrfToken = getCookie('csrftoken');

        fetch(`/chat/${chatUUID}/send/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': currentCsrfToken
            },
            body: JSON.stringify({
                content: text,
                edit_message_id: editMessageId,
                attachment_ids: currentAttachments
            }),
            signal: signal
        })
        .then(async response => {
            if (!response.ok) {
                let errorMsg = `Server Error (${response.status})`;
                try {
                    const errData = await response.json();
                    if (errData.error) errorMsg = errData.error;
                } catch (e) {}
                window.showToast(errorMsg);
                if (typingIndicator) typingIndicator.classList.add('d-none');
                setGeneratingState(false);
                if (aiNode) aiNode.remove();
                return;
            }

            const contentType = response.headers.get('content-type') || '';
            console.log(`[UMI] Response received | Status: ${response.status} | Type: ${contentType.split(';')[0]}`);
            
            if (contentType.includes('text/event-stream')) {
                const reader = response.body.getReader();
                const decoder = new TextDecoder('utf-8');
                let buffer = '';
                
                while (true) {
                    const { value, done } = await reader.read();
                    if (done) break;
                    
                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n\n');
                    buffer = lines.pop();
                    
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const dataStr = line.slice(6).trim();
                            if (dataStr) {
                                try {
                                    const eventData = JSON.parse(dataStr);
                                    if (eventData.type === 'meta') {
                                        const headerTitle = document.getElementById('headerChatTitle');
                                        if (headerTitle) headerTitle.textContent = eventData.chat_title;
                                        
                                        const modelBadge = document.getElementById('headerModelBadge');
                                        if (modelBadge) {
                                            modelBadge.textContent = `${eventData.provider}: ${eventData.model}`;
                                        }
                                    } else if (eventData.type === 'chunk') {
                                        if (typingIndicator) typingIndicator.classList.add('d-none');
                                        if (!window.streamingTextBuffer) {
                                            window.streamingTextBuffer = "";
                                        }
                                        window.streamingTextBuffer += eventData.content;
                                        if (typeof marked !== 'undefined') {
                                            aiTextContainer.innerHTML = marked.parse(window.streamingTextBuffer);
                                        } else {
                                            aiTextContainer.textContent = window.streamingTextBuffer;
                                        }
                                        scrollToBottom();
                                    } else if (eventData.type === 'done') {
                                        window.streamingTextBuffer = ""; // Reset buffer on completion
                                        const sendDuration = ((performance.now() - sendStartTime) / 1000).toFixed(2);
                                        console.log(`[UMI] AI response complete | ${eventData.duration}s server | ${sendDuration}s total`);
                                        const finalNode = createNodeFromHTML(eventData.ai_html);
                                        if (eventData.message_id) {
                                            finalNode.setAttribute('data-message-id', eventData.message_id);
                                        }
                                        aiNode.replaceWith(finalNode);
                                        
                                        // Update metadata with duration
                                        const durationEl = finalNode.querySelector('.timestamp');
                                        if (durationEl) {
                                            const badge = document.createElement('span');
                                            badge.className = 'generation-time text-xs opacity-75 ms-2';
                                            badge.textContent = `Generated in ${eventData.duration}s`;
                                            durationEl.after(badge);
                                        }
                                        
                                        // Dynamically link user_message_id if present
                                        if (eventData.user_message_id) {
                                            const userBubbles = chatMessages.querySelectorAll('.message-wrapper.justify-content-end');
                                            if (userBubbles.length > 0) {
                                                const lastUserBubble = userBubbles[userBubbles.length - 1];
                                                if (!lastUserBubble.hasAttribute('data-message-id')) {
                                                    lastUserBubble.setAttribute('data-message-id', eventData.user_message_id);
                                                }
                                            }
                                        }
                                        
                                        addCopyButtonsToCodeBlocks(finalNode);
                                        const tooltips = [].slice.call(finalNode.querySelectorAll('[title]'));
                                        tooltips.map(t => new bootstrap.Tooltip(t, {trigger: 'hover'}));
                                    }
                                } catch (e) {
                                    console.error("Error parsing stream line:", e);
                                }
                            }
                        }
                    }
                }
                
                if (typingIndicator) typingIndicator.classList.add('d-none');
                setGeneratingState(false);
                console.log('[UMI] Stream ended');
                scrollToBottom();
                
            } else {
                const data = await response.json();
                if (typingIndicator) typingIndicator.classList.add('d-none');
                setGeneratingState(false);
                
                if (data.error) {
                    window.showToast(data.error);
                    aiNode.remove();
                    return;
                }
                
                const finalNode = createNodeFromHTML(data.ai_html);
                if (data.message_id) finalNode.setAttribute('data-message-id', data.message_id);
                aiNode.replaceWith(finalNode);
                
                if (data.user_message_id) {
                    const userBubbles = chatMessages.querySelectorAll('.message-wrapper.justify-content-end');
                    if (userBubbles.length > 0) {
                        const lastUserBubble = userBubbles[userBubbles.length - 1];
                        if (!lastUserBubble.hasAttribute('data-message-id')) {
                            lastUserBubble.setAttribute('data-message-id', data.user_message_id);
                        }
                    }
                }
                
                if (data.duration) {
                    const durationEl = finalNode.querySelector('.timestamp');
                    if (durationEl) {
                        const badge = document.createElement('span');
                        badge.className = 'generation-time text-xs opacity-75 ms-2';
                        badge.textContent = `Generated in ${data.duration}s`;
                        durationEl.after(badge);
                    }
                }
                
                addCopyButtonsToCodeBlocks(finalNode);
                const headerTitle = document.getElementById('headerChatTitle');
                if (headerTitle) headerTitle.textContent = data.chat_title;
                scrollToBottom();
            }
        })
        .catch(err => {
            if (typingIndicator) typingIndicator.classList.add('d-none');
            setGeneratingState(false);
            
            if (err.name === 'AbortError') {
                console.warn('[UMI] Request aborted by user');
                aiTextContainer.textContent += "\n\n*(Generation stopped by user)*";
                return;
            }
            
            aiNode.remove();
            console.error('[UMI] Connection error:', err);
            window.showToast("Connection error: could not send message.");
        });
    }

    // Read pending message from sessionStorage
    const pendingMsg = sessionStorage.getItem('pending_message');
    if (pendingMsg) {
        sessionStorage.removeItem('pending_message');
        handleSendMessageFlow(pendingMsg);
    }

    function addUserMessageHTML(text) {
        const time = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        const msgHTML = `
        <div class="message-wrapper d-flex w-100 justify-content-end slide-in mb-4">
            <div class="message-content-box d-flex flex-column align-items-end max-w-75">
                <div class="message-bubble user-bubble">
                    <div class="message-text markdown-body">
                        ${escapeHTML(text)}
                    </div>
                </div>
                <div class="message-meta mt-1 d-flex align-items-center gap-1 text-muted ultra-small flex-row-reverse">
                    <span class="timestamp opacity-75" style="font-size: 0.72rem;">${time}</span>
                    <i class="bi bi-check2-all text-primary opacity-90" style="font-size: 0.85rem;" title="Delivered"></i>
                    <button class="btn btn-sm btn-icon text-muted p-0 me-1 hover-lift edit-message-btn" title="Edit message" style="width: 18px; height: 18px;"><i class="bi bi-pencil text-xs"></i></button>
                </div>
            </div>
            <div class="message-avatar ms-3 flex-shrink-0 mt-1">
                <div class="avatar-circle user-avatar-blue d-flex align-items-center justify-content-center shadow-sm">
                    JD
                </div>
            </div>
        </div>`;
        
        chatMessages.insertBefore(createNodeFromHTML(msgHTML), typingIndicator);
        scrollToBottom();
    }

    function scrollToBottom() {
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    function escapeHTML(str) {
        return str.replace(/[&<>'"]/g, 
            tag => ({
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                "'": '&#39;',
                '"': '&quot;'
            }[tag] || tag)
        );
    }

    function createNodeFromHTML(htmlString) {
        const div = document.createElement('div');
        div.innerHTML = htmlString.trim();
        return div.firstChild;
    }

    // --- Search functionality ---
    if (sidebarSearch) {
        let defaultGroupElements = [];
        
        sidebarSearch.addEventListener('input', () => {
            const query = sidebarSearch.value.trim();
            const sidebarContent = document.getElementById('sidebarContent');
            
            // Backup default groups on first search
            if (defaultGroupElements.length === 0 && sidebarContent) {
                defaultGroupElements = Array.from(sidebarContent.children);
            }
            
            if (!query) {
                // Restore default groups
                if (sidebarContent) {
                    sidebarContent.innerHTML = '';
                    defaultGroupElements.forEach(el => sidebarContent.appendChild(el));
                }
                return;
            }

            fetch(`/chat/search/?q=${encodeURIComponent(query)}`)
            .then(res => res.json())
            .then(data => {
                if (sidebarContent) {
                    sidebarContent.innerHTML = '';
                    
                    const searchGroup = document.createElement('div');
                    searchGroup.className = 'chat-group mb-4';
                    searchGroup.innerHTML = `<h6 class="text-muted text-xs fw-semibold px-2 mb-2 text-uppercase tracking-wider">Search Results</h6>`;
                    
                    if (data.results.length === 0) {
                        searchGroup.innerHTML += `<div class="text-muted text-xs px-2 py-2">No matching messages found.</div>`;
                    } else {
                        data.results.forEach(res => {
                            searchGroup.innerHTML += `
                            <div class="chat-item-wrapper d-flex align-items-center mb-1 rounded position-relative">
                                <a href="/chat/${res.chat_id}/" class="chat-link flex-grow-1 d-flex flex-column text-decoration-none text-dark py-2 px-2">
                                    <div class="d-flex align-items-center mb-1">
                                        <i class="bi bi-search me-2 text-primary text-xs"></i>
                                        <span class="text-truncate fw-semibold text-xs text-dark" style="max-width: 180px;">${res.highlighted_title}</span>
                                    </div>
                                    <div class="text-truncate text-muted ultra-small ms-4">${res.snippet}</div>
                                </a>
                            </div>`;
                        });
                    }
                    sidebarContent.appendChild(searchGroup);
                }
            });
        });
    }

    // --- Header button clicks & actions ---
    document.addEventListener('click', (e) => {
        const pinBtn = e.target.closest('.pin-header-btn') || e.target.closest('.pin-sidebar-btn');
        const archiveBtn = e.target.closest('.archive-header-btn') || e.target.closest('.archive-sidebar-btn');
        const duplicateBtn = e.target.closest('.duplicate-header-btn') || e.target.closest('.duplicate-sidebar-btn');
        const deleteBtn = e.target.closest('.delete-header-btn') || e.target.closest('.delete-sidebar-btn');
        const renameBtn = e.target.closest('.rename-sidebar-btn');
        const editBtn = e.target.closest('.edit-message-btn');
        const regenerateBtn = e.target.closest('[title="Regenerate"]');

        if (pinBtn) {
            e.preventDefault();
            const id = pinBtn.getAttribute('data-id');
            fetch(`/chat/${id}/pin/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrftoken }
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    window.location.reload(); // Reload to refresh sorting and headers
                }
            });
        }

        if (archiveBtn) {
            e.preventDefault();
            const id = archiveBtn.getAttribute('data-id');
            fetch(`/chat/${id}/archive/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrftoken }
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    window.showToast(data.is_archived ? "Chat archived" : "Chat unarchived");
                    setTimeout(() => window.location.href = '/', 1000);
                }
            });
        }

        if (duplicateBtn) {
            e.preventDefault();
            const id = duplicateBtn.getAttribute('data-id');
            fetch(`/chat/${id}/duplicate/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrftoken }
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    window.showToast("Chat duplicated successfully");
                    setTimeout(() => window.location.href = data.new_chat_url, 1000);
                }
            });
        }

        if (deleteBtn) {
            e.preventDefault();
            const id = deleteBtn.getAttribute('data-id');
            if (confirm("Are you sure you want to delete this conversation?")) {
                window.location.href = `/chat/${id}/delete/`;
            }
        }

        if (renameBtn) {
            e.preventDefault();
            const id = renameBtn.getAttribute('data-id');
            const currentTitle = renameBtn.getAttribute('data-title');
            const newTitle = prompt("Rename conversation:", currentTitle);
            if (newTitle && newTitle.trim()) {
                fetch(`/chat/${id}/rename/`, {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrftoken 
                    },
                    body: JSON.stringify({ title: newTitle.trim() })
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        window.location.reload();
                    } else {
                        window.showToast(data.error);
                    }
                });
            }
        }

        if (editBtn) {
            e.preventDefault();
            const messageWrapper = editBtn.closest('.message-wrapper');
            const messageId = messageWrapper.getAttribute('data-message-id');
            const bubble = messageWrapper.querySelector('.message-bubble');
            const textNode = messageWrapper.querySelector('.message-text');
            
            if (!bubble || !textNode || messageWrapper.querySelector('.edit-box')) return;
            
            const rawText = textNode.innerText.trim();
            bubble.style.display = 'none';
            
            const editBox = document.createElement('div');
            editBox.className = 'edit-box w-100 p-2 mt-2 rounded bg-body-tertiary border';
            editBox.innerHTML = `
                <textarea class="form-control mb-2 rounded" style="background: var(--card-bg); color: var(--text-main); border-color: var(--border-color);" rows="2">${rawText}</textarea>
                <div class="d-flex gap-2 justify-content-end">
                    <button class="btn btn-sm btn-outline-secondary rounded-pill px-3 cancel-edit-btn" style="font-size: 0.72rem; padding: 0.15rem 0.5rem;">Cancel</button>
                    <button class="btn btn-sm btn-primary rounded-pill px-3 save-edit-btn" style="font-size: 0.72rem; padding: 0.15rem 0.5rem;">Save & Submit</button>
                </div>
            `;
            
            messageWrapper.querySelector('.message-content-box').appendChild(editBox);
            
            const textarea = editBox.querySelector('textarea');
            textarea.focus();
            textarea.setSelectionRange(textarea.value.length, textarea.value.length);
            
            editBox.querySelector('.cancel-edit-btn').addEventListener('click', () => {
                editBox.remove();
                bubble.style.display = '';
            });
            
            editBox.querySelector('.save-edit-btn').addEventListener('click', () => {
                const newText = textarea.value.trim();
                if (newText) {
                    editBox.remove();
                    bubble.style.display = '';
                    handleSendMessageFlow(newText, messageId);
                }
            });
        }

        if (regenerateBtn) {
            e.preventDefault();
            const messageWrapper = regenerateBtn.closest('.message-wrapper');
            if (messageWrapper) {
                let prevNode = messageWrapper.previousElementSibling;
                while (prevNode) {
                    if (prevNode.classList.contains('message-wrapper') && prevNode.querySelector('.user-bubble')) {
                        const userTextNode = prevNode.querySelector('.message-text');
                        const userMsgId = prevNode.getAttribute('data-message-id');
                        if (userTextNode && userMsgId) {
                            handleSendMessageFlow(userTextNode.innerText.trim(), userMsgId);
                            return;
                        }
                    }
                    prevNode = prevNode.previousElementSibling;
                }
            }
        }
    });

    // --- Drag and Drop Sorting for Pinned Chats ---
    const pinnedList = document.getElementById('pinnedList');
    if (pinnedList) {
        let draggedItem = null;

        pinnedList.querySelectorAll('.chat-item-wrapper').forEach(item => {
            item.addEventListener('dragstart', (e) => {
                draggedItem = item;
                item.style.opacity = '0.5';
                e.dataTransfer.effectAllowed = 'move';
            });

            item.addEventListener('dragend', () => {
                draggedItem = null;
                item.style.opacity = '1';
                
                // Save new order to database
                const chatIds = Array.from(pinnedList.querySelectorAll('.chat-item-wrapper')).map(el => el.getAttribute('data-id'));
                fetch('/chat/reorder-pins/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrftoken
                    },
                    body: JSON.stringify({ chat_ids: chatIds })
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        window.showToast("Pin order saved.");
                    }
                });
            });

            item.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.dataTransfer.dropEffect = 'move';
            });

            item.addEventListener('drop', (e) => {
                e.preventDefault();
                if (draggedItem && draggedItem !== item) {
                    const allItems = Array.from(pinnedList.querySelectorAll('.chat-item-wrapper'));
                    const draggedIndex = allItems.indexOf(draggedItem);
                    const targetIndex = allItems.indexOf(item);
                    
                    if (draggedIndex < targetIndex) {
                        pinnedList.insertBefore(draggedItem, item.nextSibling);
                    } else {
                        pinnedList.insertBefore(draggedItem, item);
                    }
                }
            });
        });
    }

    // --- File Upload Queue & Drag-and-Drop ---
    let uploadedFileIds = [];

    const fileInput = document.getElementById('fileInput');
    const attachBtn = document.getElementById('attachBtn');
    const filePreviewArea = document.getElementById('filePreviewArea');

    if (attachBtn && fileInput) {
        attachBtn.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', (e) => {
            console.log(`[UMI] File(s) selected: ${e.target.files.length}`);
            handleFilesSelection(e.target.files);
        });
    }

    // Drag and drop listeners on application window
    const chatContainerEl = document.querySelector('.chat-area');
    if (chatContainerEl) {
        ['dragenter', 'dragover'].forEach(eventName => {
            chatContainerEl.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                chatContainerEl.style.border = '2px dashed var(--primary-color)';
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            chatContainerEl.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                chatContainerEl.style.border = '';
            }, false);
        });

        chatContainerEl.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files && files.length > 0) {
                handleFilesSelection(files);
            }
        });
    }

    function handleFilesSelection(files) {
        if (!files || files.length === 0) return;
        filePreviewArea.classList.remove('d-none');
        filePreviewArea.classList.add('d-flex');
        
        Array.from(files).forEach(file => {
            // Check allowed formats
            const allowed = ['.pdf', '.docx', '.txt', '.csv', '.xlsx', '.xls', '.pptx', '.png', '.jpg', '.jpeg', '.webp'];
            const ext = '.' + file.name.split('.').pop().toLowerCase();
            if (!allowed.includes(ext)) {
                window.showToast(`Unsupported format: ${ext}`, 'danger');
                return;
            }
            
            // Create preview card element
            const previewCardId = 'upload-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
            const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
            
            const cardHTML = `
                <div class="d-flex align-items-center bg-white border rounded p-2 position-relative shadow-sm" id="${previewCardId}" style="max-width: 240px; border-color: var(--border-color) !important;">
                    <div class="flex-shrink-0 me-2">
                        <i class="bi ${file.type.startsWith('image/') ? 'bi-image' : 'bi-file-earmark-text'} fs-4 text-primary"></i>
                    </div>
                    <div class="overflow-hidden flex-grow-1" style="font-size: 0.75rem; line-height: 1.1;">
                        <div class="text-truncate fw-semibold text-main mb-1" style="max-width: 140px;">${file.name}</div>
                        <div class="text-muted opacity-75">${sizeMB} MB</div>
                        <div class="progress mt-1" style="height: 4px;">
                            <div class="progress-bar progress-bar-striped progress-bar-animated bg-primary" role="progressbar" style="width: 0%"></div>
                        </div>
                    </div>
                    <button type="button" class="btn btn-sm btn-icon text-muted ms-2 remove-preview-btn hover-lift" title="Remove" style="padding: 0; line-height: 1;">
                        <i class="bi bi-x-circle fs-6"></i>
                    </button>
                </div>
            `;
            
            const cardNode = createNodeFromHTML(cardHTML);
            filePreviewArea.appendChild(cardNode);
            
            // File upload XML request
            const xhr = new XMLHttpRequest();
            const formData = new FormData();
            formData.append('file', file);
            
            xhr.open('POST', '/chat/upload/', true);
            xhr.setRequestHeader('X-CSRFToken', csrftoken);
            console.log(`[UMI] Upload started: ${file.name} (${sizeMB} MB)`);
            
            // Track upload progress
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percent = (e.loaded / e.total) * 100;
                    const pb = cardNode.querySelector('.progress-bar');
                    if (pb) pb.style.width = percent + '%';
                }
            });
            
            xhr.onreadystatechange = () => {
                if (xhr.readyState === XMLHttpRequest.DONE) {
                    if (xhr.status === 200) {
                        try {
                            const res = JSON.parse(xhr.responseText);
                            if (res.success) {
                                // Save ID
                                cardNode.setAttribute('data-attachment-id', res.id);
                                uploadedFileIds.push(res.id);
                                console.log(`[UMI] Upload complete: ${file.name}`);
                                window.showToast(`Upload complete: ${file.name}`);
                                // Hide progress bar
                                const prog = cardNode.querySelector('.progress');
                                if (prog) prog.style.display = 'none';
                            } else {
                                handleUploadFailure(cardNode, file.name, res.error);
                            }
                        } catch (err) {
                            handleUploadFailure(cardNode, file.name, "Response parsing failed");
                        }
                    } else {
                        handleUploadFailure(cardNode, file.name, xhr.statusText || `HTTP ${xhr.status}`);
                    }
                }
            };
            
            xhr.send(formData);
            
            // Close / Cancel btn listener
            cardNode.querySelector('.remove-preview-btn').addEventListener('click', () => {
                xhr.abort();
                const attId = cardNode.getAttribute('data-attachment-id');
                if (attId) {
                    uploadedFileIds = uploadedFileIds.filter(id => id !== attId);
                }
                cardNode.remove();
                if (filePreviewArea.children.length === 0) {
                    filePreviewArea.classList.add('d-none');
                    filePreviewArea.classList.remove('d-flex');
                }
            });
        });
    }

    function handleUploadFailure(node, filename, errorMsg) {
        console.error(`[UMI] Upload failed: ${filename} (${errorMsg})`);
        window.showToast(`Upload failed: ${filename} (${errorMsg})`, 'danger');
        node.classList.remove('bg-white');
        node.classList.add('bg-danger-subtle');
        const pb = node.querySelector('.progress-bar');
        if (pb) {
            pb.classList.remove('bg-primary');
            pb.classList.add('bg-danger');
            pb.style.width = '100%';
        }
    }

    // --- Speech Recognition ---
    const micBtn = document.getElementById('micBtn');
    let recognition = null;
    let isRecording = false;

    // Check compatibility
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (micBtn && SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onstart = () => {
            isRecording = true;
            micBtn.innerHTML = '<i class="bi bi-mic-fill fs-5 text-danger animate-pulse"></i>';
            micBtn.title = "Stop Recording";
            window.showToast("Voice recording active...");
        };

        recognition.onend = () => {
            isRecording = false;
            micBtn.innerHTML = '<i class="bi bi-mic fs-5"></i>';
            micBtn.title = "Microphone";
            window.showToast("Voice recording stopped.");
        };

        recognition.onerror = (event) => {
            console.error("Speech Recognition Error:", event.error);
            window.showToast(`Voice Error: ${event.error}`, 'danger');
            recognition.stop();
        };

        recognition.onresult = (event) => {
            let transcript = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    transcript += event.results[i][0].transcript;
                }
            }
            if (transcript && chatInput) {
                const startPos = chatInput.selectionStart;
                const endPos = chatInput.selectionEnd;
                chatInput.value = chatInput.value.substring(0, startPos) + transcript + chatInput.value.substring(endPos);
                chatInput.focus();
                
                // Trigger auto resize
                chatInput.style.height = 'auto';
                chatInput.style.height = chatInput.scrollHeight + 'px';
            }
        };

        micBtn.addEventListener('click', () => {
            if (isRecording) {
                recognition.stop();
            } else {
                recognition.start();
            }
        });
    } else if (micBtn) {
        micBtn.addEventListener('click', () => {
            window.showToast("Voice input is not supported in this browser.", "warning");
        });
    }

    // --- Emoji Picker ---
    const emojiBtn = document.getElementById('emojiBtn');
    let emojiPickerContainer = null;

    const emojis = [
        { category: "Smileys", list: ["😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣", "😊", "😇", "🙂", "🙃", "😉", "😌", "😍", "🥰", "😘", "😗", "😙", "😚", "😋", "😛", "😝", "😜", "🤪", "🤨", "🧐", "🤓", "😎", "🤩", "🥳", "😏", "😒", "😞", "😔", "😟", "😕", "🙁", "☹️", "😣", "😖", "😫", "😩", "🥺", "😢", "😭", "😤", "😠", "😡", "🤬", "🤯", "😳", "🥵", "🥶", "😱", "😨", "😰", "😥", "😓", "🤗", "🤔", "🤭", "🤫", "🤥", "😶", "😐", "😑", "😬", "🙄", "😯", "😦", "😧", "😮", "😲", "🥱", "😴", "🤤", "😪", "😵", "🤐", "🥴", "🤢", "🤮", "🤧", "😷", "🤒", "🤕"] },
        { category: "Gestures", list: ["👍", "👎", "👌", "🤌", "✌️", "🤞", "🤟", "🤘", "🤙", "👈", "👉", "👆", "🖕", "👇", "☝️", "👊", "✊", "🤛", "🤜", "👏", "🙌", "👐", "🤲", "🤝", "🙏", "✍️", "💅", "🤳", "💪", "🦾"] },
        { category: "Hearts & Signs", list: ["❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎", "💔", "❣️", "💕", "💞", "💓", "💗", "💖", "💘", "💝", "💟", "🕉️", "☸️", "☮️", "🕎", "🔯", "⛎", "♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"] },
        { category: "Objects", list: ["💻", "🖥️", "🖨️", "🖱️", "🖲️", "🔌", "🔋", "💾", "💿", "📀", "📷", "📸", "📹", "🎥", "📽️", "🎞️", "📞", "☎️", "📟", "📠", "📺", "📻", "🎙️", "🎛️", "🎚️", "🧭", "⏱️", "💵", "✉️", "📦", "✏️", "✒️", "🔑", "🔒", "🔓"] }
    ];

    if (emojiBtn && chatInput) {
        emojiBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (emojiPickerContainer) {
                emojiPickerContainer.remove();
                emojiPickerContainer = null;
                return;
            }

            // Create Emoji Picker Div
            emojiPickerContainer = document.createElement('div');
            emojiPickerContainer.className = 'emoji-picker-container p-3 rounded-lg shadow-lg position-absolute';
            emojiPickerContainer.style.bottom = '70px';
            emojiPickerContainer.style.left = '30px';
            emojiPickerContainer.style.width = '300px';
            emojiPickerContainer.style.height = '350px';
            emojiPickerContainer.style.zIndex = '2000';
            emojiPickerContainer.style.backgroundColor = 'var(--card-bg)';
            emojiPickerContainer.style.border = '1px solid var(--border-color)';
            emojiPickerContainer.style.overflowY = 'auto';
            
            // Build inner HTML: Search input + Category blocks
            let pickerHTML = `
                <div class="mb-2">
                    <input type="text" id="emojiSearch" class="form-control form-control-sm rounded-pill" placeholder="Search emoji..." style="background: var(--bg-color); color: var(--text-main); border-color: var(--border-color);">
                </div>
                <div class="emoji-groups-wrapper" style="max-height: 270px; overflow-y: auto;">
            `;

            // Recent emojis section (saved in localStorage)
            let recents = JSON.parse(localStorage.getItem('recent_emojis') || '[]');
            if (recents.length > 0) {
                pickerHTML += `
                    <div class="emoji-group-section mb-3" data-category="recent">
                        <div class="fw-semibold text-xs text-muted mb-1">Recent</div>
                        <div class="d-flex flex-wrap gap-2">
                            ${recents.map(emoji => `<span class="emoji-item fs-5 cursor-pointer hover-scale">${emoji}</span>`).join('')}
                        </div>
                    </div>
                `;
            }

            emojis.forEach(group => {
                pickerHTML += `
                    <div class="emoji-group-section mb-3" data-category="${group.category.toLowerCase()}">
                        <div class="fw-semibold text-xs text-muted mb-1">${group.category}</div>
                        <div class="d-flex flex-wrap gap-2">
                            ${group.list.map(emoji => `<span class="emoji-item fs-5 cursor-pointer hover-scale">${emoji}</span>`).join('')}
                        </div>
                    </div>
                `;
            });

            pickerHTML += `</div>`;
            emojiPickerContainer.innerHTML = pickerHTML;
            
            // Append container to input area wrapper
            const containerParent = document.getElementById('chatInputContainer');
            if (containerParent) {
                containerParent.appendChild(emojiPickerContainer);
            }

            // Click listener for emojis
            emojiPickerContainer.addEventListener('click', (ev) => {
                if (ev.target.classList.contains('emoji-item')) {
                    const emoji = ev.target.textContent;
                    
                    // Insert at textcursor position
                    const startPos = chatInput.selectionStart;
                    const endPos = chatInput.selectionEnd;
                    chatInput.value = chatInput.value.substring(0, startPos) + emoji + chatInput.value.substring(endPos);
                    chatInput.focus();
                    
                    // Save to recent
                    let recentList = JSON.parse(localStorage.getItem('recent_emojis') || '[]');
                    recentList = [emoji, ...recentList.filter(item => item !== emoji)].slice(0, 16);
                    localStorage.setItem('recent_emojis', JSON.stringify(recentList));
                    
                    emojiPickerContainer.remove();
                    emojiPickerContainer = null;
                }
            });

            // Search logic
            const searchInput = emojiPickerContainer.querySelector('#emojiSearch');
            searchInput.addEventListener('input', (se) => {
                const term = se.target.value.toLowerCase();
                const sections = emojiPickerContainer.querySelectorAll('.emoji-group-section');
                
                sections.forEach(sec => {
                    let hasVisible = false;
                    const items = sec.querySelectorAll('.emoji-item');
                    items.forEach(it => {
                        if (!term || it.textContent.includes(term)) {
                            it.style.display = '';
                            hasVisible = true;
                        } else {
                            it.style.display = 'none';
                        }
                    });
                    
                    if (hasVisible) {
                        sec.style.display = '';
                    } else {
                        sec.style.display = 'none';
                    }
                });
            });

            // Close when clicking outside
            document.addEventListener('click', closeEmojiPicker);
        });
    }

    function closeEmojiPicker(e) {
        if (emojiPickerContainer && !emojiPickerContainer.contains(e.target) && e.target !== emojiBtn) {
            emojiPickerContainer.remove();
            emojiPickerContainer = null;
            document.removeEventListener('click', closeEmojiPicker);
        }
    }
});
