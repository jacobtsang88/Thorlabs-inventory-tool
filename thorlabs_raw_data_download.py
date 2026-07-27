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


download, sort by category (mirrors, filters, windows, lenses, other/misc)
put repo folder into teams


"""

'''
note to future self, pls choose either to use argv or input() not both, gets messy
'''

import os #to communicate with parent OS
import re #for RegEX stuff
import sys
from urllib.parse import urlparse

import requests
from playwright.sync_api import sync_playwright

from naming_utils import filename_from_url, sanitize_filename_component, with_graphs_tab


def build_family_name(family_href: str, page_title: str) -> str:
    parsed = urlparse(family_href)
    candidate = None
    if parsed.path:
        segments = [segment for segment in parsed.path.split("/") if segment]
        if segments:
            candidate = segments[-1]

    if not candidate:
        candidate = page_title

    candidate = candidate.replace(".html", "")
    return sanitize_filename_component(candidate.replace("-", " "), default="family")


def get_raw_data(
    part_number: str,
    save_dir: str = ".",
) -> list[str]:
    #same url regardless of part type im pretty sure
    product_url = f"https://www.thorlabs.com/item/{part_number}"

    save_dir = str(save_dir)
    os.makedirs(save_dir, exist_ok=True)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.thorlabs.com/",
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print(f"[1/3] page for '{part_number}'")
        page.goto(product_url, timeout=30000)
        page.wait_for_load_state("networkidle", timeout=20000)

        print("[2/3] finding prod family")
        family_link = page.locator("a", has_text=re.compile(r"product family", re.IGNORECASE)).first
        if not family_link.is_visible():
            print("[ERROR] Could not find a 'Product Family' link on the product page.")
            browser.close()
            return []

        family_href = family_link.get_attribute("href")
        print(f"         Found: {family_href}")

        page.goto(with_graphs_tab(family_href), timeout=30000)
        page.wait_for_load_state("networkidle", timeout=20000)

        print("[3/3] collecting xlsx links from family page...")

        page_title = page.title()
        family_name = build_family_name(family_href if family_href else product_url, page_title)

        all_links = page.eval_on_selector_all(
            "a[href]",
            "els => els.map(e => e.href)"
        )

        def looks_like_xlsx_response(content: bytes, content_type: str) -> bool:
            return (
                content.startswith(b"PK\x03\x04")
                or "spreadsheetml" in content_type.lower()
                or content_type.lower().endswith("xlsx")
            )

        seen_urls = set()
        xlsx_urls = []
        for href in all_links:
            href = href or ""
            if ".xlsx" not in href.lower() or href in seen_urls:
                continue
            seen_urls.add(href)
            xlsx_urls.append(href)

        if not xlsx_urls:
            html = page.content()
            matches = re.findall(r'https?://[^\s"\'<>]+\.xlsx[^\s"\'<>]*', html, re.IGNORECASE)
            for match in matches:
                if match not in seen_urls:
                    seen_urls.add(match)
                    xlsx_urls.append(match)

        if not xlsx_urls:
            print("[ERROR] No raw data xlsx links found on the family page.")
            browser.close()
            return []

        family_save_dir = os.path.join(save_dir, sanitize_filename_component(family_name))
        os.makedirs(family_save_dir, exist_ok=True)

        downloaded_paths = []
        used_names = set()
        for xlsx_url in xlsx_urls:
            filename = filename_from_url(xlsx_url)
            if filename in used_names:
                stem, suffix = os.path.splitext(filename)
                counter = 2
                while f"{stem}_{counter}{suffix}" in used_names:
                    counter += 1
                filename = f"{stem}_{counter}{suffix}"
            used_names.add(filename)
            save_path = os.path.join(family_save_dir, filename)

            if os.path.exists(save_path):
                print(f"Skipping existing file: {save_path}")
                continue

            print(f"Downloading: {xlsx_url}")
            try:
                resp = requests.get(xlsx_url, headers=headers, timeout=60)
                resp.raise_for_status()
            except requests.RequestException as exc:
                print(f"[ERROR] Failed to download {xlsx_url}: {exc}")
                continue

            content_type = resp.headers.get("Content-Type", "")
            if not looks_like_xlsx_response(resp.content, content_type):
                print(
                    f"[ERROR] Downloaded content from {xlsx_url} does not look like an XLSX file "
                    f"(content-type: {content_type})"
                )
                continue

            with open(save_path, "wb") as f:
                f.write(resp.content)

            print(f"Saved to: {save_path}")
            downloaded_paths.append(save_path)

        browser.close()

    return downloaded_paths

def main():
    if len(sys.argv) < 2:
        print("Use it like dis: python thorlabs_lookup.py <PartNumber> [save_dir]")
        print("i.e.: python thorlabs_lookup.py WG12012")
        sys.exit(1)

    part_number = sys.argv[1]
    save_dir = sys.argv[2] if len(sys.argv) > 2 else "."
    get_raw_data(part_number, save_dir=save_dir)


if __name__ == "__main__":
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