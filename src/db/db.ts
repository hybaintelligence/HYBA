import fs from "fs";
import path from "path";
import crypto from "crypto";

const DB_FILE = path.join(process.cwd(), "src", "db", "db.json");

// High-level absolute schemas
export interface User {
  id: string;
  username: string;
  passwordHash: string;
  role: string;
  createdAt: string;
}

export interface QuantumProduct {
  id: string;
  name: string;
  description: string;
  category: string;
  difficultyScale: number;
  qubitDimension: number;
}

export interface CalibrationLog {
  id: string;
  username: string;
  targetIndex: number;
  resonanceRadius: number;
  expectedImprovement: number;
  timestamp: string;
}

export interface DatabaseSchema {
  users: User[];
  products: QuantumProduct[];
  calibrationLogs: CalibrationLog[];
}

const DEFAULT_DB: DatabaseSchema = {
  users: [],
  products: [],
  calibrationLogs: []
};

// Helper ensuring file exists and is populated
function ensureDb() {
  const dir = path.dirname(DB_FILE);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  if (!fs.existsSync(DB_FILE)) {
    fs.writeFileSync(DB_FILE, JSON.stringify(DEFAULT_DB, null, 2), "utf-8");
  }
}

export function readDb(): DatabaseSchema {
  ensureDb();
  try {
    const content = fs.readFileSync(DB_FILE, "utf-8");
    return JSON.parse(content) as DatabaseSchema;
  } catch (err) {
    console.error("Failed to read JSON DB, resetting to default:", err);
    return DEFAULT_DB;
  }
}

export function writeDb(data: DatabaseSchema) {
  ensureDb();
  fs.writeFileSync(DB_FILE, JSON.stringify(data, null, 2), "utf-8");
}

// Password utility
export function hashPassword(password: string): string {
  return crypto.createHash("sha256").update(password + "salt-quantum-99").digest("hex");
}
