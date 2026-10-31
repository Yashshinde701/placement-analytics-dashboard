"""Shortlisting model: train, evaluate, predict."""
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_score, recall_score)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import StandardScaler

from dataset import FEATURES, NUMERIC, DataError, add_skill_flags

MIN_PER_CLASS = 10  # 5-fold CV plus a stratified split need a few of each class


@dataclass(frozen=True)
class Report:
    model: Pipeline            # fitted on ALL rows; used for predictions
    accuracy: float            # the four scores below: 20% holdout
    precision: float
    recall: float
    f1: float
    cv_mean: float             # 5-fold CV accuracy: shows how stable the holdout is
    cv_std: float
    confusion: np.ndarray      # [[TN, FP], [FN, TP]] on the holdout
    weights: pd.Series         # log-odds change per +1 standard deviation
    holdout_size: int


def _pipeline() -> Pipeline:
    # Scaling makes the coefficients comparable across features.
    return make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))


def train(df: pd.DataFrame, seed: int = 0) -> Report:
    X, y = df[FEATURES], df["shortlisted"]
    if y.value_counts().reindex([0, 1], fill_value=0).min() < MIN_PER_CLASS:
        raise DataError(
            f"Need at least {MIN_PER_CLASS} shortlisted and {MIN_PER_CLASS} "
            "not-shortlisted students to train the model"
        )

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=seed
    )
    pred = _pipeline().fit(X_tr, y_tr).predict(X_te)
    cv = cross_val_score(
        _pipeline(), X, y, cv=StratifiedKFold(5, shuffle=True, random_state=seed)
    )
    final = _pipeline().fit(X, y)
    return Report(
        model=final,
        accuracy=accuracy_score(y_te, pred),
        precision=precision_score(y_te, pred, zero_division=0),
        recall=recall_score(y_te, pred, zero_division=0),
        f1=f1_score(y_te, pred, zero_division=0),
        cv_mean=float(cv.mean()),
        cv_std=float(cv.std()),
        confusion=confusion_matrix(y_te, pred, labels=[0, 1]),
        weights=pd.Series(final[-1].coef_[0], index=FEATURES).sort_values(),
        holdout_size=len(y_te),
    )


def shortlist_probability(model: Pipeline, profile: dict) -> float:
    """`profile` needs the NUMERIC columns plus a comma-separated 'skills' string."""
    row = add_skill_flags(pd.DataFrame([{**profile, "skills": profile.get("skills", "")}]))
    return float(model.predict_proba(row[FEATURES])[0, 1])
