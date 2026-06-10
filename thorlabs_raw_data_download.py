"""
AI Summary:
Given a Thorlabs part number:
  1. Goes to the product page (thorlabs.com/item/(part number here))
  2. Clicks the "Product Family" link
  3. On the family page, finds the "Click Here for Raw Data" xlsx link
  4. Downloads and saves the xlsx file

Requirements:
    pip install playwright requests
    python -m playwright install chromium

Usage example:
    python thorlabs_lookup.py WG12012
    ^^then, will download the raw data in the dir you are in


"""

import os #to communicate with parent OS
import re #for RegEX shit
import sys

import requests
from playwright.sync_api import sync_playwright


def get_raw_data(part_number: str, save_dir: str = ".") -> str | None:
    product_url = f"https://www.thorlabs.com/item/{part_number}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # ── Step 1: Load the product page ────────────────────────────────────
        print(f"[1/3] Loading product page for '{part_number}'...")
        page.goto(product_url, timeout=30000)
        page.wait_for_load_state("networkidle", timeout=20000)

        # ── Step 2: Find and click the "Product Family" link ─────────────────
        print("[2/3] Looking for 'Product Family' link...")

        family_link = page.locator("a", has_text=re.compile(r"product family", re.IGNORECASE)).first
        if not family_link.is_visible():
            print("[ERROR] Could not find a 'Product Family' link on the product page.")
            browser.close()
            return None

        family_href = family_link.get_attribute("href")
        print(f"         Found: {family_href}")

        # Navigate to the family page
        page.goto(family_href if family_href.startswith("http") else f"https://www.thorlabs.com{family_href}", timeout=30000)
        page.wait_for_load_state("networkidle", timeout=20000)

        # ── Step 3: Find the "Raw Data" xlsx link ────────────────────────────
        print("[3/3] Looking for 'Raw Data' xlsx link on family page...")

        xlsx_url = None

        # Look for an <a> whose text contains "raw data" and href ends in .xlsx
        all_links = page.eval_on_selector_all(
            "a[href]",
            "els => els.map(e => ({ href: e.href, text: e.innerText.trim() }))"
        )
        for link in all_links:
            href = link.get("href", "")
            text = link.get("text", "").lower()
            if ".xlsx" in href.lower() or ("raw" in text and "data" in text):
                xlsx_url = href
                print(f"         Found: {xlsx_url}")
                break

        # Fallback: regex scan of the raw HTML for any .xlsx URL
        if not xlsx_url:
            html = page.content()
            matches = re.findall(r'https?://[^\s"\'<>]+\.xlsx[^\s"\'<>]*', html, re.IGNORECASE)
            if matches:
                xlsx_url = matches[0]
                print(f"         Found via HTML scan: {xlsx_url}")

        browser.close()

    if not xlsx_url:
        print("[ERROR] No raw data xlsx link found on the family page.")
        return None

    # ── Step 4: Download the file ─────────────────────────────────────────────
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


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:   python thorlabs_lookup.py <PartNumber>")
        print("Example: python thorlabs_lookup.py WG12012")
        sys.exit(1)

    get_raw_data(sys.argv[1])
