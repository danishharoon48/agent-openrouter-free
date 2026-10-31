#!/usr/bin/env python3
"""Browser agent for benchmark scenarios using Playwright."""

import argparse
import json
import sys

from playwright.sync_api import sync_playwright


def run_search(page, base_url):
    page.goto(base_url)
    page.fill("#search", "browser automation")
    page.click("button[type=submit]")
    page.wait_for_selector("#search-result", state="visible")
    text = page.inner_text("#search-result").strip()
    expected = "Found: browser automation"
    success = text == expected
    return success, text, page.url


def run_dynamic_dom(page, base_url):
    page.goto(base_url.rstrip("/") + "/dynamic")
    page.click("#load-record")
    # Wait until the result div contains the exact expected text
    page.wait_for_function(
        "() => { const el = document.querySelector('#dynamic-result'); "
        "return el && el.textContent.trim() === 'Loaded record: DYNAMIC-42'; }"
    )
    text = page.inner_text("#dynamic-result").strip()
    expected = "Loaded record: DYNAMIC-42"
    success = text == expected
    return success, text, page.url


def run_pagination(page, base_url):
    page.goto(base_url.rstrip("/") + "/page/1")
    page.click("a#next")
    # Wait until the h1 indicates we are on page 2
    page.wait_for_function(
        "() => { const el = document.querySelector('h1'); "
        "return el && el.textContent.trim() === 'Page 2 of 2'; }"
    )
    text = page.inner_text("#page-record").strip()
    expected = "Record 2 of 2: pagination verified"
    success = text == expected
    return success, text, page.url


def main():
    parser = argparse.ArgumentParser(description="Run a benchmark scenario.")
    parser.add_argument("--base-url", required=True, help="Base URL of the benchmark site")
    parser.add_argument("--scenario", required=True, choices=["search", "dynamic_dom", "pagination"])
    args = parser.parse_args()

    scenario = args_scenario = args.scenario
    base_url = args.base_url

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            if scenario == "search":
                success, extracted_text, final_url = run_search(page, base_url)
            elif scenario == "dynamic_dom":
                success, extracted_text, final_url = run_dynamic_dom(page, base_url)
            elif scenario == "pagination":
                success, extracted_text, final_url = run_pagination(page, base_url)
            else:
                success, extracted_text, final_url = False, None, page.url
        except Exception:
            success, extracted_text, final_url = False, None, page.url
        finally:
            browser.close()

    result = {
        "scenario": scenario,
        "success": success,
        "extracted_text": extracted_text,
        "final_url": final_url,
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
