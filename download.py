"""**EH**"""
from typing import List
import os
from time import sleep

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


URL: str


def get_mods_for_page(driver: webdriver.Chrome, page: int) -> List[str]:
    """EH"""
    driver.get(f"{URL}?page={page}")

    root = driver.page_source
    root = BeautifulSoup(root, features="html.parser")

    file_links = root.body.find_all("a", attrs={"data-action": "file-link"})

    return list(
        map(
            lambda x: f"https://legacy.curseforge.com/{x['href']}".replace(
                "files", "download"
            ),
            file_links,
        )
    )


def mod_archive_all(modid: str) -> None:
    """EH"""
    global URL
    URL = f"https://legacy.curseforge.com/minecraft/mc-mods/{modid}/files/all"
    os.makedirs(f"./out/{modid}", exist_ok=True)

    page: int = 1
    page_num: int = 1

    options = Options()
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.add_experimental_option(
        "prefs",
        {
            "download.default_directory": os.path.realpath(f"./out/{modid}/"),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
        },
    )
    driver = webdriver.Chrome(options=options)
    driver.get(f"{URL}?page={page}")

    root = driver.page_source
    root = BeautifulSoup(root, features="html.parser")
    page_els = root.body.find_all("a", attrs={"class": "pagination-item"})
    if page_els:  # mods with only 1 page won't have a pagination item
        page_el = page_els[-1]
        page_el = page_el.find("span").text
        page_num = int(page_el)

    all_urls = []
    for page in range(page_num):
        all_urls += get_mods_for_page(driver, page + 1)
    for url in all_urls:
        driver.get(url)
        sleep(8)


if __name__ == "__main__":
    mod_archive_all("YOUR_MODID")
