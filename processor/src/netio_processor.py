"""
Performs upload/download operations
Author: oitsjustjose @ modrinth/curseforge/twitter
"""
import json
import os
from shutil import rmtree
from time import sleep
from typing import List, Tuple, Union

import requests
import selenium.common.exceptions as selex
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from pyvirtualdisplay import Display
from data import ModInfo, Status


def __extrapolate_mod(filename: str, delimiter: str) -> Union[ModInfo, None]:
    """
    Extrapolates mod info from a given jarfile name
    Args:
        filename (str): the name of the jarfile
        delimiter (str): the splitter between parts of the filename
    Returns: (ModInfo|None): the extraploted mod info, None if extrap failed
    """

    def get_versions(parts: List[str]) -> List[str]:
        """
        Most of the patches that we modders labeled as ".x" (i.e. 1.18.x) were
            specifically for .0, .1, .2 patches. This is presumptuous, but it's
            not that terrible to fix.
        Args: parts (List[str]): the split jarfile string
        Returns: (List[str]) a list of assumed supported MC versions
        """
        #
        if "x" in parts[1].lower():
            root = parts[1].replace(".x", "").replace(".X", "")
            return [root, f"{root}.1", f"{root}.2"]
        return [parts[1]]

    parts = filename.replace(".jar", "").split(delimiter)
    return ModInfo(
        name=parts[0],
        mod_version=parts[2],
        modrinth_name=" ".join(parts),
        game_version=parts[1],
        game_versions=get_versions(parts),
    )


def __get_mods_for_page(driver: webdriver.Chrome, root: str, page: int) -> List[str]:
    """
    Gets all mod download URLs for a given page
    Args:
        driver (webdriver.Chrome): the chrome driver
        root (str): the root url, i.e. https://legacy.curseforge.com/{slug}/files/all
        page (int): the page number, added as a query to the query str
    Returns:
        (List[str]): a list of download urls for the mod files
    """
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


def __get_page_count(driver: webdriver.Chrome, root: str) -> int:
    """
    Gets the page count for a given mod slug
    Args:
        driver (webdriver.Chrome): the chrome driver
        root (str): the root url, i.e. https://legacy.curseforge.com/{slug}/files/all
    Returns: (int): the number of pages for the mod
    """
    driver.get(f"{root}?page=1")
    root = driver.page_source
    root = BeautifulSoup(root, features="html.parser")
    root = root.body.find_all("a", attrs={"class": "pagination-item"})
    if root:  # mods with only 1 page won't have a pagination item
        root = root[-1]
        root = root.find("span").text
        return int(root)
    return 1


def __download_files(
    driver: webdriver.Chrome, all_urls: List[str], slug: str
) -> Tuple[List[Status], List[str]]:
    """
    Attempts to download jarfiles from the acquired list of urls
    Args:
        driver (webdriver.Chrome): the chrome driver
        all_urls (List[str]): a list of download urls for the mod files
        slug (str): the CurseForge slug, used to traverse the local filesystem
    Returns:
        (Tuple[List[Status], List[str]]) A list of statuses and logs
    """
    logs: List[str] = []
    statuses: List[Status] = []
    file_cnt = len(os.listdir(f"./out/{slug}"))

    for url in all_urls:
        try:
            driver.get(url)
            sleep(8)
            # Verify if/that file actually downloaded:
            new_file_cnt = len(os.listdir(f"./out/{slug}"))
            if new_file_cnt == file_cnt + 1:  # this should work
                file_cnt = new_file_cnt
                statuses.append(Status.SUCCESS)
            else:
                logs.append(f"Could not download jarfile from {url}")
                logs.append("This file will need manual migration")
                statuses.append(Status.FAIL)
        except selex.TimeoutException:
            logs.append(f"Timed out while reaching {url}.")
            logs.append("This file will need manual migration")
            statuses.append(Status.FAIL)
            continue
        except selex.WebDriverException as exception:
            logs.append(f"Could not download jarfile from {url}. RAW ERR: {exception}")
            logs.append("This file will need manual migration")
            statuses.append(Status.FAIL)
            continue

    # Yes, this could also be true if a download failed... oh well
    if file_cnt != len(all_urls):
        sleep(15)
    return statuses, logs


