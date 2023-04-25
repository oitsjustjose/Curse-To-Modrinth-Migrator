"""
Does the actual work behind the scenes
Author: oitsjustjose @ modrinth/curseforge/twitter
"""
from os import environ as env
from os import system as run
from time import sleep

from common import Job, Status
from curse_downloader import CurseDownloader
from mgmt_tools import MgmtApiHelper
from modrinth_uploader import ModrinthUploader


def _process(helper: MgmtApiHelper, job: Job):
    """Handles the download and upload process for a single job"""
    helper.update_job_status(job.job_id, Status.PROCESSING)

    downloader = CurseDownloader(helper, job)
    dls = downloader.download()
    if dls == Status.FAIL:
        helper.update_job_status(job.job_id, Status.COMPLETE)
        helper.append_job_log(job.job_id, "***FAILED***")
        return

    uploader = ModrinthUploader(helper, job)
    uls = uploader.upload()

    stat = Status(max(dls.value, uls.value)).name
    helper.update_job_status(job.job_id, Status.COMPLETE)
    helper.append_job_log(job.job_id, f"***{stat}***")


def _resume(helper: MgmtApiHelper):
    """Resumes processing jobs on server restart"""
    print("Resuming jobs from last run")

    for job in helper.get_resumable_jobs():
        print(f"Resuming job {job.job_id}")
        _process(helper, job)


def _work(helper: MgmtApiHelper) -> bool:
    """Does the actual lifting"""
    sleep(2)  # Sleep to make sure DB processing is done
    job: Job = helper.get_next_job()
    if not job:
        return False
    _process(helper, job)
    return True


def main_loop():
    """The main process loop"""

    print("Init DB connection")
    helper = MgmtApiHelper()
    print("DB Connected")

    print("Starting virtual display")
    run("Xvfb -ac :99 -screen 0 1280x1024x16 &")
    env["DISPLAY"] = ":99"
    print("Done initializing VDisplay")

    print("Starting the job processor")
    _resume(helper)
    while True:
        try:
            if _work(helper):
                sleep(1)
            else:
                sleep(5)
        except KeyboardInterrupt:
            run("pkill -9 Xvfb")
            print("Quitting")
            break


if __name__ == "__main__":
    main_loop()
