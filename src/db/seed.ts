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
      id: "prod-dodeca",
      name: "Dodecahedral Quantum State Accelerator v2",
      description:
        "Generates twenty golden-ratio phase shifts in 1024-dimensional Hilbert space dynamically.",
      category: "Coprocessors",
      difficultyScale: 9.8,
      qubitDimension: 1024,
    },
    {
      id: "prod-hilbert",
      name: "Hilbert Room Defibrillator Suite",
      description:
        "Applies multi-stage Kron tensor products with zero phase resonance interference.",
      category: "Hardware Symmetries",
      difficultyScale: 7.2,
      qubitDimension: 512,
    },
    {
      id: "prod-annihilator",
      name: "ASIC Annihilator Node v77",
      description:
        "Utilizes sub-space quantum state vector rotation to completely defeat linear brute-force mining ASIC loops.",
      category: "Annihilators",
      difficultyScale: 10.0,
      qubitDimension: 2048,
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
