import argparse
import json
import sys
from playwright.sync_api import sync_playwright, expect

def run_search(base_url):
    expected = "Found: browser automation"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        try:
            page.goto(base_url)
            page.fill('input#search', 'browser automation')
            page.click('button[type=submit]')
            page.wait_for_selector('#search-result', timeout=10000)
            extracted = page.locator('#search-result').inner_text().strip()
            success = extracted == expected
            return {
                "scenario": "search",
                "success": success,
                "extracted_text": extracted if success else None,
                "final_url": page.url
            }
        except Exception:
            return {
                "scenario": "search",
                "success": False,
                "extracted_text": None,
                "final_url": page.url
            }
        finally:
            context.close()
            browser.close()

def run_dynamic_dom(base_url):
    expected = "Loaded record: DYNAMIC-42"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        try:
            page.goto(f"{base_url}/dynamic")
            page.click('button#load-record')
            # Wait until the element has the exact text
            expect(page.locator('#dynamic-result')).to_have_text(expected, timeout=10000)
            extracted = page.locator('#dynamic-result').inner_text().strip()
            success = extracted == expected
            return {
                "scenario": "dynamic_dom",
                "success": success,
                "extracted_text": extracted if success else None,
                "final_url": page.url
            }
        except Exception:
            return {
                "scenario": "dynamic_dom",
                "success": False,
                "extracted_text": None,
                "final_url": page.url
            }
        finally:
            context.close()
            browser.close()

def run_pagination(base_url):
    expected = "Record 2 of 2: pagination verified"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        try:
            page.goto(f"{base_url}/page/1")
            page.click('a#next')
            # Wait for h1 to have exact text
            expect(page.locator('h1')).to_have_text('Page 2 of 2', timeout=10000)
            extracted = page.locator('#page-record').inner_text().strip()
            success = extracted == expected
            return {
                "scenario": "pagination",
                "success": success,
                "extracted_text": extracted if success else None,
                "final_url": page.url
            }
        except Exception:
            return {
                "scenario": "pagination",
                "success": False,
                "extracted_text": None,
                "final_url": page.url
            }
        finally:
            context.close()
            browser.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', required=True, help='Base URL of the application')
    parser.add_argument('--scenario', required=True, choices=['search', 'dynamic_dom', 'pagination'],
                        help='Scenario to execute')
    args = parser.parse_args()

    if args.scenario == 'search':
        result = run_search(args.base_url)
    elif args.scenario == 'dynamic_dom':
        result = run_dynamic_dom(args.base_url)
    else:  # pagination
        result = run_pagination(args.base_url)

    print(json.dumps(result))

if __name__ == '__main__':
    main()
