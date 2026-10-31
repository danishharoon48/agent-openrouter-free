import argparse
import json
import time
from playwright.sync_api import sync_playwright

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', required=True, help='Base URL')
    parser.add_argument('--scenario', required=True, choices=['search', 'dynamic_dom', 'pagination'],
                        help='Scenario to run')
    args = parser.parse_args()

    base_url = args.base_url.rstrip('/')
    scenario = args.scenario

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            if scenario == "search":
                page.goto(base_url)
                search_input = page.locator("input#search")
                search_input.fill("browser automation")
                page.locator("button[type=submit]").click()
                page.locator("#search-result").wait_for(state="visible")
                extracted_text = page.locator("#search-result").inner_text().strip()
                success = extracted_text == "Found: browser automation"
                final_url = page.url

            elif scenario == "dynamic_dom":
                page.goto(f"{base_url}/dynamic")
                page.locator("button#load-record").click()
                # Wait for the dynamic content to appear
                for _ in range(10):
                    text = page.locator("#dynamic-result").inner_text().strip()
                    if text == "Loaded record: DYNAMIC-42":
                        break
                    time.sleep(0.5)
                extracted_text = page.locator("#dynamic-result").inner_text().strip()
                success = extracted_text == "Loaded record: DYNAMIC-42"
                final_url = page.url

            elif scenario == "pagination":
                page.goto(f"{base_url}/page/1")
                page.locator("a#next").click()
                page.locator("h1").wait_for(state="visible")
                h1_text = page.locator("h1").inner_text().strip()
                success_h1 = h1_text == "Page 2 of 2"
                page.locator("#page-record").wait_for(state="visible")
                extracted_text = page.locator("#page-record").inner_text().strip()
                success = success_h1 and extracted_text == "Record 2 of 2: pagination verified"
                final_url = page.url

            result = {
                "scenario": scenario,
                "success": success,
                "extracted_text": extracted_text if success else None,
                "final_url": final_url
            }
            print(json.dumps(result))

        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    main()
