import unittest
from pathlib import Path

import app as app_module


class HomepageRedesignTestCase(unittest.TestCase):
    def setUp(self):
        self.markup = app_module.app.test_client().get("/").get_data(as_text=True)

    def test_homepage_includes_legacy_sections_and_existing_paths(self):
        for section_id in (
            "legacy",
            "player-pathway",
            "international-connections",
            "academy-life",
            "weekly-schedule",
            "joe-burns",
            "video-testimonials",
            "cricket-journey",
            "join-legacy",
        ):
            with self.subTest(section_id=section_id):
                self.assertTrue(f'id="{section_id}"' in self.markup, f"missing section: {section_id}")

        for href in (
            "/legends",
            "/legends/macneil-noronha",
            "/legends/mohammed-nafees",
            "/legends/jordan-alvares",
            "/events",
            "/tours",
            "/tournaments",
            "/girls-cricket",
            "/summer-camp",
            "/blog",
            "/locations/sharjah-english-school",
        ):
            with self.subTest(href=href):
                self.assertTrue(f'href="{href}"' in self.markup, f"missing destination: {href}")

    def test_schedule_renders_all_centres_and_exact_supplied_sessions(self):
        for centre in ("SES", "SIS", "DIS", "DPS", "BSA"):
            with self.subTest(centre=centre):
                self.assertTrue(f'data-centre="{centre}"' in self.markup, f"missing centre panel: {centre}")

        for session in (
            "4:00 PM–9:00 PM",
            "5:30 PM–7:30 PM",
            "7:30 AM–9:30 AM",
            "4:00 PM–6:00 PM",
            "3:00 PM–5:00 PM",
        ):
            with self.subTest(session=session):
                self.assertTrue(session in self.markup, f"missing supplied session: {session}")

        self.assertTrue("Last updated: 31 October 2026" in self.markup, "missing schedule date")
        self.assertTrue("DIS timetable lists overlapping Saturday and Sunday sessions" in self.markup, "missing source discrepancy note")

    def test_media_is_click_to_play_and_respects_reduced_motion(self):
        for item in ('preload="none"', "joe-burns-invitation.mp4", "parent-review.mp4", "player-review.mp4", "ecb-capping-group-2026-1600.webp"):
            with self.subTest(item=item):
                self.assertTrue(item in self.markup, f"missing media/accessibility detail: {item}")
        css = (Path(__file__).resolve().parents[1] / "static/css/homepage.css").read_text()
        self.assertTrue("prefers-reduced-motion:reduce" in css, "missing reduced-motion handling")

    def test_global_seo_schema_and_current_season_status_remain(self):
        for item in ('<title>Cricket Academy Dubai', '"@type": ["SportsOrganization", "LocalBusiness"]', "2026/27 season began 05 September", ">220+</strong>", "Players at the 2026/27 capping ceremony"):
            with self.subTest(item=item):
                self.assertTrue(item in self.markup, f"missing required content: {item}")

    def test_existing_family_testimonials_and_useful_faq_content_remain_available(self):
        for item in (
            "The coaches taught our sons discipline, sportsmanship",
            "Since Saaketh enrolled in 2021",
            "The MasterClasses with Jonty Rhodes, Chaminda Vaas, and Rumesh Ratnayake",
            "15,000+ alumni",
            "UAE Women’s Cricket Captain Esha Oza",
            "Sharjah English School on Maliha Road",
            "five cricket lanes",
            "tournaments",
            "official registration portal",
        ):
            with self.subTest(item=item):
                self.assertTrue(item in self.markup, f"missing retained homepage content: {item}")

    def test_current_uae_u19_selection_leads_player_spotlight(self):
        self.assertIn("Two Desert Cubs stars.", self.markup)
        self.assertIn("U19 Asia Cup 2026", self.markup)
        self.assertIn("in Oman", self.markup)
        self.assertIn("Meet Mohammed", self.markup)
        self.assertIn("Meet Jordan", self.markup)
        self.assertIn("Congratulations to Mohammed Nafees and Jordan Alvares on their selection", self.markup)

    def test_player_profiles_have_route_specific_seo_and_verified_milestones(self):
        client = app_module.app.test_client()
        expected = {
            "/legends/mohammed-nafees": (
                "Mohammed Nafees",
                "U19 Asia Cup 2026 in Oman",
                "127 from 114 balls",
                "U16 West Zone Cup 2025 champion",
                "2024/25",
            ),
            "/legends/jordan-alvares": (
                "Jordan Alvares",
                "U19 Asia Cup 2026 in Oman",
                "ACC U16 West Zone Cup 2025 reserve",
                "ECB U16 National Academy League champions in 2024/25",
                "U19 Ramadan Youth League champion",
            ),
        }
        for path, fragments in expected.items():
            with self.subTest(path=path):
                response = client.get(path)
                self.assertEqual(response.status_code, 200)
                markup = response.get_data(as_text=True)
                for fragment in fragments:
                    self.assertIn(fragment, markup)
                self.assertIn(f'<link rel="canonical"    href="https://www.desertcubs.com{path}">', markup)
                self.assertIn('name="description"', markup)
                self.assertIn("player-profile.css", markup)
        self.assertEqual(client.get("/legends/unknown-player").status_code, 404)
        legends_markup = client.get("/legends").get_data(as_text=True)
        self.assertIn("Mohammed Nafees and Jordan Alvares have been selected", legends_markup)
        self.assertIn("alt=\"Mohammed Nafees — UAE U16", legends_markup)
        self.assertNotIn("alt=\"Mohamed Nafees", legends_markup)

    def test_navigation_branding_and_supplied_card_images_are_used(self):
        for fragment in (
            'alt="Desert Cubs Cricket Academy Logo"',
            'alt="Siraj Finance — Main Sponsor"',
            'class="sticky top-0 w-full z-50',
            "img/homepage/cricket-coaching-2026-10-v2.webp",
            "video/homepage/flag_wave_loop.webm",
            "img/homepage/mascot-flag-wave-poster.webp",
            "img/homepage/girls-cricket.webp",
            'class="dc-national-feature"',
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, self.markup)
        sitemap = app_module.app.test_client().get("/sitemap.xml").get_data(as_text=True)
        self.assertIn("https://www.desertcubs.com/legends/mohammed-nafees", sitemap)
        self.assertIn("https://www.desertcubs.com/legends/jordan-alvares", sitemap)


if __name__ == "__main__":
    unittest.main()
