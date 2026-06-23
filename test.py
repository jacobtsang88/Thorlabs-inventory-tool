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


def get_raw_data(
    part_number: str,
    requested_wavelength: str | None = None,
    save_dir: str = ".",
) -> str | None:
    #same url regardless of part type im pretty sure
    product_url = f"https://www.thorlabs.com/item/{part_number}" 

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()


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
        page_headers = " ".join(
            page.locator("h1, h2, h3, h4, h5").all_text_contents()
        ).lower() if requested_wavelength else ""
        page_metadata = f"{page_title} {page_headers}"

        all_links = page.eval_on_selector_all(
            "a[href]",
            """
            els => els.map(e => {
                const nearestBlock = e.closest('figure, p, div, li, td, section, article, span') || e.parentElement;
                const blockText = nearestBlock ? nearestBlock.innerText.replace(/\\s+/g, ' ').trim() : '';
                const figure = e.closest('figure');
                const figureText = figure ? figure.innerText.replace(/\\s+/g, ' ').trim() : '';
                const section = e.closest('section, article, div') || e.parentElement;
                const headingText = section
                    ? (section.querySelector('h1, h2, h3, h4, h5')?.innerText || '')
                    : '';
                return {
                    href: e.href,
                    text: e.innerText.trim(),
                    blockText,
                    figureText,
                    headingText,
                };
            })
            """
        )

        def normalize_wavelength(value: str) -> float | None:
            cleaned = re.sub(r"[^0-9.\-]", "", value)
            if not cleaned:
                return None
            try:
                return float(cleaned)
            except ValueError:
                return None

        def extract_range_matches(text: str):
            return re.findall(
                r"(?:theoretical data from|from)?\s*([0-9.]+)\s*[-–]\s*([0-9.]+)\s*nm",
                text,
                re.IGNORECASE,
            )

        def range_contains_requested(text: str, requested: str) -> bool:
            requested_num = normalize_wavelength(requested)
            if requested_num is None:
                return False

            for start_str, end_str in extract_range_matches(text):
                start_num = normalize_wavelength(start_str)
                end_num = normalize_wavelength(end_str)
                if start_num is not None and end_num is not None and start_num <= requested_num <= end_num:
                    return True
            return False

        def extract_section_center_wavelength(text: str) -> float | None:
            # Prefer nearby wavelength values in the section such as 1156 nm or 1550 nm
            nums = re.findall(r"(?<!\d)([0-9]{3,4})\s*nm", text, re.IGNORECASE)
            if not nums:
                return None
            values = []
            for num_str in nums:
                num = normalize_wavelength(num_str)
                if num is not None and 100 <= num <= 3000:
                    values.append(num)
            if not values:
                return None
            return values[0]

        def looks_like_xlsx_response(content: bytes, content_type: str) -> bool:
            return (
                content.startswith(b"PK\x03\x04")
                or "spreadsheetml" in content_type.lower()
                or content_type.lower().endswith("xlsx")
            )

        candidate_links = []
        for link in all_links:
            href = link.get("href", "")
            if ".xlsx" not in href.lower():
                continue

            text = link.get("text", "")
            block_text = link.get("blockText", "")
            figure_text = link.get("figureText", "")
            heading_text = link.get("headingText", "")
            context_text = " ".join([text, block_text, figure_text, heading_text, page_title, page_headers])

            if requested_wavelength:
                requested_num = normalize_wavelength(requested_wavelength)
                if requested_num is None:
                    continue
                range_match = range_contains_requested(context_text, requested_wavelength)
                if range_match or requested_wavelength in context_text:
                    center_wl = extract_section_center_wavelength(context_text)
                    score = 0 if range_match else (abs(center_wl - requested_num) if center_wl is not None else float("inf"))
                    candidate_links.append((score, href, context_text))
            else:
                candidate_links.append((0, href, context_text))

        if requested_wavelength:
            candidate_links.sort(key=lambda item: item[0])
            if candidate_links:
                xlsx_url = candidate_links[0][1]
                print(f"         Found best match: {xlsx_url} with requested wavelength {requested_wavelength}")
        else:
            if candidate_links:
                xlsx_url = candidate_links[0][1]
                print(f"         Found: {xlsx_url}")

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
    resp = requests.get(xlsx_url, headers=headers, timeout=30)
    resp.raise_for_status()

    content_type = resp.headers.get("Content-Type", "")
    if not looks_like_xlsx_response(resp.content, content_type):
        print(
            f"[ERROR] Downloaded content from {xlsx_url} does not look like an XLSX file "
            f"(content-type: {content_type})"
        )
        return None

    filename = xlsx_url.split("/")[-1].split("?")[0]
    if not filename.lower().endswith(".xlsx"):
        filename = f"{part_number}_raw_data.xlsx"

    save_path = os.path.join(str(save_dir), str(filename))
    with open(save_path, "wb") as f:
        f.write(resp.content)

    print(f"Saved to: {save_path}")
    return save_path

def main():
    if len(sys.argv) < 3:
        print("Use it like dis: python thorlabs_lookup.py <PartNumber> <Wavelength> [save_dir]")
        print("i.e.: python thorlabs_lookup.py WG12012 850")
        sys.exit(1)

    part_number = sys.argv[1]
    requested_wavelength = sys.argv[2]
    save_dir = sys.argv[3] if len(sys.argv) > 3 else "."
    get_raw_data(part_number, requested_wavelength=requested_wavelength, save_dir=save_dir)


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