def upload(
    api_key: str, slug: str, proj_id: str, delimiter: str
) -> Tuple[Status, List[str]]:
    """
    Uploads all downloaded files from CurseForge to Modrinth using the given API Key
    Args:
        api_key (str): the GitHub PAT for the associated Modrinth account
        slug (str): the CurseForge slug, used to traverse the local filesystem
        proj_id (str): the Modrinth project id
        delimiter (str): the splitter between parts of the filename. Geolosys uses format
            "MODNAME-MCVER-MAJOR.MINOR.PATCH", where '-' is the delimiter
    Returns:
        Tuple[Status, List[str]]: The overall status and any accompanying logs
    """

    if not os.path.exists(f"./out/{slug}"):
        return Status.FAIL, [
            f"CurseForge Slug {slug} was not valid and therefore didn't download from Curse"
        ]

    logs = []
    statuses = []

    for fpath in os.listdir(f"./out/{slug}"):
        with open(f"out/{slug}/{fpath}", "rb") as modfile:
            data = modfile.read()

        mod_info = __extrapolate_mod(fpath, delimiter)
        if not mod_info:
            logs.append(f"Couldn't parse name/version info for file {fpath}")
            continue

        payload = json.dumps(
            {
                "name": mod_info.name,
                "version_number": mod_info.modrinth_name,
                "changelog": "Migrated Automagically from CurseForge",
                "dependencies": [],
                "game_versions": mod_info.game_versions,
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
            statuses.append(Status.SUCCESS)
        else:
            statuses.append(Status.FAIL)
            logs.append("----- FILE {fpath} -----")
            logs.append("API Response from Modrinth FAIL for {fpath}:")
            if response.text:  # Add text if exists
                logs.append(response.text)
            data = response.json(indent=2)
            if data:  # Add json response if exists
                logs.append(data)

    any_succ = len(list(filter(lambda x: x == Status.SUCCESS, statuses))) > 0
    any_fail = len(list(filter(lambda x: x == Status.SUCCESS, statuses))) > 0
    status = (
        Status.PARTIAL_FAIL
        if any_succ and any_fail
        else Status.SUCCESS
        if any_succ and not any_fail
        else Status.FAIL
    )
    rmtree(f"./out/{slug}")
    return status, logs


def download(slug: str) -> Tuple[Status, List[str]]:
    """
    Downloads all mod files for a given slug
    Args: slug (str): the slug for the given Curse Mod Project
    Returns: (Tuple[Status, List[str]]): The status and logs, if any
    """
    root = f"https://legacy.curseforge.com/minecraft/mc-mods/{slug}/files/all"
    os.makedirs(f"./out/{slug}", exist_ok=True)

    # REGION CHROME DRIVER AND OPTIONS
    display = Display(visible=0, size=(1366, 768))
    display.start()

    options = Options()
    options.add_argument("--no-sandbox")
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
    # ENDREGION CHROME DRIVER AND OPTIONS

    all_urls: List[str] = []
    for page in range(__get_page_count(driver, root)):
        all_urls += __get_mods_for_page(driver, root, page + 1)
    if not all_urls:
        return Status.FAIL, [
            f"Failed to find any files for CurseForge Project with Slug '{slug}' - was this spelled correctly?"
        ]
    statuses, logs = __download_files(driver, all_urls, slug)

    any_succ = len(list(filter(lambda x: x == Status.SUCCESS, statuses))) > 0
    any_fail = len(list(filter(lambda x: x == Status.SUCCESS, statuses))) > 0
    status = (
        Status.PARTIAL_FAIL
        if any_succ and any_fail
        else Status.SUCCESS
        if any_succ and not any_fail
        else Status.FAIL
    )

    display.stop()
    driver.close()
    return status, logs
