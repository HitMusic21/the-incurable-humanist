import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import LinkExt from "@tiptap/extension-link";
import ImageExt from "@tiptap/extension-image";
import Card from "@/components/Card";
import SEO from "@/components/SEO";
import { API_CONFIG, type StoryDetail } from "@/config/api";
import { authHeaders } from "@/lib/adminAuth";

type Save = { kind: "idle" } | { kind: "saving" } | { kind: "saved" } | { kind: "error"; msg: string };

const META_WARN = 160;
const META_MAX = 320;

export default function StoryEditor() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [story, setStory] = useState<StoryDetail | null>(null);
  const [title, setTitle] = useState("");
  const [slug, setSlug] = useState("");
  const [excerpt, setExcerpt] = useState("");
  const [metaDescription, setMetaDescription] = useState("");
  const [coverImageUrl, setCoverImageUrl] = useState("");
  const [canonicalUrl, setCanonicalUrl] = useState("");
  const [contentWarning, setContentWarning] = useState("");
  const [status, setStatus] = useState<"draft" | "published" | "archived">("draft");
  const [save, setSave] = useState<Save>({ kind: "idle" });
  const [loadError, setLoadError] = useState<string | null>(null);

  const editor = useEditor({
    extensions: [
      StarterKit,
      LinkExt.configure({ openOnClick: false, autolink: true, protocols: ["http", "https", "mailto"] }),
      ImageExt,
    ],
    content: "",
  });

  useEffect(() => {
    if (!id) return;
    let alive = true;
    fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.stories.adminById(id)}`, {
      headers: authHeaders(),
    })
      .then(async (r) => {
        if (!alive) return;
        if (r.status === 404) {
          setLoadError("Story not found.");
          return;
        }
        if (!r.ok) {
          setLoadError(`Failed to load story: ${r.status}`);
          return;
        }
        const s: StoryDetail = await r.json();
        setStory(s);
        setTitle(s.title);
        setSlug(s.slug);
        setExcerpt(s.excerpt || "");
        setMetaDescription(s.meta_description || "");
        setCoverImageUrl(s.cover_image_url || "");
        setCanonicalUrl(s.canonical_url || "");
        setContentWarning(s.content_warning || "");
        setStatus((s.status as "draft" | "published" | "archived") || "draft");
        editor?.commands.setContent(s.content || "");
      })
      .catch((e) => {
        if (!alive) return;
        setLoadError(e instanceof Error ? e.message : "Failed to load story");
      });
    return () => {
      alive = false;
    };
  }, [id, editor]);

  const doSave = useCallback(
    async (nextStatus?: "draft" | "published" | "archived") => {
      if (!id || !editor) return;
      setSave({ kind: "saving" });
      const payload = {
        title,
        slug,
        excerpt: excerpt || null,
        meta_description: metaDescription || null,
        cover_image_url: coverImageUrl || null,
        canonical_url: canonicalUrl || null,
        content_warning: contentWarning || null,
        content: editor.getHTML(),
        status: nextStatus ?? status,
      };
      const res = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.stories.list}/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const msg = await res.text().catch(() => `${res.status}`);
        setSave({ kind: "error", msg });
        return;
      }
      const data = await res.json();
      setStory(data);
      setSlug(data.slug);
      setStatus(data.status);
      setSave({ kind: "saved" });
      setTimeout(() => setSave({ kind: "idle" }), 2000);
    },
    [
      id,
      editor,
      title,
      slug,
      excerpt,
      metaDescription,
      coverImageUrl,
      canonicalUrl,
      contentWarning,
      status,
    ]
  );

  async function doDelete() {
    if (!id) return;
    if (!window.confirm("Delete this story permanently?")) return;
    const res = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.stories.list}/${id}`, {
      method: "DELETE",
      headers: authHeaders(),
    });
    if (res.ok) {
      navigate("/admin/stories", { replace: true });
    } else {
      alert(`Delete failed: ${res.status}`);
    }
  }

  if (loadError) {
    return (
      <section className="container mt-16 max-w-md pb-16">
        <Card className="p-8 text-center">
          <p className="text-[15px] text-accent">{loadError}</p>
          <Link
            to="/admin/stories"
            className="mt-4 inline-block text-[14px] underline text-accent2"
          >
            Back to stories
          </Link>
        </Card>
      </section>
    );
  }

  if (!story || !editor) {
    return (
      <section className="container mt-16 max-w-md">
        <p className="text-center text-[15px] text-muted-ink">Loading editor…</p>
      </section>
    );
  }

  const metaLen = metaDescription.length;
  const metaClass =
    metaLen > META_MAX
      ? "text-accent"
      : metaLen > META_WARN
      ? "text-yellow-700"
      : "text-muted-ink/80";

  return (
    <>
      <SEO
        title="Edit story — Admin"
        description="Edit story."
        canonical="https://theincurablehumanist.com/admin/stories"
        noindex
      />
      <section className="container mt-8 max-w-4xl pb-24">
        <header className="mb-6 flex items-center gap-4">
          <Link to="/admin/stories" className="text-[13px] text-muted-ink hover:text-accent">
            ← Stories
          </Link>
          <span className="text-[11px] uppercase tracking-widest text-muted-ink">
            {status}
          </span>
          <div className="ml-auto flex items-center gap-3 text-[13px]">
            {save.kind === "saving" && <span className="text-muted-ink">Saving…</span>}
            {save.kind === "saved" && <span className="text-accent">Saved</span>}
            {save.kind === "error" && (
              <span className="text-accent" title={save.msg}>Save failed</span>
            )}
            <button
              onClick={() => doSave()}
              className="px-4 h-9 rounded-pill border border-accent text-accent text-[13px] font-medium hover:bg-accent hover:text-white transition"
            >
              Save draft
            </button>
            {status !== "published" ? (
              <button
                onClick={() => doSave("published")}
                className="px-4 h-9 rounded-pill bg-accent2 text-white text-[13px] font-medium shadow-soft hover:brightness-105 transition"
              >
                Publish
              </button>
            ) : (
              <button
                onClick={() => doSave("draft")}
                className="px-4 h-9 rounded-pill border border-muted-ink text-muted-ink text-[13px] font-medium hover:border-accent hover:text-accent transition"
              >
                Unpublish
              </button>
            )}
          </div>
        </header>

        <Card className="p-6 md:p-8">
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Title"
            className="w-full font-serif text-[32px] md:text-[38px] text-ink leading-tight bg-transparent border-b border-line/60 focus:border-accent focus:outline-none pb-3 mb-6"
          />

          <div className="grid gap-4 md:grid-cols-2 mb-6">
            <label className="text-[13px] text-muted-ink">
              <span className="block mb-1">Slug</span>
              <input
                value={slug}
                onChange={(e) => setSlug(e.target.value)}
                className="w-full h-10 px-3 rounded-lg border border-line bg-white text-ink text-[14px] focus:outline-none focus:border-accent"
              />
            </label>
            <label className="text-[13px] text-muted-ink">
              <span className="block mb-1">Cover image URL</span>
              <input
                value={coverImageUrl}
                onChange={(e) => setCoverImageUrl(e.target.value)}
                placeholder="https://…"
                className="w-full h-10 px-3 rounded-lg border border-line bg-white text-ink text-[14px] focus:outline-none focus:border-accent"
              />
            </label>
            <label className="text-[13px] text-muted-ink md:col-span-2">
              <span className="block mb-1">Excerpt (list-view summary)</span>
              <textarea
                value={excerpt}
                onChange={(e) => setExcerpt(e.target.value)}
                rows={2}
                maxLength={500}
                className="w-full px-3 py-2 rounded-lg border border-line bg-white text-ink text-[14px] focus:outline-none focus:border-accent"
              />
            </label>
            <label className="text-[13px] text-muted-ink md:col-span-2">
              <span className="flex items-baseline justify-between mb-1">
                <span>Meta description (SERP snippet)</span>
                <span className={`text-[12px] ${metaClass}`}>
                  {metaLen}/{META_MAX}
                  {metaLen > META_WARN && metaLen <= META_MAX && " · past sweet spot (~160)"}
                </span>
              </span>
              <textarea
                value={metaDescription}
                onChange={(e) => setMetaDescription(e.target.value.slice(0, META_MAX))}
                rows={2}
                className="w-full px-3 py-2 rounded-lg border border-line bg-white text-ink text-[14px] focus:outline-none focus:border-accent"
              />
            </label>
            <label className="text-[13px] text-muted-ink">
              <span className="block mb-1">Canonical URL (leave blank if we own it)</span>
              <input
                value={canonicalUrl}
                onChange={(e) => setCanonicalUrl(e.target.value)}
                placeholder="https://…substack.com/…"
                className="w-full h-10 px-3 rounded-lg border border-line bg-white text-ink text-[14px] focus:outline-none focus:border-accent"
              />
            </label>
            <label className="text-[13px] text-muted-ink">
              <span className="block mb-1">Content warning (optional)</span>
              <input
                value={contentWarning}
                onChange={(e) => setContentWarning(e.target.value)}
                className="w-full h-10 px-3 rounded-lg border border-line bg-white text-ink text-[14px] focus:outline-none focus:border-accent"
              />
            </label>
          </div>

          <div className="border-t border-line/60 pt-6">
            <EditorToolbar editor={editor} />
            <div className="mt-3 rounded-lg border border-line bg-white p-4 min-h-[240px] prose prose-sm max-w-none focus-within:border-accent">
              <EditorContent editor={editor} />
            </div>
          </div>
        </Card>

        <div className="mt-8 text-right">
          <button
            onClick={doDelete}
            className="text-[13px] text-muted-ink underline hover:text-accent"
          >
            Delete story
          </button>
        </div>
      </section>
    </>
  );
}

