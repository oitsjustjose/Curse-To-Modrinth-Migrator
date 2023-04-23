"""
Does the actual work behind the scenes
Author: oitsjustjose @ modrinth/curseforge/twitter
"""
from os import environ as env
from os import system as run
from time import sleep

from common import Job, Status
from curse_downloader import CurseDownloader
from job_database import JobDb
from modrinth_uploader import ModrinthUploader


def _process(job_db: JobDb, job: Job):
    """Handles the download and upload process for a single job"""
    job_db.update_job_status(job.job_id, Status.PROCESSING)

    downloader = CurseDownloader(job_db, job)
    dls = downloader.download()
    if dls == Status.FAIL:
        job_db.update_job_status(job.job_id, Status.COMPLETE)
        job_db.append_job_log(job.job_id, "***FAILED***")
        return

    uploader = ModrinthUploader(job_db, job)
    uls = uploader.upload()

    stat = Status(max(dls.value, uls.value)).name
    job_db.update_job_status(job.job_id, Status.COMPLETE)
    job_db.append_job_log(job.job_id, f"***{stat}***")


def _resume(job_db: JobDb):
    """Resumes processing jobs on server restart"""
    print("Resuming jobs from last run")

    for job in job_db.get_active_jobs():
        print(f"Resuming job {job.job_id}")
        _process(job_db, job)


def _work(job_db: JobDb) -> bool:
    """Does the actual lifting"""
    job: Job = job_db.get_next_job()
    if not job:
        return False
    _process(job_db, job)
    return True


def main_loop():
    """The main process loop"""

    print("Init DB connection")
    job_db = JobDb(
        env["MONGO_URI"] if "MONGO_URI" in env else "localhost",
        int(env["MONGO_PORT"]) if "MONGO_PORT" in env else 27017,
    )
    print("DB Connected")

    print("Starting virtual display")
    run("Xvfb -ac :99 -screen 0 1280x1024x16 &")
    env["DISPLAY"] = ":99"
    print("Done initializing VDisplay")

    print("Starting the job processor")
    _resume(job_db)
    while True:
        try:
            if _work(job_db):
                sleep(1)
            else:
                sleep(5)
        except KeyboardInterrupt:
            run("pkill -9 Xvfb")
            print("Quitting")
            break


if __name__ == "__main__":
    main_loop()
