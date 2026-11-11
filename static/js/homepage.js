(() => {
    const tabs = Array.from(document.querySelectorAll('[data-centre-tab]'));
    const panels = Array.from(document.querySelectorAll('.dc-schedule-panel[data-centre]'));
    const requestedCentre = new URLSearchParams(window.location.search).get('centre')?.toUpperCase();
    const requestedTab = tabs.find((tab) => tab.dataset.centreTab === requestedCentre);

    function selectCentre(tab, moveFocus = false) {
        const centre = tab.dataset.centreTab;
        tabs.forEach((item) => {
            const selected = item === tab;
            item.setAttribute('aria-selected', String(selected));
            item.tabIndex = selected ? 0 : -1;
        });
        panels.forEach((panel) => {
            panel.hidden = panel.dataset.centre !== centre;
        });
        if (moveFocus) tab.focus();
    }

    tabs.forEach((tab, index) => {
        tab.addEventListener('click', () => selectCentre(tab));
        tab.addEventListener('keydown', (event) => {
            let next = index;
            if (event.key === 'ArrowRight' || event.key === 'ArrowDown') next = (index + 1) % tabs.length;
            else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') next = (index - 1 + tabs.length) % tabs.length;
            else if (event.key === 'Home') next = 0;
            else if (event.key === 'End') next = tabs.length - 1;
            else return;
            event.preventDefault();
            selectCentre(tabs[next], true);
        });
    });
    if (tabs.length) selectCentre(requestedTab || tabs.find((tab) => tab.getAttribute('aria-selected') === 'true') || tabs[0]);

    const overlay = document.getElementById('dcVideoOverlay');
    const player = document.getElementById('dcVideoPlayer');
    const title = document.getElementById('dcVideoTitle');
    const close = overlay?.querySelector('.dc-video-close');
    let lastTrigger = null;

    function closeVideo() {
        if (!overlay || !player) return;
        player.pause();
        player.removeAttribute('src');
        player.removeAttribute('poster');
        player.load();
        overlay.hidden = true;
        document.body.style.overflow = '';
        lastTrigger?.focus();
    }

    document.querySelectorAll('[data-video-src]').forEach((trigger) => {
        trigger.addEventListener('click', () => {
            if (!overlay || !player) return;
            lastTrigger = trigger;
            const videoUrl = trigger.dataset.videoSrc;
            const label = trigger.dataset.videoTitle || 'Desert Cubs video';
            player.pause();
            player.src = videoUrl;
            player.poster = trigger.querySelector('img')?.src || '';
            player.setAttribute('aria-label', label);
            title.textContent = label;
            overlay.hidden = false;
            document.body.style.overflow = 'hidden';
            player.load();
            close?.focus();
            const playRequest = player.play();
            if (playRequest && typeof playRequest.catch === 'function') playRequest.catch(() => player.focus());
        });
    });

    close?.addEventListener('click', closeVideo);
    overlay?.addEventListener('keydown', (event) => {
        if (event.key !== 'Tab' || !player || !close) return;
        if (event.shiftKey && document.activeElement === close) {
            event.preventDefault();
            player.focus();
        } else if (!event.shiftKey && document.activeElement === player) {
            event.preventDefault();
            close.focus();
        }
    });
    overlay?.addEventListener('click', (event) => {
        if (event.target === overlay) closeVideo();
    });
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && overlay && !overlay.hidden) closeVideo();
    });

    const mascot = document.querySelector('[data-mascot]');
    const mascotVideo = mascot?.querySelector('video');
    const motionPreference = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (mascot && mascotVideo) {
        function useStaticFallback() {
            mascotVideo.pause();
            mascot.classList.add('is-static');
        }

        function startMascotVideo() {
            if (document.hidden || motionPreference.matches) {
                useStaticFallback();
                return;
            }
            mascotVideo.play().then(() => mascot.classList.remove('is-static')).catch(useStaticFallback);
        }

        mascotVideo.addEventListener('error', useStaticFallback);
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) mascotVideo.pause();
            else startMascotVideo();
        });
        motionPreference.addEventListener?.('change', (event) => {
            if (event.matches) useStaticFallback();
            else startMascotVideo();
        });
        startMascotVideo();
    }

})();
