"""
Houses API Tools when communicating with the RESTful API
Author: oitsjustjose @ modrinth/curseforge/twitter
"""
from os import environ as env
from typing import Dict, List, Union

import requests
from cryptography.fernet import Fernet

from common import Job, Status


class MgmtApiHelper:
    """An API Helper for the Job API"""

    def __init__(self):
        self._mgmt_timeout = 30
        self._mgmt_host = env["MGMT_HOST"]
        self._mgmt_key = env["MGMT_KEY"]
        self._fernet = Fernet(env["SECRET"])

    # REGION NON JOB-SPECIFIC METHODS

    def get_next_job(self) -> Union[Job, None]:
        """Gets the next job to do, if any"""
        resp = requests.get(
            f"{self._mgmt_host}/api/v1/mgmt/dequeue?mgmtKey={self._mgmt_key}",
            timeout=self._mgmt_timeout,
        )
        # 404 response is for if there's nothing to dequeue
        if resp.status_code == 404:
            return None
        return self._dict_to_job(resp.json())

    def get_resumable_jobs(self) -> List[Job]:
        """Gets all active jobs - only used for resuming between restarts"""
        resp = requests.get(
            f"{self._mgmt_host}/api/v1/mgmt/resumable?mgmtKey={self._mgmt_key}",
            timeout=self._mgmt_timeout,
        )
        return [self._dict_to_job(x) for x in resp.json()]

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

    # ENDREGION NON JOB-SPECIFIC METHODS

    def update_job_status(self, job_id: str, status: Status) -> None:
        """Updates the status of a job"""
        requests.patch(
            f"{self._mgmt_host}/api/v1/mgmt/update/{job_id}?mgmtKey={self._mgmt_key}",
            timeout=self._mgmt_timeout,
            data={"status": status.value},
        )

    def append_job_log(self, job_id: str, newlog: str) -> None:
        """Appends to the logs for a job"""
        requests.patch(
            f"{self._mgmt_host}/api/v1/mgmt/update/{job_id}?mgmtKey={self._mgmt_key}",
            timeout=self._mgmt_timeout,
            data={"log": newlog},
        )


class MgmtApiLogger:
    """
    A base class for Upload and Download that indicates how to log via API
    Args:
        helper (MgmtApiHelper): the job api controller
        job_id (str): the job id for the given job
    """

    def __init__(self, helper: MgmtApiHelper, job_id: str):
        self.helper = helper
        self._job_id = job_id

    def logmsg(self, msg: str) -> None:
        """
        Logs a message to the database
        Args: msg(str): the message to log
        """
        self.helper.append_job_log(self._job_id, msg)
