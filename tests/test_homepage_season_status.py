import unittest

import app as app_module


class HomepageSeasonStatusTestCase(unittest.TestCase):
    def test_homepage_marks_the_2026_27_season_as_begun(self):
        markup = app_module.app.test_client().get("/").get_data(as_text=True)

        self.assertIn("2026/27 Season Began 05 September 2026", markup)
        self.assertIn("2026/27 Season Began Saturday, 05 September 2026", markup)
        self.assertIn("The new season began", markup)
        self.assertNotIn("2026/27 Season Begins", markup)


if __name__ == "__main__":
    unittest.main()
