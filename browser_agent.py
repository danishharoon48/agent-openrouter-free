import argparse
import json
import sys
from playwright.sync_api import sync_playwright

def wait_for_text(page, selector, expected, timeout=10000):
    """Wait for an element to have the exact text content."""
    try:
        page.wait_for_function(
            """({selector, expected}) => {
                const el = document.querySelector(selector);
                return el && el.textContent.trim() === expected;
            }""",
            arg={"selector": selector, "expected": expected},
            timeout=timeout
        )
        return True
    except Exception:
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', required=True, help='Base URL')
    parser.add_argument('--scenario', required=True, choices=['search', 'dynamic_dom', 'pagination'],
                        help='Scenario to execute')
    args = parser.parse_args()

    base_url = args.base_url.rstrip('/')
    scenario = args.scenario

    success = False
    extracted_text = None
    final_url = ""

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            if scenario == "search":
                page.goto(base_url)
                page.fill('#search', 'browser automation')
                page.click('button[type=submit]')
                if wait_for_text(page, '#search-result', "Found: browser automation"):
                    extracted_text = page.locator('#search-result').inner_text().strip()
                    success = True

            elif scenario == "dynamic_dom":
                page.goto(f"{base_url}/dynamic")
                page.click('#load-record')
                if wait_for_text(page, '#dynamic-result', "Loaded record: DYNAMIC-42"):
                    extracted_text = page.locator('#dynamic-result').inner_text().strip()
                    success = True

            elif scenario == "pagination":
                page.goto(f"{base_url}/page/1")
                page.click('a#next')
                if wait_for_text(page, 'h1', "Page 2 of 2"):
                    page.wait_for_selector('#page-record', timeout=10000)
                    extracted_text = page.locator('#page-record').inner_text().strip()
                    expected = "Record 2 of 2: pagination verified"
                    success = extracted_text == expected

            final_url = page.url

            context.close()
            browser.close()

    except Exception as e:
        print(json.dumps({
            "scenario": scenario,
            "success": False,
            "extracted_text": None,
            "final_url": final_url
        }), file=sys.stdout)
        sys.exit(1)

    print(json.dumps({
        "scenario": scenario,
        "success": success,
        "extracted_text": extracted_text,
        "final_url": final_url
    }))

if __name__ == "__main__":
    main()
