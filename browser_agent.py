import argparse
import json
import sys
from playwright.sync_api import sync_playwright

def run_search(page, base_url):
    page.goto(base_url)
    page.fill('#search', 'browser automation')
    page.click('button[type=submit]')
    page.wait_for_selector('#search-result')
    return page.inner_text('#search-result')

def run_dynamic_dom(page, base_url):
    page.goto(base_url.rstrip('/') + '/dynamic')
    page.click('#load-record')
    # Wait until the result element contains the expected text
    page.wait_for_function("""() => {
        const el = document.querySelector('#dynamic-result');
        return el && el.textContent.trim() === 'Loaded record: DYNAMIC-42';
    }""")
    return page.inner_text('#dynamic-result')

def run_pagination(page, base_url):
    page.goto(base_url.rstrip('/') + '/page/1')
    page.click('a#next')
    # Wait for the heading to indicate page 2
    page.wait_for_function("""() => {
        const el = document.querySelector('h1');
        return el && el.textContent.trim() === 'Page 2 of 2';
    }""")
    page.wait_for_selector('#page-record')
    return page.inner_text('#page-record')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', required=True)
    parser.add_argument('--scenario', required=True, choices=['search', 'dynamic_dom', 'pagination'])
    args = parser.parse_args()

    page = None
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            if args.scenario == 'search':
                extracted = run_search(page, args.base_url)
            elif args.scenario == 'dynamic_dom':
                extracted = run_dynamic_dom(page, args.base_url)
            elif args.scenario == 'pagination':
                extracted = run_pagination(page, args.base_url)
            else:
                extracted = None

            success = extracted is not None
            final_url = page.url
            result = {
                'scenario': args.scenario,
                'success': success,
                'extracted_text': extracted,
                'final_url': final_url
            }
        except Exception as e:
            result = {
                'scenario': args.scenario,
                'success': False,
                'extracted_text': None,
                'final_url': page.url if page else None
            }
        finally:
            browser.close()

    print(json.dumps(result))

if __name__ == '__main__':
    main()
