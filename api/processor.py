"""
Performs upload/download operations
Author: oitsjustjose @ modrinth/curseforge/twitter
"""
import json
import os
from shutil import rmtree
from time import sleep
from typing import List

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def upload(api_key: str, slug: str, proj_id: str, delimeter: str) -> List[str]:
    """
    Uploads all downloaded files from CurseForge to Modrinth using the given API Key
    Args:
        api_key (str): the GitHub PAT for the associated Modrinth account
        slug (str): the CurseForge slug, used to traverse the local filesystem
        proj_id (str): the Modrinth project id
        delimiter (str): the splitter between parts of the filename. Geolosys uses format
            "MODNAME-MCVER-MAJOR.MINOR.PATCH", where '-' is the delimiter
    """
    logs = []
    if not os.path.exists(f"./out/{slug}"):
        return logs

    for fpath in os.listdir(f"./out/{slug}"):
        with open(f"out/{slug}/{fpath}", "rb") as modfile:
            data = modfile.read()

        parts = fpath.split(delimeter)
        if len(parts) != 3:
            logs.append(
                f"Failed to parse name/version info for file {fpath}, it will be skipped"
            )
            continue

        version_title = " ".join(parts).replace(".jar", "")
        # .x versions somehow were only ever for the .0, .1 and .2 game vers lol
        if "x" in parts[1].lower():
            root = parts[1].replace(".x", "").replace(".X", "")
            game_versions = [root, f"{root}.1", f"{root}.2"]
        else:
            game_versions = [parts[1]]
        version = parts[2].replace(".jar", "")

        payload = json.dumps(
            {
                "name": version_title,
                "version_number": f"{parts[1]}-{version}",
                "changelog": "Migrated Automagically from CurseForge",
                "dependencies": [],
                "game_versions": game_versions,
                "loaders": ["forge"],
                "featured": False,
                "requested_status": "listed",
                "version_type": "release",
                "project_id": proj_id,
                "primary_file": fpath,
                "file_parts": [fpath],
            }
        )

        response = requests.post(
            "https://api.modrinth.com/v2/version",
            timeout=30,
            headers={"Authorization": api_key},
            files=[
                ("data", (None, payload, None)),
                ("files", (fpath, data, "application/octet-stream")),
            ],
        )

        if response.status_code == 200:
            logs.append(f"Successfully uploaded {fpath}")
        else:
            logs.append("API Response from Modrinth Failed for {fpath}:")
            logs.append(response.text)
            logs.append(json.dumps(response.json(), indent=2))

    rmtree(f"./out/{slug}")
    return logs


def __get_mods_for_page(driver: webdriver.Chrome, root: str, page: int) -> List[str]:
    """EH"""
    driver.get(f"{root}?page={page}")

    root_el = driver.page_source
    root_el = BeautifulSoup(root_el, features="html.parser")

    file_links = root_el.body.find_all("a", attrs={"data-action": "file-link"})

    return list(
        map(
            lambda x: f"https://legacy.curseforge.com/{x['href']}".replace(
                "files", "download"
            ),
            file_links,
        )
    )


def download(slug: str) -> List[str]:
    """Downloads all mod files for a given slug"""
    logs = []
    try:
        root = f"https://legacy.curseforge.com/minecraft/mc-mods/{slug}/files/all"
        os.makedirs(f"./out/{slug}", exist_ok=True)

        page_num: int = 1

        options = Options()
        options.add_argument("--ignore-ssl-errors=yes")
        options.add_argument("--ignore-certificate-errors")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_experimental_option(
            "prefs",
            {
                "download.default_directory": os.path.realpath(f"./out/{slug}/"),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
            },
        )
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=options
        )
        driver.get(f"{root}?page=1")

        root_el = driver.page_source
        root_el = BeautifulSoup(root_el, features="html.parser")
        page_els = root_el.body.find_all("a", attrs={"class": "pagination-item"})
        if page_els:  # mods with only 1 page won't have a pagination item
            page_el = page_els[-1]
            page_el = page_el.find("span").text
            page_num = int(page_el)
        all_urls = []
        for page in range(page_num):
            all_urls += __get_mods_for_page(driver, root, page + 1)
        for url in all_urls:
            driver.get(url)
            sleep(8)
    except Exception as e:
        logs.append(f"Download failed: {e}")
    return logs
