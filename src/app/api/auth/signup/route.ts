import { NextRequest, NextResponse } from "next/server";
import bcrypt from "bcryptjs";
import { getDb, toPublicUser, type UserRow } from "@/lib/db";
import { createSessionToken, jsonError, setSessionCookie } from "@/lib/auth";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const name = String(body.name || "").trim();
    const age = Number(body.age);
    const gender = String(body.gender || "").trim();
    const disease = String(body.disease || "").trim();
    const username = String(body.username || "").trim();
    const password = String(body.password || "");
    const passwordConfirm = String(body.passwordConfirm || "");

    if (!name || !gender || !disease || !username || !password) {
      return jsonError("모든 항목을 입력해 주세요.");
    }
    if (!Number.isFinite(age) || age < 1 || age > 120) {
      return jsonError("나이를 올바르게 입력해 주세요.");
    }
    if (username.length < 3) {
      return jsonError("아이디는 3자 이상이어야 합니다.");
    }
    if (password.length < 4) {
      return jsonError("비밀번호는 4자 이상이어야 합니다.");
    }
    if (password !== passwordConfirm) {
      return jsonError("비밀번호가 일치하지 않습니다.");
    }

    const db = getDb();
    const existing = db
      .prepare("SELECT id FROM users WHERE username = ? COLLATE NOCASE")
      .get(username);

    if (existing) {
      return jsonError("이미 사용 중인 아이디입니다.", 409);
    }

    const passwordHash = bcrypt.hashSync(password, 10);
    const result = db
      .prepare(
        `INSERT INTO users (username, password_hash, name, age, gender, disease, role)
         VALUES (?, ?, ?, ?, ?, ?, 'USER')`
      )
      .run(username, passwordHash, name, age, gender, disease);

    const user = db
      .prepare("SELECT * FROM users WHERE id = ?")
      .get(Number(result.lastInsertRowid)) as UserRow;

    const token = await createSessionToken({ userId: user.id, role: user.role });
    await setSessionCookie(token);

    return NextResponse.json({ user: toPublicUser(user) }, { status: 201 });
  } catch {
    return jsonError("회원가입 중 오류가 발생했습니다.", 500);
  }
}
