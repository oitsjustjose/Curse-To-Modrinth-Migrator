import { json, urlencoded } from "body-parser";
import cors from "cors";
import express from "express";
import GetJob from "./app/controllers/job/get";
import PutJob from "./app/controllers/job/put";
import DequeueJob from "./app/controllers/mgmt/dequeue";
import ListResumableJobs from "./app/controllers/mgmt/resumable";
import UpdateJob from "./app/controllers/mgmt/update";
import RequiresKey from "./app/middleware/requiresKey";

const app = express();

app.use(json({ limit: "50mb" }));
app.use(urlencoded({ extended: true }));
app.use(cors());

app.get("/api/v1/jobs/:jobId", GetJob);
app.put("/api/v1/jobs", PutJob);

app.get("/api/v1/mgmt/dequeue", RequiresKey(), DequeueJob);
app.get("/api/v1/mgmt/resumable", RequiresKey(), ListResumableJobs);
app.patch("/api/v1/mgmt/update/:jobId", RequiresKey(), UpdateJob);

export default app;
