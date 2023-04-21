"""Does the actual work behind the scenes"""
from os import environ as env
from time import sleep

from db import Job, JobDb, Status
from processor import download, upload


def resume(job_db: JobDb):
    """Resumes processing jobs on server restart"""
    print("Resuming jobs from last run")

    for job in job_db.get_active_jobs():
        sleep(1)
        job: Job = job_db.get_next_job()
        if not job:
            sleep(5)
            continue
        job_db.update_job_status(job.job_id, Status.PROCESSING)
        logs = download(job.curseforge_slug)
        job_db.update_job_status(job.job_id, Status.PROCESSING, "\n".join(logs))
        logs += upload(
            job.github_pat,
            job.curseforge_slug,
            job.modrinth_id,
            job.delimiter,
        )
        job_db.update_job_status(job.job_id, Status.COMPLETED, "\n".join(logs))


def work(job_db: JobDb) -> bool:
    """Does the actual lifting"""
    job: Job = job_db.get_next_job()
    if not job:
        return False
    job_db.update_job_status(job.job_id, Status.PROCESSING)
    logs = download(job.curseforge_slug)
    job_db.update_job_status(job.job_id, Status.PROCESSING, "\n".join(logs))
    logs += upload(
        job.github_pat,
        job.curseforge_slug,
        job.modrinth_id,
        job.delimiter,
    )
    job_db.update_job_status(job.job_id, Status.COMPLETED, "\n".join(logs))
    return True


def worker():
    """A worker thread function for processing jobs in the job db"""
    print("Starting the job processor")
    job_db = JobDb(env["MONGO_URI"], int(env["MONGO_PORT"]))
    resume(job_db)
    while True:
        try:
            if work(job_db):
                sleep(1)
            else:
                sleep(5)
        except KeyboardInterrupt:
            break
