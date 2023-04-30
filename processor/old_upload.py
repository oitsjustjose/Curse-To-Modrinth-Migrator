"""
@author: oitsjustjose @ github / twitter / modrinth
@license: MIT
@description: Uploads mod files to Modrinth
"""


class ModrinthUploader(MgmtApiLogger):
    """
    Handles uploading jar files to Modrinth
    Args:
        helper (MgmtApiHelper): the current mongo instance for the Job DB
        job (Job): the job to process
    """

    def upload(self) -> Status:
        """
        Uploads all downloaded files from CurseForge to Modrinth using the given API Key
        Args:
            api_key (str): the GitHub PAT for the associated Modrinth account
            slug (str): the CurseForge slug, used to traverse the local filesystem
            proj_id (str): the Modrinth project id
        Returns: (Status): The overall status
        """

        if not os.path.exists(f"./out/{self._job.curseforge_slug}"):
            self.logmsg("🔥 Downloads from Curse were not found")
            return Status.FAIL

        statuses = []

        for jar_fn in os.listdir(f"./out/{self._job.curseforge_slug}"):
            with open(f"./out/{self._job.curseforge_slug}/{jar_fn}", "rb") as modfile:
                jar_data = modfile.read()

            mod = self._manifest[jar_fn]
            display_nm = mod["displayName"]
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
                    print(f"✅ {display_nm}")
                else:
                    print(response.text)
                    print(response.json())
                    statuses.append(Status.FAIL)
                    self.logmsg(
                        dedent(
                            f"""----- 🔥 {display_nm} -----
                            API Response from Modrinth FAIL for {display_nm}:
                            {response.text}
                            {response.json()}
                            """
                        ).strip("\n")
                    )

                rm(f"./out/{self._job.curseforge_slug}/{jar_fn}")
            except TimeoutError:
                self.logmsg(f"🕜 Timed out uploading {jar_fn}. Manual upload required")
                statuses.append(Status.FAIL)

        any_succ = len(list(filter(lambda x: x == Status.SUCCESS, statuses))) > 0
        any_fail = len(list(filter(lambda x: x == Status.SUCCESS, statuses))) > 0
        status = (
            Status.PARTIAL_FAIL
            if any_succ and any_fail
            else Status.SUCCESS
            if any_succ and not any_fail
            else Status.FAIL
        )
        os.rmdir(f"./out/{self._job.curseforge_slug}")
        return status
