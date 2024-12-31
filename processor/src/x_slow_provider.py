"""
@author: oitsjustjose @ github / twitter / modrinth
@license: MIT
@description: A SLOW working mod migrator from Curse to Modrinth
    This one is used if you're a jerk and disable third party launchers
"""

import json
from os import environ as env
from os import makedirs, path
from os import unlink as rm
from shutil import rmtree as rmdir
from textwrap import dedent
from time import sleep
from typing import List, Union

import requests
import selenium.common.exceptions as selex
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from urllib3.exceptions import ProtocolError, ReadTimeoutError
from webdriver_manager.chrome import ChromeDriverManager

import curse_api as cf
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
        driver.get(url)
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        return True
    except TimeoutException:
        print(f"Failed to get {url}")
        return False


class SlowProvider(MgmtApiLogger):
    """
    The class for handling slow downloads
    Args:
        helper (MgmtApiHelper): the job database
        job_id (str): the job id for the given job
    """

    def __init__(self, helper: MgmtApiHelper, job: Job):
        super().__init__(helper, job.job_id)
        self._helper = helper
        self._job = job
        self._modid = cf.get_modid(job.curseforge_slug, self.logmsg)
        self._rel_map = {1: "release", 2: "beta", 3: "alpha"}
        # region CHROME DRIVER AND OPTIONS
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--ignore-ssl-errors=yes")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--disable-dev-shm-usage")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_experimental_option(
            "prefs",
            {
                "download.default_directory": path.realpath(
                    f"./out/{self._job.curseforge_slug}/"
                ),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
            },
        )
        self._driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=options
        )
        # endregion CHROME DRIVER AND OPTIONS

    def _build_manifest(self) -> Union[dict, None]:
        """
        Builds a manifest JSON to be used during Modrinth upload
        """
        self.logmsg("ℹ️ Building Manifest for Jar Info")
        manifest = {}

        self.logmsg("ℹ️ Retrieving Curse ModID from Slug")
        if not self._modid:
            return None

        self.logmsg("ℹ️ Enumerating Curse API Pages")
        pages, last_size = cf.get_pages(self._modid, self.logmsg)
        if pages == -1 and last_size == -1:
            return None

        # region ITERATE OVER PAGES AND DOWNLOAD MOD INFO
        self.logmsg(f"ℹ️ Building manifest for {(pages*50)+last_size} files")
        for idx in range(pages):
            try:
                response = requests.get(
                    f"https://api.curseforge.com/v1/mods/{self._modid}/files?index={idx}",
                    headers={"x-api-key": env["CURSE_API_KEY"]},
                    timeout=30,
                )
                for mod in response.json()["data"]:
                    manifest[mod["fileName"]] = mod
            except TimeoutError:
                self.logmsg(
                    f"🕜 Timed out enumerating files for {self._job.curseforge_slug} ({self._modid})"
                )
                continue

        if last_size != 0:
            try:
                response = requests.get(
                    f"https://api.curseforge.com/v1/mods/{self._modid}/files?index={pages}&pageSize={last_size}",
                    headers={"x-api-key": env["CURSE_API_KEY"]},
                    timeout=30,
                )
                for mod in response.json()["data"]:
                    manifest[mod["fileName"]] = mod
            except TimeoutError:
                self.logmsg(
                    f"🕜 Timed out enumerating files for {self._job.curseforge_slug} ({self._modid})"
                )

        # endregion ITERATE OVER PAGES AND DOWNLOAD MOD INFO

        for val in manifest.values():
            url = f"https://legacy.curseforge.com/minecraft/mc-mods/{self._job.curseforge_slug}/download/{val['id']}"
            val["downloadUrl"] = url

        self.logmsg(f"ℹ️ Manifest Built! {len(manifest.keys())} Mods Found")
        return manifest

    def process(self) -> Status:
        """Returns: (status): the status of the procedure"""
        self.logmsg("ℹ️ Retrieving Curse ModID from Slug")
        if not self._modid:
            return Status.FAIL

        mods = self._build_manifest()
        if not mods:
            self.logmsg("🔥 Failed to create Manifest, see logs for info")
            return Status.FAIL

        makedirs(f"./out/{self._job.curseforge_slug}", exist_ok=True)

        statuses: List[Status] = []
        for fpath, mod in mods.items():
            if (
                not mod["isAvailable"]
                or "downloadUrl" not in mod
                or not mod["downloadUrl"]
            ):
                continue

            display_nm = mod["displayName"]

            # region DOWNLOAD THE MOD
            success = False
            try:
                driver_get(self._driver, mod["downloadUrl"])
                sleep(8)
                success = True
            except selex.TimeoutException:
                self.logmsg(
                    f"🕜 Timed out while downloading {display_nm}. This file will need manual migration."
                )
                statuses.append(Status.FAIL)
                continue
            except selex.WebDriverException as exception:
                self.logmsg(
                    f"🔥 Could not download {display_nm}. RAW ERR: {exception}. This file will need manual migration"
                )
                statuses.append(Status.FAIL)
                continue
            # endregion DOWNLOAD THE MOD

            if not success:
                continue

            # region UPLOAD THE MOD
            with open(f"./out/{self._job.curseforge_slug}/{fpath}", "rb") as jar_file:
                jar_data = jar_file.read()

            game_versions, loaders = cf.get_loader_info(mod["gameVersions"])
            payload = json.dumps(
                {
                    "name": display_nm,
                    "version_number": cf.get_version(display_nm),
                    "changelog": cf.get_changelog(self._modid, mod["id"]),
                    "dependencies": [],  # Dependencies need to be manually included
                    "game_versions": game_versions,
                    "loaders": loaders,
                    "featured": False,
                    "version_type": self._rel_map[mod["releaseType"]],
                    "requested_status": "listed",
                    "project_id": self._job.modrinth_id,
                    "primary_file": fpath,
                    "file_parts": [fpath],
                }
            )

            tries, msg = 1, ""
            while tries <= 5:
                try:
                    response = requests.post(
                        "https://api.modrinth.com/v2/version",
                        timeout=30,
                        headers={"Authorization": self._job.oauth_token},
                        files=[
                            ("data", (None, payload, None)),
                            ("files", (fpath, jar_data, "application/octet-stream")),
                        ],
                    )
                    if response.status_code == 200:
                        statuses.append(Status.SUCCESS)
                        self.logmsg(f"✅ {display_nm}")
                    else:
                        statuses.append(Status.FAIL)
                        self.logmsg(
                            dedent(
                                f"""----- 🔥 {display_nm} -----
                                API Response from Modrinth FAIL for {display_nm}:
                                {self.decode_modrinth_resp(response)}
                                """
                            ).strip("\n")
                        )

                    rm(f"./out/{self._job.curseforge_slug}/{fpath}")
                    break
                except (
                    requests.exceptions.ReadTimeout,
                    ReadTimeoutError,
                    TimeoutError,
                ):
                    tries += 1
                    msg = f"🕜 Timed out uploading {fpath}. Manual upload required"
                    continue
                except (ProtocolError, requests.exceptions.ChunkedEncodingError):
                    tries += 1
                    msg = f"🔥 Uploading {display_nm} to Modrinth failed, skipping.."
                    continue
            if tries == 5:
                self.logmsg(msg)
                statuses.append(Status.FAIL)
            # endregion UPLOAD THE MOD

        any_succ = len(list(filter(lambda x: x == Status.SUCCESS, statuses))) > 0
        any_fail = len(list(filter(lambda x: x == Status.FAIL, statuses))) > 0
        status = (
            Status.PARTIAL_FAIL
            if any_succ and any_fail
            else Status.SUCCESS if any_succ and not any_fail else Status.FAIL
        )
        rmdir(f"./out/{self._job.curseforge_slug}")
        return status
