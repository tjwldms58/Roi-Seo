import { NextResponse } from "next/server";
import { getSessionUser, jsonError } from "@/lib/auth";

export async function GET() {
  const user = await getSessionUser();
  if (!user) {
    return jsonError("로그인이 필요합니다.", 401);
  }
  return NextResponse.json({ user });
}
