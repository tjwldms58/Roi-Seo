import { NextRequest, NextResponse } from "next/server";
import bcrypt from "bcryptjs";
import { getDb, toPublicUser, type UserRow } from "@/lib/db";
import { createSessionToken, jsonError, setSessionCookie } from "@/lib/auth";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const username = String(body.username || "").trim();
    const password = String(body.password || "");

    if (!username || !password) {
      return jsonError("아이디와 비밀번호를 입력해 주세요.");
    }

    const db = getDb();
    const user = db
      .prepare("SELECT * FROM users WHERE username = ? COLLATE NOCASE")
      .get(username) as UserRow | undefined;

    if (!user || !bcrypt.compareSync(password, user.password_hash)) {
      return jsonError("아이디 또는 비밀번호가 올바르지 않습니다.", 401);
    }

    const token = await createSessionToken({ userId: user.id, role: user.role });
    await setSessionCookie(token);

    return NextResponse.json({ user: toPublicUser(user) });
  } catch {
    return jsonError("로그인 중 오류가 발생했습니다.", 500);
  }
}
