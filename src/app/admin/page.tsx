"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { LogoutButton } from "@/components/LogoutButton";

type Member = {
  id: number;
  username: string;
  name: string;
  age: number;
  gender: string;
  disease: string;
  created_at: string;
};

type Workout = {
  id: number;
  date: string;
  exercise: string;
  duration_min: number | null;
  notes: string;
};

type Diet = {
  id: number;
  date: string;
  meal_type: string;
  food: string;
  calories: number | null;
  notes: string;
};

export default function AdminPage() {
  const router = useRouter();
  const [members, setMembers] = useState<Member[]>([]);
  const [selected, setSelected] = useState<Member | null>(null);
  const [workouts, setWorkouts] = useState<Workout[]>([]);
  const [diets, setDiets] = useState<Diet[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const loadMembers = useCallback(async () => {
    const meRes = await fetch("/api/auth/me");
    if (!meRes.ok) {
      router.push("/login");
      return;
    }
    const meData = await meRes.json();
    if (meData.user.role !== "ADMIN") {
      router.push("/dashboard");
      return;
    }

    const res = await fetch("/api/admin/members");
    const data = await res.json();
    if (!res.ok) {
      setError(data.error || "회원 목록을 불러오지 못했습니다.");
      setLoading(false);
      return;
    }
    setMembers(data.members || []);
    setLoading(false);
  }, [router]);

  useEffect(() => {
    loadMembers().catch(() => {
      setError("관리자 데이터를 불러오지 못했습니다.");
      setLoading(false);
    });
  }, [loadMembers]);

  async function openMember(id: number) {
    setError("");
    const res = await fetch(`/api/admin/members?id=${id}`);
    const data = await res.json();
    if (!res.ok) {
      setError(data.error || "회원 정보를 불러오지 못했습니다.");
      return;
    }
    setSelected(data.member);
    setWorkouts(data.workouts || []);
    setDiets(data.diets || []);
  }

  async function deleteMember(id: number, name: string) {
    if (!confirm(`정말 "${name}" 회원을 삭제할까요? 운동·식단 기록도 함께 삭제됩니다.`)) {
      return;
    }
    const res = await fetch(`/api/admin/members?id=${id}`, { method: "DELETE" });
    const data = await res.json();
    if (!res.ok) {
      setError(data.error || "삭제에 실패했습니다.");
      return;
    }
    if (selected?.id === id) {
      setSelected(null);
      setWorkouts([]);
      setDiets([]);
    }
    await loadMembers();
  }

  if (loading) {
    return (
      <main className="page">
        <div className="container">
          <div className="card">불러오는 중...</div>
        </div>
      </main>
    );
  }

  return (
    <main className="page">
      <div className="container">
        <div className="topbar">
          <div>
            <h1 className="brand">관리자 모드</h1>
            <p className="subtitle">모든 회원의 정보·운동·식단을 확인합니다.</p>
          </div>
          <div className="topbar-actions">
            <LogoutButton />
          </div>
        </div>

        <div className="stack">
          {error ? <div className="error-box">{error}</div> : null}

          <div className="card">
            <h2 className="section-title">회원 목록 ({members.length})</h2>
            {members.length === 0 ? (
              <div className="empty">가입된 회원이 없습니다.</div>
            ) : (
              <div className="member-grid">
                {members.map((m) => (
                  <div className="member-card" key={m.id}>
                    <div>
                      <strong style={{ fontSize: "1.1rem" }}>
                        {m.name} ({m.username})
                      </strong>
                      <div className="meta">
                        {m.age}세 · {m.gender} · {m.disease}
                      </div>
                      <div className="meta">가입일 {m.created_at}</div>
                    </div>
                    <div className="member-actions">
                      <button
                        type="button"
                        className="btn btn-primary"
                        onClick={() => openMember(m.id)}
                      >
                        상세 보기
                      </button>
                      <button
                        type="button"
                        className="btn btn-danger"
                        onClick={() => deleteMember(m.id, m.name)}
                      >
                        삭제
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {selected ? (
            <div className="card">
              <h2 className="section-title">
                {selected.name}님 상세 정보
              </h2>
              <div className="list-item" style={{ marginBottom: 16 }}>
                <strong>
                  {selected.name} / {selected.username}
                </strong>
                <div className="meta">
                  {selected.age}세 · {selected.gender} · {selected.disease}
                </div>
              </div>

              <h3 className="section-title">운동 기록</h3>
              {workouts.length === 0 ? (
                <div className="empty" style={{ marginBottom: 18 }}>
                  운동 기록이 없습니다.
                </div>
              ) : (
                <div className="list" style={{ marginBottom: 18 }}>
                  {workouts.map((w) => (
                    <div className="list-item" key={w.id}>
                      <strong>
                        {w.date} · {w.exercise}
                      </strong>
                      <div className="meta">
                        {w.duration_min != null ? `${w.duration_min}분` : "시간 미입력"}
                        {w.notes ? ` · ${w.notes}` : ""}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <h3 className="section-title">식단 기록</h3>
              {diets.length === 0 ? (
                <div className="empty">식단 기록이 없습니다.</div>
              ) : (
                <div className="list">
                  {diets.map((d) => (
                    <div className="list-item" key={d.id}>
                      <strong>
                        {d.date} · {d.meal_type} · {d.food}
                      </strong>
                      <div className="meta">
                        {d.calories != null ? `${d.calories} kcal` : "칼로리 미입력"}
                        {d.notes ? ` · ${d.notes}` : ""}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : null}
        </div>
      </div>
    </main>
  );
}
