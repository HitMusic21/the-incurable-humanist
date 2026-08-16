import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import Card from "@/components/Card";
import SEO from "@/components/SEO";
import { API_CONFIG } from "@/config/api";
import { setAdminToken } from "@/lib/adminAuth";

type LocationState = { from?: string };

export default function AdminLogin() {
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as LocationState | null)?.from || "/admin/stories";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await fetch(`${API_CONFIG.baseUrl}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const detail = await res
          .json()
          .then((d) => d?.detail || "Login failed")
          .catch(() => "Login failed");
        throw new Error(String(detail));
      }
      const data = await res.json();
      if (!data?.user?.is_author) {
        throw new Error("This account is not authorized for admin access.");
      }
      setAdminToken(data.access_token);
      navigate(from, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <SEO
        title="Admin — The Incurable Humanist"
        description="Admin sign-in."
        canonical="https://theincurablehumanist.com/admin/login"
        noindex
      />
      <section className="container mt-16 max-w-md pb-24">
        <Card className="p-8 md:p-10">
          <h1 className="font-serif text-accent2 text-[28px] mb-6">Admin sign-in</h1>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="admin-email" className="block text-[13px] text-muted-ink mb-1">
                Email
              </label>
              <input
                id="admin-email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full h-11 px-3 rounded-lg border border-line bg-white focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent/30"
              />
            </div>
            <div>
              <label htmlFor="admin-password" className="block text-[13px] text-muted-ink mb-1">
                Password
              </label>
              <input
                id="admin-password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full h-11 px-3 rounded-lg border border-line bg-white focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent/30"
              />
            </div>
            {error && (
              <div role="alert" className="text-[13px] text-accent">
                {error}
              </div>
            )}
            <button
              type="submit"
              disabled={loading}
              className="w-full h-11 rounded-pill bg-accent2 text-white font-medium shadow-soft hover:brightness-105 active:brightness-95 disabled:opacity-70 transition"
            >
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>
        </Card>
      </section>
    </>
  );
}
