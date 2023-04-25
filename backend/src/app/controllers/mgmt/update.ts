/* Updates a job with a new status or logmsg */

import { Request, Response } from "express";
import Jobs from "../../models/Job";

export default async (req: Request, res: Response) => {
  if (!req.params.jobId) {
    return res.status(400).send("Field JobId is required in the body");
  }

  const job = await Jobs.findOne({ jobId: req.params.jobId });
  if (!job) {
    return res
      .status(400)
      .send(`Job with ID ${req.params.jobId} was not found`);
  }

  req.body.status && (job.status = req.body.status);
  req.body.log && (job.logs = `${req.body.log}\n${job.logs}`);
  await job.save();

  return res.status(200).send();
};
