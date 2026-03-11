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

## Remember Login

The app now reuses your LinkedIn login across runs using:

- a persistent Chrome profile in `data/browser-profile`
- encrypted cookies in `data/linkedin_session.enc`

After the first successful login, future launches should open directly into the signed-in session unless LinkedIn expires or challenges it.

## Direct Launch

Use one of these launchers on Windows:

- `Launch-LinkJob.bat`
- `powershell -ExecutionPolicy Bypass -File .\launch-linkjob.ps1`

The launcher gives you a menu for bot run, dashboard, scheduler, bootstrap, and dry-run.

To start the dashboard:

`streamlit run ui/dashboard.py`

To run the scheduler:

`python scheduler.py`

## Notes

- `LINKEDIN_AUTO_SUBMIT=false` keeps the application flow in review mode and avoids blind submissions.
- Selenium selectors may need adjustment if LinkedIn updates the DOM.
- Use a valid Fernet key for `LINKEDIN_SESSION_KEY`.
