from __future__ import annotations

import argparse
import subprocess
import sys

from config import AppConfig
from ai_matcher import match_resume_to_job
from database import Database
from job_apply import apply_to_job
from job_filter import filter_job
from job_scraper import SEARCH_KEYWORDS, SEARCH_LOCATIONS, scrape_jobs
from linkedin_login import login_to_linkedin


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LinkedIn job automation runner")
    parser.add_argument(
        "command",
        nargs="?",
        default="run",
        choices=["run", "dashboard", "scheduler", "bootstrap", "export"],
        help="Command to execute.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Initialize config and database without opening a browser session.",
    )
    return parser.parse_args()


def run(dry_run: bool = False) -> None:
    config = AppConfig.load()
    if not dry_run and not config.resume_path.exists():
        raise FileNotFoundError(f"Resume file not found: {config.resume_path}")

    database = Database(config.db_path)
    if dry_run:
        print(f"Dry run complete. Database ready at: {config.db_path}")
        return

    driver = login_to_linkedin(config)

    applied_today = database.jobs_applied_today()
    try:
        for keyword in SEARCH_KEYWORDS:
            for location in SEARCH_LOCATIONS:
                jobs = scrape_jobs(driver, keyword, location)
                for job in jobs:
                    decision = filter_job(job)
                    if not decision.accepted:
                        continue

                    match = match_resume_to_job(
                        job_description=job.get("job_description", ""),
                        openai_api_key=config.openai_api_key,
                        model=config.openai_model,
                    )
                    job["match_score"] = match.match_score
                    job_id = database.upsert_job(job)

                    should_apply = (
                        match.match_score > 65
                        and bool(job.get("easy_apply"))
                        and applied_today < config.daily_application_limit
                    )
                    if not should_apply:
                        continue

                    success = apply_to_job(
                        driver=driver,
                        job_link=job["job_link"],
                        resume_path=config.resume_path,
                        auto_submit=config.auto_submit,
                    )
                    if success:
                        database.create_application(job_id, str(config.resume_path), None)
                        if config.auto_submit:
                            database.mark_applied(job["job_link"])
                            applied_today += 1
                        else:
                            database.mark_reviewed(job["job_link"])
    finally:
        driver.quit()

    exported_path = database.export_snapshot(config.export_path)
    print(f"Dashboard export updated: {exported_path}")


def export_dashboard_data() -> None:
    config = AppConfig.load()
    database = Database(config.db_path)
    exported_path = database.export_snapshot(config.export_path)
    print(f"Dashboard export written to: {exported_path}")


if __name__ == "__main__":
    args = parse_args()
    if args.command == "run":
        run(dry_run=args.dry_run)
    elif args.command == "dashboard":
        raise SystemExit(
            subprocess.call([sys.executable, "-m", "streamlit", "run", "ui/dashboard.py"])
        )
    elif args.command == "scheduler":
        from scheduler import start_scheduler

        start_scheduler()
    elif args.command == "bootstrap":
        from bootstrap import main as bootstrap_main

        bootstrap_main()
    elif args.command == "export":
        export_dashboard_data()
