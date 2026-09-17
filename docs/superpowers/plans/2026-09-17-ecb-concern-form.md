# ECB Concern Form 2026/27 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a terms-gated ECB Concern Form 2026/27 modal to the existing tournament page.

**Architecture:** The tournament template receives an always-visible CTA immediately after its hero. The CTA opens a self-contained modal with two states: a locally rendered terms-and-acknowledgement state, then a Google Form iframe state. The iframe remains source-free until the user explicitly acknowledges the terms and continues. Focus, scroll locking, close behavior and analytics are handled by a small page-local script.

**Tech Stack:** Flask/Jinja, vanilla JavaScript, existing Tailwind utility stylesheet, Python `unittest`, Playwright browser smoke checks.

---

### Task 1: Add rendering regression coverage

**Files:**
- Create: `tests/test_ecb_concern_form.py`
- Read: `app.py:1066-1080`, `templates/tournaments.html:1-474`

- [ ] **Step 1: Write the failing test**

```python
import html as html_module
import re
import unittest
from datetime import date
from unittest.mock import patch
import app as app_module

CONCERN_EMBED_URL = 'https://docs.google.com/forms/d/e/1FAIpQLSeyjvE0itOx97iA7GWBal8LXnzhsvSlVd8D74EWgh3W1qLVvA/viewform?embedded=true'
CONCERN_FALLBACK_URL = CONCERN_EMBED_URL.replace('?embedded=true', '')
PDF_COMMITMENTS = (
    'Each player must attend and pay for a minimum of two (2) practice sessions per week',
    'Players are required to participate in all ECB tournament matches',
    'Players must work closely with their assigned coaches',
    'No arguments or disputes with coaches, captains, or academy management will be tolerated',
    'Players and parents are not permitted to interfere with or influence coach’s decisions',
    'ECB tournament fees must be paid in full upfront',
    'Players are required to wear the proper dress code',
)
PDF_SPECIAL_NOTE = 'For U16 & U19 Emirates Cricket Board–National pool players'

def render_tournaments(show_registration):
    with patch.object(app_module, 'dubai_today', return_value=date(2026, 9, 1 if show_registration else 7)):
        return app_module.app.test_client().get('/tournaments').get_data(as_text=True)

def visible_text(html):
    return html_module.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html))).strip()

class EcbConcernFormTestCase(unittest.TestCase):
    def setUp(self):
        self.html_with_registration = render_tournaments(True)
        self.html_without_registration = render_tournaments(False)

    def test_concern_cta_is_unconditional_and_precedes_conditional_registration(self):
        self.assertIn('id="ecb-concern-cta"', self.html_with_registration)
        self.assertIn('id="ecb-concern-cta"', self.html_without_registration)
        self.assertRegex(self.html_with_registration, r'id="tournament-season-hero"[\s\S]*?</section>\s*<section id="ecb-concern-cta"')
        self.assertLess(self.html_with_registration.index('id="ecb-concern-cta"'), self.html_with_registration.index('id="ecb-national-league-registration"'))

    def test_terms_gate_is_complete_and_iframe_has_no_initial_src(self):
        self.assertIn(CONCERN_EMBED_URL, self.html_without_registration)
        self.assertIn(CONCERN_FALLBACK_URL, self.html_without_registration)
        text = visible_text(self.html_without_registration)
        for commitment in PDF_COMMITMENTS:
            self.assertIn(commitment, text)
        self.assertIn(PDF_SPECIAL_NOTE, text)
        self.assertRegex(self.html_without_registration, r'<iframe id="ecbConcernFormFrame"(?![^>]*\bsrc=)')
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests/test_ecb_concern_form.py -v`

Expected: FAIL because the CTA and modal do not yet exist.

- [ ] **Step 3: Add remaining static regression assertions**

```python
self.assertIn('id="ecbConcernAcknowledgement"', html)
self.assertIn('id="ecbConcernContinue" disabled', html)
self.assertIn('for="ecbConcernAcknowledgement"', html)
self.assertIn('role="dialog"', html)
self.assertIn('aria-describedby="ecbConcernModalDescription"', html)
self.assertIn('id="ecbConcernModalDescription"', html)
self.assertIn('tabindex="-1"', html)
for event in ('ecb_concern_form_open', 'ecb_concern_terms_acknowledged', 'ecb_concern_form_continue'):
    self.assertIn(event, html)
self.assertIn('ecbRegistrationModal', html_with_registration)
self.assertIn('ecbRegistrationUrl', html_with_registration)
self.assertIn('openEcbRegistration()', html_with_registration)
self.assertIn('id="filter-all"', html_with_registration)
self.assertIn('id="filter-all"', html_without_registration)
```

- [ ] **Step 4: Re-run the focused test**

Run: `python3 -m unittest tests/test_ecb_concern_form.py -v`

Expected: FAIL until the template is implemented.

