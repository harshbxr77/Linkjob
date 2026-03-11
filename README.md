# LinkedIn Job Automation

This project provides a Python-based workflow for:

- logging into LinkedIn with environment-based credentials
- remembering your login with a saved browser profile and encrypted session cookies
- scraping Easy Apply job listings for selected MBA-aligned roles
- filtering out marketing, HR, finance, accounting, and sales roles
- scoring job descriptions against resume skills
- storing jobs and applications in SQLite
- reviewing results in a Streamlit dashboard

## Setup

1. Create a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and fill in your credentials and session key.
4. Place your resume at `data/resume.pdf` or update `RESUME_PATH`.
5. Generate a session key with `python bootstrap.py`.
6. Run `python main.py --dry-run` to verify local setup.
7. Run `python main.py`.

## Cloud Data Sync

The deployed Streamlit dashboard cannot read your local SQLite file directly. The project now supports background sync through a GitHub-backed JSON snapshot.

To enable automatic background sync from your local bot to the deployed dashboard:

1. Run the bot locally with `python main.py run`
2. Set `AUTO_PUSH_SYNC=true` in `.env`
3. Make sure your local machine can `git push origin main`
4. After each run, the bot updates `sync/dashboard_data.json` and pushes it
5. The deployed dashboard fetches that file automatically in the background

Manual export is still available with `python main.py export`.
This writes:

- `data/dashboard_export.json`
- `sync/dashboard_data.json`

Each imported application record now keeps:

- company
- role title
- LinkedIn role ID
- job description
- applied date
- job link

## Local Preferences And Background Runs

The local dashboard sidebar now lets you save:

- search keywords
- locations
- allowed keywords
- blocked keywords
- run times
- daily application limit

These preferences are stored in `data/preferences.json` and used by:

- `python main.py run`
- `python main.py scheduler`
- the launcher background scheduler option

## Remember Login

The app now reuses your LinkedIn login across runs using:

- a persistent Chrome profile in `data/browser-profile`
- encrypted cookies in `data/linkedin_session.enc`

After the first successful login, future launches should open directly into the signed-in session unless LinkedIn expires or challenges it.

## Direct Launch

Use one of these launchers on Windows:

- `Launch-LinkJob.bat`
- `powershell -ExecutionPolicy Bypass -File .\launch-linkjob.ps1`

The launcher gives you a menu for bot run, dashboard, scheduler, background scheduler, bootstrap, and dry-run.

To start the dashboard:

`streamlit run ui/dashboard.py`

To run the scheduler:

`python scheduler.py`

## Notes

- `LINKEDIN_AUTO_SUBMIT=false` keeps the application flow in review mode and avoids blind submissions.
- Selenium selectors may need adjustment if LinkedIn updates the DOM.
- Use a valid Fernet key for `LINKEDIN_SESSION_KEY`.
