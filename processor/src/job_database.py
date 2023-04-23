"""
DB Handling for Jobs
Author: oitsjustjose @ modrinth/curseforge/twitter
"""

from os import environ as env
from typing import Dict, List, Union

from cryptography.fernet import Fernet
from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from common import Job, Status


class JobDb:
    """A database for the job queue"""

    def __init__(self, host: str = "", port: int = 0):
        self._client: MongoClient = MongoClient(host or "localhost", port or 27017)
        self._db: Database = self._client["ctmmm"]
        self._coll: Collection = self._db["jobs"]
        self._fernet = Fernet(env["SECRET"])

    def get_next_job(self) -> Union[Job, None]:
        """Gets the next job to do, if any"""
        data: List[Union[dict, None]] = list(
            self._coll.find({"status": Status.ENQUEUED.value})
            .sort("queuePlace", ASCENDING)
            .limit(1)
        )
        if data:
            return self._dict_to_job(data[0])
        return None

    def get_active_jobs(self) -> List[Job]:
        """Gets all active jobs - only used for resuming between restarts"""
        data: List[Union[dict, None]] = list(
            self._coll.find({"status": Status.PROCESSING.value}).sort(
                "queuePlace", ASCENDING
            )
        )
        return [self._dict_to_job(x) for x in data]

    def update_job_status(self, job_id: str, status: Status) -> None:
        """Updates the status of a job, and logs, if applicable"""
        self._coll.update_one({"jobId": job_id}, {"$set": {"status": status.value}})

    def append_job_log(self, job_id: str, newlog: str) -> None:
        """Updates the status of a job, and logs, if applicable"""
        job = self._coll.find_one({"jobId": job_id})
        self._coll.update_one(
            {"jobId": job_id}, {"$set": {"logs": f"{newlog}\n{job['logs']}"}}
        )

    def get_existing_queued_job(self, slug: str, proj_id: str) -> Union[str, None]:
        """Gets the existing job ID if it exists"""
        data: Union[dict, None] = self._coll.find_one(
            {
                "status": Status.ENQUEUED.value,
                "curseforgeSlug": slug,
                "modrinthId": proj_id,
            }
        )
        print(data)
        if not data:
            return None
        return data["jobId"]

    def _dict_to_job(self, data: Dict) -> Job:
        """Converts a dictionary (from mongo) into a Job"""
        return Job(
            github_pat=self._fernet.decrypt(data["githubPat"]),
            curseforge_slug=data["curseforgeSlug"],
            modrinth_id=data["modrinthId"],
            logs=data["logs"] if "logs" in data else [],
            job_id=data["jobId"],
            delimiter=data["delimiter"] if "delimiter" in data else "-",
            status=data["status"],
            queue_place=data["queuePlace"],
        )
