"use client";

import Link from "next/link";
import { FormEvent, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

export default function SignupPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    name: "",
    age: "",
    gender: "",
    disease: "",
    username: "",
    password: "",
    passwordConfirm: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const passwordMismatch = useMemo(() => {
    return (
      form.passwordConfirm.length > 0 && form.password !== form.passwordConfirm
    );
  }, [form.password, form.passwordConfirm]);

  function update<K extends keyof typeof form>(key: K, value: string) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");

    if (form.password !== form.passwordConfirm) {
      setError("비밀번호가 일치하지 않습니다.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch("/api/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: form.name,
          age: Number(form.age),
          gender: form.gender,
          disease: form.disease,
          username: form.username,
          password: form.password,
          passwordConfirm: form.passwordConfirm,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || "회원가입에 실패했습니다.");
        return;
      }
      router.push("/dashboard");
      router.refresh();
    } catch {
      setError("네트워크 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page">
      <div className="container" style={{ maxWidth: 640 }}>
        <div className="card">
          <h1 className="heading">회원가입</h1>
          <form className="form-grid" onSubmit={handleSubmit}>
            <div className="form-row">
              <label htmlFor="name">이름</label>
              <input
                id="name"
                value={form.name}
                onChange={(e) => update("name", e.target.value)}
                required
              />
            </div>

            <div className="form-row two">
              <div className="form-row">
                <label htmlFor="age">나이</label>
                <input
                  id="age"
                  type="number"
                  min={1}
                  max={120}
                  value={form.age}
                  onChange={(e) => update("age", e.target.value)}
                  required
                />
              </div>
              <div className="form-row">
                <label htmlFor="gender">성별</label>
                <select
                  id="gender"
                  value={form.gender}
                  onChange={(e) => update("gender", e.target.value)}
                  required
                >
                  <option value="">선택</option>
                  <option value="남성">남성</option>
                  <option value="여성">여성</option>
                  <option value="기타">기타</option>
                </select>
              </div>
            </div>

            <div className="form-row">
              <label htmlFor="disease">암종 또는 질환명</label>
              <input
                id="disease"
                value={form.disease}
                onChange={(e) => update("disease", e.target.value)}
                placeholder="예: 유방암, 당뇨 등"
                required
              />
            </div>

            <div className="form-row">
              <label htmlFor="username">아이디</label>
              <input
                id="username"
                value={form.username}
                onChange={(e) => update("username", e.target.value)}
                autoComplete="username"
                required
              />
            </div>

            <div className="form-row">
              <label htmlFor="password">비밀번호</label>
              <input
                id="password"
                type="password"
                value={form.password}
                onChange={(e) => update("password", e.target.value)}
                autoComplete="new-password"
                required
              />
            </div>

            <div className="form-row">
              <label htmlFor="passwordConfirm">비밀번호 확인</label>
              <input
                id="passwordConfirm"
                type="password"
                value={form.passwordConfirm}
                onChange={(e) => update("passwordConfirm", e.target.value)}
                autoComplete="new-password"
                required
              />
            </div>

            {passwordMismatch ? (
              <div className="error-box">비밀번호가 일치하지 않습니다.</div>
            ) : null}
            {error ? <div className="error-box">{error}</div> : null}

            <button
              className="btn btn-primary btn-block"
              type="submit"
              disabled={loading || passwordMismatch}
            >
              {loading ? "가입 중..." : "회원가입"}
            </button>
          </form>
          <p className="hint">
            이미 계정이 있나요? <Link href="/login">로그인</Link>
          </p>
        </div>
      </div>
    </main>
  );
}
