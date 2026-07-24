import json
import re
from pathlib import Path
from urllib.parse import urljoin

import requests
from playwright.sync_api import sync_playwright


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
        """Convert a family slug into a Thorlabs family URL."""
        return f"{self.BASE_URL}/{family_name}"

    def find_xlsx_links(self, page) -> list[str]:
        """Find all .xlsx links on the current page."""
        links = page.locator("a[href*='.xlsx']").evaluate_all(
            """
            elements => elements.map(element => ({
                href: element.href,
                text: element.innerText.trim()
            }))
            """
        )
        return [link["href"] for link in links]

    def download_file(self, url: str, family_name: str) -> Path | None:
        """Download an XLSX file and save it into ./downloads."""
        output_path = self.download_dir / f"{family_name}.xlsx"

        if output_path.exists():
            print(f"Already downloaded: {output_path}")
            return output_path

        print(f"Downloading: {url}")

        response = requests.get(url, timeout=60)
        response.raise_for_status()

        output_path.write_bytes(response.content)
        print(f"Saved to: {output_path}")

        return output_path

    def download_family(self, family_name: str) -> tuple[list[Path], bool]:
        """
        Download XLSX files for a single family.
        Returns a tuple of (downloaded_file_paths, success_flag).
        """
        family_url = self.get_family_url(family_name)

        print("\nProcessing family:")
        print(f"    {family_name}")
        print(f"    {family_url}")

        downloaded_files = []

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
                    return [], False

                print(f"Found {len(xlsx_links)} XLSX file(s).")

                for xlsx_url in xlsx_links:
                    try:
                        file_path = self.download_file(xlsx_url, family_name)
                        if file_path:
                            downloaded_files.append(file_path)
                    except requests.RequestException as e:
                        print(f"[ERROR] Failed to download {xlsx_url}: {e}")
                        return downloaded_files, False

            except Exception as e:
                print(f"[ERROR] Failed to process family {family_name}: {e}")
                return [], False

            finally:
                browser.close()

        # Success if we successfully downloaded at least one file
        success = len(downloaded_files) > 0
        return downloaded_files, success

    def download_all_families(self) -> list[str]:
        """
        Download one XLSX file for every unique product family.
        Returns a list of family names that failed to download.
        """
        families = self.get_unique_families()
        print(f"Found {len(families)} unique product families.")

        failed_families = []

        for family_name in sorted(families):
            _, success = self.download_family(family_name)
            if not success:
                failed_families.append(family_name)

        print("\nFinished downloading all families.")
        if failed_families:
            print(f"Please check/manually download the following: ({len(failed_families)}): {failed_families}")

        return failed_families