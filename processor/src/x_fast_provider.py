"""
@author: oitsjustjose @ github / twitter / modrinth
@license: MIT
@description: A fast working mod migrator from Curse to Modrinth
    Use the other one for worse performance >:[
"""

import json
from os import environ as env
from os import unlink as rm
from textwrap import dedent
from typing import List

import requests

import curse_api as cf
from common import Job, Status
from mgmt_tools import MgmtApiHelper, MgmtApiLogger


class FastProvider(MgmtApiLogger):
    """
    The class for handling curse downloads
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

    def _process_all_mods(self, mods: dict) -> List[Status]:
        """
        Downloads and then uploads all mods from a given page of mods from /list
        Args: mods (dict): the JSON payload from /list
        Returns: (List[Status]): a list of statuses for each mod
        """
        statuses = []
        for mod in mods:
            if (
                not mod["isAvailable"]
                or "downloadUrl" not in mod
                or not mod["downloadUrl"]
            ):
                continue

            jar_fn = mod["fileName"]
            display_nm = mod["displayName"]

            game_versions, loaders = cf.get_loader_info(mod["gameVersions"])
            # region DOWNLOAD JAR FILE
            try:
                with requests.get(mod["downloadUrl"], stream=True, timeout=30) as strm:
                    strm.raise_for_status()
                    with open(jar_fn, "wb") as jar:
                        for chunk in strm.iter_content(chunk_size=8192):
                            jar.write(chunk)
            except TimeoutError:
                self.logmsg(f"🕜 Timed out downloading {display_nm}, skipping..")
                statuses.append(Status.FAIL)
                continue
            # endregion DOWNLOAD JAR FILE

            # region UPLOAD JAR FILE
            with open(jar_fn, "rb") as modfile:
                jar_data = modfile.read()

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
                    "primary_file": jar_fn,
                    "file_parts": [jar_fn],
                }
            )

            try:
                response = requests.post(
                    "https://api.modrinth.com/v2/version",
                    timeout=30,
                    headers={"Authorization": self._job.github_pat},
                    files=[
                        ("data", (None, payload, None)),
                        ("files", (jar_fn, jar_data, "application/octet-stream")),
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

                rm(jar_fn)
            except TimeoutError:
                self.logmsg(f"🕜 Timed out uploading {jar_fn}. Manual upload required")
                statuses.append(Status.FAIL)
            # endregion UPLOAD JAR FILE
        return statuses

    def process(self) -> Status:
        """Returns: (status): the status of the procedure"""
        self.logmsg("ℹ️ Retrieving Curse ModID from Slug")
        if not self._modid:
            return Status.FAIL

        self.logmsg("ℹ️ Enumerating Curse API Pages")
        pages, last_size = cf.get_pages(self._modid, self.logmsg)
        if pages == -1 and last_size == -1:
            return Status.FAIL

        self.logmsg(f"ℹ️ Processing {(pages*50)+last_size} files")
        statuses: List[Status] = []
        try:
            for idx in range(pages):
                response = requests.get(
                    f"https://api.curseforge.com/v1/mods/{self._modid}/files?index={idx}",
                    headers={"x-api-key": env["CURSE_API_KEY"]},
                    timeout=30,
                )
                statuses += self._process_all_mods(response.json()["data"])
                self.logmsg(f"ℹ️ Processed {((idx+1)*50)} files")

            if last_size != 0:  # Handle the last, possibly incomplete page of mods
                response = requests.get(
                    f"https://api.curseforge.com/v1/mods/{self._modid}/files?index={pages}&pageSize={last_size}",
                    headers={"x-api-key": env["CURSE_API_KEY"]},
                    timeout=30,
                )
                statuses += self._process_all_mods(response.json()["data"])
                self.logmsg(f"ℹ️ Processed {last_size} files")
        except TimeoutError:
            statuses = [Status.FAIL]
            self.logmsg(
                f"🕜 Timed out enumerating files for {self._job.curseforge_slug} ({self._modid})"
            )

        any_succ = len(list(filter(lambda x: x == Status.SUCCESS, statuses))) > 0
        any_fail = len(list(filter(lambda x: x == Status.FAIL, statuses))) > 0
        status = (
            Status.PARTIAL_FAIL
            if any_succ and any_fail
            else Status.SUCCESS
            if any_succ and not any_fail
            else Status.FAIL
        )

        return status

    def supports_downloads(self) -> bool:
        """
        Determines if the mod even allows for third party launcher downloads
        Returns (bool): True if it does, False otherwise
        """
        try:
            modid = cf.get_modid(self._job.curseforge_slug, self.logmsg)
            if not modid:
                return False

            response = requests.get(
                f"https://api.curseforge.com/v1/mods/{modid}/files",
                headers={"x-api-key": env["CURSE_API_KEY"]},
                timeout=30,
            )
            if response.ok:
                data = response.json()["data"]
                return "downloadUrl" in data[0]
            return False
        except TimeoutError:
            self.logmsg("🕜 Timed out determining if Mod supports third party downloads")
            return False
