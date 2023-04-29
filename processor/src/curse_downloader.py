"""
Downloads mod files from Curse
Author: oitsjustjose @ modrinth/curseforge/twitter
"""
import os
from time import sleep
from typing import List

import selenium.common.exceptions as selex
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from common import Job, Status
from mgmt_tools import MgmtApiHelper, MgmtApiLogger


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
                self._driver.get(url)
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
        self._driver.get(f"{root}?page=1")
        root = self._driver.page_source
        root = BeautifulSoup(root, features="html.parser")
        root = root.body.find_all("a", attrs={"class": "pagination-item"})
        if root:  # mods with only 1 page won't have a pagination item
            root = root[-1]
            root = root.find("span").text
            return int(root)
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
        self._driver.get(f"{root}?page={page}")

        root_el = self._driver.page_source
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
