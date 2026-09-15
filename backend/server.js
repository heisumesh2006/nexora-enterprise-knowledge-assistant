const express = require("express");
const cors = require("cors");
const dotenv = require("dotenv");

dotenv.config();

const app = express();

const PORT = process.env.PORT || 5000;
const AI_SERVICE_URL = process.env.AI_SERVICE_URL || "http://127.0.0.1:8000";

app.use(cors());
app.use(express.json());

app.get("/health", (req, res) => {
  res.json({
    status: "ok",
    service: "nexora-backend",
  });
});

app.get("/api/health", (req, res) => {
  res.json({
    status: "ok",
    service: "nexora-backend",
  });
});

app.post("/api/ask", async (req, res) => {
  const { question } = req.body;

  if (typeof question !== "string" || !question.trim()) {
    return res.status(400).json({
      error: "Question is required.",
    });
  }

  try {
    const response = await fetch(`${AI_SERVICE_URL}/ask`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question: question.trim(),
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      return res.status(response.status).json({
        error: "AI service request failed.",
        details: data,
      });
    }

    return res.json(data);
  } catch (error) {
    console.error("AI service connection failed:", error);

    return res.status(502).json({
      error: "Unable to connect to AI service.",
    });
  }
});

app.listen(PORT, () => {
  console.log(`Nexora backend running on http://127.0.0.1:${PORT}`);
  console.log(`AI service configured at ${AI_SERVICE_URL}`);
});
