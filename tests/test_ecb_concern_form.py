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

    def test_concern_form_is_hidden_from_the_tournaments_page(self):
        for markup in (self.html_with_registration, self.html_without_registration):
            self.assertNotIn('id="ecb-concern-cta"', markup)
            self.assertNotIn('id="ecbConcernModal"', markup)
            self.assertNotIn(CONCERN_EMBED_URL, markup)
            self.assertNotIn(CONCERN_FALLBACK_URL, markup)
            self.assertNotIn("ECB Consent Form 2026/27", markup)

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
