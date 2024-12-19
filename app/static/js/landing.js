// Animate feature cards on scroll
const cards = document.querySelectorAll('.feature-card');

const observerCallback = (entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
        }
    });
};

const observer = new IntersectionObserver(observerCallback, {
    threshold: 0.1
});

cards.forEach(card => observer.observe(card));

// Add random movement to floating icons
const icons = document.querySelectorAll('.floating-icon');
icons.forEach(icon => {
    icon.style.animationDelay = `${Math.random() * 2}s`;
});