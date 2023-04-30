"""
Uploads mod files to Modrinth
Author: oitsjustjose @ modrinth/curseforge/twitter
"""
import json
import re
import os
from shutil import rmtree
from typing import List, Union

import requests

from common import Job, ModInfo, Status
from mgmt_tools import MgmtApiHelper, MgmtApiLogger


class ModrinthUploader(MgmtApiLogger):
    """
    Handles uploading jar files to Modrinth
    Args:
        helper (MgmtApiHelper): the current mongo instance for the Job DB
        job (Job): the job to process
    """

    def __init__(self, helper: MgmtApiHelper, job: Job):
        super().__init__(helper, job.job_id)
        self._job = job

    def __get_versions(self, parts: List[str]) -> List[str]:
        """
        Most of the patches that we modders labeled as ".x" (i.e. 1.18.x) were
            specifically for .0, .1, .2 patches. This is presumptuous, but it's
            not that terrible to fix.
        Args: parts (List[str]): the split jarfile string
        Returns: (List[str]) a list of assumed supported MC versions
        """
        if "x" in parts[1].lower():
            root = parts[1].replace(".x", "").replace(".X", "")
            return [root, f"{root}.1", f"{root}.2"]
        return [parts[1]]

    def __get_mod_info(self, filename: str) -> Union[ModInfo, None]:
        """
        Loads mod info from the manifest generated during download
        Args:
            filename (str): the name of the jarfile
        Returns: (ModInfo|None): the extraploted mod info, None if extrap failed
        """
        name = filename.replace(".jar", "")

        # Finds the versioning (like 1.19.2-1.2.3, 1.2.3) in the name
        # TODO: more robust to grab from jar metadata, but sometimes it isn't there?
        search = re.search(r"([0-9.].*)", name)
        if not search:
            return None

        mod_version = name[search.start() : search.end()]
        manifest_path = f"./out/{self._job.curseforge_slug}.mf.json"
        with open(manifest_path, "r", encoding="utf-8") as handle:
            manifest = json.loads(handle.read())

        return ModInfo(
            modrinth_name=name,
            mod_version=mod_version,
            loaders=manifest[filename]["loaders"],
            game_version=manifest[filename]["version"],
            game_versions=manifest[filename]["versions"],
        )

    def upload(self) -> Status:
        """
        Uploads all downloaded files from CurseForge to Modrinth using the given API Key
        Args:
            api_key (str): the GitHub PAT for the associated Modrinth account
            slug (str): the CurseForge slug, used to traverse the local filesystem
            proj_id (str): the Modrinth project id
        Returns:
            Tuple[Status, List[str]]: The overall status and any accompanying logs
        """

        if not os.path.exists(f"./out/{self._job.curseforge_slug}"):
            self.logmsg(
                f"CurseForge Slug {self._job.curseforge_slug} was not valid and therefore didn't download from Curse"
            )
            return Status.FAIL

        statuses = []

        for fpath in os.listdir(f"./out/{self._job.curseforge_slug}"):
            with open(f"out/{self._job.curseforge_slug}/{fpath}", "rb") as modfile:
                data = modfile.read()

            mod_info = self.__get_mod_info(fpath)
            if not mod_info:
                self.logmsg(f"Couldn't parse name/version info for file {fpath}")
                continue

            payload = json.dumps(
                {
                    "name": mod_info.modrinth_name,
                    "version_number": mod_info.mod_version,
                    "changelog": "Migrated Automagically from CurseForge",
                    "dependencies": [],
                    "game_versions": mod_info.game_versions,
                    "loaders": ["forge"],
                    "featured": False,
                    "requested_status": "listed",
                    "version_type": "release",
                    "project_id": self._job.modrinth_id,
                    "primary_file": fpath,
                    "file_parts": [fpath],
                }
            )
            print(payload)

            try:
                response = requests.post(
                    "https://api.modrinth.com/v2/version",
                    timeout=30,
                    headers={"Authorization": self._job.github_pat},
                    files=[
                        ("data", (None, payload, None)),
                        ("files", (fpath, data, "application/octet-stream")),
                    ],
                )
            except TimeoutError:
                self.logmsg(f"Timed out uploading {fpath}. Manual upload required")

            if response.status_code == 200:
                self.logmsg(f"Successfully uploaded {fpath}")
                statuses.append(Status.SUCCESS)
            else:
                statuses.append(Status.FAIL)
                self.logmsg(f"----- FILE {fpath} -----")
                self.logmsg(f"API Response from Modrinth FAIL for {fpath}:")
                if response.text:  # Add text if exists
                    self.logmsg(response.text)
                data = response.json()
                if data:  # Add json response if exists
                    self.logmsg(data)

        any_succ = len(list(filter(lambda x: x == Status.SUCCESS, statuses))) > 0
        any_fail = len(list(filter(lambda x: x == Status.SUCCESS, statuses))) > 0
        status = (
            Status.PARTIAL_FAIL
            if any_succ and any_fail
            else Status.SUCCESS
            if any_succ and not any_fail
            else Status.FAIL
        )
        rmtree(f"./out/{self._job.curseforge_slug}")
        return status
