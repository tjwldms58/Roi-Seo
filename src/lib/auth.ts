import { SignJWT, jwtVerify } from "jose";
import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";
import { getDb, toPublicUser, type PublicUser, type UserRow } from "./db";

const COOKIE_NAME = "fitness_session";
const SESSION_DAYS = 7;

function getSecret() {
  const secret = process.env.AUTH_SECRET || "fitness-diet-app-v1-dev-secret-change-me";
  return new TextEncoder().encode(secret);
}

export type SessionPayload = {
  userId: number;
  role: "USER" | "ADMIN";
};

export async function createSessionToken(payload: SessionPayload) {
  return new SignJWT(payload)
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setExpirationTime(`${SESSION_DAYS}d`)
    .sign(getSecret());
}

export async function verifySessionToken(token: string): Promise<SessionPayload | null> {
  try {
    const { payload } = await jwtVerify(token, getSecret());
    if (typeof payload.userId !== "number" || (payload.role !== "USER" && payload.role !== "ADMIN")) {
      return null;
    }
    return { userId: payload.userId, role: payload.role };
  } catch {
    return null;
  }
}

export async function setSessionCookie(token: string) {
  const cookieStore = await cookies();
  cookieStore.set(COOKIE_NAME, token, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: SESSION_DAYS * 24 * 60 * 60,
  });
}

export async function clearSessionCookie() {
  const cookieStore = await cookies();
  cookieStore.delete(COOKIE_NAME);
}

export async function getSessionUser(): Promise<PublicUser | null> {
  const cookieStore = await cookies();
  const token = cookieStore.get(COOKIE_NAME)?.value;
  if (!token) return null;

  const session = await verifySessionToken(token);
  if (!session) return null;

  const db = getDb();
  const user = db
    .prepare("SELECT * FROM users WHERE id = ?")
    .get(session.userId) as UserRow | undefined;

  if (!user) return null;
  return toPublicUser(user);
}

export async function requireUser(): Promise<PublicUser | null> {
  return getSessionUser();
}

export async function requireAdmin(): Promise<PublicUser | null> {
  const user = await getSessionUser();
  if (!user || user.role !== "ADMIN") return null;
  return user;
}

export function getTokenFromRequest(req: NextRequest) {
  return req.cookies.get(COOKIE_NAME)?.value;
}

export function jsonError(message: string, status = 400) {
  return NextResponse.json({ error: message }, { status });
}
