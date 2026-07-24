'''
use this program to find a product's product family.
'''

import os #to communicate with parent OS
import re #for RegEX stuff
from urllib.parse import urlparse
import json
from playwright.sync_api import sync_playwright

class Prod_fam_2:

    def __init__(self, part_num = "", parts_list = []):
        self.part_num = part_num
        self.parts_list = parts_list

    #turn this into a class to use later?
    def find_product_family(self):
        product_url = f"https://www.thorlabs.com/item/{self.part_num}" 

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            print(f"Finding product family for '{self.part_num}'...")
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

    def store_file(self, family_name):
        #store prod. fams in json file
        #os.makedirs(data_dir, exist_ok=True) #check if data_dir exists, if yes, then ok
        json_path = "families.json"
        #json_path = os.path.join(data_dir, "families.json")

        #init families json if not existing yet
        if os.path.exists(json_path):
            with open(json_path, "r") as f:
                products = json.load(f)
        else:
            products = {}

        #add prod name if not existing, append as dict then dumps later to turn into json
        if self.part_num not in products:
            products[self.part_num] = {
                "family": {}
            }
        else:
            "already exists in repo."

        #add families to prods
        families = products[self.part_num]["family"]
        if family_name not in families:
            families[family_name] = {
                #"wavelengths" : [wavelength]
            }
        #write back to json
        with open(json_path, "w") as f:
            json.dump(products, f, indent = 4)


        print(f"saved to {json_path}.")

    def store_file_2(self, part_list):
        for part_num in part_list:
            # Update this object's current part number
            self.part_num = part_num

            print(f"\nProcessing {part_num}...")

            family_name = self.find_product_family()

            if family_name is None:
                print(f"Skipping {part_num}: could not determine product family.")
                continue

            self.store_file(family_name)

        print("\nFinished processing all products.")

    def checkProdFamExists(self, invDict, part_num):
        if part_num in invDict:
            #next(iter()) is for going inside the dict, otherwise, it will print {} and stuff
            family_name = next(iter(invDict[part_num]["family"]))
            print(f"{part_num} has stored family: {family_name}")
            return family_name
            

 