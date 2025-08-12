/**
 * Multi-Agent Learning Assistant Interface
 * Optimized JavaScript implementation
 */

console.log('=== JavaScript文件开始加载 ===');
console.log('当前时间:', new Date().toLocaleString());

class MultiAgentInterface {
    constructor() {
        this.currentSessionId = null;
        this.isProcessing = false;
        this.messageHistory = [];
        this.healthCheckInterval = null;
        this.notificationTimeout = null;
        
        this.init();
    }

    init() {
        // 初始化会话ID
        if (!this.currentSessionId) {
            this.currentSessionId = this.generateSessionId();
        }
        
        this.setupEventListeners();
        this.initializeUI();
        this.initializeSidebarState();
        this.checkSystemHealth();
        this.loadUserProfile();
        this.startHealthCheck();
        
        // 检查是否有从首页传递的初始问题
        this.loadInitialQuestion();
        
        // 检查并恢复聊天状态
        this.restoreChatState();
        
        // 初始化当前对话信息显示
        this.updateCurrentConversationInfo();
        
        // 初始化侧边栏对话列表
        this.refreshSidebarConversationList();
        
        // 确保用户画像数据正确加载
        setTimeout(() => {
            this.loadUserProfile();
        }, 1000);
    }

    setupEventListeners() {
        // Welcome screen events
        const welcomeMessageInput = document.getElementById('welcomeMessageInput');
        const welcomeSendButton = document.getElementById('welcomeSendButton');
        
        console.log('=== 欢迎界面元素检查 ===');
        console.log('Welcome input element:', welcomeMessageInput);
        console.log('Welcome send button:', welcomeSendButton);
        console.log('Welcome input exists:', !!welcomeMessageInput);
        console.log('Welcome button exists:', !!welcomeSendButton);
        
        // 检查元素的父容器
        if (welcomeSendButton) {
            console.log('Welcome button parent:', welcomeSendButton.parentElement);
            console.log('Welcome button classes:', welcomeSendButton.className);
            console.log('Welcome button disabled:', welcomeSendButton.disabled);
        }
        
        if (welcomeMessageInput) {
            console.log('Welcome input style display:', getComputedStyle(welcomeMessageInput).display);
            console.log('Welcome input style visibility:', getComputedStyle(welcomeMessageInput).visibility);
        }
        
        if (welcomeSendButton) {
            console.log('Welcome button style display:', getComputedStyle(welcomeSendButton).display);
            console.log('Welcome button style visibility:', getComputedStyle(welcomeSendButton).visibility);
            console.log('Welcome button style pointer-events:', getComputedStyle(welcomeSendButton).pointerEvents);
        }
        
        welcomeMessageInput?.addEventListener('keypress', (e) => {
            console.log('Welcome input keypress:', e.key);
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                console.log('Enter pressed, calling sendWelcomeMessage');
                this.sendWelcomeMessage();
            }
        });

        welcomeSendButton?.addEventListener('click', (e) => {
            console.log('Welcome send button clicked');
            e.preventDefault();
            this.sendWelcomeMessage();
        });
        


        // Message input events
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        

        
        messageInput?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        sendButton?.addEventListener('click', () => {
            this.sendMessage();
        });

        // Button events
        document.getElementById('clearChatBtn')?.addEventListener('click', () => this.clearChat());
        
        const refreshBtn = document.getElementById('refreshStatusBtn');
        refreshBtn?.addEventListener('click', () => {
            this.refreshStatus();
        });
        
        document.getElementById('downloadChatBtn')?.addEventListener('click', () => this.downloadChat());

        // User profile buttons
        document.getElementById('viewProfileBtn')?.addEventListener('click', () => this.viewUserProfile());
        document.getElementById('exportProfileBtn')?.addEventListener('click', () => this.exportUserProfile());
        document.getElementById('clearProfileBtn')?.addEventListener('click', () => this.clearUserProfile());
        document.getElementById('analyzeProfileBtn')?.addEventListener('click', () => this.analyzeUserProfile());
        
        // 用户画像导航按钮
        document.getElementById('userProfileNavBtn')?.addEventListener('click', () => this.navigateToUserProfile());

        // 历史对话管理按钮
        console.log('=== 设置历史对话管理按钮事件监听器 ===');
        
        const newConversationBtn = document.getElementById('newConversationBtn');
        const conversationHistoryBtn = document.getElementById('conversationHistoryBtn');
        const createNewConversationBtn = document.getElementById('createNewConversationBtn');
        const refreshConversationListBtn = document.getElementById('refreshConversationListBtn');
        const closeConversationHistoryModal = document.getElementById('closeConversationHistoryModal');
        
        console.log('newConversationBtn element:', newConversationBtn);
        console.log('conversationHistoryBtn element:', conversationHistoryBtn);
        console.log('createNewConversationBtn element:', createNewConversationBtn);
        console.log('refreshConversationListBtn element:', refreshConversationListBtn);
        console.log('closeConversationHistoryModal element:', closeConversationHistoryModal);
        
        if (newConversationBtn) {
            console.log('新建对话按钮找到，添加事件监听器');
            newConversationBtn.addEventListener('click', (e) => {
                console.log('=== 新建对话按钮被点击 ===');
                console.log('Event:', e);
                console.log('Target:', e.target);
                console.log('调用 createNewConversation 方法');
                this.createNewConversation();
            });
        } else {
            console.error('新建对话按钮未找到！');
        }
        
        if (conversationHistoryBtn) {
            console.log('对话历史按钮找到，添加事件监听器');
            conversationHistoryBtn.addEventListener('click', (e) => {
                console.log('=== 对话历史按钮被点击 ===');
                console.log('Event:', e);
                console.log('调用 showConversationHistory 方法');
                this.showConversationHistory();
            });
        } else {
            console.error('对话历史按钮未找到！');
        }
        
        createNewConversationBtn?.addEventListener('click', () => this.createNewConversation());
        refreshConversationListBtn?.addEventListener('click', () => this.refreshConversationList());
        closeConversationHistoryModal?.addEventListener('click', () => this.closeConversationHistoryModal());

        // 边栏切换按钮
        document.getElementById('sidebarToggle')?.addEventListener('click', () => this.toggleSidebar());
        
