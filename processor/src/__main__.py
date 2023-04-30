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


def _download(helper: MgmtApiHelper, job: Job, retries=0) -> Status:
    """Performs function - returns True if success, False otherwise"""
    try:
        downloader = CurseDownloader(helper, job)
        status = downloader.download()
        if status == Status.FAIL:
            helper.update_job_status(job.job_id, Status.COMPLETE)
            helper.append_job_log(job.job_id, "***FAILED***")
        return status
    except Exception as exc:
        helper.update_job_status(job, Status.ENQUEUED)
        helper.append_job_log(
            job,
            f"Download Error: {exc}. Restarting Download.. ({3-retries} retries left)",
        )
        print(exc)
        if retries <= 3:
            sleep(10)
            return _download(helper, job, retries=retries + 1)
    return Status.FAIL


def _upload(helper: MgmtApiHelper, job: Job, retries=0) -> Status:
    """Performs function - returns True if success, False otherwise"""
    try:
        uploader = ModrinthUploader(helper, job)
        status = uploader.upload()
        return status
    except Exception as exc:
        helper.update_job_status(job, Status.ENQUEUED)
        helper.append_job_log(
            job,
            f"Upload Error: {exc}. Restarting Upload.. ({3-retries} retries left)",
        )
        if retries <= 3:
            sleep(10)
            return _upload(helper, job, retries=retries + 1)
    return Status.FAIL


def process_job(helper: MgmtApiHelper, job: Job):
    """Handles the download and upload process for a single job"""
    helper.update_job_status(job.job_id, Status.PROCESSING)

    download_status = _download(helper, job)
    if download_status == Status.FAIL:
        return

    upload_status = _upload(helper, job)

    status = Status(max(download_status.value, upload_status.value)).name
    helper.update_job_status(job.job_id, Status.COMPLETE)
    helper.append_job_log(job.job_id, f"***{status}***")


def resume(helper: MgmtApiHelper):
    """Resumes processing jobs on server restart"""
    print("Resuming jobs from last run")

    for job in helper.get_resumable_jobs():
        print(f"Resuming job {job.job_id}")
        process_job(helper, job)


def work(helper: MgmtApiHelper) -> bool:
    """Does the actual lifting"""
    sleep(2)  # Sleep to make sure DB processing is done
    job: Job = helper.get_next_job()
    if not job:
        return False
    process_job(helper, job)
    return True


def main_loop():
    """The main process loop"""
    helper = MgmtApiHelper()

    print("Starting virtual display")
    run("Xvfb -ac :99 -screen 0 1280x1024x16 &")
    env["DISPLAY"] = ":99"
    print("Done initializing VDisplay")

    print("Starting the job processor")
    resume(helper)
    while True:
        try:
            if work(helper):
                sleep(1)
            else:
                sleep(5)
        except KeyboardInterrupt:
            run("pkill -9 Xvfb")
            print("Quitting")
            break


if __name__ == "__main__":
    main_loop()
