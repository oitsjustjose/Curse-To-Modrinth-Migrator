import { Document, model, Schema } from "mongoose";
import shortid from "shortid";
import Status from "../status";

export type JobType = Document & {
  jobId: string;
  oauthToken: string;
  curseforgeSlug: string;
  modrinthId: string;
  logs: string;
  status: number;
  queuePlace: number;
};

const JobSchema = new Schema<JobType>({
  jobId: {
    type: String,
    default: shortid.generate,
    required: true,
  },
  oauthToken: {
    type: String,
    required: true,
  },
  curseforgeSlug: {
    type: String,
    required: true,
  },
  modrinthId: {
    type: String,
    required: true,
  },
  logs: {
    type: String,
    default: "",
  },
  status: {
    type: Number,
    default: Status.ENQUEUED,
  },
  queuePlace: {
    type: Number,
    required: true,
  },
});

export default model<JobType>("jobs", JobSchema, "jobs");
