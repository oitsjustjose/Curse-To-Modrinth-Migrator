/* Gets any jobs that were Processing when the processing node restarted */
import { Request, Response } from "express";
import Jobs from "../../models/Job";
import Status from "../../status";

export default async (req: Request, res: Response) => {
  const jobs = await Jobs.find({ status: Status.PROCESSING }).sort({
    queuePlace: "asc",
  });

  return res.status(200).json(jobs);
};
