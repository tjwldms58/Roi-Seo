import { NextRequest, NextResponse } from "next/server";
import { getSessionUser, jsonError } from "@/lib/auth";
import { getDb, type WorkoutRow } from "@/lib/db";

export async function GET() {
  const user = await getSessionUser();
  if (!user) return jsonError("로그인이 필요합니다.", 401);

  const db = getDb();
  const rows = db
    .prepare(
      `SELECT * FROM workouts WHERE user_id = ? ORDER BY date DESC, id DESC`
    )
    .all(user.id) as WorkoutRow[];

  return NextResponse.json({ workouts: rows });
}

export async function POST(req: NextRequest) {
  const user = await getSessionUser();
  if (!user) return jsonError("로그인이 필요합니다.", 401);
  if (user.role === "ADMIN") {
    return jsonError("관리자 계정에서는 운동 기록을 추가할 수 없습니다.", 403);
  }

  try {
    const body = await req.json();
    const date = String(body.date || "").trim();
    const exercise = String(body.exercise || "").trim();
    const durationMin =
      body.durationMin === "" || body.durationMin == null
        ? null
        : Number(body.durationMin);
    const notes = String(body.notes || "").trim();

    if (!date || !exercise) {
      return jsonError("날짜와 운동 내용을 입력해 주세요.");
    }
    if (durationMin != null && (!Number.isFinite(durationMin) || durationMin < 0)) {
      return jsonError("운동 시간을 올바르게 입력해 주세요.");
    }

    const db = getDb();
    const result = db
      .prepare(
        `INSERT INTO workouts (user_id, date, exercise, duration_min, notes)
         VALUES (?, ?, ?, ?, ?)`
      )
      .run(user.id, date, exercise, durationMin, notes);

    const workout = db
      .prepare("SELECT * FROM workouts WHERE id = ?")
      .get(Number(result.lastInsertRowid)) as WorkoutRow;

    return NextResponse.json({ workout }, { status: 201 });
  } catch {
    return jsonError("운동 기록 저장 중 오류가 발생했습니다.", 500);
  }
}

export async function DELETE(req: NextRequest) {
  const user = await getSessionUser();
  if (!user) return jsonError("로그인이 필요합니다.", 401);

  const id = Number(req.nextUrl.searchParams.get("id"));
  if (!Number.isFinite(id)) return jsonError("잘못된 요청입니다.");

  const db = getDb();
  const row = db
    .prepare("SELECT * FROM workouts WHERE id = ?")
    .get(id) as WorkoutRow | undefined;

  if (!row) return jsonError("기록을 찾을 수 없습니다.", 404);
  if (row.user_id !== user.id && user.role !== "ADMIN") {
    return jsonError("권한이 없습니다.", 403);
  }

  db.prepare("DELETE FROM workouts WHERE id = ?").run(id);
  return NextResponse.json({ ok: true });
}
