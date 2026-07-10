'''
use this program to find a product's product family.
sort the repo by product family and wavelength instead.
store the associated family product in it's own file for reference later.
have main.py take in a product, wavelength, dir path
REMINDER: check to see if we alr found product family for a certain product before scraping.
'''

import os #to communicate with parent OS
import re #for RegEX stuff
import sys
from urllib.parse import urlparse
import json
import requests
from playwright.sync_api import sync_playwright

def find_product_family(part_number: str) -> str | None:
    product_url = f"https://www.thorlabs.com/item/{part_number}" 

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print(f"Finding product family for '{part_number}'...")
        page.goto(product_url, timeout=30000)
        page.wait_for_load_state("networkidle", timeout=20000)

        family_link = page.locator("a", has_text=re.compile(r"product family", re.IGNORECASE)).first
        if not family_link.is_visible():
            print("[ERROR] Could not find a 'Product Family' link on the product page.")
            browser.close()
            return None

        family_href = family_link.get_attribute("href")
        print(f"Found product family link: {family_href}")

        parsed = urlparse(family_href)
        segments = [segment for segment in parsed.path.split("/") if segment]
        if segments:
            product_family_name = segments[-1].replace(".html", "")
            print(f"Product family name: {product_family_name}")
            return product_family_name

    return None

def store_file():
    #store prod. fams in json file


def main():
    if len(sys.argv) > 1:
        part_number = sys.argv[1]
        product_family = find_product_family(part_number)
        if product_family:
            print(f"Product family for '{part_number}': {product_family}")
        else:
            print(f"Could not find product family for '{part_number}'.")
    else:
        print("please input a product number as arg 1")

if __name__ == "__main__":
    main()