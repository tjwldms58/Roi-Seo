import { NextRequest, NextResponse } from "next/server";
import { getSessionUser, jsonError } from "@/lib/auth";
import { getDb, type DietRow } from "@/lib/db";

export async function GET() {
  const user = await getSessionUser();
  if (!user) return jsonError("로그인이 필요합니다.", 401);

  const db = getDb();
  const rows = db
    .prepare(`SELECT * FROM diets WHERE user_id = ? ORDER BY date DESC, id DESC`)
    .all(user.id) as DietRow[];

  return NextResponse.json({ diets: rows });
}

export async function POST(req: NextRequest) {
  const user = await getSessionUser();
  if (!user) return jsonError("로그인이 필요합니다.", 401);
  if (user.role === "ADMIN") {
    return jsonError("관리자 계정에서는 식단 기록을 추가할 수 없습니다.", 403);
  }

  try {
    const body = await req.json();
    const date = String(body.date || "").trim();
    const mealType = String(body.mealType || "").trim();
    const food = String(body.food || "").trim();
    const calories =
      body.calories === "" || body.calories == null ? null : Number(body.calories);
    const notes = String(body.notes || "").trim();

    if (!date || !mealType || !food) {
      return jsonError("날짜, 끼니, 음식명을 입력해 주세요.");
    }
    if (calories != null && (!Number.isFinite(calories) || calories < 0)) {
      return jsonError("칼로리를 올바르게 입력해 주세요.");
    }

    const db = getDb();
    const result = db
      .prepare(
        `INSERT INTO diets (user_id, date, meal_type, food, calories, notes)
         VALUES (?, ?, ?, ?, ?, ?)`
      )
      .run(user.id, date, mealType, food, calories, notes);

    const diet = db
      .prepare("SELECT * FROM diets WHERE id = ?")
      .get(Number(result.lastInsertRowid)) as DietRow;

    return NextResponse.json({ diet }, { status: 201 });
  } catch {
    return jsonError("식단 기록 저장 중 오류가 발생했습니다.", 500);
  }
}

export async function DELETE(req: NextRequest) {
  const user = await getSessionUser();
  if (!user) return jsonError("로그인이 필요합니다.", 401);

  const id = Number(req.nextUrl.searchParams.get("id"));
  if (!Number.isFinite(id)) return jsonError("잘못된 요청입니다.");

  const db = getDb();
  const row = db
    .prepare("SELECT * FROM diets WHERE id = ?")
    .get(id) as DietRow | undefined;

  if (!row) return jsonError("기록을 찾을 수 없습니다.", 404);
  if (row.user_id !== user.id && user.role !== "ADMIN") {
    return jsonError("권한이 없습니다.", 403);
  }

  db.prepare("DELETE FROM diets WHERE id = ?").run(id);
  return NextResponse.json({ ok: true });
}
