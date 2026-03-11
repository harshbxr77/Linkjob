from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import AppConfig


LINKEDIN_LOGIN_URL = "https://www.linkedin.com/login"
LINKEDIN_FEED_URL = "https://www.linkedin.com/feed/"


def build_driver(config: AppConfig) -> webdriver.Chrome:
    options = ChromeOptions()
    if config.headless:
        options.add_argument("--headless=new")
    config.browser_profile_dir.mkdir(parents=True, exist_ok=True)
    runtime_profile_dir = config.browser_profile_dir / "runtime"
    if runtime_profile_dir.exists():
        shutil.rmtree(runtime_profile_dir, ignore_errors=True)
    runtime_profile_dir.mkdir(parents=True, exist_ok=True)
    if config.browser_binary:
        options.binary_location = str(config.browser_binary)
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--remote-debugging-port=0")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-gpu")
    options.add_argument(f"--user-data-dir={runtime_profile_dir}")
    service = ChromeService(executable_path=str(config.driver_path)) if config.driver_path else ChromeService()
    return webdriver.Chrome(service=service, options=options)


def _cipher(session_key: str) -> Fernet:
    return Fernet(session_key.encode("utf-8"))


def save_session(driver: webdriver.Chrome, session_file: Path, session_key: str) -> None:
    cookies = driver.get_cookies()
    payload = json.dumps(cookies).encode("utf-8")
    encrypted = _cipher(session_key).encrypt(payload)
    session_file.write_bytes(encrypted)


def load_session(driver: webdriver.Chrome, session_file: Path, session_key: str) -> bool:
    if not session_file.exists():
        return False

    try:
        encrypted = session_file.read_bytes()
        cookies = json.loads(_cipher(session_key).decrypt(encrypted).decode("utf-8"))
    except (InvalidToken, json.JSONDecodeError):
        return False

    driver.get("https://www.linkedin.com")
    for cookie in cookies:
        cookie.pop("sameSite", None)
        try:
            driver.add_cookie(cookie)
        except Exception:
            continue
    driver.get(LINKEDIN_FEED_URL)
    time.sleep(2)
    return "feed" in driver.current_url


def handle_2fa(driver: webdriver.Chrome, timeout_seconds: int = 180) -> None:
    wait = WebDriverWait(driver, timeout_seconds)
    try:
        wait.until(EC.url_contains("/feed"))
        return
    except TimeoutException:
        raise TimeoutException(
            "2FA or checkpoint did not complete within the allotted time."
        )


def login_to_linkedin(config: AppConfig) -> webdriver.Chrome:
    config.validate()
    driver = build_driver(config)

    if load_session(driver, config.session_file, config.linkedin_session_key):
        return driver

    wait = WebDriverWait(driver, 20)
    driver.get(LINKEDIN_LOGIN_URL)
    wait.until(EC.visibility_of_element_located((By.ID, "username"))).send_keys(config.linkedin_email)
    wait.until(EC.visibility_of_element_located((By.ID, "password"))).send_keys(config.linkedin_password)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))).click()

    handle_2fa(driver)
    save_session(driver, config.session_file, config.linkedin_session_key)
    return driver
