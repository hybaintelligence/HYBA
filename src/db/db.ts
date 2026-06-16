import {
  collection,
  doc,
  getDoc,
  getDocs,
  setDoc,
  query,
  where,
  addDoc,
  serverTimestamp,
} from "firebase/firestore";
import { db } from "../lib/firebase";
import bcrypt from "bcryptjs";
import crypto from "crypto";

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
  userId: string;
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

export async function readDb(): Promise<DatabaseSchema> {
  try {
    const usersSnap = await getDocs(collection(db, "users"));
    const productsSnap = await getDocs(collection(db, "products"));
    const logsSnap = await getDocs(collection(db, "calibrationLogs"));

    return {
      users: usersSnap.docs.map((d) => ({ id: d.id, ...d.data() }) as User),
      products: productsSnap.docs.map((d) => ({ id: d.id, ...d.data() }) as QuantumProduct),
      calibrationLogs: logsSnap.docs.map((d) => ({ id: d.id, ...d.data() }) as CalibrationLog),
    };
  } catch (err) {
    console.error("Failed to read from Firestore:", err);
    return { users: [], products: [], calibrationLogs: [] };
  }
}

export async function writeDb(data: DatabaseSchema): Promise<void> {
  // Note: Standard writeDb is used for seeding in this app.
  // We'll implement it by batch updating or just sequential sets since it's used sparingly.
  for (const user of data.users) {
    await setDoc(doc(db, "users", user.id), user);
  }
  for (const product of data.products) {
    await setDoc(doc(db, "products", product.id), product);
  }
  for (const log of data.calibrationLogs) {
    await setDoc(doc(db, "calibrationLogs", log.id), log);
  }
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
