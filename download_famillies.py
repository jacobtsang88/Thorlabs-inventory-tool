from download_files import FamilyDownloader


def main():

    downloader = FamilyDownloader(
        json_path="families.json",
        download_dir="downloads"
    )

    downloader.download_all_families()


if __name__ == "__main__":
    main()
