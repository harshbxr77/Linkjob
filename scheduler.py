from __future__ import annotations

import time

import schedule

from main import run


def start_scheduler() -> None:
    schedule.every().day.at("08:00").do(run)
    schedule.every().day.at("20:00").do(run)

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    start_scheduler()
