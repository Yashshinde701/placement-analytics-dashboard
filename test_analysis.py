import unittest

import numpy as np
import pandas as pd

from analysis import cgpa_band, rate_by, skill_table
from dataset import add_skill_flags


class CgpaBandTest(unittest.TestCase):
    def test_band_edges_are_lower_inclusive(self):
        s = pd.Series([0.0, 5.99, 6.0, 6.99, 7.0, 9.0, 10.0])
        got = cgpa_band(s).astype(str).tolist()
        self.assertEqual(got, ["<6", "<6", "6-7", "6-7", "7-8", "9-10", "9-10"])


class RateByTest(unittest.TestCase):
    def test_rate_and_group_size(self):
        df = pd.DataFrame({"backlogs": [0, 0, 0, 1], "shortlisted": [1, 0, 1, 0]})
        out = rate_by(df, "backlogs").set_index("backlogs")
        self.assertEqual(out.loc[0, "students"], 3)
        self.assertEqual(out.loc[0, "rate"], 66.7)
        self.assertEqual(out.loc[1, "rate"], 0.0)

    def test_groups_by_series_and_skips_empty_bands(self):
        df = pd.DataFrame({"cgpa": [6.5, 6.9], "shortlisted": [1, 0]})
        out = rate_by(df, cgpa_band(df["cgpa"]))
        self.assertEqual(out["cgpa_band"].astype(str).tolist(), ["6-7"])


class SkillTableTest(unittest.TestCase):
    def test_rates_and_unheld_skill(self):
        df = add_skill_flags(pd.DataFrame({
            "skills": ["Python, SQL", "Python", "SQL"],
            "shortlisted": [1, 0, 1],
        }))
        t = skill_table(df).set_index("skill")
        self.assertEqual(t.loc["Python", "students"], 2)
        self.assertEqual(t.loc["Python", "rate"], 50.0)
        self.assertEqual(t.loc["SQL", "rate"], 100.0)
        self.assertEqual(t.loc["Java", "students"], 0)
        self.assertTrue(np.isnan(t.loc["Java", "rate"]))


if __name__ == "__main__":
    unittest.main()
