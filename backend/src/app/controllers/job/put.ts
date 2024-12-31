import { Request, Response } from "express";
import Job from "../../models/Job";
import Status from "../../status";
import { Fernet } from "fernet-nodejs";

type OAuthTokenResponse = {
  access_token: string;
  token_type: string;
  expires_in: number;
};

const getNextQueuePlace = async () => {
  const allActiveJobs = await Job.find({ status: Status.ENQUEUED }).sort({
    queuePlace: "desc",
  });
  if (allActiveJobs.length) {
    return allActiveJobs[0].queuePlace + 1;
  }
  return 1;
};

export default async (req: Request, res: Response) => {
  try {
    if (
      !req.body.clientOauthCode ||
      !req.body.curseforgeSlug ||
      !req.body.modrinthId
    ) {
      return res
        .status(403)
        .send(
          [
            "Missing a required parameter in the JSON body",
            "Required params: clientOauthCode: string, curseforgeSlug: string, modrinthId: string",
          ].join(" ")
        );
    }

    const response = await fetch(
      "https://api.modrinth.com/_internal/oauth/token",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          Authorization: process.env.MODRINTH_OAUTH_CLIENT_SECRET,
        },
        body: new URLSearchParams({
          code: req.body.clientOauthCode,
          client_id: process.env.MODRINTH_OAUTH_CLIENT_ID,
          redirect_uri: "https://ctm.oitsjustjose.com/",
          grant_type: "authorization_code",
        }),
      }
    );

    if (!response.ok) {
      return res.status(400).send(response);
    }

    const body = (await response.json()) as OAuthTokenResponse;

    const fern = new Fernet(process.env.SECRET);
    const newJob = new Job({
      oauthToken: fern.encrypt(body.access_token),
      curseforgeSlug: req.body.curseforgeSlug,
      modrinthId: req.body.modrinthId,
      queuePlace: await getNextQueuePlace(),
    });

    await newJob.save();
    return res.status(200).send(newJob.jobId);
  } catch (ex) {
    console.log(ex);
    return res.status(500).send(ex);
  }
};
