/* Article-only progressive gallery: ordinary image links work without JavaScript. */
(() => {
    'use strict';
    const root = document.querySelector('.ecb-story');
    if (!root) return;
    const dialog = root.querySelector('.ecb-lightbox');
    if (!dialog || typeof dialog.showModal !== 'function') return;
    const image = dialog.querySelector('#ecb-lightbox-image');
    const caption = dialog.querySelector('#ecb-lightbox-caption');
    const count = dialog.querySelector('#ecb-lightbox-count');
    const original = dialog.querySelector('#ecb-lightbox-original');
    let links = [], current = 0, trigger, previousOverflow = '', touchX, touchY;
    function show(index) {
        current = (index + links.length) % links.length;
        const link = links[current];
        image.src = link.href;
        image.alt = link.dataset.caption;
        caption.textContent = link.dataset.caption;
        count.textContent = `${current + 1} / ${links.length}`;
        original.href = link.href;
    }
    root.querySelectorAll('[data-ecb-gallery]').forEach(link => {
        link.addEventListener('click', event => {
            if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
            event.preventDefault();
            trigger = link;
            links = Array.from(root.querySelectorAll('[data-ecb-gallery]')).filter(item => item.dataset.ecbGallery === link.dataset.ecbGallery);
            show(links.indexOf(link));
            previousOverflow = document.body.style.overflow;
            document.body.style.overflow = 'hidden';
            dialog.showModal();
            dialog.querySelector('[data-ecb-close]').focus();
        });
    });
    dialog.querySelector('[data-ecb-close]').addEventListener('click', () => dialog.close());
    dialog.querySelector('[data-ecb-prev]').addEventListener('click', () => show(current - 1));
    dialog.querySelector('[data-ecb-next]').addEventListener('click', () => show(current + 1));
    dialog.addEventListener('close', () => {
        document.body.style.overflow = previousOverflow;
        image.removeAttribute('src');
        if (trigger) trigger.focus();
    });
    dialog.addEventListener('click', event => { if (event.target === dialog) dialog.close(); });
    dialog.addEventListener('keydown', event => {
        if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
            event.preventDefault();
            show(current + (event.key === 'ArrowRight' ? 1 : -1));
        }
    });
    const stage = dialog.querySelector('.ecb-lightbox__stage');
    stage.addEventListener('touchstart', event => {
        touchX = event.changedTouches[0].clientX;
        touchY = event.changedTouches[0].clientY;
    }, {passive:true});
    stage.addEventListener('touchend', event => {
        if (touchX === undefined) return;
        const delta = event.changedTouches[0].clientX - touchX;
        const verticalDelta = event.changedTouches[0].clientY - touchY;
        if (Math.abs(delta) > 50 && Math.abs(delta) > Math.abs(verticalDelta)) show(current + (delta < 0 ? 1 : -1));
        touchX = undefined;
    }, {passive:true});
    stage.addEventListener('touchcancel', () => { touchX = undefined; }, {passive:true});
})();
