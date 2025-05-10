class MoodHistory {
    constructor() {
        this.history = JSON.parse(localStorage.getItem('moodHistory')) || [];
        this.historyElement = document.getElementById('moodHistory');
        this.historyContainer = this.historyElement.querySelector('.history-container');
        this.maxEntries = 5;
        this.renderHistory();
    }

    addEntry(mood, recommendation) {
        const entry = {
            mood,
            recommendation,
            timestamp: new Date().toLocaleString(),
        };

        this.history.unshift(entry);
        if (this.history.length > this.maxEntries) {
            this.history.pop();
        }

        localStorage.setItem('moodHistory', JSON.stringify(this.history));
        this.renderHistory();
    }

    renderHistory() {
        this.historyContainer.innerHTML = '';
        this.history.forEach(entry => {
            const entryElement = document.createElement('div');
            entryElement.className = 'mood-entry';
            entryElement.innerHTML = `
                <div style="color: #1DB954">${entry.timestamp}</div>
                <div>${entry.mood}</div>
                <div style="font-style: italic">→ ${entry.recommendation}</div>
            `;
            this.historyContainer.appendChild(entryElement);
        });
        
        if (this.history.length > 0) {
            this.historyElement.classList.add('visible');
        }
    }
}

// Create loading animation
function createLoadingParticles() {
    const spiral = document.querySelector('.particle-spiral');
    for (let i = 0; i < 12; i++) {
        const particle = document.createElement('div');
        particle.style.cssText = `
            position: absolute;
            width: 8px;
            height: 8px;
            background: #1DB954;
            border-radius: 50%;
            top: 50%;
            left: 50%;
            transform-origin: 50px 50px;
            animation: particleSpiral 1.5s infinite;
            animation-delay: ${i * 0.1}s;
        `;
        spiral.appendChild(particle);
    }
}

// Initialize history
const moodHistory = new MoodHistory();        

const canvas = document.getElementById('visualizer');
const ctx = canvas.getContext('2d');
let particles = [];
let hue = 0;
let pulseFactor = 1;
let pulseDirection = 0.02;

function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}

window.addEventListener('resize', resizeCanvas);
resizeCanvas();



// Previous canvas and particle setup code remains the same until the Particle class

class Particle {
    constructor() {
        this.reset();
    }

    reset() {
        this.x = Math.random() * canvas.width;
        this.y = Math.random() * canvas.height;
        this.size = Math.random() * 5 + 1;
        this.speedX = Math.random() * 3 - 1.5;
        this.speedY = Math.random() * 3 - 1.5;
        this.initialSize = this.size;
        this.angle = Math.random() * 360;
        this.rotationSpeed = (Math.random() - 0.5) * 2;
        this.oscillationRadius = Math.random() * 5;
        this.oscillationSpeed = Math.random() * 0.02 + 0.01;
        this.initialX = this.x;
        this.initialY = this.y;
        this.time = Math.random() * 100;
    }

    update() {
        // Oscillating movement
        this.time += this.oscillationSpeed;
        this.x = this.initialX + Math.cos(this.time) * this.oscillationRadius;
        this.y = this.initialY + Math.sin(this.time) * this.oscillationRadius;
        
        // Regular movement
        this.initialX += this.speedX;
        this.initialY += this.speedY;
        
        // Rotation
        this.angle += this.rotationSpeed;
        
        // Size pulsing
        this.size = this.initialSize * pulseFactor;

        if (this.initialX < 0 || this.initialX > canvas.width || 
            this.initialY < 0 || this.initialY > canvas.height) {
            this.reset();
        }
    }

    draw() {
        

        ctx.save();
        ctx.translate(this.x, this.y);
        ctx.rotate(this.angle * Math.PI / 180);
        
        // Create gradient for each particle
        const gradient = ctx.createRadialGradient(0, 0, 0, 0, 0, this.size);
        gradient.addColorStop(0, `hsla(${hue}, 70%, 50%, 0.8)`);
        gradient.addColorStop(1, `hsla(${hue}, 70%, 50%, 0)`);
        
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(0, 0, this.size, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
    }
}

async function retryFetch(url, options, maxRetries = 3) {
    for (let i = 0; i < maxRetries; i++) {
        try {
            const response = await fetch(url, options);
            if (response.ok) {
                return response;
            }
            if (response.status === 503) {
                // Wait longer between each retry
                await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
                continue;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        } catch (error) {
            if (i === maxRetries - 1) throw error; // Throw if last retry
            await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
        }
    }
}


// Modify the analyzeMusicMood function
async function analyzeMusicMood() {
    const loadingAnimation = document.getElementById('loadingAnimation');
    loadingAnimation.style.display = 'flex';
    const input = document.getElementById('songInput').value;
    const moodText = document.getElementById('moodText');
    const recommendationText = document.getElementById('recommendationText');
    
    moodText.classList.remove('active');
    recommendationText.classList.remove('active');

    moodText.textContent = 'Analyzing your musical vibes...';
    moodText.classList.add('active');
    
    try {
        // First Groq call - Get mood and music recommendation
        const moodResponse = await fetch('https://api.groq.com/openai/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer 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`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: "mixtral-8x7b-32768",
                messages: [{
                    role: "user",
                    content: `Analyze this music input: "${input}". 
                    Return your response in exactly this format with no additional text:
                    mood|color|recommendation|ingredients

                    Where:
                    - mood is a poetic 2-sentence description
                    - color is just a number between 0-360
                    - recommendation is a single song or album suggestion
                    - ingredients is a JSON array of 5-7 ingredients that match the mood
                    
                    Example format:
                    A dreamy atmosphere filled with starlit wonder. The melody dances like northern lights.|240|Close To You by The Carpenters|["lavender", "honey", "vanilla bean", "chamomile flowers", "star anise"]`
                }],
                temperature: 0.7
            })
        });

