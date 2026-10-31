import argparse
import json
import sys
from playwright.sync_api import sync_playwright

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', required=True, help='Base URL')
    parser.add_argument('--scenario', required=True, choices=['search', 'dynamic_dom', 'pagination'],
                        help='Scenario to execute')
    args = parser.parse_args()

    scenario = args.scenario
    base_url = args.base_url.rstrip('/')

    paths = {
        'search': '',
        'dynamic_dom': '/dynamic',
        'pagination': '/page/1'
    }
    path = paths[scenario]

    if path:
        full_url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    else:
        full_url = base_url

    expected_results = {
        'search': "Found: browser automation",
        'dynamic_dom': "Loaded record: DYNAMIC-42",
        'pagination': "Record 2 of 2: pagination verified"
    }
    expected_text = expected_results[scenario]

    extracted_text = None
    success = False
    final_url = full_url

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(full_url)

            if scenario == 'search':
                page.locator('input#search').fill('browser automation')
                page.locator('button[type=submit]').click()
                page.wait_for_selector('#search-result', state='visible', timeout=10000)
                extracted_text = page.locator('#search-result').inner_text().strip()
                success = extracted_text == expected_text

            elif scenario == 'dynamic_dom':
                page.locator('button#load-record').click()
                # Wait until #dynamic-result contains the exact expected text
                page.wait_for_function(
                    "() => document.querySelector('#dynamic-result')?.textContent?.trim() === 'Loaded record: DYNAMIC-42'",
                    timeout=10000
                )
                extracted_text = page.locator('#dynamic-result').inner_text().strip()
                success = extracted_text == expected_text

            else:  # pagination
                page.locator('a#next').click()
                # Wait for h1 to equal exactly 'Page 2 of 2'
                page.wait_for_function(
                    "() => document.querySelector('h1')?.textContent?.trim() === 'Page 2 of 2'",
                    timeout=10000
                )
                extracted_text = page.locator('#page-record').inner_text().strip()
                success = extracted_text == expected_text

            final_url = page.url

        except Exception as e:
            # On any error, success remains False, extracted_text stays None
            pass
        finally:
            browser.close()

    result = {
        "scenario": scenario,
        "success": success,
        "extracted_text": extracted_text if success else None,
        "final_url": final_url
    }

    print(json.dumps(result))

if __name__ == '__main__':
    main()