### Task 2: Add the CTA, terms modal and consent gate

**Files:**
- Modify: `templates/tournaments.html:55` (new CTA immediately after hero)
- Modify: `templates/tournaments.html:384-472` (new independent concern modal and script)
- Test: `tests/test_ecb_concern_form.py`

- [ ] **Step 1: Add the standalone CTA section**

```html
<section id="ecb-concern-cta" ...>
  <button type="button" id="openEcbConcernForm" onclick="openEcbConcernForm()">
    <i class="fas fa-file-signature" aria-hidden="true"></i> ECB Concern Form 2026/27
  </button>
</section>
```

Keep it outside the `show_ecb_registration` condition, immediately before that existing section.

- [ ] **Step 2: Add two-state modal markup**

```html
<div id="ecbConcernModal" class="modal-overlay" role="dialog" aria-modal="true"
     aria-labelledby="ecbConcernModalTitle" aria-describedby="ecbConcernModalDescription" hidden>
  <section id="ecb-concern-terms">...</section>
<section id="ecb-concern-form-step" hidden>...
  <p id="ecbConcernLoadingStatus" role="status" aria-live="polite">Loading the ECB Concern Form…</p>
    <iframe id="ecbConcernFormFrame" title="ECB Concern Form 2026/27" loading="lazy">Loading…</iframe>
  </section>
</div>
```

Give the hero `id="tournament-season-hero"`. Give `ecbConcernModalTitle`, `ecbConcernTermsHeading` and `ecbConcernFormHeading` `tabindex="-1"`, and include the actual `ecbConcernModalDescription` element. Represent all seven commitments and the U16/U19 special note from `Condition.pdf` as semantic local HTML. Add a visible, unchecked checkbox and disabled Continue button. Include an always-present direct fallback link to `https://docs.google.com/forms/d/e/1FAIpQLSeyjvE0itOx97iA7GWBal8LXnzhsvSlVd8D74EWgh3W1qLVvA/viewform` plus a return-to-terms button.

Give the modal card `max-height:calc(100vh - 32px)` and a flex-column layout. Give each state `overflow-y:auto` and `min-height:0` so terms and the form stay scrollable inside the viewport at mobile widths.

- [ ] **Step 3: Add modal behavior**

```javascript
const ecbConcernFormUrl = 'https://docs.google.com/forms/d/e/1FAIpQLSeyjvE0itOx97iA7GWBal8LXnzhsvSlVd8D74EWgh3W1qLVvA/viewform?embedded=true';

function openEcbConcernForm() {
  resetEcbConcernModal();
  modal.hidden = false;
  modal.classList.add('active');
  document.body.style.overflow = 'hidden';
  termsHeading.focus();
  trackEvent('ecb_concern_form_open', { event_category: 'ecb_concern', event_label: 'ECB Concern Form 2026/27' });
}
```

Implement: each-open reset; consent-gated iframe assignment; a visible `ecbConcernLoadingStatus` before assignment that is removed/updated by the iframe `load` handler; an immediate visible fallback link (rather than unreliable cross-origin iframe-error detection); Escape/backdrop/close controls; focus trap; return-to-terms; triggering-button focus restoration; form-heading focus on terms→form transition; and static-only analytics events. Do not send terms acceptance or Google form data to analytics.

- [ ] **Step 4: Run static regressions**

Run: `python3 -m unittest tests/test_ecb_concern_form.py -v`

Expected: PASS.

### Task 3: Verify interactions and delete source PDF

**Files:**
- Verify: `templates/tournaments.html`
- Delete: `Condition.pdf`
- Test: `tests/test_ecb_concern_form.py`, `tests/test_ses_page.py`

- [ ] **Step 1: Run browser test**

Create and run an inline Playwright smoke test against a local Flask server at desktop and 390px mobile widths. Route `**/forms/**` requests in the test so it can assert zero Google requests before Continue and fulfill the iframe after Continue. Verify: open; initial focus on the terms heading; Tab and Shift+Tab stay within the modal; empty iframe source; blocked Continue without acknowledgement; enabled Continue after acknowledgement; exact iframe source after Continue; loading status visible until the iframe load handler runs; focus moves to the form heading; direct fallback URL; return-to-terms; reset on close/reopen; Escape close; trigger-focus restoration; modal card bounds and internal scrolling; no horizontal overflow; and no console errors.

- [ ] **Step 2: Run full available tests and checks**

Run: `python3 -m unittest discover -s tests -v && python3 -m py_compile app.py && git diff --check`

Expected: all tests pass and no whitespace errors.

- [ ] **Step 3: Delete the authorized PDF only after passing verification**

Run: `rm -f Condition.pdf && test ! -e Condition.pdf`

- [ ] **Step 4: Re-run tests after deletion**

Run: `python3 -m unittest discover -s tests -v`

Expected: PASS. Confirm terms continue to be rendered locally.
