/**
 * Multi-Agent Learning Assistant Interface
 * Optimized JavaScript implementation
 */

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
        this.setupEventListeners();
        this.initializeUI();
        this.checkSystemHealth();
        this.loadUserProfile();
        this.startHealthCheck();
        
        // 确保用户画像数据正确加载
        setTimeout(() => {
            this.loadUserProfile();
        }, 1000);
    }

    setupEventListeners() {
        // Message input events
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        
        messageInput?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        sendButton?.addEventListener('click', () => this.sendMessage());

        // Button events
        document.getElementById('clearChatBtn')?.addEventListener('click', () => this.clearChat());
        document.getElementById('refreshStatusBtn')?.addEventListener('click', () => this.refreshStatus());
        document.getElementById('downloadChatBtn')?.addEventListener('click', () => this.downloadChat());

        // User profile buttons
        document.getElementById('viewProfileBtn')?.addEventListener('click', () => this.viewUserProfile());
        document.getElementById('exportProfileBtn')?.addEventListener('click', () => this.exportUserProfile());
        document.getElementById('clearProfileBtn')?.addEventListener('click', () => this.clearUserProfile());
        document.getElementById('analyzeProfileBtn')?.addEventListener('click', () => this.analyzeUserProfile());
        document.getElementById('chartProfileBtn')?.addEventListener('click', () => this.showUserProfileChart());

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));

        // Mouse events for enhanced UX
        document.addEventListener('mouseover', (e) => this.handleMouseEvents(e, 'over'));
        document.addEventListener('mouseout', (e) => this.handleMouseEvents(e, 'out'));
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

    async sendMessage() {
        const input = document.getElementById('messageInput');
        const message = input?.value?.trim();
        
        if (!message || this.isProcessing) return;
        
        // Add user message to interface
        this.addMessage(message, 'user');
        input.value = '';
        
        // Set processing state
        this.setProcessing(true);
        
        try {
            // Send query request
            const response = await this.makeRequest('/api/multi-agent/query', {
                method: 'POST',
                body: JSON.stringify({
                    query: message,
                    session_id: this.currentSessionId
                })
            });
            
            if (response.success) {
                // Update session ID
                if (!this.currentSessionId) {
                    this.currentSessionId = response.session_id;
                    const sessionIdElement = document.getElementById('sessionId');
                    if (sessionIdElement) {
                        sessionIdElement.textContent = response.session_id.substring(0, 8) + '...';
                    }
                }
                
                // Handle response
                if (response.socratic_question) {
                    this.addSocraticQuestion(response.socratic_question);
                } else {
                    this.addMessage(response.final_response, 'assistant');
                }
                
                // Update workflow steps
                this.updateWorkflowSteps(response.steps_completed);
                
                // Update user profile display
                this.updateUserProfileFromResponse(response);
                
            } else {
                this.addMessage('抱歉，处理您的请求时出现了错误：' + (response.error || '未知错误'), 'system');
            }
            
        } catch (error) {
            console.error('Send message failed:', error);
            this.addMessage('网络错误，请检查连接后重试。', 'system');
        } finally {
            this.setProcessing(false);
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
    }

    addMessage(content, type) {
        const messagesContainer = document.getElementById('chatMessages');
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
        
        this.addMessageToContainer(messageDiv, messagesContainer);
        
        // Save to history
        this.messageHistory.push({
            content: content,
            type: type,
            timestamp: timestamp
        });
    }

    addMessageToContainer(messageDiv, container) {
        // Set initial opacity to 0
        messageDiv.style.opacity = '0';
        messageDiv.style.transform = 'translateY(10px)';
        
        container.appendChild(messageDiv);
        
        // Trigger animation
        setTimeout(() => {
            messageDiv.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            messageDiv.style.opacity = '1';
            messageDiv.style.transform = 'translateY(0)';
        }, 50);
        
        // Smooth scroll to bottom
        setTimeout(() => {
            container.scrollTo({
                top: container.scrollHeight,
                behavior: 'smooth'
            });
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
        if (!confirm('确定要清空对话记录吗？')) {
            return;
        }
        
        const chatMessages = document.getElementById('chatMessages');
        
        // Add fade out effect
        chatMessages.style.transition = 'opacity 0.3s ease';
        chatMessages.style.opacity = '0';
        
        setTimeout(() => {
            chatMessages.innerHTML = 
                `<div class="message system">
                    🎓 对话已清空，请输入新的问题开始学习。
                    <div class="learning-progress">
                        <div class="learning-progress-bar" id="learningProgress"></div>
                    </div>
                </div>`;
            
            // Fade in effect
            chatMessages.style.opacity = '1';
            
            this.messageHistory = [];
            this.currentSessionId = null;
            const sessionIdElement = document.getElementById('sessionId');
            if (sessionIdElement) {
                sessionIdElement.textContent = '未开始';
            }
            
            // Reset workflow steps
            const steps = document.querySelectorAll('.workflow-step');
            steps.forEach(step => {
                step.classList.remove('active', 'completed');
            });
            
            // Reset learning progress bar
            this.updateLearningProgress(0, 6);
        }, 300);
    }

    async refreshStatus() {
        await this.checkSystemHealth();
        if (this.currentSessionId) {
            try {
                const sessionData = await this.makeRequest(`/api/multi-agent/session/${this.currentSessionId}`);
                if (sessionData.exists) {
                    console.log('Session status:', sessionData);
                }
            } catch (error) {
                console.error('Failed to refresh session status:', error);
            }
        }
    }

    downloadChat() {
        if (this.messageHistory.length === 0) {
            this.showNotification('没有对话记录可以导出。', 'warning');
            return;
        }
        
        const chatData = {
            session_id: this.currentSessionId,
            export_time: new Date().toISOString(),
            messages: this.messageHistory
        };
        
        const dataStr = JSON.stringify(chatData, null, 2);
        const dataBlob = new Blob([dataStr], {type: 'application/json'});
        
        const link = document.createElement('a');
        link.href = URL.createObjectURL(dataBlob);
        link.download = `chat_export_${new Date().toISOString().split('T')[0]}.json`;
        link.click();
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

    async makeRequest(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json'
            }
        };
        
        const finalOptions = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, finalOptions);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Request failed:', error);
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
            console.log('User profile data loaded:', data); // 添加调试日志
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
        console.log('Updating user profile display:', profile); // 添加调试日志
        
        // Update statistics
        const entityCount = profile.graph_statistics?.entity_count || 0;
        const relationCount = profile.graph_statistics?.relation_count || 0;
        
        console.log('Entity count:', entityCount, 'Relation count:', relationCount); // 添加调试日志
        
        const entityCountElement = document.getElementById('profileEntityCount');
        const relationCountElement = document.getElementById('profileRelationCount');
        
        console.log('Entity count element:', entityCountElement); // 添加调试日志
        console.log('Relation count element:', relationCountElement); // 添加调试日志
        
        if (entityCountElement) {
            entityCountElement.textContent = entityCount;
            console.log('Updated entity count to:', entityCount); // 添加调试日志
        }
        if (relationCountElement) {
            relationCountElement.textContent = relationCount;
            console.log('Updated relation count to:', relationCount); // 添加调试日志
        }
        
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
                body: JSON.stringify({ user_id: 'default_user' })
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

    async showUserProfileChart() {
        try {
            const data = await this.makeRequest('/api/multi-agent/user-profile');
            if (data.success && data.user_profile) {
                this.showProfileCharts(data.user_profile);
            } else {
                this.showNotification('显示用户画像图表失败', 'error');
            }
        } catch (error) {
            console.error('Failed to show user profile charts:', error);
            this.showNotification('显示用户画像图表失败', 'error');
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
                graphContainer.innerHTML = '<div style="text-align: center; padding: 20px; color: #666;">图谱加载失败</div>';
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
            graphContainer.innerHTML = '<div style="text-align: center; padding: 20px; color: #666;">暂无图谱数据</div>';
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
        `;
        
        if (entityCount > 0) {
            analysis += `
                <div class="analysis-section">
                    <h4>🎯 画像丰富度</h4>
                    <p>您的用户画像包含 ${entityCount} 个实体和 ${relationCount} 个关系，这表明系统对您有较好的了解。</p>
                </div>
            `;
        } else {
            analysis += `
                <div class="analysis-section">
                    <h4>🎯 画像丰富度</h4>
                    <p>您的用户画像目前较为简单，建议多与系统交互以丰富画像信息。</p>
                </div>
            `;
        }
        
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

    showProfileCharts(profile) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content charts-modal">
                <div class="modal-header">
                    <h3>📊 用户画像统计图表</h3>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="chart-container">
                        <canvas id="profileChart" width="400" height="300"></canvas>
                    </div>
                    <div class="chart-legend">
                        <div class="legend-item">
                            <span class="legend-color" style="background: #007bff;"></span>
                            <span>实体数量</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-color" style="background: #28a745;"></span>
                            <span>关系数量</span>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">关闭</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // 简单的图表绘制（使用Canvas）
        setTimeout(() => {
            this.drawProfileChart(profile);
        }, 100);
    }

    drawProfileChart(profile) {
        const canvas = document.getElementById('profileChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        const entityCount = profile.graph_statistics?.entity_count || 0;
        const relationCount = profile.graph_statistics?.relation_count || 0;
        
        // 清空画布
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // 绘制柱状图
        const barWidth = 60;
        const barSpacing = 40;
        const startX = 50;
        const maxHeight = 200;
        const maxValue = Math.max(entityCount, relationCount, 1);
        
        // 实体数量柱状图
        const entityHeight = (entityCount / maxValue) * maxHeight;
        ctx.fillStyle = '#007bff';
        ctx.fillRect(startX, canvas.height - 50 - entityHeight, barWidth, entityHeight);
        
        // 关系数量柱状图
        const relationHeight = (relationCount / maxValue) * maxHeight;
        ctx.fillStyle = '#28a745';
        ctx.fillRect(startX + barWidth + barSpacing, canvas.height - 50 - relationHeight, barWidth, relationHeight);
        
        // 绘制标签
        ctx.fillStyle = '#333';
        ctx.font = '14px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('实体', startX + barWidth/2, canvas.height - 20);
        ctx.fillText('关系', startX + barWidth + barSpacing + barWidth/2, canvas.height - 20);
        
        // 绘制数值
        ctx.fillText(entityCount.toString(), startX + barWidth/2, canvas.height - 50 - entityHeight - 10);
        ctx.fillText(relationCount.toString(), startX + barWidth + barSpacing + barWidth/2, canvas.height - 50 - relationHeight - 10);
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
    multiAgentInterface = new MultiAgentInterface();
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (multiAgentInterface) {
        multiAgentInterface.destroy();
    }
});