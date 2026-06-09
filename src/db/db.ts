import fs from "fs";
import path from "path";
import crypto from "crypto";
import bcrypt from "bcryptjs";

const DB_FILE = path.join(process.cwd(), "data", "db.json");

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

// Simple async mutex for atomic writes
let dbLock = Promise.resolve();

export async function readDb(): Promise<DatabaseSchema> {
  return new Promise((resolve) => {
    dbLock = dbLock.then(() => {
      ensureDb();
      try {
        const content = fs.readFileSync(DB_FILE, "utf-8");
        resolve(JSON.parse(content) as DatabaseSchema);
      } catch (err) {
        console.error("Failed to read JSON DB, resetting to default:", err);
        resolve(DEFAULT_DB);
      }
    });
  });
}

export async function writeDb(data: DatabaseSchema): Promise<void> {
  return new Promise((resolve) => {
    dbLock = dbLock.then(() => {
      ensureDb();
      fs.writeFileSync(DB_FILE, JSON.stringify(data, null, 2), "utf-8");
      resolve();
    });
  });
}

// Password utility
export async function hashPassword(password: string): Promise<string> {
  const salt = await bcrypt.genSalt(12);
  return bcrypt.hash(password, salt);
}

export async function verifyPassword(password: string, hash: string): Promise<boolean> {
  return bcrypt.compare(password, hash);
}

export function generateId(): string {
  return crypto.randomUUID();
}
