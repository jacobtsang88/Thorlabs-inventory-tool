from product_family_2 import Prod_fam_2
from processtxt import txt_to_list
from download_files import FamilyDownloader


def main():

    downloader = FamilyDownloader(
        json_path="families.json",
        download_dir="downloads"
    )

    downloader.download_all_families()


if __name__ == "__main__":
    main()
'''
def main():
    print("poop")
    #download list of products and their respective families into a local .json file
    fart = txt_to_list().convert()
    pf = Prod_fam_2()
    pf.store_file_2("downloads", fart)
'''



if __name__ == "__main__":
    main()
