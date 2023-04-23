import App from "./app";
import { connectDb } from "./db";

(async () => {
  await connectDb();
  const port = process.env.PORT || 3030;
  App.listen(port, () => console.log(`Listening on http://0.0.0.0:${port}`));
})();
