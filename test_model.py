import unittest

from dataset import FEATURES, DataError
from model import shortlist_probability, train
from tests.helpers import students

BASE = {
    "cgpa": 7.0, "backlogs": 0, "internships": 0, "projects": 2,
    "certifications": 2, "aptitude_score": 60, "communication_score": 60,
    "skills": "Python, SQL",
}


class TrainTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = train(students(500, seed=7))

    def test_beats_the_majority_class_baseline(self):
        # ~45% positives, so a model that learned nothing scores ~55%.
        self.assertGreater(self.report.accuracy, 0.75)
        self.assertGreater(self.report.cv_mean, 0.75)

    def test_confusion_matrix_covers_the_holdout(self):
        self.assertEqual(int(self.report.confusion.sum()), self.report.holdout_size)

    def test_reports_one_weight_per_feature(self):
        self.assertEqual(set(self.report.weights.index), set(FEATURES))

    def test_training_is_deterministic(self):
        again = train(students(500, seed=7))
        self.assertEqual(again.accuracy, self.report.accuracy)

    def test_refuses_to_train_without_both_classes(self):
        df = students(100, seed=1)
        df["shortlisted"] = 1
        with self.assertRaises(DataError):
            train(df)

    def test_refuses_tiny_datasets(self):
        with self.assertRaises(DataError):
            train(students(20, seed=1))


class PredictTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = train(students(500, seed=7)).model

    def p(self, **changes):
        return shortlist_probability(self.model, {**BASE, **changes})

    def test_probability_is_in_unit_interval(self):
        for profile in ({}, {"cgpa": 0.0, "backlogs": 50}, {"cgpa": 10.0, "internships": 20}):
            with self.subTest(profile):
                self.assertTrue(0.0 <= self.p(**profile) <= 1.0)

    def test_better_cgpa_raises_probability(self):
        self.assertGreater(self.p(cgpa=9.0), self.p(cgpa=6.0))

    def test_backlogs_lower_probability(self):
        self.assertLess(self.p(backlogs=3), self.p(backlogs=0))

    def test_internship_raises_probability(self):
        self.assertGreater(self.p(internships=2), self.p(internships=0))

    def test_no_skills_is_a_valid_profile(self):
        self.assertLess(self.p(skills=""), self.p())


if __name__ == "__main__":
    unittest.main()
