from __future__ import annotations

import random
import re
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


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _existing_resume_present(driver: WebDriver, resume_path: Path) -> bool:
    page = driver.page_source.lower()
    return resume_path.name.lower() in page or "resume" in page and "uploaded" in page


def _upload_resume_if_needed(driver: WebDriver, resume_path: Path) -> None:
    if _existing_resume_present(driver, resume_path):
        return
    try:
        upload_input = driver.find_element(By.XPATH, "//input[@type='file']")
        upload_input.send_keys(str(resume_path))
        _human_delay()
    except NoSuchElementException:
        pass


def _field_value(profile: dict[str, str], context: str) -> str | None:
    context = _normalize(context)
    mapping = [
        (("full name", "first name", "last name", "name"), profile.get("full_name")),
        (("phone", "mobile", "contact number"), profile.get("phone")),
        (("city", "location", "current location"), profile.get("city")),
        (("linkedin", "profile url"), profile.get("linkedin_url")),
        (("experience", "years of experience"), profile.get("years_experience")),
        (("notice",), profile.get("notice_period_days")),
    ]
    for keys, value in mapping:
        if any(key in context for key in keys):
            return value or None
    return None


def _fill_text_fields(driver: WebDriver, profile: dict[str, str]) -> None:
    inputs = driver.find_elements(
        By.XPATH,
        "//input[not(@type='hidden') and not(@type='file') and not(@disabled)] | //textarea[not(@disabled)]",
    )
    for element in inputs:
        try:
            current_value = (element.get_attribute("value") or "").strip()
            if current_value:
                continue
            context = " ".join(
                filter(
                    None,
                    [
                        element.get_attribute("aria-label"),
                        element.get_attribute("name"),
                        element.get_attribute("placeholder"),
                    ],
                )
            )
            value = _field_value(profile, context)
            if not value:
                continue
            element.clear()
            element.send_keys(value)
            _human_delay()
        except Exception:
            continue


def _click_radio_or_option(driver: WebDriver, labels: tuple[str, ...]) -> bool:
    for label in labels:
        xpath = (
            f"//label[contains(translate(normalize-space(.), "
            f"'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '{label.lower()}')]"
        )
        try:
            option = driver.find_element(By.XPATH, xpath)
            driver.execute_script("arguments[0].click();", option)
            _human_delay()
            return True
        except NoSuchElementException:
            continue
        except Exception:
            continue
    return False


def _fill_choice_fields(driver: WebDriver, profile: dict[str, str]) -> None:
    sponsorship = _normalize(profile.get("requires_sponsorship", ""))
    work_auth = _normalize(profile.get("work_authorization", ""))
    page = driver.page_source.lower()

    if "sponsorship" in page:
        if sponsorship in {"no", "false"}:
            _click_radio_or_option(driver, ("no",))
        elif sponsorship in {"yes", "true"}:
            _click_radio_or_option(driver, ("yes",))

    if "authorized to work" in page or "work authorization" in page:
        if work_auth in {"yes", "true"}:
            _click_radio_or_option(driver, ("yes",))
        elif work_auth in {"no", "false"}:
            _click_radio_or_option(driver, ("no",))


def _fill_easy_apply_step(driver: WebDriver, resume_path: Path, profile: dict[str, str]) -> None:
    _upload_resume_if_needed(driver, resume_path)
    _fill_text_fields(driver, profile)
    _fill_choice_fields(driver, profile)


def apply_to_job(
    driver: WebDriver,
    job_link: str,
    resume_path: Path,
    profile: dict[str, str] | None = None,
    auto_submit: bool = False,
) -> bool:
    profile = profile or {}
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

    _fill_easy_apply_step(driver, resume_path, profile)

    # Conservative workflow: advance known form steps, then stop unless auto-submit is enabled.
    while True:
        _fill_easy_apply_step(driver, resume_path, profile)
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
