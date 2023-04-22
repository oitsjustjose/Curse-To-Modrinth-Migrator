"""
Houses data classes
Author: oitsjustjose @ modrinth/curseforge/twitter
"""
from dataclasses import dataclass
from enum import Enum
from typing import List, Union


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

    github_pat: str
    curseforge_slug: str
    modrinth_id: str
    job_id: str = ""
    delimiter: str = "-"
    logs: str = ""
    status: Status = Status.ENQUEUED
    queue_place: int = 0


@dataclass
class ModInfo:
    """Stores metadata about a jarfile to be extrapolated"""

    name: str
    mod_version: str
    modrinth_name: str
    game_version: str  # representative game ver
    game_versions: List[str]  # actual game vers