        if (!moodResponse.ok) {
            throw new Error(`HTTP error! status: ${moodResponse.status}`);
        }

        const moodData = await moodResponse.json();
        const content = moodData.choices[0].message.content;
        
        // Parse response
        let [moodDescription, colorHue, recommendation, ingredientsStr] = content.split("|");
        
        // Clean up values
        moodDescription = moodDescription.replace(/["{}\[\]]/g, '').trim();
        recommendation = recommendation.replace(/["{}\[\]]/g, '').trim();
        const ingredients = JSON.parse(ingredientsStr);
        hue = parseInt(colorHue) || 180;

        // Call your friend's recipe API
        const recipeResponse = await axios.post(
            'https://smart-health.up.railway.app/api/recipes',
            { ingredients },
            {
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': 'a75f3b2e9c1d6h8j4k2m7n5p3q6r9s1t4u8v2w6x3y5z0'
                }
            }
        );

        const recipe = recipeResponse.data.recipes[0];

        // Get recipe explanation from Groq
        const explanationResponse = await fetch('https://api.groq.com/openai/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer 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`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: "mixtral-8x7b-32768",
                messages: [{
                    role: "user",
                    content: `The recipe "${recipe.name}" was generated for the artist/song "${input}" which has a mood of "${moodDescription}". 
                    Explain in 2-3 sentences why this recipe matches the musical vibe.`
                }],
                temperature: 0.7
            })
        });

        const explanationData = await explanationResponse.json();
        const explanation = explanationData.choices[0].message.content;

        // Update UI
        setTimeout(() => {
            moodText.textContent = moodDescription;
            recommendationText.innerHTML = `
                <h3>Recommended for your mood</h3>
                ${recommendation}
                <button class="watch-button" onclick="openVideoModal('${recommendation}')">
                    Watch on YouTube (because Spotify API is hard 😅)
                </button>

                <div class="recipe-section">
                    <h3>${recipe.name}</h3>
                    <p class="recipe-explanation">${explanation}</p>
                    
                    <h4>Ingredients:</h4>
                    <ul>
                        ${recipe.ingredients.map(ing => `<li>${ing}</li>`).join('')}
                    </ul>
                    
                    <div class="recipe-instructions">
                        <h4>Instructions:</h4>
                        <ul>
                            ${recipe.instructions.map(instruction => `<li>${instruction}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            `;
            moodText.classList.add('active');
            recommendationText.classList.add('active');
        }, 500);

        moodHistory.addEntry(moodDescription, `${recommendation} | ${recipe.name}`);

    } catch (error) {
        console.error('Error:', error);
        moodText.textContent = 'Something went wrong: ' + error.message;
        moodText.classList.add('active');
    } finally {
        loadingAnimation.style.display = 'none';
    }
}

function initParticles() {
    particles = [];
    for (let i = 0; i < 150; i++) {
        particles.push(new Particle());
    }
}

function animate() {
    ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    particles.forEach(particle => {
        particle.update();
        particle.draw();
    });

    // Pulse effect
    pulseFactor += pulseDirection;
    if (pulseFactor > 1.5 || pulseFactor < 0.5) {
        pulseDirection *= -1;
    }
    
    // Color transition
    hue += 0.5;
    if (hue >= 360) hue = 0;
    
    requestAnimationFrame(animate);
}

                // Add video modal functions
function openVideoModal(searchQuery) {
    const modal = document.getElementById('videoModal');
    modal.style.display = 'flex';
    
    // Create a YouTube search URL
    const searchUrl = `https://www.youtube.com/results?search_query=${encodeURIComponent(searchQuery)}`;
    
    const videoPlayer = document.getElementById('videoPlayer');
    videoPlayer.innerHTML = `
        <div style="text-align: center; padding: 20px;">
            <p style="margin-bottom: 20px;">We couldn't embed the video directly, but you can:</p>
            <a href="${searchUrl}" target="_blank" style="
                background: #FF0000;
                color: white;
                padding: 12px 24px;
                text-decoration: none;
                border-radius: 20px;
                display: inline-block;
                margin-top: 10px;
                font-weight: bold;
            ">
                Watch on YouTube
            </a>
        </div>
    `;
}

document.querySelector('.close-video').addEventListener('click', () => {
    const modal = document.getElementById('videoModal');
    modal.style.display = 'none';
    document.getElementById('videoPlayer').innerHTML = '';
});

document.getElementById('videoModal').addEventListener('click', (e) => {
    if (e.target.id === 'videoModal') {
        e.target.style.display = 'none';
        document.getElementById('videoPlayer').innerHTML = '';
    }
});

// Initialize everything
initParticles();
animate();
createLoadingParticles();

