import mongoose from "mongoose";

export const connectDb = async () => {
  await mongoose.connect(`mongodb://${process.env.MONGO_URI}/ctmmm`, {
    autoIndex: true,
  });
};
