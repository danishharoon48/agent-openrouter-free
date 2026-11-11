import argparse
import json
import sys

from playwright.sync_api import sync_playwright


def run_search(base_url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        page.goto(base_url)

        page.locator("input#search").fill("browser automation")
        page.locator("button[type=submit]").click()

        page.wait_for_selector("#search-result")
        extracted_text = page.locator("#search-result").inner_text().strip()
        final_url = page.url

        success = extracted_text == "Found: browser automation"
        return {
            "scenario": "search",
            "success": success,
            "extracted_text": extracted_text if success else None,
            "final_url": final_url,
        }


def run_dynamic_dom(base_url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        page.goto(f"{base_url}/dynamic")

        page.locator("button#load-record").click()
        page.wait_for_function(
            "document.querySelector('#dynamic-result')?.textContent.trim() === 'Loaded record: DYNAMIC-42'",
            timeout=10000,
        )
        extracted_text = page.locator("#dynamic-result").inner_text().strip()
        final_url = page.url

        success = extracted_text == "Loaded record: DYNAMIC-42"
        return {
            "scenario": "dynamic_dom",
            "success": success,
            "extracted_text": extracted_text if success else None,
            "final_url": final_url,
        }


def run_pagination(base_url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        page.goto(f"{base_url}/page/1")

        page.locator("a#next").click()
        page.wait_for_function(
            "document.querySelector('h1')?.innerText === 'Page 2 of 2'",
            timeout=10000,
        )
        extracted_text = page.locator("#page-record").inner_text().strip()
        final_url = page.url

        success = extracted_text == "Record 2 of 2: pagination verified"
        return {
            "scenario": "pagination",
            "success": success,
            "extracted_text": extracted_text if success else None,
            "final_url": final_url,
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True, help="Base URL to run the scenario against")
    parser.add_argument(
        "--scenario",
        required=True,
        choices=["search", "dynamic_dom", "pagination"],
        help="Scenario to execute",
    )
    args = parser.parse_args()

    if args.scenario == "search":
        result = run_search(args.base_url)
    elif args.scenario == "dynamic_dom":
        result = run_dynamic_dom(args.base_url)
    else:  # pagination
        result = run_pagination(args.base_url)

    print(json.dumps(result))


if __name__ == "__main__":
    main()
