"""
Does the actual work behind the scenes
Author: oitsjustjose @ modrinth/curseforge/twitter
"""
from os import environ as env
from os import system as run
from time import sleep

from common import Job, Status
from mgmt_tools import MgmtApiHelper
from x_fast_provider import FastProvider
from x_slow_provider import SlowProvider


def process_job(helper: MgmtApiHelper, job: Job):
    """Handles the download and upload process for a single job"""
    helper.update_job_status(job.job_id, Status.PROCESSING)

    # Try to use the fast provider first
    fast_prov = FastProvider(helper, job)
    if fast_prov.supports_downloads():
        helper.append_job_log(
            job.job_id,
            f"ℹ️ Mod {job.curseforge_slug} supports third-party launchers, migration will be quick 🙂",
        )
        status = fast_prov.process()
        helper.update_job_status(job.job_id, Status.COMPLETE)
        helper.append_job_log(job.job_id, f"***{status.name}***")
        return

    # Otherwise use the slow provider since you're a goblin 👺
    slow_prov = SlowProvider(helper, job)
    helper.append_job_log(
        job.job_id,
        f"ℹ️ Mod {job.curseforge_slug} does not support third-party launchers, migration will be slowed by workarounds 😭",
    )
    status = slow_prov.process()
    helper.update_job_status(job.job_id, Status.COMPLETE)
    helper.append_job_log(job.job_id, f"***{status.name}***")


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
