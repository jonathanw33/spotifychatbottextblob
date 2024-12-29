class SpotifyChatWidget {
    constructor() {
        this.apiBaseUrl = window.location.hostname === 'localhost' 
            ? 'http://localhost:8000'
            : 'https://spotify-bot.azurewebsites.net';
        this.userId = null;
        this.oauthPopup = null;
        this.isAiMode = false;
        this.chatHistory = {
            support: [],
            ai: []
        };
        // Add mode persistence
        this.restoreMode();
        // Add event listener for Enter key
        this.setupEnterKeyListener();
        this.currentMode = 'support';

        // Define welcome messages
        this.welcomeMessages = {
            support: "👋 Hi there! I'm your Spotify Support assistant (powered by a decision tree, so I might be a bit... quirky! 😅). Fun fact: if you want to test our support ticket system, try sending me three angry messages - I can take it, no hard feelings! 🎯\n\nFor a smarter, more natural conversation about music, try switching to AI mode above! 🎵",
            
            ai: "🎵 Hey there! I'm MusicMate, your AI music companion powered by Groq! While I can't peek at your Spotify playlists (my creator's still figuring that part out 😅), I'd love to explore how music can enhance your website's vibe! I especially enjoy music trivia - try testing my knowledge about your favorite bands! What kind of site are you working on? 🎸✨"
        };

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupEventListeners());
        } else {
            this.setupEventListeners();
        }



        // Listen for OAuth success message
        window.addEventListener('message', (event) => {
            console.log('Widget received message:', event.data);
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
            `${this.apiBaseUrl}/api/v1/auth/${provider}`,
            'OAuth Login',
            `width=${width},height=${height},left=${left},top=${top}`
        );

        // Monitor popup status
        const popupMonitor = setInterval(() => {
            if (this.oauthPopup && this.oauthPopup.closed) {
                clearInterval(popupMonitor);
                this.oauthPopup = null;
            }
        }, 1000);
    }

    restoreMode() {
        // Restore previous mode from localStorage
        const savedMode = localStorage.getItem('chatbotMode');
        if (savedMode === 'ai') {
            document.getElementById('chatModeToggle').checked = true;
            this.currentMode = 'ai';
            this.updateModeLabel('ai');
        }
    }

    handleModeToggle(checkbox) {
        const newMode = checkbox.checked ? 'ai' : 'support';
        
        // Save mode to localStorage
        localStorage.setItem('chatbotMode', newMode);
        
        // Clear chat messages
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.innerHTML = '';
        
        // Update current mode
        this.currentMode = newMode;
        
        // Update mode label
        this.updateModeLabel(newMode);
        
        // Add welcome message for the new mode
        this.addMessage(this.welcomeMessages[newMode], 'bot');
    }

    updateModeLabel(mode) {
        const modeLabel = document.querySelector('.mode-label');
        modeLabel.textContent = mode === 'ai' ? '🎵 AI Music Assistant' : '🎧 Support Mode';
    }

    setupEnterKeyListener() {
        const messageInput = document.querySelector('.message-input input');
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault(); // Prevent default Enter key behavior
                this.sendMessage();
            }
        });
    }

    setupEventListeners() {
        const modeToggle = document.getElementById('chatModeToggle');
        if (modeToggle) {
            modeToggle.addEventListener('change', (e) => {
                const chatMessages = document.getElementById('chatMessages');
                const newMode = e.target.checked ? 'ai' : 'support';
                
                // Clear chat display
                chatMessages.innerHTML = '';
                
                // Update mode
                this.currentMode = newMode;
                
                // If no history exists, add welcome messages
                if (this.chatHistory[newMode].length === 0) {
                    this.addMessage(this.welcomeMessages[newMode], 'bot');

                } else {
                    // Display existing history
                    this.chatHistory[newMode].forEach(msg => {
                        this.displayMessage(msg.message, msg.type);
                    });
                }

                // Update mode label
                const modeLabel = document.querySelector('.mode-label');
                modeLabel.textContent = newMode === 'ai' ? '🎵 AI Music Assistant' : '🎧 Support Mode';
            });
        }
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

        // Minimize button
        document.querySelector('.minimize-btn').addEventListener('click', () => {
            const widget = document.querySelector('.spotify-chat-widget');
            const content = document.querySelector('.widget-content');
            const messageInput = document.querySelector('.message-input');
            
            if (widget.style.height === '40px') {
                widget.style.height = '500px';
                setTimeout(() => {
                    content.style.display = 'block';
                    if (this.userId) messageInput.style.display = 'flex';
                }, 50);
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

        // Close button
        document.querySelector('.close-btn').addEventListener('click', () => {
            const widget = document.querySelector('.spotify-chat-widget');
            const opener = document.getElementById('widget-opener');
            widget.style.opacity = '0';
            
            setTimeout(() => {
                widget.style.display = 'none';
                opener.style.display = 'block';
                widget.style.opacity = '1';
            }, 300);
        });

        // Open widget button
        document.querySelector('.open-widget-btn').addEventListener('click', () => {
            const widget = document.querySelector('.spotify-chat-widget');
            const opener = document.getElementById('widget-opener');
            widget.style.display = 'flex';
            widget.style.height = '500px';
            opener.style.display = 'none';
            
            if (this.userId) {
                document.querySelector('.widget-content').style.display = 'block';
                document.getElementById('messageInput').style.display = 'flex';
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
            const response = await fetch(`${this.apiBaseUrl}/api/v1/auth/signin`, {
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
            const response = await fetch(`${this.apiBaseUrl}/api/v1/auth/signup`, {
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
            // Log the request payload
            const requestPayload = {
                user_id: this.userId,
                message: message,
                mode: this.currentMode
            };
            console.log('Request Payload:', requestPayload);
    
            this.addMessage(message, 'user');
            input.value = '';
            this.showTypingIndicator();

            this.scrollToBottom();

    
            const response = await fetch(`${this.apiBaseUrl}/api/v1/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestPayload),
            });
    
            // Log raw response
            console.log('Raw Response:', response);
    
            const responseText = await response.text(); // Get response as text first
            console.log('Response Text:', responseText);
    
            // Try to parse the response
            let data;
            try {
                data = JSON.parse(responseText);
                console.log('Parsed Response Data:', data);
            } catch (e) {
                console.error('Error parsing response:', e);
                console.log('Invalid JSON:', responseText);
            }
    
            this.hideTypingIndicator();
    
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
    
            if (data) {
                console.log('Bot Message:', data.message);
                console.log('Debug Info:', data.debug_info);
                this.addMessage(data.message, 'bot');
            }
    
            // Only handle support-specific features in support mode
            if (this.currentMode === 'support' && data?.debug_info?.choice === "end_chat") {
                this.endChat();
            }
        } catch (error) {
            console.error('Detailed Error:', {
                message: error.message,
                stack: error.stack,
                toString: error.toString()
            });
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
    // Add to chat history array
    this.chatHistory[this.currentMode].push({
        message: message,
        type: type,
        timestamp: new Date().toISOString()
    });
    
    // Display the message
    this.displayMessage(message, type);
}

displayMessage(message, type) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;

    const messageElement = this.createMessageElement(message, type);
    chatMessages.appendChild(messageElement);
    
    // Auto-scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Add a method to scroll to bottom on demand
scrollToBottom() {
    const chatMessages = document.getElementById('chatMessages');
    if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
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

    // Show initial messages if no history exists
    if (this.chatHistory[this.currentMode].length === 0) {
        this.addMessage(this.welcomeMessages[this.currentMode], 'bot');
        setTimeout(() => {
            this.addMessage(this.followUpMessages[this.currentMode], 'bot');
        }, 500);
    } else {
        // Display existing history
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.innerHTML = '';
        this.chatHistory[this.currentMode].forEach(msg => {
            this.displayMessage(msg.message, msg.type);
        });
    }

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

showChatInterface() {
    document.getElementById('authForm').classList.remove('active');
    document.getElementById('chatInterface').classList.add('active');
    document.getElementById('messageInput').style.display = 'flex';
    
    // Show initial messages
    this.showModeMessages(this.currentMode);
    
    const errorDiv = document.getElementById('authError');
    if (errorDiv) {
        errorDiv.style.display = 'none';
    }
}

async showModeMessages(mode) {
    const chatMessages = document.getElementById('chatMessages');
    
    // Clear any existing messages if this is the first time
    if (!this.chatHistory[mode]) {
        // Add welcome message
        this.addMessage(this.welcomeMessages[mode], 'bot');
        
        // Wait a bit before showing follow-up
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Add follow-up message
        this.addMessage(this.followUpMessages[mode], 'bot');
        
        // Save to history
        this.chatHistory[mode] = chatMessages.innerHTML;
    } else {
        // Load existing history
        chatMessages.innerHTML = this.chatHistory[mode];
    }
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



// Initialize widget when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.spotifyChatWidget = new SpotifyChatWidget();
});