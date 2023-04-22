"""
DB Handling for Jobs
Author: oitsjustjose @ modrinth/curseforge/twitter
"""

from dataclasses import asdict
from os import environ as env
from typing import Dict, List, Tuple, Union

from cryptography.fernet import Fernet
from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from shortuuid import ShortUUID

from data import Job, Status


class JobDb:
    """A database for the job queue"""

    def __init__(self, host: str, port: int):
        self._client: MongoClient = MongoClient(host, port)
        self._db: Database = self._client["ctmmm"]
        self._coll: Collection = self._db["jobs"]
        self._fernet = Fernet(env["SECRET"])
        self._shrt = ShortUUID()

    def get_job(self, job_id: str) -> Union[Job, None]:
        """Gets a job by the job's short ID"""
        data: Union[dict, None] = self._coll.find_one({"job_id": job_id})
        if not data:
            return None
        return self._dict_to_job(data)

    def get_next_job(self) -> Union[Job, None]:
        """Gets the next job to do, if any"""
        data: List[Union[dict, None]] = list(
            self._coll.find({"status": Status.ENQUEUED.value})
            .sort("queue_place", ASCENDING)
            .limit(1)
        )
        if data:
            return self._dict_to_job(data[0])
        return None

    def get_active_jobs(self) -> List[Job]:
        data: List[Union[dict, None]] = list(
            self._coll.find({"status": Status.PROCESSING.value})
            .sort("queue_place", ASCENDING)
            .limit(1)
        )
        return [self._dict_to_job(x) for x in data]

    def enqueue_job(self, job: Job) -> str:
        """Inserts the job, with corrected Queue Place and encrypted PAT"""
        queue_place = 0
        data: List[Union[dict, None]] = list(
            self._coll.find({"status": Status.ENQUEUED.value})
            .sort("queue_place", DESCENDING)
            .limit(1)
        )
        if data:
            queue_place = data[0]["queue_place"] + 1
        job.queue_place = queue_place
        job.github_pat = self._fernet.encrypt(job.github_pat.encode())
        job.status = job.status.value
        job.job_id = self._shrt.random(length=8)
        self._coll.insert_one(asdict(job))
        return job.job_id

    def update_job_status(
        self, job_id: str, status: Status, logs: Union[str, None] = None
    ) -> None:
        """Updates the status of a job, and logs, if applicable"""
        update = {"status": status.value}
        if logs:
            update["logs"] = logs
        self._coll.update_one({"job_id": job_id}, {"$set": update})

    def get_job_status(self, job_id: str) -> Tuple[Status, str, int]:
        """Gets the status of a job, including queue place and logs"""
        data: Union[dict, None] = self._coll.find_one({"job_id": job_id})
        if not data:
            return (Status.NOTFOUND, [], -1)
        return (
            Status(data["status"]),
            data["logs"],
            data["queue_place"],
        )

    def get_existing_queued_job(self, slug: str, proj_id: str) -> Union[str, None]:
        """Gets the existing job ID if it exists"""
        data: Union[dict, None] = self._coll.find_one(
            {
                "status": Status.ENQUEUED.value,
                "curseforge_slug": slug,
                "modrinth_id": proj_id,
            }
        )
        print(data)
        if not data:
            return None
        return data["job_id"]

    def _dict_to_job(self, data: Dict) -> Job:
        """Converts a dictionary (from mongo) into a Job"""
        return Job(
            github_pat=self._fernet.decrypt(data["github_pat"].decode()),
            curseforge_slug=data["curseforge_slug"],
            modrinth_id=data["modrinth_id"],
            logs=data["logs"] if "logs" in data else [],
            job_id=data["job_id"],
            delimiter=data["delimiter"] if "delimiter" in data else "-",
            status=data["status"],
            queue_place=data["queue_place"],
        )
