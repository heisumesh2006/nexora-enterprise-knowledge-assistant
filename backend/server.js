const express = require("express");
const cors = require("cors");
const dotenv = require("dotenv");

const { askAI } = require("./services/aiService");

dotenv.config();

const app = express();

const PORT = Number(process.env.PORT) || 5000;

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
    const data = await askAI(question.trim());

    return res.status(200).json({
      question: data.question,
      answer: data.answer,
      citations: data.citations,
    });
  } catch (error) {
    console.error("AI service request failed:", error);

    if (error.code === "AI_SERVICE_TIMEOUT") {
      return res.status(504).json({
        error: "AI service request timed out.",
      });
    }

    if (error.status) {
      return res.status(502).json({
        error: "AI service returned an error.",
        details: error.details,
      });
    }

    return res.status(503).json({
      error: "AI service is unavailable.",
    });
  }
});

app.listen(PORT, () => {
  console.log(`Nexora backend running on http://127.0.0.1:${PORT}`);
});
