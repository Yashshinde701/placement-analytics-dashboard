"""Generate a synthetic placement dataset.  Usage: python generate_data.py [--n 500]"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from dataset import COLUMNS, DATA_PATH, SKILLS, add_skill_flags

BRANCHES = ["CSE", "IT", "AI&DS", "ECS", "Mechanical", "Civil"]
BRANCH_P = [0.30, 0.20, 0.15, 0.15, 0.10, 0.10]
TECH = ["CSE", "IT", "AI&DS", "ECS"]


def generate(n: int = 500, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    branch = rng.choice(BRANCHES, size=n, p=BRANCH_P)
    cgpa = np.clip(rng.normal(7.3, 1.0, n), 5.0, 10.0).round(2)
    n_skills = np.where(np.isin(branch, TECH), rng.integers(3, 7, n), rng.integers(1, 4, n))

    df = pd.DataFrame({
        "student_id": [f"S{i:04d}" for i in range(1, n + 1)],
        "branch": branch,
        "cgpa": cgpa,
        "backlogs": rng.choice([0, 1, 2, 3], size=n, p=[0.70, 0.15, 0.10, 0.05]),
        "internships": rng.choice([0, 1, 2], size=n, p=[0.60, 0.30, 0.10]),
        "projects": rng.choice([0, 1, 2, 3, 4], size=n, p=[0.10, 0.25, 0.30, 0.20, 0.15]),
        "certifications": rng.choice([0, 1, 2, 3, 4], size=n, p=[0.20, 0.30, 0.25, 0.15, 0.10]),
        "aptitude_score": np.clip(rng.normal(60 + (cgpa - 7) * 6, 12), 20, 100).round(1),
        "communication_score": np.clip(rng.normal(60, 15, n), 20, 100).round(1),
        "skills": [", ".join(rng.choice(SKILLS, size=k, replace=False)) for k in n_skills],
    })

    # The "recruiter" rule the model is supposed to rediscover, plus noise.
    f = add_skill_flags(df)
    score = (
        0.9 * (f["cgpa"] - 7) - 0.8 * f["backlogs"] + 0.5 * f["internships"]
        + 0.15 * f["projects"] + 0.2 * f["certifications"]
        + 0.03 * (f["aptitude_score"] - 60) + 0.02 * (f["communication_score"] - 60)
        + 0.4 * f["has_python"] + 0.4 * f["has_sql"]
        + rng.normal(0, 0.6, n)
    )
    df["shortlisted"] = (score > np.quantile(score, 0.55)).astype(int)  # top 45%
    return df[COLUMNS]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, default=500)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=Path, default=DATA_PATH)
    args = ap.parse_args()

    df = generate(args.n, args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(f"Wrote {len(df)} students to {args.out} "
          f"(shortlist rate {df['shortlisted'].mean():.1%})")


if __name__ == "__main__":
    main()
