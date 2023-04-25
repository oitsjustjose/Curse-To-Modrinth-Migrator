import { Request, Response } from "express";
import Jobs from "../../models/Job";
import Status from "../../status";

export default async (req: Request, res: Response) => {
  try {
    if (!req.params.jobId) {
      return res.status(400).send("URL Param for Job ID is required");
    }

    const job = await Jobs.findOne({ jobId: req.params.jobId });
    if (!job) {
      return res
        .status(404)
        .send(`Job with id ${req.params.jobId} was not found`);
    }

    // Determine how many items in the queue are ahead of this one
    const aheadInQueue = await Jobs.find({
      queue_place: { $lt: job.queuePlace },
    });

    let text: string = "";
    if (job.status == Status.ENQUEUED) {
      text = `Enqueued: ${aheadInQueue.length} Job(s) ahead in queue`;
    } else if (job.status == Status.PROCESSING) {
      text = `Currently Processing\n${job.logs}`;
    } else if (job.status == Status.COMPLETE) {
      text = job.logs;
    } else {
      text = "Could not find job status";
    }

    return res.status(200).send(text);
  } catch (ex) {
    return res.status(500).json(ex);
  }
};
