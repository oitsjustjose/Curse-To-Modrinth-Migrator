import { json, urlencoded } from "body-parser";
import cors from "cors";
import express from "express";
import GetJob from "./app/controllers/job/get";
import PutJob from "./app/controllers/job/put";

const app = express();

app.use(json({ limit: "50mb" }));
app.use(urlencoded({ extended: true }));
app.use(cors());

app.post("/api/v1/jobs/:jobId", GetJob);
app.put("/api/v1/jobs", PutJob);

export default app;
