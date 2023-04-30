"""
Downloads mod files from Curse
Author: oitsjustjose @ modrinth/curseforge/twitter
"""
import json
import os
import re
from time import sleep
from typing import List

import selenium.common.exceptions as selex
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from common import Job, Status
from mgmt_tools import MgmtApiHelper, MgmtApiLogger


def driver_get(driver: webdriver, url: str, timeout=30) -> bool:
    """
    Attempts to get a URL with a given webdriver with a timeout
    Args:
        driver (webdriver): the webdriver
        url (str): the url to navigate to
        timeout (int) = 30: the time to wait before quitting
    Returns:
        (bool): True if successfully navigated, False otherwise
    """
    try:
        print(f"Attempting to get URL {url}")
        driver.get(url)
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        return True
    except TimeoutException:
        print(f"Failed to get {url}")
        return False


class CurseDownloader(MgmtApiLogger):
    """
    The class for handling curse downloads
    Args:
        helper (MgmtApiHelper): the job database
        job_id (str): the job id for the given job
    """

    def __init__(self, helper: MgmtApiHelper, job: Job):
        super().__init__(helper, job.job_id)
        self._slug = job.curseforge_slug
        self._helper = helper
        self._job_id = job.job_id
        # REGION CHROME DRIVER AND OPTIONS
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--ignore-ssl-errors=yes")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--disable-dev-shm-usage")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_experimental_option(
            "prefs",
            {
                "download.default_directory": os.path.realpath(f"./out/{self._slug}/"),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
            },
        )
        self._driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=options
        )
        # ENDREGION CHROME DRIVER AND OPTIONS

    def download(self) -> Status:
        """
        Downloads all mod files for a given slug
        Returns: (Status): The status of the download
        """
        root = f"https://legacy.curseforge.com/minecraft/mc-mods/{self._slug}/files/all"
        os.makedirs(f"./out/{self._slug}", exist_ok=True)

        self.logmsg("Populating list of mod download urls")
        all_urls: List[str] = []
        for page in range(self.__get_page_count(root)):
            all_urls += self.__get_dl_urls_for_page(root, page + 1)

        if all_urls:
            self.logmsg(f"Found {len(all_urls)} Mod files to Download")
        else:
            self.logmsg(
                f"Failed to find any files for CurseForge Project with Slug '{self._slug}' - was this spelled correctly?"
            )
            return Status.FAIL

        self.__build_manifest(all_urls)
        # Convert to DL links AFTER building mf.json
        all_urls = list(map(lambda x: x.replace("files", "download"), all_urls))
        statuses = self.__download_files(all_urls)
        any_succ = len(list(filter(lambda x: x == Status.SUCCESS, statuses))) > 0
        any_fail = len(list(filter(lambda x: x == Status.SUCCESS, statuses))) > 0
        status = (
            Status.PARTIAL_FAIL
            if any_succ and any_fail
            else Status.SUCCESS
            if any_succ and not any_fail
            else Status.FAIL
        )
        return status

    def __build_manifest(self, all_urls: List[str]) -> None:
        """Builds the manifest with important metadata"""
        self.logmsg("Building Manifest")
        manifest = {}
        all_loaders = ["forge", "fabric", "quilt"]
        for url in all_urls:
            driver_get(self._driver, url)
            soup = BeautifulSoup(self._driver.page_source, features="html.parser")

            # REGION GET FILE NAME
            header = soup.find_all(
                "span", attrs={"class": "font-bold text-sm leading-loose"}
            )
            header = list(filter(lambda x: x.text == "Filename", header))[0]
            file_name = header.parent()[-1].text
            # ENDREGION GET FILE NAME

            # REGION GET VERSIONS
            vers = soup.find_all("span", attrs={"class": "tag"})
            vers = list(filter(lambda x: re.match(r"^[0-9.]", x.text), vers))
            vers = list(map(lambda x: re.sub(r"[^0-9.]", "", x.text), vers))
            vers.sort()
            # ENDREGION GET VERSIONS

            # REGION GET LOADER
            loaders = soup.find_all("span", attrs={"class": "tag"})
            loaders = list(filter(lambda x: x.text.lower() in all_loaders, loaders))
            loaders = list(map(lambda x: x.text.lower(), loaders))
            # ENDREGION GET LOADER

            manifest[file_name] = {
                "versions": vers,
                "version": vers[-1],
                "loaders": loaders or ["forge"],
            }
        with open(f"./out/{self._slug}.mf.json", "w", encoding="utf-8") as handle:
            handle.write(json.dumps(manifest))

    def __download_files(self, all_urls: List[str]) -> List[Status]:
        """
        Attempts to download jarfiles from the acquired list of urls
        Args:
            driver (webdriver.Chrome): the chrome driver
            all_urls (List[str]): a list of download urls for the mod files
            slug (str): the CurseForge slug, used to traverse the local filesystem
        Returns:
            (Tuple[List[Status], List[str]]) A list of statuses and logs
        """
        statuses: List[Status] = []
        file_cnt = len(os.listdir(f"./out/{self._slug}"))

        for url in all_urls:
            try:
                driver_get(self._driver, url)
                sleep(8)
                # Verify if/that file actually downloaded:
                new_file_cnt = len(os.listdir(f"./out/{self._slug}"))
                if new_file_cnt == file_cnt + 1:  # this should work
                    file_cnt = new_file_cnt
                    statuses.append(Status.SUCCESS)
                    self.logmsg(f"Successfully downloaded {url}")
                else:
                    self.logmsg(
                        f"Could not download jarfile from {url}. This file will need manual migration."
                    )
                    statuses.append(Status.FAIL)
            except selex.TimeoutException:
                self.logmsg(
                    f"Timed out while reaching {url}. This file will need manual migration."
                )
                statuses.append(Status.FAIL)
                continue
            except selex.WebDriverException as exception:
                self.logmsg(
                    f"Could not download jarfile from {url}. RAW ERR: {exception}. This file will need manual migration"
                )
                statuses.append(Status.FAIL)
                continue

        # Yes, this could also be true if a download failed... oh well
        if file_cnt != len(all_urls):
            sleep(5)
        return statuses

    def __get_page_count(self, root: str) -> int:
        """
        Gets the page count for a given mod slug
        Args:
            driver (webdriver.Chrome): the chrome driver
            root (str): the root url, i.e. https://legacy.curseforge.com/{slug}/files/all
        Returns: (int): the number of pages for the mod
        """
        driver_get(self._driver, f"{root}?page=1")
        soup = BeautifulSoup(self._driver.page_source, features="html.parser")
        soup = soup.body.find_all("a", attrs={"class": "pagination-item"})
        if soup:  # mods with only 1 page won't have a pagination item
            soup = soup[-1]
            soup = soup.find("span").text
            return int(soup)
        return 1

    def __get_dl_urls_for_page(self, root: str, page: int) -> List[str]:
        """
        Gets all mod download URLs for a given page
        Args:
            driver (webdriver.Chrome): the chrome driver
            root (str): the root url, i.e. https://legacy.curseforge.com/{slug}/files/all
            page (int): the page number, added as a query to the query str
        Returns:
            (List[str]): a list of download urls for the mod files
        """
        driver_get(self._driver, f"{root}?page={page}")

        soup = BeautifulSoup(self._driver.page_source, features="html.parser")
        file_links = soup.find_all("a", attrs={"data-action": "file-link"})
        file_links = list(map(lambda x: x["href"], file_links))
        file_links = list(
            map(lambda x: f"https://legacy.curseforge.com{x}", file_links)
        )
        return file_links
