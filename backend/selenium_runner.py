# backend/selenium_runner.py
"""
Selenium runner (robust). Uses webdriver-manager to auto-download the driver.
Creates Chrome driver using a Service object to avoid multiple-values TypeError.
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import os
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_TARGET_MAP = {
    "login_page": None,
    "username_field": "username_field",
    "password_field": "password_field",
    "login_button": "login_button",
    "dashboard": "dashboard",
    "registration_page": None,
    "name_field": "name_field",
    "email_field": "email_field",
    "register_button": "register_button",
    "confirmation": "confirmation",
    "home_page": None,
    "search_box": "search_box",
    "search_button": "search_button",
    "results": "results",
    "product_page": None,
    "add_to_cart_button": "add_to_cart_button",
    "cart": "cart"
}

def _get_driver(headless: bool = True) -> webdriver.Chrome:
    options = Options()
    if headless:
        # modern headless flag; include safety flags
        try:
            options.add_argument("--headless=new")
        except Exception:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

    # Try to use webdriver-manager if available (auto-download)
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        driver_path = ChromeDriverManager().install()
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        logger.info("Started Chrome via webdriver-manager, driver path: %s", driver_path)
        return driver
    except Exception as e:
        logger.warning("webdriver-manager not usable or failed: %s", e)

    # Fallback: use CHROMEDRIVER_PATH env var or driver on PATH
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH")
    if chromedriver_path and os.path.exists(chromedriver_path):
        try:
            service = Service(chromedriver_path)
            driver = webdriver.Chrome(service=service, options=options)
            logger.info("Started Chrome via CHROMEDRIVER_PATH: %s", chromedriver_path)
            return driver
        except Exception as e:
            logger.exception("Failed to start Chrome using CHROMEDRIVER_PATH: %s", e)

    # Final fallback: try without explicit service (relies on chromedriver on PATH)
    try:
        driver = webdriver.Chrome(options=options)
        logger.info("Started Chrome via default PATH")
        return driver
    except Exception as e:
        logger.exception("Unable to initialize Chrome WebDriver. Install webdriver-manager or set CHROMEDRIVER_PATH.")
        raise RuntimeError("No suitable Chrome WebDriver found. Install webdriver-manager or set CHROMEDRIVER_PATH.") from e

def run_testcase(tc: Dict, headless: bool = True, target_map: Optional[Dict[str,str]] = None) -> List[Dict]:
    """
    Run a single testcase (dict) and return per-step results.
    Demo-level runner: doesn't implement sophisticated waits or selectors.
    """
    if target_map is None:
        target_map = DEFAULT_TARGET_MAP
    results = []
    driver = _get_driver(headless=headless)
    try:
        # Use local sample site file
        base_file = os.path.abspath("data/sample_site/index.html")
        file_url = "file://" + base_file
        for step in tc.get("steps", []):
            action = step.get("action")
            target = step.get("target")
            mapped = target_map.get(target, target) if target is not None else None
            result = {"step": step.get("step"), "action": action, "target": target, "status": "SKIP", "error": None}
            try:
                if action == "open":
                    driver.get(file_url)
                    result["status"] = "PASS"
                elif action == "input":
                    if not mapped:
                        result["status"] = "FAIL"
                        result["error"] = "No mapping for target"
                    else:
                        elem = driver.find_element(By.ID, mapped)
                        elem.clear()
                        elem.send_keys(step.get("value") or "test")
                        result["status"] = "PASS"
                elif action == "click":
                    if not mapped:
                        result["status"] = "FAIL"
                        result["error"] = "No mapping for target"
                    else:
                        elem = driver.find_element(By.ID, mapped)
                        elem.click()
                        result["status"] = "PASS"
                elif action == "assert":
                    if not mapped:
                        result["status"] = "FAIL"
                        result["error"] = "No mapping for target"
                    else:
                        elems = driver.find_elements(By.ID, mapped)
                        if elems:
                            result["status"] = "PASS"
                        else:
                            result["status"] = "FAIL"
                            result["error"] = "Element not found"
                else:
                    result["status"] = "SKIP"
                # short delay to allow JS to run in simple sample site
                time.sleep(0.4)
            except Exception as e:
                logger.exception("Step failed: %s", e)
                result["status"] = "FAIL"
                result["error"] = str(e)
            results.append(result)
    finally:
        try:
            driver.quit()
        except Exception:
            pass
    return results

if __name__ == "__main__":
    # quick manual demo
    tc = {
        "id": "tc_demo",
        "title": "Demo login",
        "steps": [
            {"step":1,"action":"open","target":"login_page"},
            {"step":2,"action":"input","target":"username_field","value":"user1"},
            {"step":3,"action":"input","target":"password_field","value":"pass1"},
            {"step":4,"action":"click","target":"login_button"},
            {"step":5,"action":"assert","target":"dashboard"}
        ]
    }
    print(run_testcase(tc, headless=True))
