"""
Does the actual work behind the scenes
Author: oitsjustjose @ modrinth/curseforge/twitter
"""
from os import environ as env
from time import sleep

from data import Job, Status
from job_database import JobDb
from netio_processor import download, upload


def _resume(job_db: JobDb):
    """Resumes processing jobs on server restart"""
    print("Resuming jobs from last run")

    for job in job_db.get_active_jobs():
        print(f"Resuming job {job.job_id}")
        job_db.update_job_status(job.job_id, Status.PROCESSING)
        dl_status, dl_logs = download(job.curseforge_slug)
        if dl_status == Status.FAIL:  # Failed - early exit, update DB for user
            job_db.update_job_status(
                job.job_id, Status.COMPLETE, "\n".join(["**FAILED**"] + dl_logs)
            )
            continue
        # Didn't fail, update DB with latest logs and same status
        job_db.update_job_status(job.job_id, Status.PROCESSING, "\n".join(dl_logs))
        ul_status, ul_logs = upload(
            job.github_pat, job.curseforge_slug, job.modrinth_id, job.delimiter
        )
        # Take the higher severity - it would only be
        text_status = Status(max(dl_status.value, ul_status.value)).name
        job_db.update_job_status(
            job.job_id,
            Status.COMPLETE,
            "\n".join([f"**{text_status}**"] + ul_logs + dl_logs),
        )


def _work(job_db: JobDb) -> bool:
    """Does the actual lifting"""
    job: Job = job_db.get_next_job()
    if not job:
        return False

    job_db.update_job_status(job.job_id, Status.PROCESSING)
    dl_status, dl_logs = download(job.curseforge_slug)
    if dl_status == Status.FAIL:  # Failed - early exit, update DB for user
        job_db.update_job_status(
            job.job_id, Status.COMPLETE, "\n".join(["**FAILED**"] + dl_logs)
        )
        return True
    # Didn't fail, update DB with latest logs and same status
    job_db.update_job_status(job.job_id, Status.PROCESSING, "\n".join(dl_logs))
    ul_status, ul_logs = upload(
        job.github_pat, job.curseforge_slug, job.modrinth_id, job.delimiter
    )
    # Take the higher severity - it would only be
    text_status = Status(max(dl_status.value, ul_status.value)).name
    job_db.update_job_status(
        job.job_id,
        Status.COMPLETE,
        "\n".join([f"**{text_status}**"] + ul_logs + dl_logs),
    )
    return True


def worker():
    """A worker thread function for processing jobs in the job db"""
    print("Starting the job processor")
    job_db = JobDb(env["MONGO_URI"], int(env["MONGO_PORT"]))
    _resume(job_db)
    while True:
        try:
            if _work(job_db):
                sleep(1)
            else:
                sleep(5)
        except KeyboardInterrupt:
            break
