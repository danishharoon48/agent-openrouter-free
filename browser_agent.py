#!/usr/bin/env python3
"""
Browser Agent - Playwright automation script for three scenarios.
Accepts --base-url and --scenario command-line arguments.
"""

import json
import sys
import argparse
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


def run_search_scenario(base_url: str) -> dict:
    """Run the search scenario: fill search, submit, extract result."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(base_url)

        # Fill search input
        page.fill("input#search", "browser automation")
        # Submit the form
        page.click("button[type=submit]")

        # Wait for search results to appear
        search_result = page.locator("#search-result")
        search_result.wait_for(state="visible")
        extracted_text = search_result.inner_text().strip()

        # Verify the extracted text matches expected
        if extracted_text != "Found: browser automation":
            print(f"ERROR: Expected 'Found: browser automation' but got '{extracted_text}'", file=sys.stderr)
            browser.close()
            return {
                "scenario": "search",
                "success": False,
                "extracted_text": extracted_text,
                "final_url": page.url
            }

        browser.close()
        return {
            "scenario": "search",
            "success": True,
            "extracted_text": extracted_text,
            "final_url": page.url
        }


def run_dynamic_dom_scenario(base_url: str) -> dict:
    """Run the dynamic DOM scenario: load record and extract result."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(urljoin(base_url, "/dynamic"))

        # Click the load-record button
        page.click("button#load-record")

        # Wait for the dynamically inserted content with exact text
        dynamic_result = page.locator("#dynamic-result")
        dynamic_result.wait_for(state="visible")
        # Wait until the text matches exactly
        dynamic_result.locator("text='Loaded record: DYNAMIC-42'").wait_for(state="visible")
        extracted_text = dynamic_result.inner_text().strip()

        if extracted_text != "Loaded record: DYNAMIC-42":
            print(f"ERROR: Expected 'Loaded record: DYNAMIC-42' but got '{extracted_text}'", file=sys.stderr)
            browser.close()
            return {
                "scenario": "dynamic_dom",
                "success": False,
                "extracted_text": extracted_text,
                "final_url": page.url
            }

        browser.close()
        return {
            "scenario": "dynamic_dom",
            "success": True,
            "extracted_text": extracted_text,
            "final_url": page.url
        }


def run_pagination_scenario(base_url: str) -> dict:
    """Run the pagination scenario: navigate pages and extract record text."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(urljoin(base_url, "/page/1"))

        # Click next button to go to page 2
        page.click("a#next")

        # Wait for h1 to equal 'Page 2 of 2'
        h1 = page.locator("h1")
        h1.wait_for(state="visible")
        h1.locator("text='Page 2 of 2'").wait_for(state="visible")

        # Now extract from #page-record on page 2
        page_record = page.locator("#page-record")
        page_record.wait_for(state="visible")
        extracted_text = page_record.inner_text().strip()

        if extracted_text != "Record 2 of 2: pagination verified":
            print(f"ERROR: Expected 'Record 2 of 2: pagination verified' but got '{extracted_text}'", file=sys.stderr)
            browser.close()
            return {
                "scenario": "pagination",
                "success": False,
                "extracted_text": extracted_text,
                "final_url": page.url
            }

        browser.close()
        return {
            "scenario": "pagination",
            "success": True,
            "extracted_text": extracted_text,
            "final_url": page.url
        }


def main():
    parser = argparse.ArgumentParser(description="Browser Agent - Playwright automation")
    parser.add_argument("--base-url", default="http://127.0.0.1:45265", help="Base URL for the test")
    parser.add_argument("--scenario", required=True, choices=["search", "dynamic_dom", "pagination"],
                        help="Scenario to run")
    args = parser.parse_args()

    if args.scenario == "search":
        result = run_search_scenario(args.base_url)
    elif args.scenario == "dynamic_dom":
        result = run_dynamic_dom_scenario(args.base_url)
    elif args.scenario == "pagination":
        result = run_pagination_scenario(args.base_url)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
