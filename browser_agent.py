import argparse
import json
from playwright.sync_api import sync_playwright, expect

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--scenario", required=True, choices=["search", "dynamic_dom", "pagination"])
    args = parser.parse_args()
    
    base_url = args.base_url.rstrip("/")
    scenario = args.scenario
    
    extracted_text = None
    success = False
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            if scenario == "search":
                page.goto(base_url)
                page.fill("input#search", "browser automation")
                page.click("button[type=submit]")
                expect(page.locator("#search-result")).to_have_text("Found: browser automation")
                extracted_text = page.locator("#search-result").inner_text().strip()
                success = extracted_text == "Found: browser automation"
            
            elif scenario == "dynamic_dom":
                page.goto(base_url + "/dynamic")
                page.click("button#load-record")
                expect(page.locator("#dynamic-result")).to_have_text("Loaded record: DYNAMIC-42")
                extracted_text = page.locator("#dynamic-result").inner_text().strip()
                success = extracted_text == "Loaded record: DYNAMIC-42"
            
            elif scenario == "pagination":
                page.goto(base_url + "/page/1")
                page.click("a#next")
                expect(page.locator("h1")).to_have_text("Page 2 of 2")
                extracted_text = page.locator("#page-record").inner_text().strip()
                success = extracted_text == "Record 2 of 2: pagination verified"
        
        except Exception:
            success = False
            extracted_text = None
        
        finally:
            context.close()
            browser.close()
    
    result = {
        "scenario": scenario,
        "success": success,
        "extracted_text": extracted_text,
        "final_url": page.url
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
