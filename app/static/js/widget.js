// app/static/js/widget.js
class SpotifyChatWidget {
    constructor() {
        this.userId = null;
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Auth form submissions
        document.getElementById('loginForm').addEventListener('submit', (e) => {
            e.preventDefault();
            const form = e.target;
            if (form.dataset.mode === 'signup') {
                this.handleSignup(form);
            } else {
                this.handleLogin(form);
            }
        });

        document.querySelector('.minimize-btn').addEventListener('click', () => {
            const widget = document.querySelector('.spotify-chat-widget');
            const content = document.querySelector('.widget-content');
            const messageInput = document.querySelector('.message-input');
            
            if (widget.style.height === '40px') {
                widget.style.height = '500px';
                content.style.display = 'block';
                if (this.userId) messageInput.style.display = 'flex';
            } else {
                widget.style.height = '40px';
                content.style.display = 'none';
                messageInput.style.display = 'none';
            }
        });

        document.querySelector('.open-widget-btn').addEventListener('click', () => {
            const widget = document.querySelector('.spotify-chat-widget');
            const opener = document.getElementById('widget-opener');
            widget.style.display = 'flex';
            widget.style.height = '500px';
            opener.style.display = 'none';
            
            // If user was previously chatting, show the chat interface
            if (this.userId) {
                document.querySelector('.widget-content').style.display = 'block';
                document.getElementById('messageInput').style.display = 'flex';
            }
        });
    
        document.querySelector('.close-btn').addEventListener('click', () => {
            const widget = document.querySelector('.spotify-chat-widget');
            const opener = document.getElementById('widget-opener');
            
            // Fade out widget
            widget.style.opacity = '0';
            
            setTimeout(() => {
                widget.style.display = 'none';
                opener.style.display = 'block';
                widget.style.opacity = '1';
            }, 300);
        });

        document.querySelector('.minimize-btn').addEventListener('click', () => {
            const widget = document.querySelector('.spotify-chat-widget');
            const content = document.querySelector('.widget-content');
            const messageInput = document.querySelector('.message-input');
            
            if (widget.style.height === '40px') {
                widget.style.height = '500px';
                setTimeout(() => {
                    content.style.display = 'block';
                    if (this.userId) messageInput.style.display = 'flex';
                }, 50); // Small delay for smoother animation
            } else {
                widget.style.height = '40px';
                content.style.opacity = '0';
                messageInput.style.opacity = '0';
                
                setTimeout(() => {
                    content.style.display = 'none';
                    messageInput.style.display = 'none';
                    content.style.opacity = '1';
                    messageInput.style.opacity = '1';
                }, 200);
            }
        });

        // Message input
        const messageInput = document.querySelector('.message-input button');
        if (messageInput) {
            messageInput.addEventListener('click', () => this.sendMessage());
        }

        // Toggle signup/login
        document.getElementById('showSignup').addEventListener('click', (e) => {
            e.preventDefault();
            this.toggleAuthForms();
        });
    }

