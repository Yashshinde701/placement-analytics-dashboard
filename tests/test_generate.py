import unittest

import pandas as pd

from dataset import add_skill_flags, validate
from generate_data import TECH, generate


class GenerateTest(unittest.TestCase):
    def test_same_seed_same_data_different_seed_different_data(self):
        pd.testing.assert_frame_equal(generate(100, 1), generate(100, 1))
        self.assertFalse(generate(100, 1).equals(generate(100, 2)))

    def test_output_satisfies_the_data_contract(self):
        df = generate(300, 3)
        self.assertEqual(len(validate(df)), 300)
        self.assertTrue(df["student_id"].is_unique)

    def test_about_45_percent_are_shortlisted(self):
        self.assertAlmostEqual(generate(1000, 4)["shortlisted"].mean(), 0.45, delta=0.01)

    def test_tech_branches_have_more_skills(self):
        df = add_skill_flags(generate(1000, 5))
        means = df.groupby(df["branch"].isin(TECH))["skill_count"].mean()
        self.assertGreater(means[True], means[False] + 1)

    def test_shortlisted_students_have_higher_cgpa(self):
        df = generate(1000, 6)
        means = df.groupby("shortlisted")["cgpa"].mean()
        self.assertGreater(means[1], means[0])


if __name__ == "__main__":
    unittest.main()
