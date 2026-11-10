#!/usr/bin/env python3
"""
Browser Agent - Playwright browser automation script for three scenarios.
Accepts --base-url and --scenario command-line arguments.
"""

import argparse
import json

from playwright.sync_api import sync_playwright


def run_search(base_url: str) -> dict:
    """Execute the search scenario."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.goto(base_url)

            page.locator("input#search").fill("browser automation")
            page.locator("button[type=submit]").click()
            page.locator("#search-result").wait_for()

            result_text = page.locator("#search-result").inner_text()
            extracted_text = result_text.strip()

            success = extracted_text == "Found: browser automation"
            final_url = page.url

            return {
                "scenario": "search",
                "success": success,
                "extracted_text": extracted_text,
                "final_url": final_url,
            }
        finally:
            browser.close()


def run_dynamic_dom(base_url: str) -> dict:
    """Execute the dynamic DOM scenario."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.goto(f"{base_url.rstrip('/')}/dynamic")

            page.locator("button#load-record").click()
            page.locator("#dynamic-result:has-text('Loaded record: DYNAMIC-42')").wait_for()

            result_text = page.locator("#dynamic-result").inner_text()
            extracted_text = result_text.strip()

            success = extracted_text == "Loaded record: DYNAMIC-42"
            final_url = page.url

            return {
                "scenario": "dynamic_dom",
                "success": success,
                "extracted_text": extracted_text,
                "final_url": final_url,
            }
        finally:
            browser.close()


def run_pagination(base_url: str) -> dict:
    """Execute the pagination scenario."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.goto(f"{base_url.rstrip('/')}/page/1")

            page.locator("a#next").click()
            page.locator("h1:has-text('Page 2 of 2')").wait_for()

            result_text = page.locator("#page-record").inner_text()
            extracted_text = result_text.strip()

            success = extracted_text == "Record 2 of 2: pagination verified"
            final_url = page.url

            return {
                "scenario": "pagination",
                "success": success,
                "extracted_text": extracted_text,
                "final_url": final_url,
            }
        finally:
            browser.close()


def main():
    parser = argparse.ArgumentParser(description="Browser automation agent for Playwright")
    parser.add_argument("--base-url", type=str, default="http://127.0.0.1:41721",
                        help="Base URL for the browser tests")
    parser.add_argument("--scenario", type=str, choices=["search", "dynamic_dom", "pagination"],
                        required=True, help="Scenario to execute")
    args = parser.parse_args()

    if args.scenario == "search":
        result = run_search(args.base_url)
    elif args.scenario == "dynamic_dom":
        result = run_dynamic_dom(args.base_url)
    elif args.scenario == "pagination":
        result = run_pagination(args.base_url)
    else:
        result = {
            "scenario": args.scenario,
            "success": False,
            "extracted_text": None,
            "final_url": None,
        }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
