"""
Houses commonly used dataclasses and Enums
Author: oitsjustjose @ modrinth/curseforge/twitter
"""

from dataclasses import dataclass
from enum import Enum
from typing import List


class Status(Enum):
    """Job Status"""

    ENQUEUED = 0
    PROCESSING = 1
    COMPLETE = 2
    SUCCESS = 3
    PARTIAL_FAIL = 4
    FAIL = 5
    NOTFOUND = -1


@dataclass
class Job:
    """A single job"""

    oauth_token: str
    curseforge_slug: str
    modrinth_id: str
    job_id: str = ""
    logs: str = ""
    status: Status = Status.ENQUEUED
    queue_place: int = 0


@dataclass
class ModInfo:
    """Stores metadata about a jarfile to be extrapolated"""

    mod_version: str
    modrinth_name: str
    loaders: List[str]
    game_version: str  # representative game ver
    game_versions: List[str]  # actual game vers
