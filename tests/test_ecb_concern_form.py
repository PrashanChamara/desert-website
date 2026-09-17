import html
import re
import unittest
from datetime import date
from unittest.mock import patch

import app as app_module


CONCERN_EMBED_URL = (
    "https://docs.google.com/forms/d/e/1FAIpQLSeyjvE0itOx97iA7GWBal8LXnzhsvSlVd8D74EWgh3W1qLVvA/"
    "viewform?embedded=true"
)
CONCERN_FALLBACK_URL = CONCERN_EMBED_URL.replace("?embedded=true", "")
PDF_COMMITMENTS = (
    "Each player must attend and pay for a minimum of two (2) practice sessions per week",
    "Players are required to participate in all ECB tournament matches",
    "Players must work closely with their assigned coaches",
    "No arguments or disputes with coaches, captains, or academy management will be tolerated",
    "Players and parents are not permitted to interfere with or influence coach’s decisions",
    "ECB tournament fees must be paid in full upfront",
    "Players are required to wear the proper dress code",
)
PDF_SPECIAL_NOTE = "For U16 & U19 Emirates Cricket Board–National pool players"


def render_tournaments(show_registration):
    render_date = date(2026, 9, 1 if show_registration else 7)
    with patch.object(app_module, "dubai_today", return_value=render_date):
        return app_module.app.test_client().get("/tournaments").get_data(as_text=True)


def visible_text(markup):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", markup))).strip()


class EcbConcernFormTestCase(unittest.TestCase):
    def setUp(self):
        self.html_with_registration = render_tournaments(True)
        self.html_without_registration = render_tournaments(False)

    def test_concern_cta_is_unconditional_and_directly_follows_hero(self):
        for markup in (self.html_with_registration, self.html_without_registration):
            self.assertIn('id="ecb-concern-cta"', markup)
            self.assertRegex(
                markup,
                r'id="tournament-season-hero"[\s\S]*?</section>(?:\s*<!--[\s\S]*?-->\s*)*<section id="ecb-concern-cta"',
            )
        self.assertLess(
            self.html_with_registration.index('id="ecb-concern-cta"'),
            self.html_with_registration.index('id="ecb-national-league-registration"'),
        )

    def test_terms_gate_contains_pdf_content_and_no_initial_iframe_source(self):
        self.assertIn(CONCERN_EMBED_URL, self.html_without_registration)
        self.assertIn(CONCERN_FALLBACK_URL, self.html_without_registration)
        text = visible_text(self.html_without_registration)
        for commitment in PDF_COMMITMENTS:
            self.assertIn(commitment, text)
        self.assertIn(PDF_SPECIAL_NOTE, text)
        self.assertRegex(
            self.html_without_registration,
            r'<iframe id="ecbConcernFormFrame"(?![^>]*\bsrc=)',
        )

    def test_modal_has_accessible_consent_controls_and_tracking(self):
        markup = self.html_without_registration
        for fragment in (
            'id="ecbConcernModal"',
            'role="dialog"',
            'aria-modal="true"',
            'aria-describedby="ecbConcernModalDescription"',
            'id="ecbConcernModalDescription"',
            'id="ecbConcernAcknowledgement"',
            'for="ecbConcernAcknowledgement"',
            'id="ecbConcernContinue"',
            'id="ecbConcernLoadingStatus"',
            "ecb_concern_form_open",
            "ecb_concern_terms_acknowledged",
            "ecb_concern_form_continue",
        ):
            self.assertIn(fragment, markup)
        self.assertRegex(markup, r'id="ecbConcernContinue"[^>]*\bdisabled\b')
        self.assertRegex(markup, r'id="ecbConcernTermsHeading"[^>]*\btabindex="-1"')
        self.assertRegex(markup, r'id="ecbConcernFormHeading"[^>]*\btabindex="-1"')

    def test_google_form_step_uses_the_tour_style_full_height_frame(self):
        markup = self.html_without_registration
        self.assertIn("height:min(88vh,840px)", markup)
        self.assertNotIn('class="ecb-concern-form-toolbar"', markup)
        self.assertNotIn('class="ecb-concern-fallback"', markup)
        self.assertRegex(markup, r'\.ecb-concern-form-wrap \{[^}]*flex:1 1 auto;[^}]*min-height:0;')

    def test_existing_registration_and_tournament_filters_are_preserved(self):
        for markup in (self.html_with_registration, self.html_without_registration):
            self.assertIn('id="filter-all"', markup)
            self.assertIn('function filterTournaments(type)', markup)

        for fragment in (
            'id="ecbRegistrationModal"',
            "const ecbRegistrationUrl",
            "function openEcbRegistration()",
            "ecb_registration_open",
        ):
            self.assertIn(fragment, self.html_with_registration)
        self.assertNotIn('id="ecbRegistrationModal"', self.html_without_registration)


if __name__ == "__main__":
    unittest.main()
