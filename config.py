from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UI_DIR = BASE_DIR / "ui"
SYNC_DIR = BASE_DIR / "sync"
SESSION_FILE = DATA_DIR / "linkedin_session.enc"
DB_PATH = DATA_DIR / "jobs.db"
EXPORT_PATH = DATA_DIR / "dashboard_export.json"
PUBLIC_EXPORT_PATH = SYNC_DIR / "dashboard_data.json"


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class AppConfig:
    linkedin_email: str
    linkedin_password: str
    linkedin_session_key: str
    openai_api_key: str | None
    openai_model: str
    browser: str
    headless: bool
    auto_submit: bool
    daily_application_limit: int
    resume_path: Path
    browser_profile_dir: Path
    auto_push_sync: bool
    public_sync_url: str
    db_path: Path = field(default=DB_PATH)
    session_file: Path = field(default=SESSION_FILE)
    export_path: Path = field(default=EXPORT_PATH)
    public_export_path: Path = field(default=PUBLIC_EXPORT_PATH)
    default_location: str = "India"

    @classmethod
    def load(cls) -> "AppConfig":
        load_dotenv()
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        UI_DIR.mkdir(parents=True, exist_ok=True)
        SYNC_DIR.mkdir(parents=True, exist_ok=True)

        return cls(
            linkedin_email=os.getenv("LINKEDIN_EMAIL", ""),
            linkedin_password=os.getenv("LINKEDIN_PASSWORD", ""),
            linkedin_session_key=os.getenv("LINKEDIN_SESSION_KEY", ""),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            browser=os.getenv("LINKEDIN_DRIVER", "chrome").strip().lower(),
            headless=_as_bool(os.getenv("LINKEDIN_HEADLESS"), default=False),
            auto_submit=_as_bool(os.getenv("LINKEDIN_AUTO_SUBMIT"), default=False),
            daily_application_limit=int(os.getenv("LINKEDIN_DAILY_APPLICATION_LIMIT", "10")),
            resume_path=(BASE_DIR / os.getenv("RESUME_PATH", "./data/resume.pdf")).resolve(),
            browser_profile_dir=(BASE_DIR / os.getenv("LINKEDIN_PROFILE_DIR", "./data/browser-profile")).resolve(),
            auto_push_sync=_as_bool(os.getenv("AUTO_PUSH_SYNC"), default=False),
            public_sync_url=os.getenv(
                "PUBLIC_SYNC_URL",
                "https://raw.githubusercontent.com/harshbxr77/Linkjob/main/sync/dashboard_data.json",
            ),
            default_location=os.getenv("DEFAULT_LOCATION", "India"),
        )

    def validate(self) -> None:
        missing = []
        if not self.linkedin_email:
            missing.append("LINKEDIN_EMAIL")
        if not self.linkedin_password:
            missing.append("LINKEDIN_PASSWORD")
        if not self.linkedin_session_key:
            missing.append("LINKEDIN_SESSION_KEY")
        if missing:
            missing_text = ", ".join(missing)
            raise ValueError(f"Missing required environment variables: {missing_text}")
