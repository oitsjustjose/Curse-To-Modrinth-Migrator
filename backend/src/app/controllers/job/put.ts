import { Request, Response } from "express";
import Job from "../../models/Job";
import Status from "../../status";
import { Fernet } from "fernet-nodejs";

const getNextQueuePlace = async () => {
  const allActiveJobs = await Job.find({ status: Status.ENQUEUED }).sort({
    queue_place: "desc",
  });
  if (allActiveJobs.length) {
    return allActiveJobs[0].queuePlace + 1;
  }
  return 1;
};

export default async (req: Request, res: Response) => {
  try {
    if (
      !req.body.githubPat ||
      !req.body.curseforgeSlug ||
      !req.body.modrinthId
    ) {
      return res
        .status(403)
        .send(
          [
            "Missing a required parameter in the JSON body",
            "Required params: githubPat: string, curseforgeSlug: string, modrinthId: string",
          ].join(" ")
        );
    }

    const fern = new Fernet(process.env.SECRET);

    const newJob = new Job({
      githubPat: fern.encrypt(req.body.githubPat),
      curseforgeSlug: req.body.curseforgeSlug,
      modrinthId: req.body.modrinthId,
      delimiter: req.body.delimiter || "-",
      queuePlace: await getNextQueuePlace(),
    });

    await newJob.save();
    return res.status(200).send(newJob.jobId);
  } catch (ex) {
    console.log(ex);
    return res.status(500).send(ex);
  }
};