function EditorToolbar({ editor }: { editor: ReturnType<typeof useEditor> }) {
  if (!editor) return null;
  const btn = (active: boolean) =>
    `px-2 h-7 text-[12px] rounded ${
      active ? "bg-accent text-white" : "text-muted-ink hover:bg-line/40"
    } transition`;
  return (
    <div className="flex flex-wrap gap-1">
      <button
        type="button"
        onClick={() => editor.chain().focus().toggleBold().run()}
        className={btn(editor.isActive("bold"))}
      >
        Bold
      </button>
      <button
        type="button"
        onClick={() => editor.chain().focus().toggleItalic().run()}
        className={btn(editor.isActive("italic"))}
      >
        Italic
      </button>
      <button
        type="button"
        onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
        className={btn(editor.isActive("heading", { level: 2 }))}
      >
        H2
      </button>
      <button
        type="button"
        onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
        className={btn(editor.isActive("heading", { level: 3 }))}
      >
        H3
      </button>
      <button
        type="button"
        onClick={() => editor.chain().focus().toggleBlockquote().run()}
        className={btn(editor.isActive("blockquote"))}
      >
        Quote
      </button>
      <button
        type="button"
        onClick={() => editor.chain().focus().toggleBulletList().run()}
        className={btn(editor.isActive("bulletList"))}
      >
        • List
      </button>
      <button
        type="button"
        onClick={() => {
          const url = window.prompt("URL");
          if (!url) return;
          editor.chain().focus().extendMarkRange("link").setLink({ href: url }).run();
        }}
        className={btn(editor.isActive("link"))}
      >
        Link
      </button>
      <button
        type="button"
        onClick={() => editor.chain().focus().unsetLink().run()}
        className={btn(false)}
      >
        Unlink
      </button>
      <button
        type="button"
        onClick={() => {
          const url = window.prompt("Image URL");
          if (url) editor.chain().focus().setImage({ src: url }).run();
        }}
        className={btn(false)}
      >
        Image
      </button>
      <button
        type="button"
        onClick={() => editor.chain().focus().undo().run()}
        className={btn(false)}
      >
        Undo
      </button>
    </div>
  );
}
