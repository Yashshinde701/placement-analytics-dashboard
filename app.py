"""Placement Analytics Dashboard.  Run: streamlit run app.py"""
import logging

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from analysis import cgpa_band, rate_by, skill_table
from dataset import SKILLS, DataError, load_data
from model import Report, shortlist_probability, train

log = logging.getLogger(__name__)
NOISY_GROUP = 20  # rates over fewer students than this are mostly noise

st.set_page_config(page_title="Placement Analytics Dashboard", layout="wide")


@st.cache_data(ttl=600)
def get_data() -> pd.DataFrame:
    return load_data()


@st.cache_resource
def get_report(df: pd.DataFrame) -> Report:
    return train(df)


def rate_chart(data: pd.DataFrame, x: str, title: str) -> None:
    fig = px.bar(
        data.astype({x: str}), x=x, y="rate", hover_data=["students"],
        labels={"rate": "Shortlisted (%)"}, title=title,
    )
    fig.update_yaxes(range=[0, 100])
    st.plotly_chart(fig)
    # Charts are not readable by screen readers; the table is the text alternative.
    with st.expander(f"Data table: {title}"):
        st.dataframe(data, hide_index=True)


def overview_tab(df: pd.DataFrame) -> None:
    st.caption(f"Groups with fewer than {NOISY_GROUP} students give unreliable "
               "rates. Check the student counts in the tooltip or table.")
    left, right = st.columns(2)
    with left:
        rate_chart(rate_by(df, "branch"), "branch", "Shortlist rate by branch")
    with right:
        rate_chart(rate_by(df, cgpa_band(df["cgpa"])), "cgpa_band", "Shortlist rate by CGPA band")
    left, right = st.columns(2)
    with left:
        rate_chart(rate_by(df, "backlogs"), "backlogs", "Shortlist rate by backlogs")
    with right:
        rate_chart(rate_by(df, "internships"), "internships", "Shortlist rate by internships")


def skills_tab(df: pd.DataFrame) -> None:
    table = skill_table(df)
    left, right = st.columns(2)
    with left:
        fig = px.bar(table, x="skill", y="students", title="Students holding each skill")
        st.plotly_chart(fig)
    with right:
        rate_chart(table, "skill", "Shortlist rate among holders of each skill")


def model_tab(df: pd.DataFrame) -> None:
    try:
        report = get_report(df)
    except DataError as exc:
        st.warning(str(exc))
        return

    cols = st.columns(4)
    cols[0].metric("Accuracy (holdout)", f"{report.accuracy:.1%}")
    cols[1].metric("Precision", f"{report.precision:.1%}")
    cols[2].metric("Recall", f"{report.recall:.1%}")
    cols[3].metric("5-fold CV accuracy", f"{report.cv_mean:.1%} ± {report.cv_std:.1%}")
    st.caption(f"Holdout = {report.holdout_size} students not used for training. "
               "Scores describe this dataset only; they are not a general claim.")

    (tn, fp), (fn, tp) = report.confusion
    st.dataframe(
        pd.DataFrame({"Predicted no": [tn, fn], "Predicted yes": [fp, tp]},
                     index=["Actually no", "Actually yes"]),
    )

    weights = report.weights.rename_axis("feature").reset_index(name="weight")
    st.plotly_chart(px.bar(
        weights, x="weight", y="feature", orientation="h",
        title="Effect on shortlisting odds (log-odds per +1 standard deviation)",
    ))

    st.subheader("Try a student profile")
    with st.form("profile"):
        a, b, c = st.columns(3)
        profile = {
            "cgpa": a.number_input("CGPA", 0.0, 10.0, 7.5, 0.1),
            "backlogs": a.number_input("Backlogs", 0, 50, 0),
            "internships": b.number_input("Internships", 0, 20, 0),
            "projects": b.number_input("Projects", 0, 50, 2),
            "certifications": c.number_input("Certifications", 0, 50, 2),
            "aptitude_score": c.slider("Aptitude score", 0, 100, 60),
            "communication_score": st.slider("Communication score", 0, 100, 60),
        }
        chosen = st.multiselect("Skills", SKILLS, default=["Python", "SQL"])
        submitted = st.form_submit_button("Predict")
    if submitted:
        prob = shortlist_probability(report.model, {**profile, "skills": ", ".join(chosen)})
        st.metric("Estimated shortlisting probability", f"{prob:.0%}")
        st.caption("Output of a model fitted to this dataset. Illustrative only.")


def main() -> None:
    st.title("Placement Analytics Dashboard")
    st.caption("Which factors decide who gets shortlisted?")

    try:
        df = get_data()
    except DataError as exc:
        log.exception("Could not load data")
        st.error(str(exc))
        st.stop()

    branches = sorted(df["branch"].unique())
    picked = st.sidebar.multiselect("Branch", branches, default=branches)
    lo, hi = float(np.floor(df["cgpa"].min())), float(np.ceil(df["cgpa"].max()))
    cgpa_lo, cgpa_hi = st.sidebar.slider("CGPA range", lo, hi, (lo, hi), 0.1)

    view = df[df["branch"].isin(picked) & df["cgpa"].between(cgpa_lo, cgpa_hi)]
    if view.empty:
        st.warning("No students match these filters.")
        st.stop()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Students", len(view))
    c2.metric("Shortlisted", int(view["shortlisted"].sum()))
    c3.metric("Shortlist rate", f"{view['shortlisted'].mean():.1%}")
    c4.metric("Average CGPA", f"{view['cgpa'].mean():.2f}")

    overview, skills, modelling = st.tabs(["Overview", "Skills", "Model & prediction"])
    with overview:
        overview_tab(view)
    with skills:
        skills_tab(view)
    with modelling:
        model_tab(df)  # trained on everyone; the sidebar filters are for exploration


main()
