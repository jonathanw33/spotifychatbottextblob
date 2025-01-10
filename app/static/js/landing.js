

// Add random movement to floating icons
const icons = document.querySelectorAll('.floating-icon');
console.log('Found floating icons:', icons.length); // Check if icons are found
icons.forEach(icon => {
    icon.style.animationDelay = `${Math.random() * 2}s`;
    console.log('Set animation delay for icon');
});


function createConfetti() {
    const colors = ['#1DB954', '#FFFFFF', '#121212'];
    const confettiContainer = document.querySelector('.celebration-section');
    
    for (let i = 0; i < 50; i++) {
        const confetti = document.createElement('div');
        confetti.className = 'confetti';
        confetti.style.left = Math.random() * 100 + '%';
        confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
        confetti.style.animationDelay = Math.random() * 5 + 's';
        confettiContainer.appendChild(confetti);
    }
}

// Call the function when page loads
window.addEventListener('load', createConfetti);