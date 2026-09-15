const dotenv = require("dotenv");

dotenv.config();

const AI_SERVICE_URL = process.env.AI_SERVICE_URL || "http://127.0.0.1:8000";

const AI_SERVICE_TIMEOUT_MS =
  Number(process.env.AI_SERVICE_TIMEOUT_MS) || 30000;

async function askAI(question) {
  const controller = new AbortController();

  const timeout = setTimeout(() => {
    controller.abort();
  }, AI_SERVICE_TIMEOUT_MS);

  try {
    const response = await fetch(`${AI_SERVICE_URL}/ask`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question,
      }),
      signal: controller.signal,
    });

    let data;

    try {
      data = await response.json();
    } catch {
      throw new Error("AI service returned an invalid JSON response.");
    }

    if (!response.ok) {
      const error = new Error("AI service returned an error.");
      error.status = response.status;
      error.details = data;
      throw error;
    }

    return data;
  } catch (error) {
    if (error.name === "AbortError") {
      const timeoutError = new Error("AI service request timed out.");
      timeoutError.code = "AI_SERVICE_TIMEOUT";
      throw timeoutError;
    }

    if (error.status) {
      throw error;
    }

    const connectionError = new Error("Unable to connect to AI service.");
    connectionError.code = "AI_SERVICE_UNAVAILABLE";
    connectionError.cause = error;

    throw connectionError;
  } finally {
    clearTimeout(timeout);
  }
}

module.exports = {
  askAI,
};
