"""
Performs upload/download operations
Author: oitsjustjose @ modrinth/curseforge/twitter
"""
import json
import os
from shutil import rmtree
from typing import List, Union

import requests

from common import DbLogger, Job, ModInfo, Status
from job_database import JobDb


class ModrinthUploader(DbLogger):
    def __init__(self, job_db: JobDb, job: Job):
        super().__init__(job_db, job.job_id)
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

    def __extrapolate_mod(self, filename: str) -> Union[ModInfo, None]:
        """
        Extrapolates mod info from a given jarfile name
        Args:
            filename (str): the name of the jarfile
            delimiter (str): the splitter between parts of the filename
        Returns: (ModInfo|None): the extraploted mod info, None if extrap failed
        """

        parts = filename.replace(".jar", "").split(self._job.delimiter)
        return ModInfo(
            name=parts[0],
            mod_version=parts[2],
            modrinth_name=" ".join(parts),
            game_version=parts[1],
            game_versions=self.__get_versions(parts),
        )

    def upload(self) -> Status:
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

        if not os.path.exists(f"./out/{self._job.curseforge_slug}"):
            self.logmsg(
                f"CurseForge Slug {self._job.curseforge_slug} was not valid and therefore didn't download from Curse"
            )
            return Status.FAIL

        statuses = []

        for fpath in os.listdir(f"./out/{self._job.curseforge_slug}"):
            with open(f"out/{self._job.curseforge_slug}/{fpath}", "rb") as modfile:
                data = modfile.read()

            mod_info = self.__extrapolate_mod(fpath)
            if not mod_info:
                self.logmsg(f"Couldn't parse name/version info for file {fpath}")
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
                    "project_id": self._job.modrinth_id,
                    "primary_file": fpath,
                    "file_parts": [fpath],
                }
            )

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
                self.logmsg("----- FILE {fpath} -----")
                self.logmsg("API Response from Modrinth FAIL for {fpath}:")
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
        rmtree(f"./out/{self._job.github_pat}")
        return status
