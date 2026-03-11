from __future__ import annotations

import json
import sqlite3
import sys
from urllib.request import urlopen
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import AppConfig, DB_PATH
from database import Database


def load_frame(query: str, db_path: Path) -> pd.DataFrame:
    with sqlite3.connect(db_path) as connection:
        return pd.read_sql_query(query, connection)


@st.cache_data(ttl=300, show_spinner=False)
def load_public_sync(url: str) -> dict:
    with urlopen(url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    st.set_page_config(page_title="LinkedIn Job Automation", layout="wide")
    st.title("LinkedIn Job Automation")

    config = AppConfig.load()
    db_path = DB_PATH
    database = Database(db_path)

    with st.sidebar:
        st.header("Data Sync")
        if st.button("Refresh background sync", use_container_width=True):
            st.cache_data.clear()
        st.caption("This dashboard pulls synced application records from the GitHub-backed JSON snapshot in the background.")

    public_data: dict | None = None
    sync_error = None
    try:
        public_data = load_public_sync(config.public_sync_url)
    except Exception as exc:
        sync_error = str(exc)

    if public_data:
        summary = pd.Series(public_data.get("summary", {})).fillna(0)
        history_df = pd.DataFrame(public_data.get("applications", []))
        jobs_df = history_df[["company", "job_title", "location", "match_score", "applied_status", "posted_date"]].copy() if not history_df.empty else pd.DataFrame(columns=["company", "job_title", "location", "match_score", "applied_status", "posted_date"])
        companies_df = (
            history_df.groupby("company", dropna=False)
            .size()
            .reset_index(name="total_applied")
            .sort_values(["total_applied", "company"], ascending=[False, True])
            .head(10)
            if not history_df.empty
            else pd.DataFrame(columns=["company", "total_applied"])
        )
        pending_count = int((history_df.get("response_status", pd.Series(dtype="object")).fillna("pending") == "pending").sum()) if not history_df.empty else 0
        pending_df = pd.DataFrame([{"pending_responses": pending_count}])
    else:
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
        history_df = load_frame(
            """
            SELECT
                jobs.company,
                jobs.job_title,
                jobs.role_id,
                jobs.date_applied,
                jobs.job_description,
                jobs.job_link,
                jobs.applied_status,
                applications.response_status
            FROM jobs
            LEFT JOIN applications ON applications.job_id = jobs.id
            WHERE jobs.applied_status IN ('applied', 'reviewed')
            ORDER BY COALESCE(jobs.date_applied, applications.created_at) DESC, jobs.company ASC
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

    st.subheader("Application Records")
    if sync_error and history_df.empty:
        st.warning(f"Background sync unavailable: {sync_error}")
    if history_df.empty:
        st.info("No application records yet.")
    else:
        history_df["job_description"] = history_df["job_description"].fillna("").str.slice(0, 600)
        st.dataframe(
            history_df.rename(
                columns={
                    "company": "Company",
                    "job_title": "Role",
                    "role_id": "Role ID",
                    "date_applied": "Date Applied",
                    "job_description": "Job Description",
                    "job_link": "Job Link",
                    "applied_status": "Status",
                    "response_status": "Response",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )


if __name__ == "__main__":
    main()
