from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

from config import DB_PATH


def load_frame(query: str, db_path: Path) -> pd.DataFrame:
    with sqlite3.connect(db_path) as connection:
        return pd.read_sql_query(query, connection)


def main() -> None:
    st.set_page_config(page_title="LinkedIn Job Automation", layout="wide")
    st.title("LinkedIn Job Automation")

    db_path = DB_PATH
    if not db_path.exists():
        st.warning("Database not found. Run the bot first to create application data.")
        return

    summary_df = load_frame(
        """
        SELECT
            COUNT(*) AS total_jobs_scanned,
            SUM(CASE WHEN applied_status = 'applied' THEN 1 ELSE 0 END) AS jobs_applied,
            ROUND(AVG(match_score), 2) AS average_match_score
        FROM jobs
        """,
        db_path,
    )
    jobs_df = load_frame(
        """
        SELECT company, job_title, location, match_score, applied_status, posted_date
        FROM jobs
        ORDER BY COALESCE(match_score, 0) DESC
        """,
        db_path,
    )
    companies_df = load_frame(
        """
        SELECT company, COUNT(*) AS total_applied
        FROM jobs
        WHERE applied_status = 'applied'
        GROUP BY company
        ORDER BY total_applied DESC, company ASC
        LIMIT 10
        """,
        db_path,
    )
    pending_df = load_frame(
        """
        SELECT COUNT(*) AS pending_responses
        FROM applications
        WHERE response_status = 'pending'
        """,
        db_path,
    )

    summary = summary_df.iloc[0].fillna(0)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Jobs Found", int(summary["total_jobs_scanned"]))
    c2.metric("Applied", int(summary["jobs_applied"]))
    c3.metric("Match Rate", f'{float(summary["average_match_score"]):.1f}%')
    c4.metric("Pending Responses", int(pending_df.iloc[0]["pending_responses"]))

    left, right = st.columns([2, 1])
    with left:
        st.subheader("Match Score Distribution")
        st.bar_chart(jobs_df["match_score"].fillna(0))
        st.subheader("Recommended Jobs")
        st.dataframe(jobs_df.head(20), use_container_width=True)

    with right:
        st.subheader("Top Companies")
        st.dataframe(companies_df, use_container_width=True)


if __name__ == "__main__":
    main()
