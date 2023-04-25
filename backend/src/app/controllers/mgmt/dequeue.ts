/* Gets the next job in the queue */
import { Request, Response } from "express";
import Jobs from "../../models/Job";
import Status from "../../status";

export default async (req: Request, res: Response) => {
  const [job] = await Jobs.find({ status: Status.ENQUEUED })
    .sort({ queuePlace: "asc" })
    .limit(1);

  if (job) {
    return res.status(200).json(job);
  }

  return res.status(404).send();
};
