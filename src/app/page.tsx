import Link from "next/link";
import { redirect } from "next/navigation";
import { getSessionUser } from "@/lib/auth";

export default async function HomePage() {
  const user = await getSessionUser();
  if (user) {
    redirect(user.role === "ADMIN" ? "/admin" : "/dashboard");
  }

  return (
    <main className="page">
      <div className="container" style={{ maxWidth: 560 }}>
        <div className="card hero-card">
          <p className="badge">v1.0</p>
          <h1 className="brand" style={{ marginTop: 14 }}>
            건강케어
          </h1>
          <p className="subtitle">
            운동과 식단을 쉽고 크게, 깔끔하게 관리하세요.
          </p>
          <div className="hero-actions">
            <Link className="btn btn-primary btn-block" href="/login">
              로그인
            </Link>
            <Link className="btn btn-secondary btn-block" href="/signup">
              회원가입
            </Link>
          </div>
          <p className="hint">
            관리자 체험: 아이디 <strong>admin</strong> / 비밀번호{" "}
            <strong>admin1234</strong>
          </p>
        </div>
      </div>
    </main>
  );
}