        // 移除边栏遮罩层点击关闭功能，允许用户正常使用右侧内容
        // document.getElementById('sidebarOverlay')?.addEventListener('click', () => this.closeSidebar());



        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));

        // Mouse events for enhanced UX
        document.addEventListener('mouseover', (e) => this.handleMouseEvents(e, 'over'));
        document.addEventListener('mouseout', (e) => this.handleMouseEvents(e, 'out'));
        
        // 模态框点击外部关闭
        document.addEventListener('click', (e) => {
            const modal = document.getElementById('conversationHistoryModal');
            if (modal && e.target === modal) {
                this.closeConversationHistoryModal();
            }
        });
    }

    initializeUI() {
        // Add typing effect to welcome message
        const welcomeMessage = document.querySelector('.message.system');
        if (welcomeMessage) {
            welcomeMessage.style.opacity = '0';
            setTimeout(() => {
                welcomeMessage.style.transition = 'opacity 0.5s ease';
                welcomeMessage.style.opacity = '1';
            }, 500);
        }

        // Add panel entrance animations
        const panels = document.querySelectorAll('.panel');
        panels.forEach((panel, index) => {
            panel.style.opacity = '0';
            panel.style.transform = 'translateY(20px)';
            setTimeout(() => {
                panel.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                panel.style.opacity = '1';
                panel.style.transform = 'translateY(0)';
            }, 200 * (index + 1));
        });
    }

    async checkSystemHealth() {
        try {
            const response = await this.makeRequest('/api/multi-agent/health');
            if (response.status === 'healthy') {
                this.updateConnectionStatus('在线', 'online');
                await this.loadSystemStats();
            } else {
                this.updateConnectionStatus('异常', 'offline');
            }
        } catch (error) {
            console.error('Health check failed:', error);
            this.updateConnectionStatus('离线', 'offline');
        }
    }

    async loadSystemStats() {
        try {
            const stats = await this.makeRequest('/api/multi-agent/stats');
            const successRateElement = document.getElementById('successRate');
            if (successRateElement) {
                successRateElement.textContent = (stats.success_rate * 100).toFixed(1) + '%';
            }
        } catch (error) {
            console.error('Failed to load stats:', error);
        }
    }

    updateConnectionStatus(status, type) {
        const statusElement = document.getElementById('connectionStatus');
        if (statusElement) {
            statusElement.innerHTML = `${status} <span class="status-indicator ${type}"></span>`;
        }
    }

    loadInitialQuestion() {
        // 检查sessionStorage中是否有初始问题
        const initialQuestion = sessionStorage.getItem('initialQuestion');
        if (initialQuestion) {
            // 将问题填入欢迎界面的输入框
            const welcomeMessageInput = document.getElementById('welcomeMessageInput');
            if (welcomeMessageInput) {
                welcomeMessageInput.value = initialQuestion;
                // 聚焦到输入框
                welcomeMessageInput.focus();
                // 将光标移到文本末尾
                welcomeMessageInput.setSelectionRange(initialQuestion.length, initialQuestion.length);
            }
            
            // 清除sessionStorage中的问题，避免重复使用
            sessionStorage.removeItem('initialQuestion');
        }
    }

    async sendWelcomeMessage() {
        console.log('sendWelcomeMessage called');
        const input = document.getElementById('welcomeMessageInput');
        const message = input?.value?.trim();
        
        console.log('Input element:', input);
        console.log('Message:', message);
        console.log('isProcessing:', this.isProcessing);
        
        if (!message) {
            console.log('No message provided');
            alert('请输入您想要学习的问题');
            return;
        }
        
        if (this.isProcessing) {
            console.log('Already processing');
            return;
        }
        
        console.log('Switching to chat interface...');
        // Switch to chat interface
        this.switchToChatInterface();
        
        // Clear welcome input
        input.value = '';
        
        // Wait for interface switch animation to complete, then send message
        setTimeout(async () => {
            console.log('Sending message after interface switch:', message);
            await this.sendMessageWithContent(message);
        }, 800); // Wait for animation to complete
    }

    switchToChatInterface() {
        const welcomeScreen = document.getElementById('welcomeScreen');
        const chatContainer = document.getElementById('chatContainer');
        
        if (welcomeScreen && chatContainer) {
            // Add welcome message first before switching interface
            this.addMessage('🎓 欢迎使用多智能体学习助手！我将通过苏格拉底式对话帮助您深入理解知识。', 'system');
            
            // 保存聊天状态
            this.saveChatState();
            
            // Add fade out animation to welcome screen
            welcomeScreen.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            welcomeScreen.style.opacity = '0';
            welcomeScreen.style.transform = 'scale(0.95)';
            
            setTimeout(() => {
                welcomeScreen.style.display = 'none';
                chatContainer.style.display = 'flex';
                
                // Add fade in animation to chat container
                chatContainer.style.opacity = '0';
                chatContainer.style.transform = 'translateY(20px)';
                
                setTimeout(() => {
                    chatContainer.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                    chatContainer.style.opacity = '1';
                    chatContainer.style.transform = 'translateY(0)';
                }, 50);
            }, 500);
        }
    }

    async sendMessage() {
        console.log('sendMessage called');
        const input = document.getElementById('messageInput');
        const message = input?.value?.trim();
        
        console.log('Chat input element:', input);
        console.log('Chat message:', message);
        console.log('isProcessing:', this.isProcessing);
        
        if (!message) {
            console.log('No message in chat input');
            return;
        }
        
        if (this.isProcessing) {
            console.log('Already processing, skipping');
            return;
        }
        
        // Clear input
        input.value = '';
        console.log('Chat input cleared, sending message:', message);
        
        // Send message with content
        await this.sendMessageWithContent(message);
    }

    async sendMessageWithContent(message) {
        console.log('sendMessageWithContent called with:', message);
        
        if (!message) {
            console.log('No message provided to sendMessageWithContent');
            return;
        }
        
        if (this.isProcessing) {
            console.log('Already processing, skipping sendMessageWithContent');
            return;
        }
        
        console.log('Adding user message to interface:', message);
        // Add user message to interface
        this.addMessage(message, 'user');
        
        console.log('Setting processing state to true');
        // Set processing state
        this.setProcessing(true);
        
        try {
            console.log('Preparing API request...');
            const requestData = {
                query: message,
                session_id: this.currentSessionId,
                user_id: 'anonymous'  // 添加用户ID以确保用户画像更新
            };
            console.log('Request data:', requestData);
            
            console.log('Sending request to /api/multi-agent/query...');
            // Send query request
            const response = await this.makeRequest('/api/multi-agent/query', {
                method: 'POST',
                body: JSON.stringify(requestData)
            });
            
            console.log('API response received:', response);
            
            if (response && response.success) {
                console.log('Response is successful');
                
                // Update session ID
                if (!this.currentSessionId && response.session_id) {
                    console.log('Setting new session ID:', response.session_id);
                    this.currentSessionId = response.session_id;
                    const sessionIdElement = document.getElementById('sessionId');
                    if (sessionIdElement) {
                        sessionIdElement.textContent = response.session_id.substring(0, 8) + '...';
                    }
                }
                
                // Handle response
                if (response.socratic_question) {
                    console.log('Adding socratic question:', response.socratic_question);
                    this.addSocraticQuestion(response.socratic_question);
                } else if (response.final_response) {
                    console.log('Adding assistant message:', response.final_response);
                    this.addMessage(response.final_response, 'assistant');
                } else {
                    console.log('No response content found, adding default message');
                    this.addMessage('收到您的消息，正在处理中...', 'assistant');
                }
                
                // Update workflow steps
                if (response.steps_completed) {
                    console.log('Updating workflow steps:', response.steps_completed);
                    this.updateWorkflowSteps(response.steps_completed);
                }
                
                // Update user profile display
                if (response.state_summary) {
                    console.log('Updating user profile from response');
                    this.updateUserProfileFromResponse(response);
                }
                
            } else {
                console.log('Response indicates failure:', response);
                const errorMsg = response ? (response.error || '未知错误') : '服务器无响应';
                this.addMessage('抱歉，处理您的请求时出现了错误：' + errorMsg, 'system');
            }
            
        } catch (error) {
            console.error('Send message failed:', error);
            console.error('Error details:', error.message, error.stack);
            this.addMessage('网络错误，请检查连接后重试。错误详情：' + error.message, 'system');
        } finally {
            console.log('Setting processing state to false');
            this.setProcessing(false);
            
            // 保存聊天状态
            this.saveChatState();
            
            // 自动保存对话到历史记录（如果有消息内容）
            if (this.messageHistory.length > 0) {
                this.saveCurrentConversation();
                this.updateCurrentConversationInfo();
            }
        }
    }

    addSocraticQuestion(questionData) {
        const messagesContainer = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant socratic';
        
        // 处理不同格式的苏格拉底问题数据
        let questionText = '';
        let purposeText = '';
        
        if (typeof questionData === 'string') {
            // 如果是字符串，直接使用
            questionText = questionData;
        } else if (questionData && typeof questionData === 'object') {
            // 如果是对象，提取question和purpose
            questionText = questionData.question || questionData.content || '请思考这个问题';
            purposeText = questionData.purpose || questionData.hint || '';
        } else {
            // 如果是undefined或其他类型，使用默认文本
            questionText = '请继续思考这个问题';
        }
        
        // Build Socratic question content
        let content = `🤔 **苏格拉底式引导**\n\n${questionText}`;
        
        if (purposeText) {
            content += `\n\n*💡 思考方向：${purposeText}*`;
        }
        
        // Process message content
        const processedContent = this.processMessageContent(content);
        messageDiv.innerHTML = processedContent;
        
        // Add special style identifier
        messageDiv.style.borderLeft = '4px solid #667eea';
        messageDiv.style.background = 'linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%)';
        
        // Add timestamp
        const timestamp = new Date().toLocaleTimeString();
        const metaDiv = document.createElement('div');
        metaDiv.className = 'message-meta';
        metaDiv.textContent = timestamp + ' • 苏格拉底引导';
        messageDiv.appendChild(metaDiv);
        
        this.addMessageToContainer(messageDiv, messagesContainer);
        
        // Save to history
        this.messageHistory.push({
            content: questionText,
            type: 'socratic',
            timestamp: timestamp,
            questionData: questionData,
            purpose: purposeText
        });
        
        // 保存聊天状态
        this.saveChatState();
    }

    addMessage(content, type, saveToHistory = true) {
        console.log('addMessage called with:', content, type, 'saveToHistory:', saveToHistory);
        const messagesContainer = document.getElementById('chatMessages');
        console.log('Messages container:', messagesContainer);
        
        if (!messagesContainer) {
            console.error('Messages container not found!');
            return;
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        // Process message content
        const processedContent = this.processMessageContent(content);
        messageDiv.innerHTML = processedContent;
        
        // Add timestamp
        const timestamp = new Date().toLocaleTimeString();
        const metaDiv = document.createElement('div');
        metaDiv.className = 'message-meta';
        metaDiv.textContent = timestamp;
        messageDiv.appendChild(metaDiv);
        
        console.log('Adding message to container');
        this.addMessageToContainer(messageDiv, messagesContainer);
        
        // Save to history only if requested
        if (saveToHistory) {
            this.messageHistory.push({
                content: content,
                type: type,
                timestamp: timestamp
            });
            console.log('Message added to history');
        }
    }

    addMessageToContainer(messageDiv, container) {
        console.log('addMessageToContainer called');
        console.log('Container:', container);
        console.log('Container scrollHeight before:', container.scrollHeight);
        
        // Set initial opacity to 0
        messageDiv.style.opacity = '0';
        messageDiv.style.transform = 'translateY(10px)';
        
        container.appendChild(messageDiv);
        console.log('Message div appended to container');
        console.log('Container scrollHeight after:', container.scrollHeight);
        
        // Trigger animation
        setTimeout(() => {
            messageDiv.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            messageDiv.style.opacity = '1';
            messageDiv.style.transform = 'translateY(0)';
            console.log('Message animation triggered');
        }, 50);
        
        // Smooth scroll to bottom
        setTimeout(() => {
            console.log('Scrolling to bottom, scrollHeight:', container.scrollHeight);
            container.scrollTo({
                top: container.scrollHeight,
                behavior: 'smooth'
            });
            console.log('Scroll command executed');
        }, 100);
    }

    processMessageContent(content) {
        // Escape HTML special characters
        content = content.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        
        // Process code blocks with language identifier
        content = content.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
            const language = lang ? lang.trim() : 'text';
            const codeId = 'code_' + Math.random().toString(36).substr(2, 9);
            const copyBtn = `<button class="copy-btn" onclick="multiAgentInterface.copyCode('${codeId}')">复制</button>`;
            const header = language !== 'text' ? `<div class="code-header">${language}${copyBtn}</div>` : '';
            return `${header}<pre><code id="${codeId}">${code.trim()}</code></pre>`;
        });
        
        // Process simple code blocks
        content = content.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
        
        // Process headers
        content = content.replace(/^### (.*$)/gm, '<h3>$1</h3>');
        content = content.replace(/^## (.*$)/gm, '<h2>$1</h2>');
        content = content.replace(/^# (.*$)/gm, '<h1>$1</h1>');
        content = content.replace(/^#### (.*$)/gm, '<h4>$1</h4>');
        content = content.replace(/^##### (.*$)/gm, '<h5>$1</h5>');
        content = content.replace(/^###### (.*$)/gm, '<h6>$1</h6>');
        
        // Process horizontal rules
        content = content.replace(/^---$/gm, '<hr>');
        content = content.replace(/^\*\*\*$/gm, '<hr>');
        
        // Process blockquotes
        content = content.replace(/^> (.*)$/gm, '<blockquote>$1</blockquote>');
        
        // Process bold and italic
        content = content.replace(/\*\*\*(.*?)\*\*\*/g, '<strong><em>$1</em></strong>');
        content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        content = content.replace(/\*(.*?)\*/g, '<em>$1</em>');
        content = content.replace(/__(.*?)__/g, '<strong>$1</strong>');
        content = content.replace(/_(.*?)_/g, '<em>$1</em>');
        
        // Process inline code
        content = content.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // Process links
        content = content.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
        content = content.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
        
        // Process lists
        content = this.processMarkdownLists(content);
        
        // Process tables
        content = this.processMarkdownTable(content);
        
        // Process paragraphs
        content = this.processMarkdownParagraphs(content);
        
        // Process line breaks
        content = content.replace(/\n/g, '<br>');
        
        return content;
    }

    processMarkdownTable(content) {
        const lines = content.split('\n');
        let result = [];
        let inTable = false;
        let tableRows = [];
        
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            
            if (line.includes('|') && line.split('|').length > 2) {
                if (!inTable) {
                    inTable = true;
                    tableRows = [];
                }
                
                const cells = line.split('|').map(cell => cell.trim()).filter(cell => cell);
                
                // Check if it's a separator row
                if (cells.every(cell => /^:?-+:?$/.test(cell))) {
                    continue;
                }
                
                const isHeader = tableRows.length === 0;
                const tag = isHeader ? 'th' : 'td';
                const row = `<tr>${cells.map(cell => `<${tag}>${cell}</${tag}>`).join('')}</tr>`;
                tableRows.push(row);
            } else {
                if (inTable) {
                    result.push(`<table>${tableRows.join('')}</table>`);
                    inTable = false;
                    tableRows = [];
                }
                result.push(line);
            }
        }
        
        if (inTable) {
            result.push(`<table>${tableRows.join('')}</table>`);
        }
        
        return result.join('\n');
    }

    processMarkdownLists(content) {
        const lines = content.split('\n');
        let result = [];
        let inUnorderedList = false;
        let inOrderedList = false;
        let listItems = [];
        
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const trimmedLine = line.trim();
            
            // Check task list items
            const taskMatch = trimmedLine.match(/^[\*\-\+]\s+\[([ x])\]\s+(.*)$/);
            // Check unordered list items
            const unorderedMatch = trimmedLine.match(/^[\*\-\+]\s+(.*)$/);
            // Check ordered list items
            const orderedMatch = trimmedLine.match(/^\d+\.\s+(.*)$/);
            
            if (taskMatch) {
                if (inOrderedList) {
                    result.push(`<ol>${listItems.join('')}</ol>`);
                    listItems = [];
                    inOrderedList = false;
                }
                if (!inUnorderedList) {
                    inUnorderedList = true;
                }
                const checked = taskMatch[1] === 'x' ? 'checked' : '';
                listItems.push(`<li class="task-item"><input type="checkbox" ${checked} disabled><span>${taskMatch[2]}</span></li>`);
            } else if (unorderedMatch && !taskMatch) {
                if (inOrderedList) {
                    result.push(`<ol>${listItems.join('')}</ol>`);
                    listItems = [];
                    inOrderedList = false;
                }
                if (!inUnorderedList) {
                    inUnorderedList = true;
                }
                listItems.push(`<li>${unorderedMatch[1]}</li>`);
            } else if (orderedMatch) {
                if (inUnorderedList) {
                    result.push(`<ul>${listItems.join('')}</ul>`);
                    listItems = [];
                    inUnorderedList = false;
                }
                if (!inOrderedList) {
                    inOrderedList = true;
                }
                listItems.push(`<li>${orderedMatch[1]}</li>`);
            } else {
                // End current list
                if (inUnorderedList) {
                    result.push(`<ul>${listItems.join('')}</ul>`);
                    listItems = [];
                    inUnorderedList = false;
                }
                if (inOrderedList) {
                    result.push(`<ol>${listItems.join('')}</ol>`);
                    listItems = [];
                    inOrderedList = false;
                }
                result.push(line);
            }
        }
        
        // Handle remaining lists
        if (inUnorderedList) {
            result.push(`<ul>${listItems.join('')}</ul>`);
        }
        if (inOrderedList) {
            result.push(`<ol>${listItems.join('')}</ol>`);
        }
        
        return result.join('\n');
    }

    processMarkdownParagraphs(content) {
        const lines = content.split('\n');
        let result = [];
        let currentParagraph = [];
        
        for (let line of lines) {
            line = line.trim();
            
            // If it's an empty line or HTML tag line, end current paragraph
            if (!line || line.startsWith('<') || line.match(/^#{1,6}\s/)) {
                if (currentParagraph.length > 0) {
                    result.push(`<p>${currentParagraph.join(' ')}</p>`);
                    currentParagraph = [];
                }
                if (line) {
                    result.push(line);
                }
            } else {
                currentParagraph.push(line);
            }
        }
        
        // Handle remaining paragraph
        if (currentParagraph.length > 0) {
            result.push(`<p>${currentParagraph.join(' ')}</p>`);
        }
        
        return result.join('\n');
    }

    setProcessing(processing) {
        this.isProcessing = processing;
        const sendButton = document.getElementById('sendButton');
        const input = document.getElementById('messageInput');
        const statusElement = document.getElementById('processingStatus');
        
        if (processing) {
            sendButton?.setAttribute('disabled', 'true');
            sendButton.innerHTML = '<span class="loading"></span>';
            input?.setAttribute('disabled', 'true');
            if (statusElement) {
                statusElement.innerHTML = '处理中 <span class="status-indicator processing"></span>';
            }
        } else {
            sendButton?.removeAttribute('disabled');
            sendButton.textContent = '发送';
            input?.removeAttribute('disabled');
            if (statusElement) {
                statusElement.textContent = '空闲';
            }
        }
    }

    updateWorkflowSteps(completedSteps) {
        const steps = document.querySelectorAll('.workflow-step');
        const stepNames = ['query_interpreter', 'knowledge_retriever', 'user_profile', 'socratic_guide', 'planner', 'executor', 'learner'];
        
        steps.forEach((step, index) => {
            step.classList.remove('active', 'completed');
            
            if (completedSteps.includes(stepNames[index])) {
                setTimeout(() => {
                    step.classList.add('completed');
                }, index * 100);
            }
        });

        // Update learning progress bar
        this.updateLearningProgress(completedSteps.length, stepNames.length);
    }

    updateLearningProgress(completed, total) {
        const progressBar = document.getElementById('learningProgress');
        if (progressBar) {
            const percentage = (completed / total) * 100;
            progressBar.style.width = percentage + '%';
        }
    }

    clearChat() {
        if (!confirm('确定要清空所有对话记录吗？这将删除当前对话和所有历史对话，此操作无法撤销。')) {
            return;
        }
        
        const chatMessages = document.getElementById('chatMessages');
        
        // Add fade out effect
        chatMessages.style.transition = 'opacity 0.3s ease';
        chatMessages.style.opacity = '0';
        
        setTimeout(() => {
            chatMessages.innerHTML = 
                `<div class="message system">
                    🎓 所有对话记录已清空，请输入新的问题开始学习。
                    <div class="learning-progress">
                        <div class="learning-progress-bar" id="learningProgress"></div>
                    </div>
                </div>`;
            
            // Fade in effect
            chatMessages.style.opacity = '1';
            
            // 重置对话状态
            this.messageHistory = [];
            this.currentSessionId = this.generateSessionId();
            const sessionIdElement = document.getElementById('sessionId');
            if (sessionIdElement) {
                sessionIdElement.textContent = this.currentSessionId.substring(0, 8) + '...';
            }
            
            // 清除所有历史对话记录
            localStorage.removeItem('conversationHistory');
            
            // 清除聊天状态
            this.clearChatState();
            
            // Reset workflow steps
            const steps = document.querySelectorAll('.workflow-step');
            steps.forEach(step => {
                step.classList.remove('active', 'completed');
            });
            
            // Reset learning progress bar
            this.updateLearningProgress(0, 6);
            
            // 更新当前对话信息
            this.updateCurrentConversationInfo();
            
            // 刷新侧边栏对话列表
            this.refreshSidebarConversationList();
            
            this.showNotification('所有对话记录已清空', 'success');
        }, 300);
    }

    async refreshStatus() {
        console.log('🔄 refreshStatus method called');
        
        // 显示刷新开始的通知
        this.showNotification('正在刷新系统状态...', 'info');
        
        try {
            console.log('🔍 Checking system health...');
            await this.checkSystemHealth();
            console.log('✅ System health check completed');
            
            if (this.currentSessionId) {
                console.log('🔍 Checking session status for:', this.currentSessionId);
                try {
                    const sessionData = await this.makeRequest(`/api/multi-agent/session/${this.currentSessionId}`);
                    if (sessionData.exists) {
                        console.log('✅ Session status:', sessionData);
                        this.showNotification('会话状态已刷新', 'success');
                    } else {
                        console.log('⚠️ Session does not exist');
                        this.showNotification('会话不存在', 'warning');
                    }
                } catch (error) {
                    console.error('❌ Failed to refresh session status:', error);
                    this.showNotification('刷新会话状态失败: ' + error.message, 'error');
                }
            } else {
                console.log('ℹ️ No current session ID');
                this.showNotification('系统状态已刷新（无活动会话）', 'success');
            }
            
            // 刷新用户画像
            console.log('🔍 Refreshing user profile...');
            await this.loadUserProfile();
            console.log('✅ User profile refreshed');
            
        } catch (error) {
            console.error('❌ Failed to refresh status:', error);
            this.showNotification('刷新状态失败: ' + error.message, 'error');
        }
        
        console.log('🔄 refreshStatus method completed');
    }

    downloadChat() {
        // 获取所有历史对话
        const conversations = this.getConversationHistory();
        
        // 如果当前对话有内容，也包含在导出中
        let currentConversation = null;
        if (this.messageHistory.length > 0) {
            const firstUserMessage = this.messageHistory.find(msg => msg.type === 'user');
            const title = firstUserMessage ? 
                (firstUserMessage.content.length > 30 ? 
                    firstUserMessage.content.substring(0, 30) + '...' : 
                    firstUserMessage.content) : 
                '当前对话';
            
            currentConversation = {
                id: this.currentSessionId,
                title: title,
                timestamp: new Date().toISOString(),
                messages: this.messageHistory,
                messageCount: this.messageHistory.length,
                lastMessage: this.messageHistory.length > 0 ? 
                    this.messageHistory[this.messageHistory.length - 1].content : ''
            };
        }
        
        // 合并所有对话数据
        const allConversations = [...conversations];
        if (currentConversation) {
            // 检查当前对话是否已经在历史记录中
            const existingIndex = allConversations.findIndex(conv => conv.id === currentConversation.id);
            if (existingIndex >= 0) {
                allConversations[existingIndex] = currentConversation;
            } else {
                allConversations.unshift(currentConversation);
            }
        }
        
        if (allConversations.length === 0) {
            this.showNotification('没有对话记录可以导出。', 'warning');
            return;
        }
        
        const exportData = {
            export_info: {
                export_time: new Date().toISOString(),
                total_conversations: allConversations.length,
                export_type: 'all_conversations'
            },
            conversations: allConversations
        };
        
        const dataStr = JSON.stringify(exportData, null, 2);
        const dataBlob = new Blob([dataStr], {type: 'application/json'});
        
        const link = document.createElement('a');
        link.href = URL.createObjectURL(dataBlob);
        link.download = `all_conversations_export_${new Date().toISOString().split('T')[0]}.json`;
        link.click();
        
        this.showNotification(`已导出 ${allConversations.length} 个对话记录`, 'success');
    }

    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + Enter send message
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            this.sendMessage();
        }
        
        // Ctrl/Cmd + L clear chat
        if ((e.ctrlKey || e.metaKey) && e.key === 'l') {
            e.preventDefault();
            this.clearChat();
        }
        
        // ESC key to close sidebar
        if (e.key === 'Escape') {
            const sidebar = document.getElementById('collapsibleSidebar');
            if (sidebar && sidebar.classList.contains('open')) {
                e.preventDefault();
                this.closeSidebar();
            }
        }
    }

    handleMouseEvents(e, type) {
        const message = e.target.closest('.message');
        if (message && !message.classList.contains('system')) {
            if (type === 'over') {
                message.style.transform = 'translateY(-1px)';
                message.style.boxShadow = '0 6px 20px rgba(0, 0, 0, 0.12)';
            } else {
                message.style.transform = 'translateY(0)';
                message.style.boxShadow = '';
            }
        }
    }

    startHealthCheck() {
        this.healthCheckInterval = setInterval(() => {
            this.checkSystemHealth();
        }, 30000); // Check every 30 seconds
    }

    copyCode(codeId) {
        const codeElement = document.getElementById(codeId);
        if (!codeElement) return;
        
        const text = codeElement.textContent;
        
        // Use modern Clipboard API
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(text).then(() => {
                this.showCopySuccess(codeId);
            }).catch(err => {
                console.error('Copy failed:', err);
                this.fallbackCopyTextToClipboard(text, codeId);
            });
        } else {
            // Fallback
            this.fallbackCopyTextToClipboard(text, codeId);
        }
    }

    fallbackCopyTextToClipboard(text, codeId) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            const successful = document.execCommand('copy');
            if (successful) {
                this.showCopySuccess(codeId);
            } else {
                console.error('Copy failed');
            }
        } catch (err) {
            console.error('Copy failed:', err);
        }
        
        document.body.removeChild(textArea);
    }

    showCopySuccess(codeId) {
        const codeElement = document.getElementById(codeId);
        if (!codeElement) return;
        
        const copyBtn = codeElement.parentElement.previousElementSibling?.querySelector('.copy-btn');
        if (copyBtn) {
            const originalText = copyBtn.textContent;
            copyBtn.textContent = '已复制!';
            copyBtn.classList.add('copied');
            
            setTimeout(() => {
                copyBtn.textContent = originalText;
                copyBtn.classList.remove('copied');
            }, 2000);
        }
    }

    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    async makeRequest(url, options = {}) {
        // 使用相对路径，因为前端和后端在同一个端口（8000）
        const fullUrl = url.startsWith('http') ? url : url;
        
        console.log('makeRequest called with URL:', url);
        console.log('Full URL:', fullUrl);
        console.log('makeRequest options:', options);
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json'
            }
        };
        
        const finalOptions = { ...defaultOptions, ...options };
        console.log('Final request options:', finalOptions);
        
        try {
            console.log('Sending fetch request...');
            const response = await fetch(fullUrl, finalOptions);
            console.log('Fetch response received:', response);
            console.log('Response status:', response.status);
            console.log('Response ok:', response.ok);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('Response error text:', errorText);
                throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
            }
            
            console.log('Parsing response as JSON...');
            const jsonData = await response.json();
            console.log('Parsed JSON data:', jsonData);
            return jsonData;
        } catch (error) {
            console.error('Request failed:', error);
            console.error('Error type:', error.constructor.name);
            console.error('Error message:', error.message);
            throw error;
        }
    }

    showNotification(message, type = 'info') {
        const container = document.getElementById('notificationContainer');
        if (!container) return;
        
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        container.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    // User profile methods
    async loadUserProfile() {
        try {
            const data = await this.makeRequest('/api/multi-agent/user-profile');
            
            if (data.success && data.user_profile) {
                this.updateUserProfileDisplay(data.user_profile);
            }
        } catch (error) {
            console.error('Failed to load user profile:', error);
        }
    }

    /**
     * 从用户上下文生成摘要信息
     * @param {Object} userContext - 用户上下文数据
     * @returns {string} 生成的用户摘要
     */
    generateUserSummaryFromContext(userContext) {
        if (!userContext) {
            return '暂无用户画像信息';
        }

        const totalConversations = userContext.total_conversations || 0;
        const learningPreferences = userContext.learning_preferences || [];
        const socraticScore = userContext.socratic_preference_score || 0;
        const avgSessionDuration = userContext.average_session_duration || 0;

        if (totalConversations === 0 && learningPreferences.length === 0) {
            return '暂无用户画像信息';
        }

        let summary = '<div class="generated-summary">';
        
        if (totalConversations > 0) {
            summary += `<p>📊 已进行 <strong>${totalConversations}</strong> 次对话`;
            if (avgSessionDuration > 0) {
                summary += `，平均会话时长 <strong>${avgSessionDuration.toFixed(1)}</strong> 分钟`;
            }
            summary += '</p>';
        }

        if (socraticScore > 0) {
            const preference = socraticScore > 0.7 ? '偏好' : socraticScore > 0.3 ? '适中' : '较少';
            summary += `<p>🤔 苏格拉底式引导偏好: <strong>${preference}</strong> (${(socraticScore * 100).toFixed(0)}%)</p>`;
        }

        if (learningPreferences.length > 0) {
            summary += `<p>📚 学习偏好: ${learningPreferences.map(pref => `<span class="preference-tag">${pref}</span>`).join(' ')}</p>`;
        }

        summary += '</div>';
        return summary;
    }

    updateUserProfileDisplay(profile) {
        // 顶部统计卡片已删除，无需更新统计数据
        
        // Update user profile summary
        const summaryElement = document.getElementById('profileSummary');
        const userContext = profile.user_context || {};
        const userSummary = userContext.user_summary || profile.user_summary;
        
        if (summaryElement) {
            if (userSummary && userSummary !== '暂无用户画像信息') {
                summaryElement.innerHTML = `
                    <div class="summary-content">${userSummary}</div>
                    <div class="profile-entities" id="profileEntities"></div>
                `;
                
                // Display user entity tags
                const entities = userContext.user_entities || profile.user_entities || [];
                const entitiesContainer = document.getElementById('profileEntities');
                if (entitiesContainer && entities.length > 0) {
                    entitiesContainer.innerHTML = entities.map(entity => 
                        `<span class="entity-tag">${entity}</span>`
                    ).join('');
                }
            } else {
                // 显示用户画像的基本信息，即使没有user_summary
                const totalConversations = userContext.total_conversations || 0;
                const learningPreferences = userContext.learning_preferences || [];
                const socraticScore = userContext.socratic_preference_score || 0;
                
                if (totalConversations > 0 || learningPreferences.length > 0) {
                    summaryElement.innerHTML = `
                        <div class="summary-content">
                            <div class="profile-stats">
                                <div class="stat-row">
                                    <span class="stat-label">💬 对话次数:</span>
                                    <span class="stat-value">${totalConversations}</span>
                                </div>
                                <div class="stat-row">
                                    <span class="stat-label">🤔 苏格拉底偏好:</span>
                                    <span class="stat-value">${(socraticScore * 100).toFixed(0)}%</span>
                                </div>
                                ${learningPreferences.length > 0 ? `
                                <div class="stat-row">
                                    <span class="stat-label">📚 学习偏好:</span>
                                    <span class="stat-value">${learningPreferences.length}项</span>
                                </div>` : ''}
                            </div>
                        </div>
                        <div class="profile-entities" id="profileEntities"></div>
                    `;
                } else {
                    summaryElement.innerHTML = `
                        <div class="summary-placeholder">
                            💭 开始对话后，我会逐步了解您的兴趣和背景
                        </div>
                    `;
                }
            }
        }
    }

    updateUserProfileFromResponse(responseData) {
        if (responseData.state_summary?.user_profile_data) {
            const profileData = responseData.state_summary.user_profile_data;
            this.updateUserProfileDisplay({
                graph_statistics: {
                    entity_count: profileData.user_context?.entity_count || 0,
                    relation_count: profileData.user_context?.relation_count || 0
                },
                user_context: profileData.user_context,
                user_summary: profileData.user_context?.user_summary
            });
        }
    }

    // 实现完整的用户画像功能
    async viewUserProfile() {
        try {
            const data = await this.makeRequest('/api/multi-agent/user-profile');
            if (data.success && data.user_profile) {
                this.showUserProfileModal(data.user_profile);
            } else {
                this.showNotification('获取用户画像失败', 'error');
            }
        } catch (error) {
            console.error('Failed to view user profile:', error);
            this.showNotification('获取用户画像失败', 'error');
        }
    }

    async exportUserProfile() {
        try {
            const data = await this.makeRequest('/api/multi-agent/user-profile');
            if (data.success && data.user_profile) {
                this.exportProfileData(data.user_profile);
            } else {
                this.showNotification('导出用户画像失败', 'error');
            }
        } catch (error) {
            console.error('Failed to export user profile:', error);
            this.showNotification('导出用户画像失败', 'error');
        }
    }

    async clearUserProfile() {
        if (!confirm('确定要清空用户画像吗？此操作不可撤销。')) {
            return;
        }
        
        try {
            // 调用后端API来清空用户画像
            const response = await this.makeRequest('/api/multi-agent/clear-user-profile', { 
                method: 'POST',
                body: JSON.stringify({ user_id: 'anonymous' })
            });
            
            if (response.success) {
                // 清空本地显示
                this.updateUserProfileDisplay({
                    graph_statistics: { entity_count: 0, relation_count: 0 },
                    user_context: { user_summary: '暂无用户画像信息' }
                });
                
                this.showNotification('用户画像已清空', 'success');
            } else {
                this.showNotification('清空用户画像失败', 'error');
            }
        } catch (error) {
            console.error('Failed to clear user profile:', error);
            this.showNotification('清空用户画像失败', 'error');
        }
    }

    async analyzeUserProfile() {
        try {
            const data = await this.makeRequest('/api/multi-agent/user-profile');
            if (data.success && data.user_profile) {
                this.showProfileAnalysis(data.user_profile);
            } else {
                this.showNotification('分析用户画像失败', 'error');
            }
        } catch (error) {
            console.error('Failed to analyze user profile:', error);
            this.showNotification('分析用户画像失败', 'error');
        }
    }



    // 辅助方法
    showUserProfileModal(profile) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content profile-modal">
                <div class="modal-header">
                    <h3>👤 用户画像详情</h3>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="profile-section">
                        <h4>📊 基础统计</h4>
                        <div class="stats-grid">
                            <div class="stat-item">
                                <span class="stat-label">实体数量</span>
                                <span class="stat-value">${profile.graph_statistics?.entity_count || 0}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">关系数量</span>
                                <span class="stat-value">${profile.graph_statistics?.relation_count || 0}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">画像完整度</span>
                                <span class="stat-value">${profile.profile_completeness ? (profile.profile_completeness * 100).toFixed(1) + '%' : '0%'}</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="profile-section">
                        <h4>👤 用户信息</h4>
                        <div class="user-summary">
                            ${profile.user_context?.user_summary || this.generateUserSummaryFromContext(profile.user_context)}
                        </div>
                    </div>
                    
                    ${this.renderUserEntities(profile)}
                    ${this.renderUserContext(profile)}
                    
                    <div class="profile-section">
                        <h4>🕸️ 知识图谱可视化</h4>
                        <div class="graph-container">
                            <div id="userProfileGraph" style="width: 100%; height: 400px; border: 1px solid #ddd; border-radius: 8px; background: #f9f9f9;"></div>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">关闭</button>
                    <button class="btn btn-primary" onclick="multiAgentInterface.exportUserProfile()">导出</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // 加载并显示图谱
        this.loadUserProfileGraph(modal);
        
        // 添加样式
        if (!document.getElementById('profile-modal-styles')) {
            const style = document.createElement('style');
            style.id = 'profile-modal-styles';
            style.textContent = `
                .modal-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.5);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    z-index: 1000;
                }
                .profile-modal, .analysis-modal, .charts-modal {
                    background: white;
                    border-radius: 12px;
                    max-width: 800px;
                    width: 90%;
                    max-height: 80vh;
                    overflow-y: auto;
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
                }
                .modal-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 20px;
                    border-bottom: 1px solid #eee;
                }
                .modal-close {
                    background: none;
                    border: none;
                    font-size: 24px;
                    cursor: pointer;
                    color: #666;
                }
                .modal-body {
                    padding: 20px;
                }
                .profile-section, .analysis-section {
                    margin-bottom: 24px;
                }
                .profile-section h4, .analysis-section h4 {
                    margin: 0 0 12px 0;
                    color: #333;
                    font-size: 16px;
                }
                .stats-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 16px;
                }
                .stat-item {
                    background: #f8f9fa;
                    padding: 16px;
                    border-radius: 8px;
                    text-align: center;
                }
                .stat-label {
                    display: block;
                    font-size: 12px;
                    color: #666;
                    margin-bottom: 4px;
                }
                .stat-value {
                    display: block;
                    font-size: 24px;
                    font-weight: bold;
                    color: #007bff;
                }
                .user-summary {
                    background: #f8f9fa;
                    padding: 16px;
                    border-radius: 8px;
                    line-height: 1.6;
                }
                .entities-container {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 8px;
                }
                .entity-tag {
                    background: #e3f2fd;
                    color: #1976d2;
                    padding: 4px 12px;
                    border-radius: 16px;
                    font-size: 12px;
                    border: 1px solid #bbdefb;
                }
                .context-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 12px;
                }
                .context-item {
                    background: #f8f9fa;
                    padding: 12px;
                    border-radius: 6px;
                    font-size: 14px;
                }
                .completeness-bar {
                    position: relative;
                    background: #e9ecef;
                    height: 24px;
                    border-radius: 12px;
                    overflow: hidden;
                    margin: 12px 0;
                }
                .completeness-fill {
                    background: linear-gradient(90deg, #28a745, #20c997);
                    height: 100%;
                    transition: width 0.3s ease;
                }
                .completeness-text {
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    color: #333;
                    font-weight: bold;
                    font-size: 12px;
                }
                .chart-container {
                    text-align: center;
                    margin: 20px 0;
                }
                .chart-legend {
                    display: flex;
                    justify-content: center;
                    gap: 20px;
                    margin-top: 16px;
                }
                .legend-item {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    font-size: 14px;
                }
                .legend-color {
                    width: 16px;
                    height: 16px;
                    border-radius: 4px;
                }
                .modal-footer {
                    padding: 20px;
                    border-top: 1px solid #eee;
                    display: flex;
                    justify-content: flex-end;
                    gap: 12px;
                }
                .btn {
                    padding: 8px 16px;
                    border: none;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 14px;
                }
                .btn-primary {
                    background: #007bff;
                    color: white;
                }
                .btn-secondary {
                    background: #6c757d;
                    color: white;
                }
                .analysis-section ul {
                    margin: 12px 0;
                    padding-left: 20px;
                }
                .analysis-section li {
                    margin-bottom: 8px;
                    line-height: 1.5;
                }
            `;
            document.head.appendChild(style);
        }
    }

    renderUserEntities(profile) {
        const entities = profile.user_context?.user_entities || [];
        if (entities.length === 0) return '';
        
        return `
            <div class="profile-section">
                <h4>🏷️ 用户实体标签</h4>
                <div class="entities-container">
                    ${entities.map(entity => `<span class="entity-tag">${entity}</span>`).join('')}
                </div>
            </div>
        `;
    }
    
    async loadUserProfileGraph(modal) {
        try {
            const data = await this.makeRequest('/api/multi-agent/user-profile-graph');
            if (data.success && data.graph) {
                this.renderUserProfileGraph(data.graph, modal);
            }
        } catch (error) {
            console.error('Failed to load user profile graph:', error);
            const graphContainer = modal.querySelector('#userProfileGraph');
            if (graphContainer) {
                graphContainer.textContent = '图谱加载失败';
                graphContainer.style.textAlign = 'center';
                graphContainer.style.padding = '20px';
                graphContainer.style.color = '#666';
            }
        }
    }
    
    renderUserProfileGraph(graphData, modal) {
        const graphContainer = modal.querySelector('#userProfileGraph');
        if (!graphContainer) return;
        
        // 使用简单的SVG绘制图谱
        const nodes = graphData.nodes || [];
        const edges = graphData.edges || [];
        
        if (nodes.length === 0) {
            graphContainer.textContent = '暂无图谱数据';
            graphContainer.style.textAlign = 'center';
            graphContainer.style.padding = '20px';
            graphContainer.style.color = '#666';
            return;
        }
        
        // 计算布局
        const centerX = 200;
        const centerY = 200;
        const radius = 150;
        
        // 为节点分配位置
        const nodePositions = {};
        nodes.forEach((node, index) => {
            const angle = (index / nodes.length) * 2 * Math.PI;
            nodePositions[node.id] = {
                x: centerX + radius * Math.cos(angle),
                y: centerY + radius * Math.sin(angle)
            };
        });
        
        // 创建SVG
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', '100%');
        svg.setAttribute('height', '100%');
        svg.setAttribute('viewBox', '0 0 400 400');
        
        // 绘制边
        edges.forEach(edge => {
            const sourcePos = nodePositions[edge.source];
            const targetPos = nodePositions[edge.target];
            
            if (sourcePos && targetPos) {
                const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                line.setAttribute('x1', sourcePos.x);
                line.setAttribute('y1', sourcePos.y);
                line.setAttribute('x2', targetPos.x);
                line.setAttribute('y2', targetPos.y);
                line.setAttribute('stroke', '#666');
                line.setAttribute('stroke-width', '2');
                svg.appendChild(line);
                
                // 添加关系标签
                const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                text.setAttribute('x', (sourcePos.x + targetPos.x) / 2);
                text.setAttribute('y', (sourcePos.y + targetPos.y) / 2);
                text.setAttribute('text-anchor', 'middle');
                text.setAttribute('font-size', '10');
                text.setAttribute('fill', '#333');
                text.textContent = edge.label;
                svg.appendChild(text);
            }
        });
        
        // 绘制节点
        nodes.forEach(node => {
            const pos = nodePositions[node.id];
            if (pos) {
                const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                circle.setAttribute('cx', pos.x);
                circle.setAttribute('cy', pos.y);
                circle.setAttribute('r', '15');
                circle.setAttribute('fill', '#4CAF50');
                circle.setAttribute('stroke', '#2E7D32');
                circle.setAttribute('stroke-width', '2');
                svg.appendChild(circle);
                
                // 添加节点标签
                const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                text.setAttribute('x', pos.x);
                text.setAttribute('y', pos.y + 25);
                text.setAttribute('text-anchor', 'middle');
                text.setAttribute('font-size', '12');
                text.setAttribute('fill', '#333');
                text.textContent = node.label;
                svg.appendChild(text);
            }
        });
        
        graphContainer.innerHTML = '';
        graphContainer.appendChild(svg);
    }

    renderUserContext(profile) {
        const context = profile.user_context;
        if (!context) return '';
        
        const contextItems = [];
        
        if (context.socratic_preference_score !== undefined) {
            contextItems.push(`苏格拉底式偏好: ${(context.socratic_preference_score * 100).toFixed(1)}%`);
        }
        if (context.learning_preference_score !== undefined) {
            contextItems.push(`学习偏好: ${(context.learning_preference_score * 100).toFixed(1)}%`);
        }
        if (context.knowledge_level) {
            contextItems.push(`知识水平: ${context.knowledge_level}`);
        }
        if (context.learning_style) {
            contextItems.push(`学习风格: ${context.learning_style}`);
        }
        
        if (contextItems.length === 0) return '';
        
        return `
            <div class="profile-section">
                <h4>⚙️ 用户偏好设置</h4>
                <div class="context-grid">
                    ${contextItems.map(item => `<div class="context-item">${item}</div>`).join('')}
                </div>
            </div>
        `;
    }

    exportProfileData(profile) {
        const dataStr = JSON.stringify(profile, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = `user_profile_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        
        this.showNotification('用户画像已导出', 'success');
    }

    showProfileAnalysis(profile) {
        const analysis = this.generateProfileAnalysis(profile);
        
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content analysis-modal">
                <div class="modal-header">
                    <h3>🔍 用户画像分析</h3>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
                </div>
                <div class="modal-body">
                    ${analysis}
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">关闭</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }

    generateProfileAnalysis(profile) {
        const entityCount = profile.graph_statistics?.entity_count || 0;
        const relationCount = profile.graph_statistics?.relation_count || 0;
        const completeness = profile.profile_completeness || 0;
        
        let analysis = `
            <div class="analysis-section">
                <h4>📈 画像完整度分析</h4>
                <div class="completeness-bar">
                    <div class="completeness-fill" style="width: ${completeness * 100}%"></div>
                    <span class="completeness-text">${(completeness * 100).toFixed(1)}%</span>
                </div>
                <p>${this.getCompletenessDescription(completeness)}</p>
            </div>
            
            <div class="analysis-section">
                <h4>🧠 画像丰富度</h4>
                <p>${entityCount > 0 ? 
                    `您的用户画像包含 ${entityCount} 个实体和 ${relationCount} 个关系，知识图谱较为丰富。` : 
                    '您的用户画像目前较为简单，建议多进行学习互动以丰富您的知识图谱。'
                }</p>
            </div>
        `;
        

        
        const context = profile.user_context;
        if (context) {
            analysis += `
                <div class="analysis-section">
                    <h4>💡 个性化建议</h4>
                    <ul>
                        ${this.generatePersonalizedSuggestions(context)}
                    </ul>
                </div>
            `;
        }
        
        return analysis;
    }

    getCompletenessDescription(completeness) {
        if (completeness >= 0.8) return '您的用户画像非常完整，系统能够提供高度个性化的服务。';
        if (completeness >= 0.6) return '您的用户画像较为完整，系统能够提供良好的个性化服务。';
        if (completeness >= 0.4) return '您的用户画像有一定基础，建议继续交互以提升个性化体验。';
        return '您的用户画像还在构建中，建议多与系统交互以完善画像信息。';
    }

    generatePersonalizedSuggestions(context) {
        const suggestions = [];
        
        if (context.socratic_preference_score > 0.7) {
            suggestions.push('<li>您偏好苏格拉底式教学，系统会更多使用引导性问题来帮助您学习。</li>');
        }
        
        if (context.learning_preference_score > 0.7) {
            suggestions.push('<li>您有明确的学习偏好，系统会据此调整教学方式。</li>');
        }
        
        if (context.knowledge_level === 'beginner') {
            suggestions.push('<li>作为初学者，建议从基础概念开始，逐步深入。</li>');
        } else if (context.knowledge_level === 'advanced') {
            suggestions.push('<li>作为高级学习者，系统会提供更深入的分析和挑战性内容。</li>');
        }
        
        if (suggestions.length === 0) {
            suggestions.push('<li>继续与系统交互，系统会更好地了解您的学习需求。</li>');
        }
        
        return suggestions.join('');
    }

    // 导航到用户画像页面
    navigateToUserProfile() {
        window.location.href = '/static/user_profile.html';
    }

    // 切换边栏显示/隐藏
    toggleSidebar() {
        const sidebar = document.getElementById('collapsibleSidebar');
        const toggleButton = document.getElementById('sidebarToggle');
        const mainContent = document.querySelector('.main-content');
        const overlay = document.getElementById('sidebarOverlay');
        
        if (sidebar && toggleButton && mainContent) {
            const isOpen = sidebar.classList.contains('open');
            
            if (isOpen) {
                this.closeSidebar();
            } else {
                this.openSidebar();
            }
        }
    }

    // 打开边栏
    openSidebar() {
        console.log('=== 打开边栏方法被调用 ===');
        const sidebar = document.getElementById('collapsibleSidebar');
        const toggleButton = document.getElementById('sidebarToggle');
        const mainContent = document.querySelector('.main-content');
        const overlay = document.getElementById('sidebarOverlay');
        
        console.log('边栏元素:', sidebar);
        console.log('切换按钮:', toggleButton);
        console.log('主内容区:', mainContent);
        console.log('遮罩层:', overlay);
        
        if (sidebar) {
            sidebar.classList.add('open');
            sidebar.classList.remove('closed');
            console.log('已添加open类到边栏，移除closed类');
        }
        if (toggleButton) {
            toggleButton.classList.add('active');
            console.log('已添加active类到切换按钮');
        }
        if (mainContent) {
            mainContent.classList.add('sidebar-open');
            console.log('已添加sidebar-open类到主内容区');
        }
        if (overlay) {
            overlay.classList.add('active');
            console.log('已添加active类到遮罩层');
        }
        
        localStorage.setItem('sidebarOpen', 'true');
        console.log('已保存边栏状态到localStorage');
    }

    // 关闭边栏
    closeSidebar() {
        console.log('=== 关闭边栏方法被调用 ===');
        const sidebar = document.getElementById('collapsibleSidebar');
        const toggleButton = document.getElementById('sidebarToggle');
        const mainContent = document.querySelector('.main-content');
        const overlay = document.getElementById('sidebarOverlay');
        
        if (sidebar) {
            sidebar.classList.remove('open');
            sidebar.classList.add('closed');
            console.log('已添加closed类到边栏');
        }
        if (toggleButton) {
            toggleButton.classList.remove('active');
            console.log('已移除active类从切换按钮');
        }
        if (mainContent) {
            mainContent.classList.remove('sidebar-open');
            console.log('已移除sidebar-open类从主内容区');
        }
        if (overlay) {
            overlay.classList.remove('active');
            console.log('已移除active类从遮罩层');
        }
        
        localStorage.setItem('sidebarOpen', 'false');
        console.log('已保存边栏关闭状态到localStorage');
    }

    // 初始化边栏状态
    initializeSidebarState() {
        console.log('=== 初始化边栏状态 ===');
        
        // 临时清除localStorage中的边栏状态，强制打开边栏
        localStorage.removeItem('sidebarOpen');
        console.log('已清除localStorage中的sidebarOpen');
        
        const sidebarOpen = localStorage.getItem('sidebarOpen');
        console.log('localStorage中的sidebarOpen值:', sidebarOpen);
        
        const sidebar = document.getElementById('collapsibleSidebar');
        console.log('边栏元素:', sidebar);
        
        // 强制打开边栏
        console.log('强制打开边栏');
        this.openSidebar();
        
        // 检查边栏状态
        setTimeout(() => {
            const isOpen = sidebar?.classList.contains('open');
            console.log('边栏是否打开:', isOpen);
            console.log('边栏类名:', sidebar?.className);
            
            // 检查按钮是否可见
            const newBtn = document.getElementById('newConversationBtn');
            if (newBtn) {
                const rect = newBtn.getBoundingClientRect();
                console.log('新建对话按钮位置:', rect);
                console.log('新建对话按钮是否可见:', rect.width > 0 && rect.height > 0);
            }
        }, 100);
    }



    // 保存聊天状态到localStorage
    saveChatState() {
        try {
            const chatState = {
                isChatMode: true,
                sessionId: this.currentSessionId,
                messageHistory: this.messageHistory,
                timestamp: Date.now()
            };
            localStorage.setItem('chatState', JSON.stringify(chatState));
            console.log('Chat state saved:', chatState);
        } catch (error) {
            console.error('Failed to save chat state:', error);
        }
    }

    // 恢复聊天状态
    restoreChatState() {
        try {
            // 检查URL参数，判断是否从用户画像返回
            const urlParams = new URLSearchParams(window.location.search);
            const fromProfile = urlParams.get('from') === 'profile';
            
            console.log('Checking chat state restoration...');
            console.log('From profile:', fromProfile);
            
            const savedState = localStorage.getItem('chatState');
            if (savedState) {
                const chatState = JSON.parse(savedState);
                console.log('Found saved chat state:', chatState);
                
                // 检查状态是否过期（24小时）
                const isExpired = Date.now() - chatState.timestamp > 24 * 60 * 60 * 1000;
                console.log('State expired:', isExpired);
                
                // 只有在从用户画像返回时才自动恢复聊天状态
                if (fromProfile && !isExpired && chatState.messageHistory && chatState.messageHistory.length > 0) {
                    console.log('Restoring chat interface from profile...');
                    
                    // 恢复会话ID
                    if (chatState.sessionId) {
                        this.currentSessionId = chatState.sessionId;
                        const sessionIdElement = document.getElementById('sessionId');
                        if (sessionIdElement) {
                            sessionIdElement.textContent = chatState.sessionId.substring(0, 8) + '...';
                        }
                    }
                    
                    // 恢复消息历史
                    this.messageHistory = chatState.messageHistory;
                    
                    // 切换到聊天界面（不添加欢迎消息）
                    this.switchToChatInterfaceWithoutWelcome();
                    
                    // 恢复消息显示
                    setTimeout(() => {
                        this.restoreMessages();
                    }, 600);
                    
                    // 清除URL参数
                    const newUrl = window.location.pathname;
                    window.history.replaceState({}, document.title, newUrl);
                } else {
                    // 其他情况下显示欢迎界面
                    console.log('Showing welcome interface...');
                    this.showWelcomeInterface();
                    
                    // 如果状态过期，清除它
                    if (isExpired) {
                        console.log('Chat state expired, clearing...');
                        localStorage.removeItem('chatState');
                    }
                }
            } else {
                // 没有保存的状态，显示欢迎界面
                console.log('No saved state, showing welcome interface...');
                this.showWelcomeInterface();
            }
        } catch (error) {
            console.error('Failed to restore chat state:', error);
            localStorage.removeItem('chatState');
            this.showWelcomeInterface();
        }
    }

    // 显示欢迎界面
    showWelcomeInterface() {
        const welcomeScreen = document.getElementById('welcomeScreen');
        const chatContainer = document.getElementById('chatContainer');
        
        if (welcomeScreen && chatContainer) {
            console.log('Displaying welcome screen...');
            welcomeScreen.style.display = 'flex';
            chatContainer.style.display = 'none';
        }
    }

    // 切换到聊天界面（不添加欢迎消息）
    switchToChatInterfaceWithoutWelcome() {
        const welcomeScreen = document.getElementById('welcomeScreen');
        const chatContainer = document.getElementById('chatContainer');
        
        if (welcomeScreen && chatContainer) {
            // 直接切换界面，不添加欢迎消息
            welcomeScreen.style.display = 'none';
            chatContainer.style.display = 'flex';
            chatContainer.style.opacity = '1';
            chatContainer.style.transform = 'translateY(0)';
        }
    }

    // 恢复消息显示
    restoreMessages() {
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages && this.messageHistory.length > 0) {
            // 清空现有消息
            chatMessages.innerHTML = '';
            
            // 重新添加所有消息
            this.messageHistory.forEach(msg => {
                this.addMessage(msg.content, msg.type, false); // false表示不保存到历史记录
            });
            
            // 滚动到底部
            setTimeout(() => {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }, 100);
        }
    }

    // 清除聊天状态
    clearChatState() {
        localStorage.removeItem('chatState');
        console.log('Chat state cleared');
    }



    // 历史对话管理方法
    
    // 创建新对话
    createNewConversation() {
        console.log('=== createNewConversation 方法被调用 ===');
        console.log('当前消息历史长度:', this.messageHistory.length);
        console.log('当前会话ID:', this.currentSessionId);
        
        try {
            let savedTitle = '';
            
            // 保存当前对话到历史记录
            if (this.messageHistory.length > 0) {
                console.log('保存当前对话到历史记录...');
                
                // 获取当前对话的标题用于通知
                const firstUserMessage = this.messageHistory.find(msg => msg.type === 'user');
                if (firstUserMessage && firstUserMessage.content) {
                    const cleanContent = firstUserMessage.content.trim().replace(/\s+/g, ' ');
                    savedTitle = cleanContent.length > 5 ? cleanContent.substring(0, 5) : cleanContent;
                }
                
                this.saveCurrentConversation();
                
                // 显示保存成功的通知
                if (savedTitle) {
                    this.showNotification(`对话"${savedTitle}"已保存到历史记录`, 'success');
                } else {
                    this.showNotification('当前对话已保存到历史记录', 'success');
                }
            }
            
            // 重置当前对话状态
            console.log('重置对话状态...');
            this.resetConversation();
            
            // 关闭历史对话模态框（如果打开）
            console.log('关闭历史对话模态框...');
            this.closeConversationHistoryModal();
            
            // 切换到聊天界面（不显示欢迎界面）
            console.log('切换到聊天界面...');
            this.switchToChatInterfaceWithoutWelcome();
            
            // 更新当前对话信息
            console.log('更新当前对话信息...');
            this.updateCurrentConversationInfo();
            
            // 刷新侧边栏对话列表
            this.refreshSidebarConversationList();
            
            // 如果没有保存对话，显示新建对话的通知
            if (this.messageHistory.length === 0 && !savedTitle) {
                setTimeout(() => {
                    this.showNotification('已创建新对话，开始您的学习之旅吧！', 'success');
                }, 500);
            }
            
            console.log('=== createNewConversation 方法执行完成 ===');
        } catch (error) {
            console.error('createNewConversation 方法执行出错:', error);
            console.error('错误堆栈:', error.stack);
            this.showNotification('创建新对话失败，请重试', 'error');
        }
    }
    
    // 保存当前对话到历史记录
    saveCurrentConversation() {
        if (this.messageHistory.length === 0) return;
        
        try {
            const conversations = this.getConversationHistory();
            const conversationId = this.currentSessionId || this.generateSessionId();
            
            // 获取对话标题（使用第一条用户消息的前5个字符或默认标题）
            const firstUserMessage = this.messageHistory.find(msg => msg.type === 'user');
            let title = '新对话';
            
            if (firstUserMessage && firstUserMessage.content) {
                // 移除多余的空格和换行符
                const cleanContent = firstUserMessage.content.trim().replace(/\s+/g, ' ');
                if (cleanContent.length > 0) {
                    // 取前5个字符，如果不足5个字符则取全部
                    title = cleanContent.length > 5 ? cleanContent.substring(0, 5) : cleanContent;
                }
            }
            
            const conversation = {
                id: conversationId,
                title: title,
                messages: [...this.messageHistory],
                timestamp: Date.now(),
                messageCount: this.messageHistory.length,
                lastMessage: this.messageHistory[this.messageHistory.length - 1]?.content || ''
            };
            
            // 检查是否已存在相同ID的对话，如果存在则更新
            const existingIndex = conversations.findIndex(conv => conv.id === conversationId);
            if (existingIndex !== -1) {
                conversations[existingIndex] = conversation;
            } else {
                conversations.unshift(conversation); // 添加到开头
            }
            
            // 限制历史记录数量（最多保存50个对话）
            if (conversations.length > 50) {
                conversations.splice(50);
            }
            
            localStorage.setItem('conversationHistory', JSON.stringify(conversations));
            console.log('Conversation saved:', conversation);
            
            // 刷新侧边栏对话列表
            this.refreshSidebarConversationList();
        } catch (error) {
            console.error('Failed to save conversation:', error);
        }
    }
    
    // 获取对话历史记录
    getConversationHistory() {
        try {
            const history = localStorage.getItem('conversationHistory');
            return history ? JSON.parse(history) : [];
        } catch (error) {
            console.error('Failed to get conversation history:', error);
            return [];
        }
    }
    
    // 重置对话状态
    resetConversation() {
        this.messageHistory = [];
        this.currentSessionId = this.generateSessionId();
        this.isProcessing = false;
        this.currentWorkflowStep = 0;
        
        // 清空聊天界面
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.innerHTML = '';
        }
        
        // 重置进度条
        this.updateLearningProgress(0, 6);
        
        // 清除聊天状态
        this.clearChatState();
        
        // 更新会话ID显示
        const sessionIdElement = document.getElementById('sessionId');
        if (sessionIdElement) {
            sessionIdElement.textContent = this.currentSessionId.substring(0, 8) + '...';
        }
    }
    
    // 显示对话历史模态框
    showConversationHistory() {
        const modal = document.getElementById('conversationHistoryModal');
        if (modal) {
            modal.style.display = 'block';
            this.refreshConversationList();
        }
    }
    
    // 关闭对话历史模态框
    closeConversationHistoryModal() {
        const modal = document.getElementById('conversationHistoryModal');
        if (modal) {
            modal.style.display = 'none';
        }
    }
    
    // 刷新对话列表
    refreshConversationList() {
        const listContainer = document.getElementById('conversationList');
        if (!listContainer) return;
        
        const conversations = this.getConversationHistory();
        
        if (conversations.length === 0) {
            listContainer.innerHTML = `
                <div class="empty-state">
                    <p>暂无历史对话</p>
                    <p>开始一个新对话来创建历史记录</p>
                </div>
            `;
            return;
        }
        
        listContainer.innerHTML = conversations.map(conv => {
            const date = new Date(conv.timestamp);
            const timeStr = this.formatTime(date);
            
            // 获取更好的预览内容
            let preview = '';
            if (conv.lastMessage) {
                preview = conv.lastMessage.length > 60 ? 
                    conv.lastMessage.substring(0, 60) + '...' : 
                    conv.lastMessage;
            } else {
                // 如果没有最后消息，尝试从第一条用户消息获取
                const firstUserMsg = conv.messages?.find(msg => msg.type === 'user');
                if (firstUserMsg) {
                    preview = firstUserMsg.content.length > 60 ? 
                        firstUserMsg.content.substring(0, 60) + '...' : 
                        firstUserMsg.content;
                } else {
                    preview = '暂无内容';
                }
            }
            
            return `
                <div class="conversation-item" data-id="${conv.id}">
                    <div class="conversation-header">
                        <h4 class="conversation-title" title="${conv.title}">${conv.title}</h4>
                        <div class="conversation-actions">
                            <button class="action-btn load-btn" onclick="multiAgentInterface.loadConversation('${conv.id}')" title="加载对话">
                                📂 加载
                            </button>
                            <button class="action-btn delete-btn" onclick="multiAgentInterface.deleteConversation('${conv.id}')" title="删除对话">
                                🗑️ 删除
                            </button>
                        </div>
                    </div>
                    <div class="conversation-meta">
                        <span class="conversation-id">ID: ${conv.id.substring(0, 8)}...</span>
                        <span class="conversation-time">${timeStr}</span>
                    </div>
                    <div class="conversation-preview" title="${preview}">${preview}</div>
                    <div class="conversation-stats">
                        <span class="message-count">${conv.messageCount} 条消息</span>
                        <span class="conversation-status">📝 历史对话</span>
                    </div>
                </div>
            `;
        }).join('');
    }

    // 刷新侧边栏对话列表
    refreshSidebarConversationList() {
        const listContainer = document.getElementById('sidebarConversationList');
        if (!listContainer) return;
        
        const conversations = this.getConversationHistory();
        
        if (conversations.length === 0) {
            listContainer.innerHTML = `
                <div class="empty-state" style="text-align: center; color: var(--text-muted); font-size: 0.8rem; padding: 10px;">
                    暂无历史对话
                </div>
            `;
            return;
        }
        
        listContainer.innerHTML = conversations.map(conv => {
            const date = new Date(conv.timestamp);
            const timeStr = this.formatTime(date);
            
            // 获取对话预览（第一条用户消息的前30个字符）
            let preview = '';
            if (conv.lastMessage) {
                preview = conv.lastMessage.length > 30 ? 
                    conv.lastMessage.substring(0, 30) + '...' : 
                    conv.lastMessage;
            } else {
                const firstUserMsg = conv.messages?.find(msg => msg.type === 'user');
                if (firstUserMsg) {
                    preview = firstUserMsg.content.length > 30 ? 
                        firstUserMsg.content.substring(0, 30) + '...' : 
                        firstUserMsg.content;
                } else {
                    preview = '暂无内容';
                }
            }
            
            // 检查是否为当前对话
            const isActive = conv.id === this.currentSessionId ? 'active' : '';
            
            return `
                <div class="sidebar-conversation-item ${isActive}" data-id="${conv.id}" onclick="multiAgentInterface.loadConversation('${conv.id}')">
                    <div class="sidebar-conversation-title">${conv.title}</div>
                    <div class="sidebar-conversation-meta">
                        <span>${timeStr}</span>
                        <span>${conv.messageCount} 条</span>
                    </div>
                    <div class="sidebar-conversation-preview">${preview}</div>
                    <div class="sidebar-conversation-actions">
                        <button class="sidebar-action-btn sidebar-delete-btn" onclick="event.stopPropagation(); multiAgentInterface.deleteConversation('${conv.id}')" title="删除对话">
                            🗑️ 删除
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }
    
    // 加载指定对话
    loadConversation(conversationId) {
        try {
            const conversations = this.getConversationHistory();
            const conversation = conversations.find(conv => conv.id === conversationId);
            
            if (!conversation) {
                this.showNotification('对话不存在', 'error');
                return;
            }
            
            // 保存当前对话（如果有内容）
            if (this.messageHistory.length > 0) {
                console.log('保存当前对话...');
                this.saveCurrentConversation();
            }
            
            // 加载选中的对话
            console.log('加载历史对话:', conversation.title);
            this.messageHistory = [...conversation.messages];
            this.currentSessionId = conversation.id;
            
            // 更新会话ID显示
            const sessionIdElement = document.getElementById('sessionId');
            if (sessionIdElement) {
                sessionIdElement.textContent = this.currentSessionId.substring(0, 8) + '...';
            }
            
            // 切换到聊天界面
            this.switchToChatInterfaceWithoutWelcome();
            
            // 恢复消息显示
            setTimeout(() => {
                this.restoreMessages();
                
                // 滚动到聊天区域底部
                const chatMessages = document.getElementById('chatMessages');
                if (chatMessages) {
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                }
            }, 100);
            
            // 更新当前对话信息
            this.updateCurrentConversationInfo();
            
            // 刷新侧边栏对话列表（更新活跃状态）
            this.refreshSidebarConversationList();
            
            // 关闭模态框
            this.closeConversationHistoryModal();
            
            // 显示加载成功的通知
            this.showNotification(`已加载对话"${conversation.title}"`, 'success');
            
            console.log('对话加载完成，消息数量:', this.messageHistory.length);
        } catch (error) {
            console.error('Failed to load conversation:', error);
            this.showNotification('加载对话失败，请重试', 'error');
        }
    }
    
    // 删除指定对话
    deleteConversation(conversationId) {
        if (!confirm('确定要删除这个对话吗？此操作无法撤销。')) {
            return;
        }
        
        try {
            const conversations = this.getConversationHistory();
            const filteredConversations = conversations.filter(conv => conv.id !== conversationId);
            
            localStorage.setItem('conversationHistory', JSON.stringify(filteredConversations));
            this.refreshConversationList();
            this.refreshSidebarConversationList();
            this.showNotification('对话已删除', 'success');
        } catch (error) {
            console.error('Failed to delete conversation:', error);
            this.showNotification('删除对话失败', 'error');
        }
    }
    
    // 更新当前对话信息显示
    updateCurrentConversationInfo() {
        // 只更新会话ID显示，因为当前对话信息区域已被移除
        const sessionIdElement = document.getElementById('sessionId');
        if (sessionIdElement) {
            sessionIdElement.textContent = this.currentSessionId.substring(0, 8) + '...';
        }
    }
    
    // 格式化时间显示
    formatTime(date) {
        const now = new Date();
        const diff = now - date;
        
        if (diff < 60000) { // 1分钟内
            return '刚刚';
        } else if (diff < 3600000) { // 1小时内
            return Math.floor(diff / 60000) + '分钟前';
        } else if (diff < 86400000) { // 24小时内
            return Math.floor(diff / 3600000) + '小时前';
        } else if (diff < 604800000) { // 7天内
            return Math.floor(diff / 86400000) + '天前';
        } else {
            return date.toLocaleDateString('zh-CN');
        }
    }

    // Cleanup method
    destroy() {
        if (this.healthCheckInterval) {
            clearInterval(this.healthCheckInterval);
        }
        if (this.notificationTimeout) {
            clearTimeout(this.notificationTimeout);
        }
    }
}

// Initialize the interface when DOM is loaded
let multiAgentInterface;

document.addEventListener('DOMContentLoaded', function() {
    console.log('=== DOM 内容已加载 ===');
    console.log('开始初始化 MultiAgentInterface...');
    
    try {
        multiAgentInterface = new MultiAgentInterface();
        console.log('MultiAgentInterface 初始化成功');
        console.log('multiAgentInterface 对象:', multiAgentInterface);
    } catch (error) {
        console.error('MultiAgentInterface 初始化失败:', error);
        console.error('错误堆栈:', error.stack);
    }
    
    // 检查URL参数中是否有初始问题
    const urlParams = new URLSearchParams(window.location.search);
    const initialQuestion = urlParams.get('question');
    
    if (initialQuestion) {
        // 等待界面完全加载后自动填入问题到欢迎界面
        setTimeout(() => {
            const welcomeInput = document.getElementById('welcomeMessageInput');
            if (welcomeInput) {
                welcomeInput.value = decodeURIComponent(initialQuestion);
                // 可选：自动聚焦到输入框
                welcomeInput.focus();
                console.log('Initial question loaded from URL:', initialQuestion);
            }
        }, 500);
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (multiAgentInterface) {
        multiAgentInterface.destroy();
    }
});