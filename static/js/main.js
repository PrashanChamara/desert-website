/**
 * Desert Cubs Cricket Academy — Main JavaScript
 * Handles: Counter animations, scroll effects, and utilities
 */

document.addEventListener('DOMContentLoaded', () => {

    // =========================================================
    // ANIMATED COUNTERS
    // Usage: <p class="counter" data-target="15000" data-suffix="K+">0</p>
    // =========================================================
    const counters = document.querySelectorAll('.counter');

    if (counters.length > 0) {
        const counterObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const el = entry.target;
                    const target = parseInt(el.getAttribute('data-target'));
                    const suffix = el.getAttribute('data-suffix') || '';
                    const duration = 1800; // ms
                    const steps = 60;
                    const increment = target / steps;
                    let current = 0;
                    
                    const timer = setInterval(() => {
                        current += increment;
                        if (current >= target) {
                            current = target;
                            clearInterval(timer);
                        }
                        // Format large numbers nicely
                        if (target >= 1000) {
                            el.textContent = (current / 1000).toFixed(1) + suffix;
                        } else {
                            el.textContent = Math.floor(current) + suffix;
                        }
                    }, duration / steps);

                    counterObserver.unobserve(el);
                }
            });
        }, { threshold: 0.5 });

        counters.forEach(counter => counterObserver.observe(counter));
    }


    // =========================================================
    // FADE-IN-UP ON SCROLL
    // =========================================================
    const fadeEls = document.querySelectorAll('.fade-in-up');

    if (fadeEls.length > 0) {
        const fadeObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.animationPlayState = 'running';
                    fadeObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.15 });

        fadeEls.forEach(el => {
            el.style.animationPlayState = 'paused';
            fadeObserver.observe(el);
        });
    }


    // =========================================================
    // SMOOTH SCROLL for anchor links (e.g. href="#branches")
    // =========================================================
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            const target = document.querySelector(targetId);
            if (target) {
                e.preventDefault();
                const navHeight = document.getElementById('mainNav')?.offsetHeight || 80;
                const top = target.getBoundingClientRect().top + window.scrollY - navHeight - 16;
                window.scrollTo({ top, behavior: 'smooth' });
            }
        });
    });


    // =========================================================
    // NAV — highlight current page link
    // =========================================================
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath || (href !== '/' && currentPath.startsWith(href))) {
            link.classList.add('active');
        }
    });


    // =========================================================
    // NAV — scroll shadow effect
    // =========================================================
    const nav = document.getElementById('mainNav');
    if (nav) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 60) {
                nav.classList.add('scrolled');
                nav.style.boxShadow = '0 4px 30px rgba(0,0,0,0.4)';
            } else {
                nav.classList.remove('scrolled');
                nav.style.boxShadow = 'none';
            }
        }, { passive: true });
    }


    // =========================================================
    // LAZY LOADING for images (performance boost)
    // =========================================================
    if ('IntersectionObserver' in window) {
        const lazyImages = document.querySelectorAll('img[data-src]');
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    imageObserver.unobserve(img);
                }
            });
        }, { rootMargin: '200px' });

        lazyImages.forEach(img => imageObserver.observe(img));
    }


    // =========================================================
    // COPY TO CLIPBOARD utility (for phone/email)
    // =========================================================
    window.copyToClipboard = function(text, btn) {
        navigator.clipboard.writeText(text).then(() => {
            const original = btn.innerHTML;
            btn.innerHTML = '<i class="fas fa-check mr-1"></i> Copied!';
            btn.classList.add('text-green-500');
            setTimeout(() => {
                btn.innerHTML = original;
                btn.classList.remove('text-green-500');
            }, 2000);
        });
    };


    // =========================================================
    // IMAGE ERROR FALLBACK
    // =========================================================
    document.querySelectorAll('img').forEach(img => {
        img.addEventListener('error', function () {
            if (this.dataset.fallback) {
                this.src = this.dataset.fallback;
            }
        });
    });

    console.log('🏏 Desert Cubs — Built with love for cricket. www.desertcubs.com');
});
