"""Pure aggregation helpers behind the dashboard charts (no Streamlit here)."""
import numpy as np
import pandas as pd

from dataset import SKILL_FLAGS, SKILLS

CGPA_BINS = [0, 6, 7, 8, 9, np.inf]
CGPA_LABELS = ["<6", "6-7", "7-8", "8-9", "9-10"]


def cgpa_band(cgpa: pd.Series) -> pd.Series:
    # right=False -> bands are [lo, hi): 6.0 belongs to "6-7", 10.0 to "9-10".
    return pd.cut(cgpa, CGPA_BINS, labels=CGPA_LABELS, right=False).rename("cgpa_band")


def rate_by(df: pd.DataFrame, key) -> pd.DataFrame:
    """Shortlist rate (%) and group size per value of a column name or Series."""
    out = df.groupby(key, observed=True)["shortlisted"].agg(
        students="size", rate="mean"
    )
    out["rate"] = (out["rate"] * 100).round(1)
    return out.reset_index()


def skill_table(df: pd.DataFrame) -> pd.DataFrame:
    """Per skill: holders and their shortlist rate (NaN if nobody has it)."""
    flags = df[SKILL_FLAGS]
    holders = flags.sum()
    shortlisted = flags.mul(df["shortlisted"], axis=0).sum()
    rate = (shortlisted / holders.replace(0, np.nan) * 100).round(1)
    return pd.DataFrame(
        {"skill": SKILLS, "students": holders.to_numpy(), "rate": rate.to_numpy()}
    ).sort_values("rate", ascending=False, na_position="last", ignore_index=True)
