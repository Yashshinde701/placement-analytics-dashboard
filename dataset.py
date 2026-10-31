"""Load, validate and featurize the student dataset (CSV or SQL database)."""
import os
from pathlib import Path

import pandas as pd

DATA_PATH = Path(__file__).parent / "data" / "students.csv"
DB_URL_ENV = "PLACEMENT_DB_URL"

SKILLS = ["Python", "Java", "SQL", "C", "Cloud", "ML", "Web"]
SKILL_FLAGS = [f"has_{s.lower()}" for s in SKILLS]

# Inclusive limits for every numeric input column.
BOUNDS = {
    "cgpa": (0, 10),
    "backlogs": (0, 50),
    "internships": (0, 20),
    "projects": (0, 50),
    "certifications": (0, 50),
    "aptitude_score": (0, 100),
    "communication_score": (0, 100),
}
NUMERIC = list(BOUNDS)
FEATURES = NUMERIC + SKILL_FLAGS
COLUMNS = ["student_id", "branch", *NUMERIC, "skills", "shortlisted"]


class DataError(Exception):
    """Bad, missing or unreachable input data. The message is safe to show users."""


def validate(df: pd.DataFrame) -> pd.DataFrame:
    """Check the external-data contract; return a clean copy with COLUMNS only."""
    missing = [c for c in COLUMNS if c not in df.columns]
    if missing:
        raise DataError(f"Missing columns: {', '.join(missing)}")
    df = df[COLUMNS].copy()
    if df.empty:
        raise DataError("The dataset contains no students")

    numeric = [*NUMERIC, "shortlisted"]
    df[numeric] = df[numeric].apply(pd.to_numeric, errors="coerce")
    null_cols = [c for c in [*numeric, "student_id", "branch"] if df[c].isna().any()]
    if null_cols:
        raise DataError(f"Missing or non-numeric values in: {', '.join(null_cols)}")

    df["student_id"] = df["student_id"].astype(str)
    if df["student_id"].duplicated().any():
        raise DataError("Duplicate student_id values")
    for col, (lo, hi) in BOUNDS.items():
        n_bad = int((~df[col].between(lo, hi)).sum())
        if n_bad:
            raise DataError(f"{col}: {n_bad} value(s) outside [{lo}, {hi}]")
    if not df["shortlisted"].isin([0, 1]).all():
        raise DataError("shortlisted must be 0 or 1")

    df["shortlisted"] = df["shortlisted"].astype(int)
    df["skills"] = df["skills"].fillna("")
    return df


def add_skill_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Expand the comma-separated 'skills' text into has_<skill> 0/1 columns.

    Exact token match, not substring: 'Cloud' must not count as skill 'C'.
    Unknown skills are ignored.
    """
    df = df.copy()
    tokens = df["skills"].fillna("").map(
        lambda s: {t.strip().casefold() for t in s.split(",")}
    )
    for skill, flag in zip(SKILLS, SKILL_FLAGS):
        df[flag] = tokens.map(lambda t, k=skill.casefold(): int(k in t))
    df["skill_count"] = df[SKILL_FLAGS].sum(axis=1)
    return df


def _read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except FileNotFoundError as exc:
        raise DataError(f"{path.name} not found. Run: python generate_data.py") from exc
    except (pd.errors.EmptyDataError, pd.errors.ParserError) as exc:
        raise DataError(f"{path.name} is not a valid CSV file") from exc


def _read_db(url: str) -> pd.DataFrame:
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.exc import SQLAlchemyError
    except ImportError as exc:
        raise DataError(
            "Database support is not installed: pip install -r requirements-mysql.txt"
        ) from exc

    engine = None
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            return pd.read_sql(text(f"SELECT {', '.join(COLUMNS)} FROM students"), conn)
    except SQLAlchemyError as exc:
        # The cause (host, driver error) goes to the server log via the exception
        # chain; the user-facing message must not echo connection details.
        raise DataError(
            "Could not read students from the database. Check "
            f"{DB_URL_ENV} and that the server is reachable."
        ) from exc
    finally:
        if engine is not None:
            engine.dispose()


def load_data(path: Path = DATA_PATH) -> pd.DataFrame:
    """Read from PLACEMENT_DB_URL if set, otherwise from the CSV at `path`."""
    url = os.getenv(DB_URL_ENV)
    raw = _read_db(url) if url else _read_csv(path)
    return add_skill_flags(validate(raw))
