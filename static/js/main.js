document.addEventListener('DOMContentLoaded', () => {
    
    // Mobile Menu Toggle
    const btn = document.getElementById('mobile-btn');
    const menu = document.getElementById('mobile-menu');

    btn.addEventListener('click', () => {
        menu.classList.toggle('hidden');
    });

    // Add sticky nav logic if needed later
    
    // Simple intersection observer for scroll animations (optional)
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in-up');
            }
        });
    });

    document.querySelectorAll('.card-hover').forEach((el) => observer.observe(el));
});