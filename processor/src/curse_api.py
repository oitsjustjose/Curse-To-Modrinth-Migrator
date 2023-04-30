"""
@author: oitsjustjose @ github / twitter / modrinth
@license: MIT
@description: Common core CurseAPI utils
"""

import re
from os import environ as env
from typing import Callable, List, Tuple, Union

import requests


def get_modid(slug: str, logmsg: Callable[[str], None]) -> Union[str, None]:
    """
    Gets the ModID for this job
    Returns (str): the mod name if any
    """
    try:
        response = requests.get(
            f"https://api.curseforge.com/v1/mods/search?gameId=432&slug={slug}",
            headers={"x-api-key": env["CURSE_API_KEY"]},
            timeout=30,
        )
        if not response.ok:
            logmsg(f"🔥 Failed to get mod_id for {slug}.")
            return None

        mod_id = response.json()["data"][0]["id"]
        return mod_id
    except TimeoutError:
        logmsg("🕜 Timed out getting mod_id from slug")
        return None


def get_pages(mod_id: str, logmsg: Callable[[str], None]) -> Tuple[int, int]:
    """
    Gets the number of pages and the item count of the final page for the mod
    Returns (Tuple[int, int]): (-1,-1) on failure, values above otherwise
    """
    try:
        response = requests.get(
            f"https://api.curseforge.com/v1/mods/{mod_id}/files",
            headers={"x-api-key": env["CURSE_API_KEY"]},
            timeout=30,
        )
        data = response.json()["pagination"]
        num_pages = data["totalCount"] // data["pageSize"]
        last_page_size = data["totalCount"] % data["pageSize"]
        return num_pages, last_page_size
    except TimeoutError:
        logmsg("🕜 Timed out getting mod list")
        return -1, -1


def get_changelog(mod_id: str, file_id: str) -> str:
    """
    Gets the changelog from Curse for a given File ID.
    Args: file_id (str): the File ID in question
    Returns: (str): the changelog or a reasonable fallback
    """
    try:
        response = requests.get(
            f"https://api.curseforge.com/v1/mods/{mod_id}/files/{file_id}/changelog",
            headers={"x-api-key": env["CURSE_API_KEY"]},
            timeout=30,
        )
        return response.json()["data"]
    except TimeoutError:
        return "Automagically migrated from CurseForge via https://ctm.oitsjustjose.com"


# region NON-API-CALL FUNCTIONS
def get_loader_info(game_versions: List[str]) -> Tuple[List[str], List[str]]:
    """
    Gets the game version(s) and loader(s) for the mod given the mod's `gameVersions` attr
    Args: game_versions (List[str]): the list of game versions
    Returns: (Tuple[List[str], List[str]]): the minecraft versions and the loader(s), respectively
    """
    mc_versions = list(
        filter(lambda x: re.match(r"^1.[0-9].*.[0-9]?", x), game_versions)
    )
    loaders = list(
        filter(lambda x: x.lower() in ["forge", "quilt", "fabric"], game_versions)
    )
    return mc_versions, [x.lower() for x in loaders] or ["forge"]


def get_version(file_name: str) -> str:
    """
    Gets the version string to be used in Modrinth only, by removing everything but
        numbers and concatenating with a hyphen ("-")
    Args: file_name (str): the file's display name
    Returns: (str): a Modrinth RegEx friendly version number
    """
    ver = re.sub(r"[^0-9.-]", "-", file_name)
    while "--" in ver:
        ver = ver.replace("--", "-")
    while (
        ver.startswith(".")
        or ver.startswith("-")
        or ver.endswith("-")
        or ver.endswith(".")
    ):
        ver = ver.strip(".")
        ver = ver.strip("-")
    return ver


# endregion NON-API-CALL FUNCTIONS
