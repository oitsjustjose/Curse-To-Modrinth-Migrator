import { NextFunction, Request, Response } from "express";

export default () => {
  return (req: Request, res: Response, next: NextFunction) => {
    if (!req.query.mgmtKey || req.query.mgmtKey != process.env.MGMT_KEY) {
      return res.status(403).send(`Key is not authorized`);
    }
    return next();
  };
};
