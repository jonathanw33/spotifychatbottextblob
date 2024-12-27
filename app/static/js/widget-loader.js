// app/static/js/widget-loader.js
(function() {
    const API_BASE_URL = 'https://spotify-bot.azurewebsites.net/';
    
    // Create widget container
    const container = document.createElement('div');
    container.id = 'spotify-support-widget';
    
    // Create Google Font link
    const fontLink = document.createElement('link');
    fontLink.href = 'https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap';
    fontLink.rel = 'stylesheet';
    document.head.appendChild(fontLink);


    // Add both the widget HTML and CSS
    container.innerHTML = `
        <div id="widget-opener" style="display: none;">
            <button class="open-widget-btn">
                Need help?
            </button>
        </div>

        <div class="spotify-chat-widget">
            <div class="widget-header">
                Spotify Support
                <div class="widget-controls">
                    <button class="minimize-btn">_</button>
                    <button class="close-btn">×</button>
                </div>
            </div>
            <div class="widget-content">
                <div class="auth-form active" id="authForm">
                    <h3>Login or Sign Up</h3>
                    <div class="social-login">
                        <button class="social-btn spotify-btn" onclick="window.spotifyChatWidget.handleOAuthLogin('spotify')">
                            Continue with Spotify
                        </button>
                        <button class="social-btn google-btn" onclick="window.spotifyChatWidget.handleOAuthLogin('google')">
                            Continue with Google
                        </button>
                    </div>
            
                    <div class="separator">
                        <span>or</span>
                    </div>

                    <form id="loginForm">
                        <input type="email" placeholder="Email" required>
                        <input type="password" placeholder="Password" required>
                        <button type="submit">Login</button>
                    </form>
                    <p>Don't have an account? <a href="#" id="showSignup">Sign up</a></p>
                </div>
                
                <div class="chat-interface" id="chatInterface">
                    <div id="chatMessages"></div>
                </div>
            </div>
            <div class="typing-indicator" id="typingIndicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
            <div class="message-input" id="messageInput" style="display: none;">
                <input type="text" placeholder="Type your message...">
                <button>Send</button>
            </div>
        </div>
          `;


        const styleElement = document.createElement('style');
        styleElement.textContent = `
        #widget-opener {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 999;
        }

        .open-widget-btn {
            background: #1DB954;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 50px;
            cursor: pointer;
            font-weight: bold;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            transition: transform 0.2s, background-color 0.2s;
        }

        .open-widget-btn:hover {
            transform: scale(1.05);
            background-color: #1ed760;
        }

        .spotify-chat-widget {
            font-family: 'Montserrat', sans-serif;
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 350px;
            height: 500px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            background: white;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            transition: height 0.3s ease, opacity 0.3s ease;
        }
        
        .widget-header {
            background: #1DB954;
            color: white;
            padding: 15px;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .widget-controls {
            display: flex;
            gap: 8px;
        }

        .minimize-btn, .close-btn {
            background: none;
            border: none;
            color: white;
            cursor: pointer;
            padding: 0 5px;
            font-size: 18px;
            line-height: 1;
            transition: opacity 0.2s;
        }

        .minimize-btn:hover, .close-btn:hover {
            opacity: 0.8;
        }

        .close-btn {
            font-size: 20px;
        }
        
        .widget-content {
            flex: 1;
            overflow-y: auto;
            padding: 15px;
            transition: all 0.3s ease;
        }
        
        .auth-form, .chat-interface {
            display: none;
        }
        
        .auth-form.active, .chat-interface.active {
            display: block;
        }
        
        .message-input {
            padding: 15px;
            border-top: 1px solid #eee;
            display: flex;
            transition: all 0.3s ease;
        }
        
        .message-input input {
            flex: 1;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin-right: 8px;
        }
        
        .message-input button {
            background: #1DB954;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 4px;
            cursor: pointer;
        }
        
        .chat-message {
            position: relative;  /* Important for absolute positioning of timestamp */
            margin: 12px 0 25px 0;  /* Extra bottom margin for timestamp */
            padding: 12px;
            border-radius: 8px;
            max-width: 85%;
            word-wrap: break-word;
            line-height: 1.4;
            z-index: 1;  /* Add this to ensure message is above timestamp */
        }

        .message-content {
            position: relative;
            z-index: 2;  /* Ensure content is above timestamp */
        }
        
        .user-message {
            background: #f0f0f0;
            margin-left: auto;  /* Right-align user messages */
            margin-right: 12px;
        }
        
        .bot-message {
            background: #e8f5e9;
            margin-right: auto;  /* Left-align bot messages */
            margin-left: 12px;
        }

        .user-message .message-timestamp {
            right: 0;
        }
        
        .bot-message .message-timestamp {
            left: 0;
        }

        .agent-indicator {
            font-size: 0.7em;
            color: #1DB954;
            position: absolute;
            top: -15px;
            left: 0;
        }

        @keyframes pulseReady {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .reopen-btn {
            background: #1DB954;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 50px;
            cursor: pointer;
            margin: 15px auto;
            display: block;
            font-weight: bold;
            transition: all 0.3s ease;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }

        .reopen-btn:hover:not(:disabled) {
            background: #1ed760;
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }

        .reopen-btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }

        .reopen-btn.ready {
            animation: fadeIn 0.5s ease-out, pulseReady 2s infinite ease-in-out;
        }

        .countdown {
            text-align: center;
            color: #666;
            font-size: 0.9em;
            margin: 5px 0;
            transition: all 0.3s ease;
        }

        .countdown.complete {
            color: #1DB954;
            font-weight: bold;
        }

        .typing-indicator {
            background-color: #e8f5e9;
            padding: 8px;
            border-radius: 4px;
            margin-right: 20px;
            margin-bottom: 8px;
            display: none;
        }

        .typing-indicator span {
            width: 8px;
            height: 8px;
            background-color: #1DB954;
            display: inline-block;
            border-radius: 50%;
            margin: 0 2px;
            opacity: 0.4;
            animation: typing 1s infinite;
        }

        .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
        .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

        @keyframes typing {
            0%, 100% { opacity: 0.4; }
            50% { opacity: 1; }
        }

        /* Message timestamp */

        .message-timestamp {
            position: absolute;
            bottom: -20px;  /* Move it a bit lower */
            right: 5px;
            font-size: 0.7em;
            color: #888;
            background: transparent;  /* Ensure no background color */
            padding: 2px 5px;
            z-index: 1;
        }



        /* Font weights */
        .widget-header {
            font-weight: 600;
        }

        #authForm h3 {
            font-weight: 600;
        }

        button {
            font-family: 'Montserrat', sans-serif;
            font-weight: 500;
        }

        input {
            font-family: 'Montserrat', sans-serif;
        }

        .social-login {
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .social-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            padding: 10px 16px;
            border-radius: 4px;
            border: 1px solid #ddd;
            background: white;
            cursor: pointer;
            font-weight: 500;
            transition: background-color 0.2s;
        }
        
        .spotify-btn {
            background-color: #1DB954;
            color: white;
            border: none;
        }
        
        .spotify-btn:hover {
            background-color: #1ed760;
        }
        
        .google-btn {
            background-color: white;
            color: #444;
            border: 1px solid #ddd;
        }
        
        .google-btn:hover {
            background-color: #f8f8f8;
        }
        
        .separator {
            display: flex;
            align-items: center;
            text-align: center;
            margin: 20px 0;
        }
        
        .separator::before,
        .separator::after {
            content: '';
            flex: 1;
            border-bottom: 1px solid #ddd;
        }
        
        .separator span {
            padding: 0 10px;
            color: #777;
            font-size: 14px;
        }
        
        /* Update existing button styles to match */
        .login-btn {
            width: 100%;
            padding: 10px 16px;
            border-radius: 4px;
            border: none;
            background-color: #007bff;
            color: white;
            font-weight: 500;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        
        .login-btn:hover {
            background-color: #0056b3;
        }
        
        /* Ensure consistent input styling */
        input[type="email"],
        input[type="password"] {
            width: 100%;
            padding: 10px;
            margin-bottom: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
            ${document.querySelector('style').textContent}
    `;
    document.head.appendChild(styleElement);


    // Add widget JavaScript
    const script = document.createElement('script');
    script.textContent = `
        // Your SpotifyChatWidget class with API_BASE_URL modification
        class SpotifyChatWidget {
            constructor() {
                this.apiBaseUrl = '${API_BASE_URL}';
                this.userId = null;
                this.oauthPopup = null;


                window.addEventListener('message', (event) => {
                    console.log('Widget received message:', event.data);
                    // Accept messages from our API origin or from popups (*)
                    if (event.origin !== this.apiBaseUrl && event.origin !== 'null') {
                        console.log('Message accepted from:', event.origin);
                    }

                    if (event.data.type === 'oauth-success' && event.data.userId) {
                        this.userId = event.data.userId;
                        this.showChatInterface();
                        
                        // Close popup if it exists
                        if (this.oauthPopup && !this.oauthPopup.closed) {
                            this.oauthPopup.close();
                        }
                    }
                });

                this.setupEventListeners();
            }


            handleOAuthLogin(provider) {
                console.log('Opening OAuth popup for:', provider);
                // Prevent multiple popups
                if (this.oauthPopup && !this.oauthPopup.closed) {
                    this.oauthPopup.focus();
                    return;
                }

                const width = 600;
                const height = 700;
                const left = (window.innerWidth - width) / 2;
                const top = (window.innerHeight - height) / 2;

                // Store popup reference
                this.oauthPopup = window.open(
                    this.apiBaseUrl + '/api/v1/auth/' + provider,
                    'OAuth Login',
                    'width=' + width + ',height=' + height + ',left=' + left + ',top=' + top
                );

                // Monitor popup status
                const popupMonitor = setInterval(() => {
                    if (this.oauthPopup && this.oauthPopup.closed) {
                        clearInterval(popupMonitor);
                        this.oauthPopup = null;
                    }
                }, 1000);
            }

            showChatInterface() {
                const authForm = document.querySelector('#authForm');
                const chatInterface = document.querySelector('#chatInterface');
                const messageInput = document.querySelector('#messageInput');

                if (authForm) {
                    console.log('Removing auth form...');
                    authForm.classList.remove('active');
                    authForm.style.display = 'none'; // Add this line

                }
                if (chatInterface) {
                    console.log('Showing chat interface...');
                    chatInterface.classList.add('active');
                    authForm.style.display = 'none'; // Add this line
                }
                if (messageInput) {
                    console.log('Showing message input...');
                    messageInput.style.display = 'flex';
                }
            }

    setupEventListeners() {
                // Add OAuth buttons event listeners

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

    // Add new OAuth-related methods
    handleOAuthRedirect(authUrl) {
        // Store current widget state if needed
        localStorage.setItem('widgetState', 'opened');
        // Redirect to OAuth provider
        window.location.href = authUrl;
    }

    checkOAuthRedirect() {
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('logged_in') === 'true' && urlParams.has('user_id')) {
            this.userId = urlParams.get('user_id');
            this.showChatInterface();
            // Clean up URL
            window.history.replaceState({}, document.title, window.location.pathname);
        }
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

            // Use the full API URL including the base
            const response = await fetch(this.apiBaseUrl + '/api/v1/chat', {
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

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();
            this.addMessage(data.message, 'bot');

            // Handle chat ending if user chose to end
            if (data.debug_info && data.debug_info.choice === "end_chat") {
                this.endChat();
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTypingIndicator();
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
            countdownDiv.textContent = \`Can reopen chat in \${minutes}:\${seconds.toString().padStart(2, '0')}\`;
            
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

    createMessageElement(message, type) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('chat-message', type + '-message');
        
        // Create message content container
        const contentDiv = document.createElement('div');
        contentDiv.classList.add('message-content');
        contentDiv.textContent = message;
        messageDiv.appendChild(contentDiv);
        
        // Add timestamp
        const timestamp = document.createElement('div');
        timestamp.classList.add('message-timestamp');
        const time = new Date().toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        timestamp.textContent = time;
        messageDiv.appendChild(timestamp);
        
        // Add agent indicator for bot messages
        if (type === 'bot') {
            const agentIndicator = document.createElement('div');
            agentIndicator.classList.add('agent-indicator');
            agentIndicator.textContent = 'Spotify Support';
            messageDiv.appendChild(agentIndicator);
        }
        
        return messageDiv;
    }

    addMessage(message, type) {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) {
            console.error('Chat messages container not found!');
            return;
        }
        
        const messageElement = this.createMessageElement(message, type);
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Debug log
        console.log('Added message:', {
            type,
            hasTimestamp: !!messageElement.querySelector('.message-timestamp'),
            timestampText: messageElement.querySelector('.message-timestamp')?.textContent
        });
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
        const errorDiv = document.getElementById('authError');
        if (errorDiv) {
            errorDiv.style.display = 'none';
        }
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
        // Using escaped backticks \` for inner template literal
        errorDiv.style.cssText = \`
            color: #e74c3c;
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
            background: #fde8e8;
            display: none;
        \`;
        const form = document.getElementById('loginForm');
        form.insertBefore(errorDiv, form.firstChild);
        return errorDiv;
    }

    handleOAuthLogin(provider) {
        const width = 600;
        const height = 700;
        const left = (window.innerWidth - width) / 2;
        const top = (window.innerHeight - height) / 2;
        
        // Use escaped template literals for URLs
        const popup = window.open(
            \`\${this.apiBaseUrl}/api/v1/auth/\${provider}\`,
            'OAuth Login',
            \`width=\${width},height=\${height},left=\${left},top=\${top}\`
        );
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
                spinner.style.cssText = \`
                    display: none;
                    width: 20px;
                    height: 20px;
                    border: 2px solid #f3f3f3;
                    border-top: 2px solid #1DB954;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin-left: 10px;
                \`;

                const style = document.createElement('style');
                // Use string concatenation for keyframes instead of template literals
                style.textContent = 
                    "@keyframes spin {" +
                    "   0% { transform: rotate(0deg); }" +
                    "   100% { transform: rotate(360deg); }" +
                    "}";

                document.head.appendChild(style);
                const submitButton = document.querySelector('#loginForm button');
                submitButton.parentNode.insertBefore(spinner, submitButton.nextSibling);
                return spinner;
            }
        }

        window.spotifyChatWidget = new SpotifyChatWidget();
    `;

    // Add everything to the page
    document.body.appendChild(container);
    document.body.appendChild(script);
})();