const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const REGISTRY_PATH = path.join(__dirname, "..", "data", "documents.json");

function ensureRegistryExists() {
  const registryDirectory = path.dirname(REGISTRY_PATH);

  if (!fs.existsSync(registryDirectory)) {
    fs.mkdirSync(registryDirectory, { recursive: true });
  }

  if (!fs.existsSync(REGISTRY_PATH)) {
    fs.writeFileSync(REGISTRY_PATH, "[]", "utf8");
  }
}

function readDocuments() {
  ensureRegistryExists();

  const contents = fs.readFileSync(REGISTRY_PATH, "utf8");

  try {
    const documents = JSON.parse(contents);

    if (!Array.isArray(documents)) {
      throw new Error("Document registry must contain an array.");
    }

    return documents;
  } catch (error) {
    throw new Error(`Failed to read document registry: ${error.message}`);
  }
}

function writeDocuments(documents) {
  ensureRegistryExists();

  fs.writeFileSync(REGISTRY_PATH, JSON.stringify(documents, null, 2), "utf8");
}

function addDocument(document) {
  const documents = readDocuments();

  const record = {
    id: crypto.randomUUID(),
    originalName: document.originalName,
    storedName: document.storedName,
    size: document.size,
    type: document.type,
    uploadedAt: new Date().toISOString(),
  };

  documents.push(record);
  writeDocuments(documents);

  return record;
}

function getDocuments() {
  return readDocuments();
}

module.exports = {
  addDocument,
  getDocuments,
};
