import json
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright

from naming_utils import filename_from_url, with_graphs_tab


class FamilyDownloader:
    BASE_URL = "https://www.thorlabs.com"

    def __init__(self, json_path: str, download_dir: str = "downloads"):
        self.json_path = Path(json_path)
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def load_products(self) -> dict:
        """Load the product-family JSON file."""
        with self.json_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def get_unique_families(self) -> set[str]:
        """Extract all unique family names from the JSON file."""
        products = self.load_products()
        families = set()

        for part_number, product_data in products.items():
            family_data = product_data.get("family", {})
            for family_name in family_data:
                families.add(family_name)

        return families

    def get_family_url(self, family_name: str) -> str:
        """Convert a family slug into a Thorlabs family URL, on the "Graphs"
        tab -- the raw-data xlsx links only render there, not on the default
        Overview tab."""
        return with_graphs_tab(f"/{family_name}")

    def find_xlsx_links(self, page) -> list[str]:
        """Find every distinct .xlsx link on the current page."""
        links = page.locator("a[href*='.xlsx']").evaluate_all(
            """
            elements => elements.map(element => ({
                href: element.href,
                text: element.innerText.trim()
            }))
            """
        )
        seen = set()
        hrefs = []
        for link in links:
            href = link.get("href", "") or ""
            if href and href not in seen:
                seen.add(href)
                hrefs.append(href)
        return hrefs

    def download_file(self, url: str, save_path: Path) -> Path | None:
        """Download an XLSX file to an exact path, skipping if it already exists."""
        if save_path.exists():
            print(f"Already downloaded: {save_path}")
            return save_path

        print(f"Downloading: {url}")

        response = requests.get(url, timeout=60)
        response.raise_for_status()

        save_path.write_bytes(response.content)
        print(f"Saved to: {save_path}")

        return save_path

    def download_family(self, family_name: str) -> dict[str, Path]:
        """
        Download every distinct coating/uncoated variant's XLSX file for a
        family, into downloads/<family_name>/, keeping Thorlabs' own default
        filename for each (e.g. a_broadband_ar-coating.xlsx).
        Returns {filename_stem: path} for every variant present on disk
        after the run (previously downloaded + newly downloaded).
        """
        family_url = self.get_family_url(family_name)
        family_dir = self.download_dir / family_name
        family_dir.mkdir(parents=True, exist_ok=True)

        print("\nProcessing family:")
        print(f"    {family_name}")
        print(f"    {family_url}")

        variants: dict[str, Path] = {}

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            try:
                page.goto(
                    family_url, timeout=30000, wait_until="networkidle"
                )

                print("Looking for XLSX links...")
                xlsx_links = self.find_xlsx_links(page)

                if not xlsx_links:
                    print(f"[WARNING] No XLSX files found for {family_name}")
                    return variants

                print(f"Found {len(xlsx_links)} XLSX file(s).")

                used_names = set()
                for href in xlsx_links:
                    filename = filename_from_url(href)
                    save_path = family_dir / filename
                    if filename in used_names:
                        # Two different links happen to share Thorlabs' filename.
                        stem, suffix = save_path.stem, save_path.suffix
                        counter = 2
                        while f"{stem}_{counter}{suffix}" in used_names:
                            counter += 1
                        save_path = family_dir / f"{stem}_{counter}{suffix}"
                    used_names.add(save_path.name)

                    try:
                        downloaded_path = self.download_file(href, save_path)
                        if downloaded_path:
                            variants[downloaded_path.stem] = downloaded_path
                    except requests.RequestException as e:
                        print(f"[ERROR] Failed to download {href}: {e}")

            except Exception as e:
                print(f"[ERROR] Failed to process family {family_name}: {e}")

            finally:
                browser.close()

        return variants

    def download_all_families(self) -> list[str]:
        """
        Download every coating/uncoated variant for every unique product
        family. Returns a list of family names that failed to download.
        """
        families = self.get_unique_families()
        print(f"Found {len(families)} unique product families.")

        failed_families = []

        for family_name in sorted(families):
            variants = self.download_family(family_name)
            if not variants:
                failed_families.append(family_name)

        print("\nFinished downloading all families.")
        if failed_families:
            print(f"Please check/manually download the following: ({len(failed_families)}): {failed_families}")

        return failed_families
