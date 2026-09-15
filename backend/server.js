const express = require("express");
const cors = require("cors");
const dotenv = require("dotenv");
const multer = require("multer");
const path = require("path");
const fs = require("fs");

const { askAI } = require("./services/aiService");
const { addDocument, getDocuments } = require("./services/documentRegistry");

dotenv.config();

const app = express();

const PORT = Number(process.env.PORT) || 5000;

const UPLOAD_DIR = path.join(__dirname, "uploads");

if (!fs.existsSync(UPLOAD_DIR)) {
  fs.mkdirSync(UPLOAD_DIR, { recursive: true });
}

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, UPLOAD_DIR);
  },

  filename: (req, file, cb) => {
    const uniqueSuffix = `${Date.now()}-${Math.round(Math.random() * 1e9)}`;
    const extension = path.extname(file.originalname);

    cb(
      null,
      `${path.basename(file.originalname, extension)}-${uniqueSuffix}${extension}`,
    );
  },
});

const upload = multer({
  storage,
  limits: {
    fileSize: 10 * 1024 * 1024,
  },
  fileFilter: (req, file, cb) => {
    const allowedExtensions = [".pdf", ".txt", ".docx"];
    const extension = path.extname(file.originalname).toLowerCase();

    if (!allowedExtensions.includes(extension)) {
      return cb(new Error("Only PDF, TXT, and DOCX files are supported."));
    }

    cb(null, true);
  },
});

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
app.get("/api/documents", (req, res) => {
  try {
    const documents = getDocuments();

    return res.status(200).json({
      documents,
    });
  } catch (error) {
    console.error("Failed to load document registry:", error);

    return res.status(500).json({
      error: "Failed to load documents.",
    });
  }
});

app.post("/api/documents/upload", upload.single("document"), (req, res) => {
  if (!req.file) {
    return res.status(400).json({
      error: "No document was uploaded.",
    });
  }

  try {
    const document = addDocument({
      originalName: req.file.originalname,
      storedName: req.file.filename,
      size: req.file.size,
      type: req.file.mimetype,
    });

    return res.status(201).json({
      message: "Document uploaded successfully.",
      document,
    });
  } catch (error) {
    console.error("Failed to register uploaded document:", error);

    return res.status(500).json({
      error: "Document was uploaded but could not be registered.",
    });
  }
});
app.use((error, req, res, next) => {
  if (error instanceof multer.MulterError) {
    if (error.code === "LIMIT_FILE_SIZE") {
      return res.status(413).json({
        error: "File size must not exceed 10 MB.",
      });
    }

    return res.status(400).json({
      error: error.message,
    });
  }

  if (error) {
    return res.status(400).json({
      error: error.message,
    });
  }

  next();
});

app.listen(PORT, () => {
  console.log(`Nexora backend running on http://127.0.0.1:${PORT}`);
});
