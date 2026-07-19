import { useEffect, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { API_CONFIG } from "@/config/api";
import { authHeaders, clearAdminToken, getAdminToken } from "@/lib/adminAuth";

type Status = "checking" | "authed" | "unauthed";

/**
 * Guards /admin/* routes. Checks that the stored JWT still resolves to an
 * `is_author` user via GET /auth/me. On failure, clears the token and
 * redirects to /admin/login (preserving the intended destination).
 */
export default function RequireAuth({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<Status>("checking");
  const location = useLocation();

  useEffect(() => {
    const token = getAdminToken();
    if (!token) {
      setStatus("unauthed");
      return;
    }
    let alive = true;
    fetch(`${API_CONFIG.baseUrl}/auth/me`, { headers: authHeaders() })
      .then(async (r) => {
        if (!alive) return;
        if (!r.ok) {
          clearAdminToken();
          setStatus("unauthed");
          return;
        }
        const user = await r.json();
        if (!user?.is_author) {
          clearAdminToken();
          setStatus("unauthed");
          return;
        }
        setStatus("authed");
      })
      .catch(() => {
        if (!alive) return;
        clearAdminToken();
        setStatus("unauthed");
      });
    return () => {
      alive = false;
    };
  }, []);

  if (status === "checking") {
    return (
      <section className="container mt-16 max-w-md">
        <p className="text-center text-[15px] text-muted-ink">Checking access…</p>
      </section>
    );
  }
  if (status === "unauthed") {
    return <Navigate to="/admin/login" replace state={{ from: location.pathname }} />;
  }
  return <>{children}</>;
}
