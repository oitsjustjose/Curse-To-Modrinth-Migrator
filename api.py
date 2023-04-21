"""
The API endpoints for the proessor
Author: oitsjustjose @ modrinth/curseforge/twitter
"""

import json
from dataclasses import asdict, dataclass
from multiprocessing import Manager, Process
from os import environ as env
from os.path import exists
from time import sleep
from typing import Dict, List, Union

from cryptography.fernet import Fernet
from flask import Flask, request
from shortuuid import ShortUUID

from processor import download, upload


@dataclass
class Job:
    """A single job"""

    github_pat: str
    curseforge_slug: str
    modrinth_id: str
    logs = []
    job_id: str = ShortUUID().random(length=8)
    delimiter: str = "-"


app = Flask(__name__)
fer = Fernet(env["key"])


manager = Manager()
active_jobs: List[Job] = manager.list()
jobs: List[Job] = manager.list()
completed: List[Job] = manager.list()


def job_processor():
    print("Starting the job processor")
    while True:
        try:
            sleep(1)
            if not jobs:
                continue
            active_job = jobs[0]
            active_jobs.append(active_job)

            active_job.logs += download(active_job.curseforge_slug)
            active_job.logs += upload(
                active_job.github_pat,
                active_job.curseforge_slug,
                active_job.modrinth_id,
                active_job.delimiter,
            )

            active_job.github_pat = ""
            completed.append(active_job)

            for idx, obj in enumerate(active_jobs):
                if obj.job_id == active_job.job_id:
                    del active_jobs[idx]
            for idx, obj in enumerate(jobs):
                if obj.job_id == active_job.job_id:
                    del jobs[idx]

        except KeyboardInterrupt:
            break


def save():
    """Saves the current application state to an encrypted file"""

    data = {
        "jobs": [asdict(x) for x in active_jobs] + [asdict(x) for x in jobs],
        "completed": dict(completed),
    }
    with open("./state.dat", "wb") as handle:
        handle.write(fer.encrypt(json.dumps(data).encode()))


def load():
    """Loads the current application state from encrypted file"""
    global active_job, jobs, completed
    if not exists("./state.dat"):
        return
    with open("./state.dat", "rb") as handle:
        data = json.loads(fer.decrypt(handle.read().decode()))
    if "jobs" in data:
        for job in data["jobs"]:
            jobs.append(
                Job(
                    github_pat=job["github_pat"],
                    curseforge_slug=job["curseforge_slug"],
                    modrinth_id=job["modrinth_id"],
                    job_id=job["job_id"],
                    delimiter=job["delimiter"],
                )
            )

    if "completed" in data:
        completed = data["completed"]
    print(completed, jobs)


@app.route("/jobs/status/<uuid>", methods=["GET", "POST"])
def get_job_status(uuid: str) -> str:
    "Gets the queue status for a given job"
    for job in active_jobs:
        if job.job_id == uuid:
            return "Currently Processing", 200

    for job in completed:
        if job.job_id == uuid:
            logs = "\\n".join(job.logs)
            return f"Completed!\n{logs}", 200

    for idx, job in enumerate(jobs):
        if job.job_id == uuid:
            return f"Enqueued: {idx+1} Job(s) Ahead In Queue", 200

    return "Failed to find job", 404


@app.route("/jobs/info/<uuid>", methods=["GET", "POST"])
def get_job_info(uuid: str):
    """Gets the job info for a given uuid"""
    for job in jobs:
        if job.job_id == uuid:
            data = asdict(job)
            data.pop("github_pat")
            return json.dumps(data), 200
    return "Failed to find job", 404


@app.route("/jobs/new", methods=["POST"])
def new_job():
    """Creates a new job"""
    try:
        data = json.loads(request.data)
        jobe = Job(
            github_pat=data["githubPat"],
            curseforge_slug=data["slug"],
            modrinth_id=data["projId"],
            delimiter=data["delimiter"] if "delimiter" in data else "-",
        )

        # Don't enqueue a task that already exists
        for job in jobs:
            if (
                job.github_pat == jobe.github_pat
                and job.curseforge_slug == jobe.curseforge_slug
                and job.modrinth_id == jobe.modrinth_id
                and job.delimiter == jobe.delimiter
            ):
                return job.job_id, 200

        jobs.append(jobe)
        return jobe.job_id, 200
    except:
        return "Internal Server Error", 500


load()
proc = Process(target=job_processor)
proc.start()

app.run("0.0.0.0", 3000)
proc.join()
save()
