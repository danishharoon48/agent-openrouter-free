import argparse
import json
import sys
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


def run_search(base_url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        extracted_text = None
        success = False
        final_url = ""
        try:
            page.goto(base_url)
            page.fill('input#search', 'browser automation')
            page.click('button[type=submit]')
            page.wait_for_selector('#search-result', timeout=10000)
            extracted_text = page.locator('#search-result').inner_text().strip()
            success = extracted_text == "Found: browser automation"
            final_url = page.url
        except Exception:
            success = False
            extracted_text = None
            try:
                final_url = page.url
            except Exception:
                final_url = ""
        finally:
            browser.close()
    return {
        "scenario": "search",
        "success": success,
        "extracted_text": extracted_text if success else None,
        "final_url": final_url,
    }


def run_dynamic_dom(base_url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        extracted_text = None
        success = False
        final_url = ""
        try:
            page.goto(f"{base_url}/dynamic")
            page.click('button#load-record')
            page.wait_for_function(
                "() => { const el = document.querySelector('#dynamic-result'); return el && el.textContent.trim() === 'Loaded record: DYNAMIC-42'; }",
                timeout=10000,
            )
            extracted_text = page.locator('#dynamic-result').inner_text().strip()
            success = extracted_text == "Loaded record: DYNAMIC-42"
            final_url = page.url
        except Exception:
            success = False
            extracted_text = None
            try:
                final_url = page.url
            except Exception:
                final_url = ""
        finally:
            browser.close()
    return {
        "scenario": "dynamic_dom",
        "success": success,
        "extracted_text": extracted_text if success else None,
        "final_url": final_url,
    }


def run_pagination(base_url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        extracted_text = None
        success = False
        final_url = ""
        try:
            page.goto(f"{base_url}/page/1")
            page.click('a#next')
            page.wait_for_function(
                "() => { const el = document.querySelector('h1'); return el && el.textContent.trim() === 'Page 2 of 2'; }",
                timeout=10000,
            )
            page.wait_for_selector('#page-record', timeout=10000)
            extracted_text = page.locator('#page-record').inner_text().strip()
            success = extracted_text == "Record 2 of 2: pagination verified"
            final_url = page.url
        except Exception:
            success = False
            extracted_text = None
            try:
                final_url = page.url
            except Exception:
                final_url = ""
        finally:
            browser.close()
    return {
        "scenario": "pagination",
        "success": success,
        "extracted_text": extracted_text if success else None,
        "final_url": final_url,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', required=True, help='Base URL')
    parser.add_argument('--scenario', required=True, choices=['search', 'dynamic_dom', 'pagination'],
                        help='Scenario to execute')
    args = parser.parse_args()
    base_url = args.base_url.rstrip('/')

    if args.scenario == "search":
        result = run_search(base_url)
    elif args.scenario == "dynamic_dom":
        result = run_dynamic_dom(base_url)
    else:
        result = run_pagination(base_url)

    print(json.dumps({
        "scenario": result["scenario"],
        "success": result["success"],
        "extracted_text": result["extracted_text"],
        "final_url": result["final_url"]
    }))


if __name__ == "__main__":
    main()
