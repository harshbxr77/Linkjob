from __future__ import annotations

import time

import schedule

from config import AppConfig, load_preferences
from main import run


def start_scheduler() -> None:
    config = AppConfig.load()
    preferences = load_preferences(config.preferences_path)
    for run_time in preferences.get("run_times", ["08:00", "20:00"]):
        schedule.every().day.at(run_time).do(run)

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    start_scheduler()
