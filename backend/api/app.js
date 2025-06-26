//backend\api\app.js
import express from "express";
import {
  insertSignal,
  insertOrder,
  insertTrade,
  insertEvent,
} from "./services/db.js";

const app = express();
app.use(express.json());

app.post("/signal", async (req, res) => {
  try {
    const result = await insertSignal(req.body);
    res.json(result);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Failed to save signal" });
  }
});

app.post("/order", async (req, res) => {
  try {
    const result = await insertOrder(req.body);
    res.json(result);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Failed to save order" });
  }
});

app.post("/trade", async (req, res) => {
  try {
    const result = await insertTrade(req.body);
    res.json(result);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Failed to save trade" });
  }
});

app.post("/event", async (req, res) => {
  try {
    const result = await insertEvent(req.body);
    res.json(result);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Failed to save event" });
  }
});

export default app;

if (process.env.NODE_ENV !== "test") {
  const port = process.env.PORT || 3000;
  app.listen(port, () => {
    console.log(`API server listening on port ${port}`);
  });
}
