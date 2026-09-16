document.addEventListener('DOMContentLoaded', () => {
    const sendEvent = (name, params = {}) => {
        if (typeof window.trackEvent === 'function') {
            window.trackEvent(name, { branch: 'SHJ01', ...params });
        }
    };

    const campaignKeys = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content'];
    const query = new URLSearchParams(window.location.search);
    const campaign = {};
    campaignKeys.forEach((key) => {
        const currentValue = query.get(key);
        try {
            if (currentValue) sessionStorage.setItem(`ses_${key}`, currentValue);
            campaign[key] = currentValue || sessionStorage.getItem(`ses_${key}`) || '';
        } catch (error) {
            campaign[key] = currentValue || '';
        }
    });

    sendEvent('view_sharjah_landing', campaign);

    const observeOnce = (selector, eventName) => {
        const elements = document.querySelectorAll(selector);
        if (!elements.length) return;
        let sent = false;
        const observer = new IntersectionObserver((entries) => {
            if (sent || !entries.some((entry) => entry.isIntersecting)) return;
            sent = true;
            sendEvent(eventName, campaign);
            observer.disconnect();
        }, { threshold: 0.35 });
        elements.forEach((element) => observer.observe(element));
    };

    observeOnce('[data-ses-price]', 'view_sharjah_price');
    observeOnce('[data-ses-beginner]', 'view_beginner_section');

    const coachingForm = document.getElementById('ses-coaching-form');
    const coachingInterest = document.getElementById('coaching-interest');
    let coachingStarted = false;

    document.querySelectorAll('[data-track-event="start_ses_lead"]').forEach((link) => {
        link.addEventListener('click', () => {
            coachingStarted = true;
        }, { capture: true });
    });

    document.querySelectorAll('[data-program="beginner"]').forEach((link) => {
        link.addEventListener('click', () => {
            if (coachingInterest) coachingInterest.value = 'Beginner Plastic Ball';
            sendEvent('select_sharjah_squad', { ...campaign, program: 'Beginner Plastic Ball' });
        });
    });

    if (coachingInterest) {
        coachingInterest.addEventListener('change', () => {
            if (!coachingInterest.value) return;
            sendEvent('select_sharjah_squad', { ...campaign, program: coachingInterest.value });
        });
    }

    if (coachingForm) {
        coachingForm.addEventListener('focusin', () => {
            if (coachingStarted) return;
            coachingStarted = true;
            sendEvent('start_ses_lead', campaign);
        });

        coachingForm.addEventListener('submit', (event) => {
            event.preventDefault();
            if (!coachingForm.reportValidity()) return;

            const data = new FormData(coachingForm);
            const interest = data.get('coaching_interest');
            const message = [
                'Hi Desert Cubs. I am enquiring about cricket coaching at Sharjah English School.',
                `Parent: ${data.get('parent_name')}`,
                `Mobile: ${data.get('mobile')}`,
                `Child age / date of birth: ${data.get('child_age')}`,
                `Interest: ${interest}`,
                `Preferred callback or assessment time: ${data.get('callback_time') || 'Please advise'}`,
                'Please share the suitable squad, current schedule and availability.'
            ].join('\n');

            sendEvent('submit_ses_lead', { ...campaign, program: interest });
            document.getElementById('ses-coaching-status').textContent =
                `Your ${interest} enquiry for the SES branch is ready in WhatsApp. Please send the message to complete your enquiry.`;
            window.open(`https://wa.me/971588274266?text=${encodeURIComponent(message)}`, '_blank', 'noopener');
        });
    }

    const hireDialog = document.getElementById('ses-facility-dialog');
    const hireForm = document.getElementById('ses-facility-form');
    const openHire = () => {
        if (!hireDialog) return;
        if (typeof hireDialog.showModal === 'function') hireDialog.showModal();
        else hireDialog.setAttribute('open', '');
    };
    const closeHire = () => {
        if (!hireDialog) return;
        if (typeof hireDialog.close === 'function') hireDialog.close();
        else hireDialog.removeAttribute('open');
    };

    document.querySelectorAll('[data-open-hire]').forEach((button) => button.addEventListener('click', openHire));
    document.querySelectorAll('[data-close-hire]').forEach((button) => button.addEventListener('click', closeHire));
    if (hireDialog) {
        hireDialog.addEventListener('click', (event) => {
            if (event.target === hireDialog) closeHire();
        });
    }

    if (hireForm) {
        hireForm.addEventListener('submit', (event) => {
            event.preventDefault();
            if (!hireForm.reportValidity()) return;

            const data = new FormData(hireForm);
            const activity = data.get('activity_type');
            const message = [
                'Hi Desert Cubs. I am enquiring about facility hiring at Sharjah English School.',
                `Name: ${data.get('hire_name')}`,
                `Mobile: ${data.get('hire_mobile')}`,
                `Organization or team: ${data.get('organization')}`,
                `Activity: ${activity}`,
                `Preferred date: ${data.get('preferred_date')}`,
                `Preferred time: ${data.get('preferred_time')}`,
                `Estimated participants: ${data.get('participants')}`,
                'Please confirm availability and booking requirements.'
            ].join('\n');

            sendEvent('submit_ses_facility_lead', { ...campaign, activity_type: activity });
            document.getElementById('ses-facility-status').textContent =
                `Your ${activity} enquiry for the SES facility is ready in WhatsApp. Please send the message to complete your enquiry.`;
            window.open(`https://wa.me/971588274266?text=${encodeURIComponent(message)}`, '_blank', 'noopener');
        });
    }
});
