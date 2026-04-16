document.addEventListener('DOMContentLoaded', () => {
const counters = document.querySelectorAll('.counter');
if (counters.length > 0) {
const counterObserver = new IntersectionObserver((entries) => {
entries.forEach(entry => {
if (entry.isIntersecting) {
const el = entry.target;
const target = parseInt(el.getAttribute('data-target'));
const suffix = el.getAttribute('data-suffix') || '';
const duration = 1800; 
const steps = 60;
const increment = target / steps;
let current = 0;
const timer = setInterval(() => {
current += increment;
if (current >= target) {
current = target;
clearInterval(timer);
}
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
const currentPath = window.location.pathname;
document.querySelectorAll('.nav-link').forEach(link => {
const href = link.getAttribute('href');
if (href === currentPath || (href !== '/' && currentPath.startsWith(href))) {
link.classList.add('active');
}
});
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
document.querySelectorAll('img').forEach(img => {
img.addEventListener('error', function () {
if (this.dataset.fallback) {
this.src = this.dataset.fallback;
}
});
});
console.log('🏏 Desert Cubs — Built with love for cricket. www.desertcubs.com');
});