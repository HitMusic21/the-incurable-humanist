import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Card from "@/components/Card";
import SEO from "@/components/SEO";
import { API_CONFIG, type StoryPublic } from "@/config/api";
import { authHeaders, clearAdminToken } from "@/lib/adminAuth";

type State =
  | { kind: "loading" }
  | { kind: "ready"; stories: StoryPublic[] }
  | { kind: "error"; message: string };

export default function AdminStoriesIndex() {
  const [state, setState] = useState<State>({ kind: "loading" });
  const navigate = useNavigate();

  useEffect(() => {
    let alive = true;
    // Admin view lists ALL statuses (draft/published/archived).
    fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.stories.list}?status=all&limit=100`, {
      headers: authHeaders(),
    })
      .then(async (r) => {
        if (!r.ok) throw new Error(`GET /stories → ${r.status}`);
        return r.json();
      })
      .then((data) => {
        if (!alive) return;
        setState({ kind: "ready", stories: Array.isArray(data?.stories) ? data.stories : [] });
      })
      .catch((e) => {
        if (!alive) return;
        setState({ kind: "error", message: e instanceof Error ? e.message : "unknown" });
      });
    return () => {
      alive = false;
    };
  }, []);

  function signOut() {
    clearAdminToken();
    navigate("/admin/login", { replace: true });
  }

  async function createDraft() {
    const res = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.stories.list}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({
        title: "Untitled draft",
        content: "<p>Start writing…</p>",
        status: "draft",
      }),
    });
    if (!res.ok) {
      alert(`Create failed: ${res.status}`);
      return;
    }
    const story = await res.json();
    navigate(`/admin/stories/${story.id}/edit`);
  }

  return (
    <>
      <SEO
        title="Stories — Admin"
        description="Story management."
        canonical="https://theincurablehumanist.com/admin/stories"
        noindex
      />
      <section className="container mt-10 max-w-5xl pb-16">
        <header className="flex items-center justify-between mb-6">
          <h1 className="font-serif text-accent2 text-[28px]">Stories</h1>
          <div className="flex gap-3">
            <button
              onClick={createDraft}
              className="px-5 h-10 rounded-pill bg-accent2 text-white text-[14px] font-medium shadow-soft hover:brightness-105 transition"
            >
              New draft
            </button>
            <button
              onClick={signOut}
              className="px-5 h-10 rounded-pill border border-line text-muted-ink text-[14px] hover:border-accent hover:text-accent transition"
            >
              Sign out
            </button>
          </div>
        </header>

        {state.kind === "loading" && (
          <p className="text-[15px] text-muted-ink">Loading…</p>
        )}
        {state.kind === "error" && (
          <p className="text-[15px] text-accent">Error: {state.message}</p>
        )}
        {state.kind === "ready" && state.stories.length === 0 && (
          <Card className="p-8 text-center">
            <p className="text-[15px] text-muted-ink">No stories yet. Import from Substack or create a draft.</p>
          </Card>
        )}
        {state.kind === "ready" && state.stories.length > 0 && (
          <div className="space-y-3">
            {state.stories.map((s) => (
              <Card key={s.id} className="p-5 flex items-center justify-between">
                <div className="min-w-0 mr-4">
                  <div className="flex items-center gap-3 mb-1">
                    <span
                      className={`text-[10px] uppercase tracking-widest font-medium px-2 py-0.5 rounded ${
                        s.status === "published"
                          ? "bg-accent/10 text-accent"
                          : s.status === "draft"
                          ? "bg-line/40 text-muted-ink"
                          : "bg-line/20 text-muted-ink/70"
                      }`}
                    >
                      {s.status}
                    </span>
                    <span className="text-[12px] text-muted-ink truncate">{s.slug}</span>
                  </div>
                  <div className="font-serif text-[18px] text-ink truncate">{s.title}</div>
                </div>
                <Link
                  to={`/admin/stories/${s.id}/edit`}
                  className="shrink-0 px-4 h-9 inline-flex items-center rounded-pill border border-accent text-accent text-[13px] font-medium hover:bg-accent hover:text-white transition"
                >
                  Edit
                </Link>
              </Card>
            ))}
          </div>
        )}
      </section>
    </>
  );
}
