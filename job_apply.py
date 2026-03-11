from __future__ import annotations

import random
import time
from pathlib import Path

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def _human_delay() -> None:
    time.sleep(random.uniform(1.0, 2.2))


def _detect_captcha(driver: WebDriver) -> bool:
    page = driver.page_source.lower()
    return "captcha" in page or "security verification" in page


def apply_to_job(
    driver: WebDriver,
    job_link: str,
    resume_path: Path,
    auto_submit: bool = False,
) -> bool:
    driver.get(job_link)
    wait = WebDriverWait(driver, 10)
    _human_delay()

    if _detect_captcha(driver):
        return False

    try:
        easy_apply_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Easy Apply')]"))
        )
        easy_apply_button.click()
        _human_delay()
    except TimeoutException:
        return False

    try:
        upload_input = driver.find_element(By.XPATH, "//input[@type='file']")
        upload_input.send_keys(str(resume_path))
        _human_delay()
    except NoSuchElementException:
        pass

    # Conservative workflow: advance known form steps, then stop unless auto-submit is enabled.
    while True:
        try:
            next_button = driver.find_element(
                By.XPATH,
                "//button[contains(., 'Next') or contains(., 'Review')]",
            )
            if next_button.is_enabled():
                next_button.click()
                _human_delay()
                continue
        except NoSuchElementException:
            pass
        break

    if not auto_submit:
        return True

    try:
        submit_button = driver.find_element(By.XPATH, "//button[contains(., 'Submit application')]")
        if submit_button.is_enabled():
            submit_button.click()
            _human_delay()
            return True
    except NoSuchElementException:
        return False
    return False
