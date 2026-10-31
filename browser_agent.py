import sys
import json
from playwright.sync_api import sync_playwright

def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        with browser.new_page() as page:
            page.goto(url)
            title = page.title()
            heading_elem = page.query_selector('h1')
            heading = heading_elem.inner_text().strip() if heading_elem else None

            result = {
                "url": url,
                "title": title,
                "heading": heading
            }
            print(json.dumps(result))

if __name__ == "__main__":
    main()
