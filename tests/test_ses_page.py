import json
import html
import re
import unittest

from app import BRANCHES, app


SES_PATH = "/locations/sharjah-english-school"
SES_CANONICAL = "https://www.desertcubs.com/locations/sharjah-english-school"
SES_MAP_URL = "https://maps.app.goo.gl/6SmMmAASK5GRcmwp9"
EXPECTED_COACHES = [
    ("Janaka Senevirathne", "SES Centre In-Charge / Senior Cricket Coach", "ICC Global Level 2 / Sri Lanka Cricket Level 1", "19+ years coaching"),
    ("Murali Sockalingam", "Deputy Head Coach", "ICC Global Level 3 / ACC Level 2", "16+ years coaching"),
    ("Aruna Bandaranayaka", "Senior Cricket Coach", "ICC Global Level 3 / Cricket Australia Level 2", "17+ years coaching"),
    ("Shanesh Weerawansha", "Senior Cricket Coach", "ICC Global Level 2", "18+ years coaching"),
    ("Kelum Fernando", "Senior Cricket Coach", "ICC Global Level 2", "14+ years coaching"),
    ("Vishwa Fernandopulle", "Operation Officer & Coordinator / Cricket Coach", "ICC Global Level 2 / Sri Lanka Cricket Level 1", "8+ years coaching"),
    ("Moin Sabir", "Cricket Coach", "PCB Level 1", "7+ years coaching"),
    ("Asanga Aluthgedara", "Fitness Trainer", "Diploma in Sports Medicine / AIBA 1-Star Coach", "22+ years coaching"),
]


class SesPageTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()
        cls.response = cls.client.get(SES_PATH)
        cls.html = cls.response.get_data(as_text=True)
        cls.visible_text = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", cls.html)).strip())
        with open("static/js/ses-location.js", encoding="utf-8") as script_file:
            cls.ses_script = script_file.read()

    def test_route_and_required_seo_are_in_place(self):
        self.assertEqual(self.response.status_code, 200)
        self.assertIn("<title>Kids Cricket Academy in Sharjah | Desert Cubs SES</title>", self.html)
        self.assertIn(
            'content="Beginner to U19 cricket coaching at Sharjah English School. Natural turf, qualified coaches, matches and facility hire. Plans from AED 360 per month."',
            self.html,
        )
        self.assertIn(f'rel="canonical"    href="{SES_CANONICAL}"', self.html)
        h1s = re.findall(r"<h1\b[^>]*>(.*?)</h1>", self.html, flags=re.DOTALL | re.IGNORECASE)
        self.assertEqual(len(h1s), 1)
        self.assertIn("Kids Cricket Academy in Sharjah at SES", re.sub(r"<[^>]+>", " ", h1s[0]))

    def test_existing_coaches_map_and_location_data_are_preserved(self):
        ses = next(branch for branch in BRANCHES if branch["id"] == "sharjah-english-school")
        actual_coaches = [
            (coach["name"], coach["role"], coach["qual"], coach["exp"])
            for coach in ses["coaches"]
        ]
        self.assertEqual(actual_coaches, EXPECTED_COACHES)
        self.assertEqual(ses["map_url"], SES_MAP_URL)
        self.assertEqual(ses["area"], "Sharjah (Maliha Road)")
        self.assertIn(SES_MAP_URL, self.html)
        for coach in EXPECTED_COACHES:
            for value in coach:
                self.assertIn(value, self.visible_text)

    def test_training_timing_uses_replaceable_schedule_image_only(self):
        self.assertIn("SES_Schedule.webp", self.html)
        self.assertNotIn('class="ses-table"', self.html)
        self.assertNotIn("Friday 04/09/26", self.visible_text)
        self.assertNotIn("Sunday 06/09/26", self.visible_text)

    def test_only_approved_coaching_price_is_present(self):
        amounts = re.findall(r"AED\s*[\d,]+(?:\.\d+)?", self.visible_text, flags=re.IGNORECASE)
        self.assertGreaterEqual(len(amounts), 2)
        self.assertEqual({re.sub(r"\s+", " ", amount.upper()) for amount in amounts}, {"AED 360"})
        self.assertIn("Sharjah Coaching Plans From AED 360 Per Month", self.visible_text)
        self.assertIn("Conditions Apply", self.visible_text)

    def test_required_sections_and_separate_enquiry_forms_exist(self):
        required_ids = [
            "beginner-coaching",
            "player-pathway",
            "ses-facilities",
            "training-matches",
            "facility-hire",
            "coaching-team",
            "training-schedule",
            "local-proof",
            "location-contact",
            "ses-faq",
            "ses-enquiry",
        ]
        for section_id in required_ids:
            self.assertRegex(self.html, rf'id=["\']{section_id}["\']')
        self.assertRegex(self.html, r'id=["\']ses-coaching-form["\']')
        self.assertRegex(self.html, r'id=["\']ses-facility-form["\']')
        for field in ["parent_name", "mobile", "child_age", "coaching_interest", "callback_time", "consent"]:
            self.assertRegex(self.html, rf'name=["\']{field}["\']')
        for field in ["hire_name", "hire_mobile", "organization", "activity_type", "preferred_date", "preferred_time", "participants"]:
            self.assertRegex(self.html, rf'name=["\']{field}["\']')

    def test_location_and_visible_faq_structured_data_match_page(self):
        payloads = re.findall(
            r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            self.html,
            flags=re.DOTALL | re.IGNORECASE,
        )
        parsed = [json.loads(payload) for payload in payloads]
        serialized = json.dumps(parsed)
        self.assertIn(f'{SES_CANONICAL}#location', serialized)
        self.assertIn('"FAQPage"', serialized)
        self.assertNotIn("What is the best cricket academy in UAE?", serialized)
        for question in [
            "Where is the Desert Cubs Sharjah branch?",
            "Can a complete beginner join?",
            "Can teams hire the facility?",
        ]:
            self.assertIn(question, self.visible_text)
            self.assertIn(question, serialized)

        faq_payload = next(
            node
            for payload in parsed
            for node in payload.get("@graph", [])
            if node.get("@type") == "FAQPage"
        )
        schema_questions = [item["name"] for item in faq_payload["mainEntity"]]
        visible_questions = [
            html.unescape(re.sub(r"<[^>]+>", "", value)).strip()
            for value in re.findall(r"<summary>(.*?)</summary>", self.html, flags=re.DOTALL)
        ]
        self.assertEqual(schema_questions, visible_questions)

    def test_images_are_responsive_and_page_tracking_is_declared(self):
        self.assertIn("srcset=", self.html)
        self.assertIn('fetchpriority="high"', self.html)
        for image_name in [
            "ses-kids-cricket-academy-sharjah",
            "sharjah-beginner-cricket-coaching",
            "ses-natural-turf-cricket-ground",
            "ses-cricket-practice-nets",
            "ses-junior-centre-wicket-match",
            "ses-floodlit-cricket-ground",
        ]:
            self.assertIn(image_name, self.html)
        for event_name in [
            "view_sharjah_landing",
            "view_sharjah_price",
            "view_beginner_section",
            "select_sharjah_squad",
            "click_ses_whatsapp",
            "start_ses_lead",
            "submit_ses_lead",
            "click_ses_facility_hire",
            "submit_ses_facility_lead",
        ]:
            self.assertIn(event_name, self.html + self.ses_script)

    def test_no_duplicate_sharjah_route_exists(self):
        sharjah_rules = [
            rule.rule
            for rule in app.url_map.iter_rules()
            if "sharjah" in rule.rule.lower() or "ses" in rule.rule.lower()
        ]
        self.assertEqual(sharjah_rules, [])
        location_rules = [rule.rule for rule in app.url_map.iter_rules() if rule.rule == "/locations/<branch_id>"]
        self.assertEqual(location_rules, ["/locations/<branch_id>"])

    def test_ses_shared_ctas_and_cross_domain_measurement_are_page_specific(self):
        self.assertNotIn("desertcubs-admin.app/kiosk/register", self.html)
        self.assertGreaterEqual(self.html.count('href="#ses-enquiry"'), 3)
        self.assertIn("'linker': {'domains': ['desertcubs.com', 'desertcubs-admin.app']}", self.html)
        self.assertNotIn('class="whatsapp-float"', self.html)

        other_page = self.client.get("/locations/delhi-private-school").get_data(as_text=True)
        self.assertIn("desertcubs-admin.app/kiosk/register", other_page)
        self.assertNotIn("ses-location.css", other_page)
        self.assertIn("What is the best cricket academy in UAE?", other_page)

    def test_sitemap_and_robots_expose_the_existing_ses_url(self):
        sitemap = self.client.get("/sitemap.xml").get_data(as_text=True)
        self.assertEqual(sitemap.count(SES_CANONICAL), 1)
        robots = self.client.get("/robots.txt").get_data(as_text=True)
        self.assertIn("User-agent: OAI-SearchBot\nAllow: /", robots)


if __name__ == "__main__":
    unittest.main()
