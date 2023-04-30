# def download(self) -> Union[Status, dict]:
#     """
#     Downloads all mod files for a given slug
#     Returns: Union[Status, dict]: The status of the download and the manifest
#     """
#     if not self._manifest:
#         self.logmsg("🔥 Failed to create Manifest, see logs for info")
#         return Status.FAIL

#     os.makedirs(f"./out/{self._job.curseforge_slug}", exist_ok=True)

#     statuses = self.__download_files()
#     any_succ = len(list(filter(lambda x: x == Status.SUCCESS, statuses))) > 0
#     any_fail = len(list(filter(lambda x: x == Status.SUCCESS, statuses))) > 0
#     status = (
#         Status.PARTIAL_FAIL
#         if any_succ and any_fail
#         else Status.SUCCESS
#         if any_succ and not any_fail
#         else Status.FAIL
#     )
#     return status, self._manifest

# def __download_files(self) -> List[Status]:
#     """
#     Attempts to download jarfiles from the acquired list of urls
#     Args:
#         driver (webdriver.Chrome): the chrome driver
#         all_urls (List[str]): a list of download urls for the mod files
#         slug (str): the CurseForge slug, used to traverse the local filesystem
#     Returns:
#         (Tuple[List[Status], List[str]]) A list of statuses and logs
#     """
#     statuses: List[Status] = []
#     file_cnt = len(os.listdir(f"./out/{self._job.curseforge_slug}"))

#     for mod in self._manifest.values():
#         try:
#             url = mod["downloadUrl"]
#             driver_get(self._driver, url)
#             sleep(8)
#             # Verify if/that file actually downloaded:
#             new_file_cnt = len(os.listdir(f"./out/{self._job.curseforge_slug}"))
#             if new_file_cnt == file_cnt + 1:  # this should work
#                 file_cnt = new_file_cnt
#                 statuses.append(Status.SUCCESS)
#                 self.logmsg(f"✅ Successfully downloaded {url}")
#             else:
#                 self.logmsg(f"🔥 Could not download jarfile from {url}. Skipping..")
#                 statuses.append(Status.FAIL)
#         except selex.TimeoutException:
#             self.logmsg(
#                 f"🕜 Timed out while reaching {url}. This file will need manual migration."
#             )
#             statuses.append(Status.FAIL)
#             continue
#         except selex.WebDriverException as exception:
#             self.logmsg(
#                 f"🔥 Could not download jarfile from {url}. RAW ERR: {exception}. This file will need manual migration"
#             )
#             statuses.append(Status.FAIL)
#             continue

#     # Yes, this could also be true if a download failed... oh well
#     if file_cnt != len(self._manifest.keys()):
#         sleep(5)
#     return statuses
