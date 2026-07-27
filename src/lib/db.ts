import Database from "better-sqlite3";
import fs from "fs";
import path from "path";
import bcrypt from "bcryptjs";

const dataDir = path.join(process.cwd(), "data");
const dbPath = path.join(dataDir, "app.db");

if (!fs.existsSync(dataDir)) {
  fs.mkdirSync(dataDir, { recursive: true });
}

const globalForDb = globalThis as unknown as { __fitnessDb?: Database.Database };

function createDb() {
  const db = new Database(dbPath);
  db.pragma("journal_mode = WAL");
  db.pragma("foreign_keys = ON");

  db.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT NOT NULL UNIQUE COLLATE NOCASE,
      password_hash TEXT NOT NULL,
      name TEXT NOT NULL,
      age INTEGER NOT NULL,
      gender TEXT NOT NULL,
      disease TEXT NOT NULL,
      role TEXT NOT NULL DEFAULT 'USER' CHECK(role IN ('USER', 'ADMIN')),
      created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
    );

    CREATE TABLE IF NOT EXISTS workouts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      date TEXT NOT NULL,
      exercise TEXT NOT NULL,
      duration_min INTEGER,
      notes TEXT DEFAULT '',
      created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS diets (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      date TEXT NOT NULL,
      meal_type TEXT NOT NULL,
      food TEXT NOT NULL,
      calories INTEGER,
      notes TEXT DEFAULT '',
      created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
  `);

  const admin = db
    .prepare("SELECT id FROM users WHERE username = ?")
    .get("admin") as { id: number } | undefined;

  if (!admin) {
    const passwordHash = bcrypt.hashSync("admin1234", 10);
    db.prepare(
      `INSERT INTO users (username, password_hash, name, age, gender, disease, role)
       VALUES (?, ?, ?, ?, ?, ?, ?)`
    ).run("admin", passwordHash, "관리자", 30, "기타", "관리자", "ADMIN");
  }

  return db;
}

export function getDb() {
  if (!globalForDb.__fitnessDb) {
    globalForDb.__fitnessDb = createDb();
  }
  return globalForDb.__fitnessDb;
}

export type UserRow = {
  id: number;
  username: string;
  password_hash: string;
  name: string;
  age: number;
  gender: string;
  disease: string;
  role: "USER" | "ADMIN";
  created_at: string;
};

export type PublicUser = Omit<UserRow, "password_hash">;

export type WorkoutRow = {
  id: number;
  user_id: number;
  date: string;
  exercise: string;
  duration_min: number | null;
  notes: string;
  created_at: string;
};

export type DietRow = {
  id: number;
  user_id: number;
  date: string;
  meal_type: string;
  food: string;
  calories: number | null;
  notes: string;
  created_at: string;
};

export function toPublicUser(user: UserRow): PublicUser {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { password_hash, ...rest } = user;
  return rest;
}