    async handleLogin(form) {
        console.log("Login attempt starting...");
        this.setLoading(true);
        const email = form.querySelector('input[type="email"]').value;
        const password = form.querySelector('input[type="password"]').value;

        try {
            console.log("Making login request to:", '/api/v1/auth/signin');
            const response = await fetch('/api/v1/auth/signin', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password }),
            });

            console.log("Login response status:", response.status);
            const data = await response.json();
            console.log("Login response data:", data);

            if (data.success) {
                this.userId = data.user.id;
                this.showChatInterface();
            } else {
                this.showError('Login failed: ' + (data.detail || 'Please try again'));
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showError('An error occurred during login');
        } finally {
            this.setLoading(false);
        }
    }

    async handleSignup(form) {
        this.setLoading(true);
        const email = form.querySelector('input[type="email"]').value;
        const password = form.querySelector('input[type="password"]').value;

        try {
            const response = await fetch('/api/v1/auth/signup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password }),
            });

            const data = await response.json();

            if (data.success) {
                this.userId = data.user.id;
                this.showChatInterface();
            } else {
                this.showError('Signup failed: ' + (data.detail || 'Please try again'));
            }
        } catch (error) {
            console.error('Signup error:', error);
            this.showError('An error occurred during signup');
        } finally {
            this.setLoading(false);
        }
    }

    async sendMessage() {
        const input = document.querySelector('.message-input input');
        const message = input.value.trim();
        
        if (!message) return;
    
        try {
            this.addMessage(message, 'user');
            input.value = '';

            this.showTypingIndicator();
    
            const response = await fetch('/api/v1/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: this.userId,
                    message: message
                }),
            });

            this.hideTypingIndicator();

    
            const data = await response.json();
            this.addMessage(data.message, 'bot');
    
            // Handle chat ending if user chose to end
            if (data.debug_info && data.debug_info.choice === "end_chat") {
                this.endChat();
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.addMessage('Sorry, an error occurred. Please try again.', 'bot');
        }
    }

    endChat() {
        const chatMessages = document.getElementById('chatMessages');
        const messageInput = document.querySelector('.message-input');
        messageInput.style.display = 'none';
        
        // Add reopen button when chat ends
        this.addReopenButton();
        
        // Optional: Add a message that chat has ended
        const endMessage = document.createElement('div');
        endMessage.classList.add('chat-message', 'system-message');
        endMessage.textContent = 'Chat ended. Support team will contact you soon.';
        chatMessages.appendChild(endMessage);
    }


    addReopenButton() {
        const container = document.createElement('div');
        container.className = 'reopen-container';
    
        const button = document.createElement('button');
        button.textContent = 'Reopen Chat';
        button.className = 'reopen-btn';
        button.disabled = true;
    
        const countdownDiv = document.createElement('div');
        countdownDiv.className = 'countdown';
        
        container.appendChild(button);
        container.appendChild(countdownDiv);
        document.getElementById('chatMessages').appendChild(container);
    
        // Set countdown time (5 minutes = 300 seconds)
        let timeLeft = 300;
        
        const updateCountdown = () => {
            const minutes = Math.floor(timeLeft / 60);
            const seconds = timeLeft % 60;
            countdownDiv.textContent = `Can reopen chat in ${minutes}:${seconds.toString().padStart(2, '0')}`;
            
            if (timeLeft <= 0) {
                button.disabled = false;
                countdownDiv.textContent = 'You can now reopen the chat';
                countdownDiv.classList.add('complete');
                button.classList.add('ready'); // Add ready class for animation
                clearInterval(timer);
    
                // Add attention-grabbing effect
                button.addEventListener('mouseleave', () => {
                    // Reset animation
                    button.style.animation = 'none';
                    button.offsetHeight; // Trigger reflow
                    button.style.animation = null;
                });
            }
            timeLeft--;
        };
    
        // Start countdown
        updateCountdown();
        const timer = setInterval(updateCountdown, 1000);
    
        button.onclick = async () => {
            try {
                button.disabled = true; // Prevent double-clicks
                button.textContent = 'Reopening...';
                
                const response = await fetch('/api/v1/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_id: this.userId,
                        message: '/reopen'
                    })
                });
                
                const data = await response.json();
                if (data.debug_info.chat_reopened) {
                    container.style.animation = 'fadeOut 0.3s ease-out forwards';
                    setTimeout(() => {
                        document.querySelector('.message-input').style.display = 'flex';
                        container.remove();
                        this.addMessage("Chat reopened. How can I help you?", 'bot');
                    }, 300);
                }
            } catch (error) {
                console.error('Error reopening chat:', error);
                this.addMessage('Sorry, an error occurred while trying to reopen the chat.', 'bot');
                button.disabled = false;
                button.textContent = 'Reopen Chat';
            }
        };
    }

    addMessage(message, type) {
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('chat-message', `${type}-message`);
        
        // Add message text
        messageDiv.textContent = message;
        
        // Add timestamp
        const timestamp = document.createElement('div');
        timestamp.classList.add('message-timestamp');
        timestamp.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        messageDiv.appendChild(timestamp);
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

        // Add new method for typing indicator
    showTypingIndicator() {
        const indicator = document.getElementById('typingIndicator');
        indicator.style.display = 'block';
        document.getElementById('chatMessages').scrollTop = document.getElementById('chatMessages').scrollHeight;
    }

    hideTypingIndicator() {
        document.getElementById('typingIndicator').style.display = 'none';
    }

    showChatInterface() {
        document.getElementById('authForm').classList.remove('active');
        document.getElementById('chatInterface').classList.add('active');
        document.getElementById('messageInput').style.display = 'flex';
    }

    toggleAuthForms() {
        const loginForm = document.getElementById('loginForm');
        const signupText = document.getElementById('showSignup');
        
        if (loginForm.dataset.mode === 'signup') {
            loginForm.dataset.mode = 'login';
            signupText.textContent = 'Sign up';
            loginForm.querySelector('button').textContent = 'Login';
        } else {
            loginForm.dataset.mode = 'signup';
            signupText.textContent = 'Login';
            loginForm.querySelector('button').textContent = 'Sign up';
        }
    }

    showError(message) {
        const errorDiv = document.getElementById('authError') || this.createErrorDiv();
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
    }

    createErrorDiv() {
        const errorDiv = document.createElement('div');
        errorDiv.id = 'authError';
        errorDiv.style.cssText = `
            color: #e74c3c;
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
            background: #fde8e8;
            display: none;
        `;
        const form = document.getElementById('loginForm');
        form.insertBefore(errorDiv, form.firstChild);
        return errorDiv;
    }

    setLoading(isLoading) {
        const submitButton = document.querySelector('#loginForm button');
        const loadingSpinner = document.getElementById('loadingSpinner') || this.createLoadingSpinner();
        
        if (isLoading) {
            submitButton.disabled = true;
            loadingSpinner.style.display = 'inline-block';
            submitButton.textContent = submitButton.dataset.mode === 'signup' ? 'Signing up...' : 'Logging in...';
        } else {
            submitButton.disabled = false;
            loadingSpinner.style.display = 'none';
            submitButton.textContent = submitButton.dataset.mode === 'signup' ? 'Sign up' : 'Login';
        }
    }

    createLoadingSpinner() {
        const spinner = document.createElement('div');
        spinner.id = 'loadingSpinner';
        spinner.style.cssText = `
            display: none;
            width: 20px;
            height: 20px;
            border: 2px solid #f3f3f3;
            border-top: 2px solid #1DB954;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-left: 10px;
        `;
        const style = document.createElement('style');
        style.textContent = `
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
        const submitButton = document.querySelector('#loginForm button');
        submitButton.parentNode.insertBefore(spinner, submitButton.nextSibling);
        return spinner;
    }
}

// Initialize widget when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.spotifyChatWidget = new SpotifyChatWidget();
});