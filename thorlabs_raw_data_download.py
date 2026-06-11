"""
AI Summary:
Given a Thorlabs part number:
  1. Goes to the product page (thorlabs.com/item/(part number here))
  2. Clicks the "Product Family" link
  3. On the family page, finds the correct "Click Here for Raw Data" xlsx link
  4. Downloads and saves the xlsx file locally for use later

Requirements:
    pip install playwright requests
    python -m playwright install chromium

Usage example:
    python thorlabs_lookup.py WG12012
    ^^then, will download the raw data in the dir you are in


"""

'''
note to future self, pls choose either to use argv or input() not both, gets messy
'''

import os #to communicate with parent OS
import re #for RegEX stuff
import sys

import requests
from playwright.sync_api import sync_playwright


def get_raw_data(part_number: str, save_dir: str = ".") -> str | None:
    #same url regardless of part type im pretty sure
    product_url = f"https://www.thorlabs.com/item/{part_number}" 

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        #check for second user inputting arg, and if so store it in dis thing
        requested_wavelength = sys.argv[2] if len(sys.argv) > 2 else None   


        #part 1, grab the product pg
        print(f"[1/3] getting page for '{part_number}'")
        page.goto(product_url, timeout=30000)
        page.wait_for_load_state("networkidle", timeout=20000)

        # pt2, find the product family link and click it to get to the family page where the raw data usually is
        print("[2/3] looking for 'Product Family' link")

        family_link = page.locator("a", has_text=re.compile(r"product family", re.IGNORECASE)).first
        if not family_link.is_visible():
            print("[ERROR] Could not find a 'Product Family' link on the product page.")
            browser.close()
            return None

        family_href = family_link.get_attribute("href")
        print(f"         Found: {family_href}")

        page.goto(family_href if family_href.startswith("http") else f"https://www.thorlabs.com{family_href}", timeout=30000)
        page.wait_for_load_state("networkidle", timeout=20000)

        #pt3 look for raw data link based on the wavelength user provided
        print("[3/3] Looking for correct 'Raw Data' xlsx link on family page...")

        xlsx_url = None

        page_title = page.title().lower() if requested_wavelength else ""
        page_headers = " ".join(page.locator("h1, h2, h3").all_text_contents()).lower() if requested_wavelength else ""
        page_metadata = f"{page_title} {page_headers}"

        all_links = page.eval_on_selector_all(
            "a[href]",
            "els => els.map(e => ({ href: e.href, text: e.innerText.trim() }))"
        )
        for link in all_links:
            href = link.get("href", "")
            text = link.get("text", "").lower()
            #literally scans for any link that has .xlsx in it, or has "raw" and "data" in the text. This is because thorlabs is inconsistent with how they label their raw data links across different product families
            if ".xlsx" in href.lower() or ("raw" in text and "data" in text):
                if requested_wavelength:
                    if requested_wavelength in text or requested_wavelength in href or requested_wavelength in page_metadata:
                        xlsx_url = href
                        print(f"         Found: {xlsx_url} with requested wavelength {requested_wavelength}")
                        break
                '''
                xlsx_url = href
                print(f"         Found: {xlsx_url}, ")
                break
                '''

        if not xlsx_url:
            html = page.content()
            matches = re.findall(r'https?://[^\s"\'<>]+\.xlsx[^\s"\'<>]*', html, re.IGNORECASE)
            if matches:
                xlsx_url = matches[0]
                print(f"         Found via HTML scan: {xlsx_url} - NONIDEAL, MAY NOT BE CORRECT LINK PLEASE DOUBLE CHECK")

        browser.close()

    if not xlsx_url:
        print("[ERROR] No raw data xlsx link found on the family page.")
        return None

    print("\nDownloading xlsx...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.thorlabs.com/",
    }
    resp = requests.get(xlsx_url, headers=headers, timeout=20)
    resp.raise_for_status()

    filename = xlsx_url.split("/")[-1].split("?")[0]
    if not filename.lower().endswith(".xlsx"):
        filename = f"{part_number}_raw_data.xlsx"

    save_path = os.path.join(save_dir, filename)
    with open(save_path, "wb") as f:
        f.write(resp.content)

    print(f"Saved to: {save_path}")
    return save_path

def main():
    if len(sys.argv) < 3:
        print("Use it like dis: python thorlabs_lookup.py <PartNumber> <Wavelength>")
        print("i.e.: python thorlabs_lookup.py WG12012 850")
        sys.exit(1)

    get_raw_data(sys.argv[1], int(sys.argv[2]))


main()

'''
use this for when you want to run as script, 
or want it to be importable as a module
without running the main func immediately when u import it
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:   python thorlabs_lookup.py <PartNumber>")
        print("Example: python thorlabs_lookup.py WG12012")
        sys.exit(1)

    get_raw_data(sys.argv[1])
'''