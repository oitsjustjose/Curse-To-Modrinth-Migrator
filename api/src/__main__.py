"""
The API endpoints for the proessor
Author: oitsjustjose @ modrinth/curseforge/twitter
"""

import json
from dataclasses import asdict
from multiprocessing import Process
from os import environ as env

from flask import Flask, request

from data import Status
from job_database import Job, JobDb, Status
from job_processor import worker

app = Flask(__name__)

db = JobDb(env["MONGO_URI"], int(env["MONGO_PORT"]))


@app.route("/jobs/status/<job_id>", methods=["GET", "POST"])
def get_job_status(job_id: str) -> str:
    "Gets the queue status for a given job"

    status, logs, queue = db.get_job_status(job_id)
    if status == Status.ENQUEUED:
        return f"Enqueued: {queue} Job(s) Ahead In Queue", 200
    if status == Status.PROCESSING:
        return f"Currently Processing\n{logs}", 200
    if status == Status.COMPLETE:
        return logs, 200
    return "Failed to find job", 404


@app.route("/jobs/info/<job_id>", methods=["GET", "POST"])
def get_job_info(job_id: str):
    """Gets the job info for a given uuid"""
    job = db.get_job(job_id)
    if not job:
        return "Failed to find job", 404
    job.github_pat = ""
    return json.dumps(asdict(job), indent=2), 200


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

        # Job already exists in queue, give it back
        existing = db.get_existing_queued_job(jobe.curseforge_slug, jobe.modrinth_id)
        if existing:
            return existing, 200
        return db.enqueue_job(jobe), 200
    except:
        return "Internal Server Error", 500


if __name__ == "__main__":
    proc_cnt: int = int(env["PROCS"]) if "PROCS" in env else 1
    processes = [Process(target=worker) for _ in range(proc_cnt)]
    _ = [p.start() for p in processes]
    app.run("0.0.0.0", env["PORT"] if "PORT" in env else 3000)
    _ = [p.join() for p in processes]
