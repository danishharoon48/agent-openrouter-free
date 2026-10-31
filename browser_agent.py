import argparse
import json
import sys
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


def run_search(page, base_url):
    try:
        page.goto(base_url)
        page.fill("input#search", "browser automation")
        page.click("button[type=submit]")
        page.wait_for_selector("#search-result", state="visible")
        text = page.locator("#search-result").inner_text().strip()
        success = text == "Found: browser automation"
        return success, text if success else None, page.url
    except Exception:
        return False, None, page.url


def run_dynamic_dom(page, base_url):
    try:
        page.goto(urljoin(base_url, "/dynamic"))
        page.click("button#load-record")
        page.wait_for_selector("#dynamic-result", state="attached")
        page.wait_for_function(
            "() => document.querySelector('#dynamic-result').textContent.trim() === 'Loaded record: DYNAMIC-42'"
        )
        text = page.locator("#dynamic-result").inner_text().strip()
        success = text == "Loaded record: DYNAMIC-42"
        return success, text if success else None, page.url
    except Exception:
        return False, None, page.url


def run_pagination(page, base_url):
    try:
        page.goto(urljoin(base_url, "/page/1"))
        page.click("a#next")
        page.wait_for_function(
            "() => document.querySelector('h1').textContent.trim() === 'Page 2 of 2'"
        )
        text = page.locator("#page-record").inner_text().strip()
        success = text == "Record 2 of 2: pagination verified"
        return success, text if success else None, page.url
    except Exception:
        return False, None, page.url


def main():
    parser = argparse.ArgumentParser(description="Playwright scenario runner")
    parser.add_argument("--base-url", required=True, help="Base URL of the application")
    parser.add_argument("--scenario", required=True, choices=["search", "dynamic_dom", "pagination"])
    args = parser.parse_args()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            if args.scenario == "search":
                success, extracted, final_url = run_search(page, args.base_url)
            elif args.scenario == "dynamic_dom":
                success, extracted, final_url = run_dynamic_dom(page, args.base_url)
            else:
                success, extracted, final_url = run_pagination(page, args.base_url)
        finally:
            browser.close()

    result = {
        "scenario": args.scenario,
        "success": success,
        "extracted_text": extracted,
        "final_url": final_url,
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
