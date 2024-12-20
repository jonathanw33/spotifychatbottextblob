console.log('Landing.js loaded');


// Animate feature cards on scroll
const cards = document.querySelectorAll('.feature-card');
console.log('Found feature cards:', cards.length); // Check if cards are found

document.addEventListener('DOMContentLoaded', () => {
    const cards = document.querySelectorAll('.feature-card');
    console.log('Found cards:', cards.length);
    
    // Make cards visible immediately
    cards.forEach(card => {
        card.classList.add('visible');
        console.log('Added visible class to card');
    });
});

const observerCallback = (entries) => {
    console.log('Observer callback triggered', entries.length); // Debug observer
    entries.forEach(entry => {
        console.log('Entry intersection status:', entry.isIntersecting);
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            console.log('Added visible class to card');
        }
    });
};

const observer = new IntersectionObserver(observerCallback, {
    threshold: 0.1
});

cards.forEach(card => {
    observer.observe(card);
    console.log('Observing card');
});

// Add random movement to floating icons
const icons = document.querySelectorAll('.floating-icon');
console.log('Found floating icons:', icons.length); // Check if icons are found
icons.forEach(icon => {
    icon.style.animationDelay = `${Math.random() * 2}s`;
    console.log('Set animation delay for icon');
});