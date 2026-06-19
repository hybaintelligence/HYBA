import { readDb, writeDb, hashPassword, User, QuantumProduct, CalibrationLog } from "./db";

export async function seed() {
  console.log("Initializing Quantum Database Seeder...");

  const data = await readDb();

  // 1. Seed Accounts (Idempotent: replace or check exists)
  const defaultUsers: User[] = [
    {
      id: "u1",
      username: "admin",
      passwordHash: await hashPassword("admin123"),
      role: "admin",
      createdAt: new Date().toISOString(),
    },
    {
      id: "u2",
      username: "operator",
      passwordHash: await hashPassword("operator123"),
      role: "operator",
      createdAt: new Date().toISOString(),
    },
  ];

  defaultUsers.forEach((u) => {
    const exists = data.users.find((existing) => existing.username === u.username);
    if (!exists) {
      data.users.push(u);
      console.log(`Seeded user: ${u.username}`);
    } else {
      console.log(`User already exists: ${u.username}`);
    }
  });

  // 2. Seed Quantum Products
  const defaultProducts: QuantumProduct[] = [
    {
      id: "prod-pulvini-evidence-console",
      name: "PULVINI Evidence Console",
      description:
        "Operator-facing catalog record for deterministic certificate review, runtime evidence packets, and no-claim production handover controls.",
      category: "Operator Evidence",
      difficultyScale: 8.4,
      qubitDimension: 512,
    },
    {
      id: "prod-stratum-v1-command-room",
      name: "Stratum v1 Command-Room Adapter",
      description:
        "ViaBTC-ready Stratum v1 profile, handshake, job-flow, and share-acceptance evidence surface for controlled mining cutover.",
      category: "Mining Operations",
      difficultyScale: 7.8,
      qubitDimension: 256,
    },
    {
      id: "prod-phi-memory-folding",
      name: "Phi Memory Folding Workbench",
      description:
        "PULVINI memory-folding workbench for retained-kernel replay, deterministic reconstruction checks, and bounded compression evidence.",
      category: "Mathematical Runtime",
      difficultyScale: 9.1,
      qubitDimension: 1024,
    },
  ];

  defaultProducts.forEach((p) => {
    const idx = data.products.findIndex((existing) => existing.id === p.id);
    if (idx === -1) {
      data.products.push(p);
      console.log(`Seeded product: ${p.name}`);
    } else {
      data.products[idx] = p; // update/overwrite is idempotent
      console.log(`Updated product: ${p.name}`);
    }
  });

  // 3. Seed Calibration Logs
  const defaultLogs: CalibrationLog[] = [
    {
      id: "cal-1",
      userId: "u1",
      username: "admin",
      targetIndex: 42,
      resonanceRadius: 0.618,
      expectedImprovement: 74.2,
      timestamp: new Date(Date.now() - 3600000 * 2).toISOString(),
    },
    {
      id: "cal-2",
      userId: "u2",
      username: "operator",
      targetIndex: 17,
      resonanceRadius: 0.124,
      expectedImprovement: 12.8,
      timestamp: new Date(Date.now() - 3600000 * 1).toISOString(),
    },
  ];

  defaultLogs.forEach((l) => {
    const idx = data.calibrationLogs.findIndex((existing) => existing.id === l.id);
    if (idx === -1) {
      data.calibrationLogs.push(l);
      console.log(`Seeded calibration log: ${l.id}`);
    } else {
      data.calibrationLogs[idx] = l;
      console.log(`Updated calibration log: ${l.id}`);
    }
  });

  await writeDb(data);
  console.log("Database Seeding Completed Successfully.");
}

// Run if called directly
if (process.env.NODE_ENV !== "test") {
  seed().catch((err) => {
    console.error("Seeding failed:", err);
    process.exit(1);
  });
}
