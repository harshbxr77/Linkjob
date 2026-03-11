from __future__ import annotations

import random
import re
import time
from urllib.parse import quote_plus

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


SEARCH_KEYWORDS = [
    "Technology Manager",
    "Product Manager",
    "Technology Consultant",
    "Risk Consultant",
    "Digital Transformation",
    "Strategy Consulting",
    "Program Manager",
    "IT Strategy",
]

SEARCH_LOCATIONS = ["India", "Bangalore", "Mumbai", "Remote"]


def human_pause(min_seconds: float = 1.2, max_seconds: float = 2.8) -> None:
    time.sleep(random.uniform(min_seconds, max_seconds))


def _safe_text(parent, xpath: str) -> str:
    try:
        return parent.find_element(By.XPATH, xpath).text.strip()
    except NoSuchElementException:
        return ""


def _extract_description(driver: WebDriver) -> str:
    selectors = [
        "//div[contains(@class,'jobs-description__content')]",
        "//div[contains(@class,'jobs-box__html-content')]",
    ]
    for xpath in selectors:
        try:
            return driver.find_element(By.XPATH, xpath).text.strip()
        except NoSuchElementException:
            continue
    return ""


def extract_role_id(job_link: str) -> str:
    match = re.search(r"/jobs/view/(\d+)", job_link)
    return match.group(1) if match else ""


def search_jobs(driver: WebDriver, keyword: str, location: str) -> None:
    encoded_keyword = quote_plus(keyword)
    encoded_location = quote_plus(location)
    url = (
        "https://www.linkedin.com/jobs/search/"
        f"?keywords={encoded_keyword}&location={encoded_location}&f_AL=true"
    )
    driver.get(url)
    human_pause()


def scrape_jobs(driver: WebDriver, keyword: str, location: str, limit: int = 20) -> list[dict[str, str]]:
    search_jobs(driver, keyword, location)
    wait = WebDriverWait(driver, 15)

    try:
        wait.until(
            EC.presence_of_all_elements_located((By.XPATH, "//ul[contains(@class,'jobs-search__results-list')]/li"))
        )
    except TimeoutException:
        return []

    cards = driver.find_elements(By.XPATH, "//ul[contains(@class,'jobs-search__results-list')]/li")[:limit]
    jobs: list[dict[str, str]] = []
    for card in cards:
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
            human_pause(0.8, 1.6)
            clickable = card.find_element(By.XPATH, ".//a[contains(@href,'/jobs/view/')]")
            job_link = clickable.get_attribute("href")
            clickable.click()
            human_pause()
            jobs.append(
                {
                    "job_title": _safe_text(card, ".//strong"),
                    "company": _safe_text(card, ".//*[contains(@class,'base-search-card__subtitle')]"),
                    "location": _safe_text(card, ".//*[contains(@class,'job-search-card__location')]"),
                    "job_description": _extract_description(driver),
                    "job_link": job_link,
                    "role_id": extract_role_id(job_link),
                    "easy_apply": "Easy Apply" in card.text,
                    "posted_date": _safe_text(card, ".//time"),
                }
            )
        except Exception:
            continue
    return jobs
