import unittest

import app as app_module


class GirlsCricketPageTestCase(unittest.TestCase):
    def setUp(self):
        self.markup = app_module.app.test_client().get("/girls-cricket").get_data(as_text=True)

    def test_murali_is_the_girls_cricket_head_coach_from_ses(self):
        self.assertIn("Murali Sockalingam", self.markup)
        self.assertIn("Girls Cricket Head Coach", self.markup)
        self.assertIn("Deputy Head Coach, Sharjah English School (SES)", self.markup)
        self.assertIn("ICC Global Level 3 / ACC Level 2", self.markup)
        self.assertIn("16+ years coaching", self.markup)
        self.assertIn("Head Coach — UAE Women's National Cricket Team (2016–2019)", self.markup)

    def test_judith_is_presented_as_a_senior_coach_not_head_coach(self):
        self.assertIn("Judith Jose Peter", self.markup)
        self.assertIn("Senior Cricket Coach", self.markup)
        self.assertIn("ICC Global Level 2", self.markup)
        self.assertNotIn("Judith Jose Peter (ICC Level 1", self.markup)
        self.assertNotIn("Girls Head Coach", self.markup)
        self.assertNotIn("Female Head Coach", self.markup)


if __name__ == "__main__":
    unittest.main()
