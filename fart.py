import os #to communicate with parent OS
import re #for RegEX stuff
import sys

import requests
from playwright.sync_api import sync_playwright

def get_raw_data(
    part_number: str,
    requested_wavelength: str | None = None,
    save_dir: str = ".",
) -> str | None:
    #same url regardless of part type im pretty sure
    product_url = f"https://www.thorlabs.com/item/{part_number}" 
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) #launch chromium browser, no GUI
        page = browser.new_page() #open new page
        page.goto(product_url, timeout=30000) #go to the product page, wait up to 30s
        page.wait_for_load_state("networkidle", timeout=20000)


        #find family link
        family_link = page.locator("a", has_text=re.compile(r"product family", re.IGNORECASE)).first
        if not family_link.is_visible():
            print("[ERROR] Could not find a 'Product Family' link on the product page.")
            browser.close()
            return None  
        return family_link.get_attribute("href")
    browser.close()


print(get_raw_data("ibd14p8"))