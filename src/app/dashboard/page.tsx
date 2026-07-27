"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { LogoutButton } from "@/components/LogoutButton";

type User = {
  id: number;
  name: string;
  username: string;
  role: "USER" | "ADMIN";
  disease: string;
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

function today() {
  return new Date().toISOString().slice(0, 10);
}

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [tab, setTab] = useState<"workout" | "diet">("workout");
  const [workouts, setWorkouts] = useState<Workout[]>([]);
  const [diets, setDiets] = useState<Diet[]>([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);

  const [workoutForm, setWorkoutForm] = useState({
    date: today(),
    exercise: "",
    durationMin: "",
    notes: "",
  });
  const [dietForm, setDietForm] = useState({
    date: today(),
    mealType: "아침",
    food: "",
    calories: "",
    notes: "",
  });

  const loadData = useCallback(async () => {
    setError("");
    const meRes = await fetch("/api/auth/me");
    if (!meRes.ok) {
      router.push("/login");
      return;
    }
    const meData = await meRes.json();
    if (meData.user.role === "ADMIN") {
      router.push("/admin");
      return;
    }
    setUser(meData.user);

    const [wRes, dRes] = await Promise.all([
      fetch("/api/workouts"),
      fetch("/api/diets"),
    ]);
    const wData = await wRes.json();
    const dData = await dRes.json();
    setWorkouts(wData.workouts || []);
    setDiets(dData.diets || []);
    setLoading(false);
  }, [router]);

  useEffect(() => {
    loadData().catch(() => {
      setError("데이터를 불러오지 못했습니다.");
      setLoading(false);
    });
  }, [loadData]);

  async function submitWorkout(e: FormEvent) {
    e.preventDefault();
    setError("");
    setMessage("");
    const res = await fetch("/api/workouts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(workoutForm),
    });
    const data = await res.json();
    if (!res.ok) {
      setError(data.error || "저장 실패");
      return;
    }
    setMessage("운동 기록이 저장되었습니다.");
    setWorkoutForm((prev) => ({ ...prev, exercise: "", durationMin: "", notes: "" }));
    await loadData();
  }

  async function submitDiet(e: FormEvent) {
    e.preventDefault();
    setError("");
    setMessage("");
    const res = await fetch("/api/diets", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dietForm),
    });
    const data = await res.json();
    if (!res.ok) {
      setError(data.error || "저장 실패");
      return;
    }
    setMessage("식단 기록이 저장되었습니다.");
    setDietForm((prev) => ({ ...prev, food: "", calories: "", notes: "" }));
    await loadData();
  }

  async function removeWorkout(id: number) {
    await fetch(`/api/workouts?id=${id}`, { method: "DELETE" });
    await loadData();
  }

  async function removeDiet(id: number) {
    await fetch(`/api/diets?id=${id}`, { method: "DELETE" });
    await loadData();
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
            <h1 className="brand">건강케어</h1>
            <p className="subtitle">
              {user?.name}님 · {user?.disease}
            </p>
          </div>
          <div className="topbar-actions">
            <LogoutButton />
          </div>
        </div>

        <div className="stack">
          <div className="card">
            <div className="tabs">
              <button
                type="button"
                className={`tab ${tab === "workout" ? "active" : ""}`}
                onClick={() => setTab("workout")}
              >
                운동 기록
              </button>
              <button
                type="button"
                className={`tab ${tab === "diet" ? "active" : ""}`}
                onClick={() => setTab("diet")}
              >
                식단 기록
              </button>
            </div>

            {error ? <div className="error-box" style={{ marginBottom: 14 }}>{error}</div> : null}
            {message ? (
              <div className="success-box" style={{ marginBottom: 14 }}>
                {message}
              </div>
            ) : null}

            {tab === "workout" ? (
              <form className="form-grid" onSubmit={submitWorkout}>
                <div className="form-row two">
                  <div className="form-row">
                    <label htmlFor="w-date">날짜</label>
                    <input
                      id="w-date"
                      type="date"
                      value={workoutForm.date}
                      onChange={(e) =>
                        setWorkoutForm((p) => ({ ...p, date: e.target.value }))
                      }
                      required
                    />
                  </div>
                  <div className="form-row">
                    <label htmlFor="w-duration">운동 시간(분)</label>
                    <input
                      id="w-duration"
                      type="number"
                      min={0}
                      value={workoutForm.durationMin}
                      onChange={(e) =>
                        setWorkoutForm((p) => ({
                          ...p,
                          durationMin: e.target.value,
                        }))
                      }
                    />
                  </div>
                </div>
                <div className="form-row">
                  <label htmlFor="w-exercise">운동 내용</label>
                  <input
                    id="w-exercise"
                    value={workoutForm.exercise}
                    onChange={(e) =>
                      setWorkoutForm((p) => ({ ...p, exercise: e.target.value }))
                    }
                    placeholder="예: 산책, 스트레칭"
                    required
                  />
                </div>
                <div className="form-row">
                  <label htmlFor="w-notes">메모</label>
                  <textarea
                    id="w-notes"
                    value={workoutForm.notes}
                    onChange={(e) =>
                      setWorkoutForm((p) => ({ ...p, notes: e.target.value }))
                    }
                  />
                </div>
                <button className="btn btn-primary" type="submit">
                  운동 저장
                </button>
              </form>
            ) : (
              <form className="form-grid" onSubmit={submitDiet}>
                <div className="form-row two">
                  <div className="form-row">
                    <label htmlFor="d-date">날짜</label>
                    <input
                      id="d-date"
                      type="date"
                      value={dietForm.date}
                      onChange={(e) =>
                        setDietForm((p) => ({ ...p, date: e.target.value }))
                      }
                      required
                    />
                  </div>
                  <div className="form-row">
                    <label htmlFor="d-meal">끼니</label>
                    <select
                      id="d-meal"
                      value={dietForm.mealType}
                      onChange={(e) =>
                        setDietForm((p) => ({ ...p, mealType: e.target.value }))
                      }
                    >
                      <option value="아침">아침</option>
                      <option value="점심">점심</option>
                      <option value="저녁">저녁</option>
                      <option value="간식">간식</option>
                    </select>
                  </div>
                </div>
                <div className="form-row two">
                  <div className="form-row">
                    <label htmlFor="d-food">음식</label>
                    <input
                      id="d-food"
                      value={dietForm.food}
                      onChange={(e) =>
                        setDietForm((p) => ({ ...p, food: e.target.value }))
                      }
                      required
                    />
                  </div>
                  <div className="form-row">
                    <label htmlFor="d-cal">칼로리(kcal)</label>
                    <input
                      id="d-cal"
                      type="number"
                      min={0}
                      value={dietForm.calories}
                      onChange={(e) =>
                        setDietForm((p) => ({ ...p, calories: e.target.value }))
                      }
                    />
                  </div>
                </div>
                <div className="form-row">
                  <label htmlFor="d-notes">메모</label>
                  <textarea
                    id="d-notes"
                    value={dietForm.notes}
                    onChange={(e) =>
                      setDietForm((p) => ({ ...p, notes: e.target.value }))
                    }
                  />
                </div>
                <button className="btn btn-primary" type="submit">
                  식단 저장
                </button>
              </form>
            )}
          </div>

          <div className="card">
            <h2 className="section-title">
              {tab === "workout" ? "내 운동 기록" : "내 식단 기록"}
            </h2>
            {tab === "workout" ? (
              workouts.length === 0 ? (
                <div className="empty">아직 운동 기록이 없습니다.</div>
              ) : (
                <div className="list">
                  {workouts.map((w) => (
                    <div className="list-item" key={w.id}>
                      <strong>
                        {w.date} · {w.exercise}
                      </strong>
                      <div className="meta">
                        {w.duration_min != null ? `${w.duration_min}분` : "시간 미입력"}
                        {w.notes ? ` · ${w.notes}` : ""}
                      </div>
                      <div>
                        <button
                          type="button"
                          className="btn btn-danger"
                          onClick={() => removeWorkout(w.id)}
                        >
                          삭제
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )
            ) : diets.length === 0 ? (
              <div className="empty">아직 식단 기록이 없습니다.</div>
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
                    <div>
                      <button
                        type="button"
                        className="btn btn-danger"
                        onClick={() => removeDiet(d.id)}
                      >
                        삭제
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
