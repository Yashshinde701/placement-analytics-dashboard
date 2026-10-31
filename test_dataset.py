import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd

from dataset import DB_URL_ENV, DataError, add_skill_flags, load_data, validate
from tests.helpers import raw_students

try:
    import sqlalchemy
except ImportError:
    sqlalchemy = None


def with_value(col, value, row=0):
    def mutate(df):
        df = df.copy()
        df[col] = df[col].astype(object)
        df.loc[df.index[row], col] = value
        return df
    return mutate


class AddSkillFlagsTest(unittest.TestCase):
    def test_matches_whole_skills_only(self):
        df = add_skill_flags(pd.DataFrame({"skills": ["Cloud, Python", " c ,sql", "", None]}))
        self.assertEqual(df.loc[0, ["has_c", "has_cloud", "has_python"]].tolist(), [0, 1, 1])
        self.assertEqual(df.loc[1, ["has_c", "has_sql"]].tolist(), [1, 1])
        self.assertEqual(df.loc[[2, 3], "skill_count"].tolist(), [0, 0])

    def test_unknown_skills_are_ignored(self):
        df = add_skill_flags(pd.DataFrame({"skills": ["Rust, Python"]}))
        self.assertEqual(df.loc[0, "skill_count"], 1)


class ValidateTest(unittest.TestCase):
    def test_accepts_generated_data(self):
        self.assertEqual(len(validate(raw_students(50))), 50)

    def test_coerces_numeric_strings_as_read_from_csv_or_db(self):
        df = raw_students(20).astype({"cgpa": str, "shortlisted": str})
        clean = validate(df)
        self.assertEqual(clean["cgpa"].dtype.kind, "f")
        self.assertEqual(clean["shortlisted"].dtype.kind, "i")

    def test_rejects_bad_input(self):
        cases = {
            "missing column": lambda d: d.drop(columns=["cgpa"]),
            "no rows": lambda d: d.iloc[0:0],
            "cgpa above 10": with_value("cgpa", 11.0),
            "negative backlogs": with_value("backlogs", -1),
            "score above 100": with_value("aptitude_score", 101),
            "null value": with_value("cgpa", None),
            "non-numeric value": with_value("cgpa", "n/a"),
            "label not 0/1": with_value("shortlisted", 2),
            "duplicate id": lambda d: with_value("student_id", d["student_id"].iloc[0], row=1)(d),
            "null id": with_value("student_id", None),
        }
        for name, mutate in cases.items():
            with self.subTest(name), self.assertRaises(DataError):
                validate(mutate(raw_students(30)))

    def test_boundary_values_are_accepted(self):
        df = with_value("cgpa", 10.0, row=0)(with_value("cgpa", 0.0, row=1)(raw_students(30)))
        validate(df)


class LoadDataTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        patcher = mock.patch.dict(os.environ)
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop(DB_URL_ENV, None)

    def test_missing_csv_points_to_generator(self):
        with self.assertRaisesRegex(DataError, "generate_data"):
            load_data(self.tmp / "nope.csv")

    def test_empty_csv(self):
        path = self.tmp / "empty.csv"
        path.write_text("")
        with self.assertRaises(DataError):
            load_data(path)

    def test_csv_round_trip_adds_skill_flags(self):
        path = self.tmp / "s.csv"
        raw_students(40).to_csv(path, index=False)
        df = load_data(path)
        self.assertEqual(len(df), 40)
        self.assertIn("has_python", df.columns)

    @unittest.skipIf(sqlalchemy is None, "sqlalchemy not installed")
    def test_database_takes_precedence_over_csv(self):
        db = self.tmp / "t.db"
        engine = sqlalchemy.create_engine(f"sqlite:///{db}")
        raw_students(25).to_sql("students", engine, index=False)
        engine.dispose()
        os.environ[DB_URL_ENV] = f"sqlite:///{db}"
        self.assertEqual(len(load_data(self.tmp / "nope.csv")), 25)

    @unittest.skipIf(sqlalchemy is None, "sqlalchemy not installed")
    def test_unreachable_database_hides_connection_details(self):
        os.environ[DB_URL_ENV] = "sqlite:////no/such/dir/x.db"
        with self.assertRaises(DataError) as ctx:
            load_data(self.tmp / "nope.csv")
        self.assertNotIn("/no/such/dir", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
