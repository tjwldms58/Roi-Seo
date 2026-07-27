import { NextRequest, NextResponse } from "next/server";
import { requireAdmin, jsonError } from "@/lib/auth";
import { getDb, toPublicUser, type DietRow, type UserRow, type WorkoutRow } from "@/lib/db";

export async function GET(req: NextRequest) {
  const admin = await requireAdmin();
  if (!admin) return jsonError("관리자만 접근할 수 있습니다.", 403);

  const db = getDb();
  const memberId = req.nextUrl.searchParams.get("id");

  if (memberId) {
    const id = Number(memberId);
    const member = db
      .prepare("SELECT * FROM users WHERE id = ? AND role = 'USER'")
      .get(id) as UserRow | undefined;

    if (!member) return jsonError("회원을 찾을 수 없습니다.", 404);

    const workouts = db
      .prepare(
        `SELECT * FROM workouts WHERE user_id = ? ORDER BY date DESC, id DESC`
      )
      .all(id) as WorkoutRow[];

    const diets = db
      .prepare(`SELECT * FROM diets WHERE user_id = ? ORDER BY date DESC, id DESC`)
      .all(id) as DietRow[];

    return NextResponse.json({
      member: toPublicUser(member),
      workouts,
      diets,
    });
  }

  const members = (
    db
      .prepare(
        `SELECT * FROM users WHERE role = 'USER' ORDER BY created_at DESC, id DESC`
      )
      .all() as UserRow[]
  ).map(toPublicUser);

  return NextResponse.json({ members });
}

export async function DELETE(req: NextRequest) {
  const admin = await requireAdmin();
  if (!admin) return jsonError("관리자만 접근할 수 있습니다.", 403);

  const id = Number(req.nextUrl.searchParams.get("id"));
  if (!Number.isFinite(id)) return jsonError("잘못된 요청입니다.");

  const db = getDb();
  const member = db
    .prepare("SELECT * FROM users WHERE id = ? AND role = 'USER'")
    .get(id) as UserRow | undefined;

  if (!member) return jsonError("회원을 찾을 수 없습니다.", 404);

  db.prepare("DELETE FROM workouts WHERE user_id = ?").run(id);
  db.prepare("DELETE FROM diets WHERE user_id = ?").run(id);
  db.prepare("DELETE FROM users WHERE id = ?").run(id);

  return NextResponse.json({ ok: true });
}
