import React from "react";
import ReactDOM from "react-dom/client";
import { createBrowserRouter, Navigate, RouterProvider } from "react-router-dom";
import { PostHogProvider } from "posthog-js/react";
import "./styles/globals.css";
import App from "./shell/App";
import Home from "./pages/Home";
import About from "./pages/About";
import Archive from "./pages/Archive";
import Speak from "./pages/Speak";
import Listen from "./pages/Listen";
import Links from "./pages/Links";
import Subscribed from "./pages/Subscribed";
import EssayDetail from "./pages/EssayDetail";
import TopicLanding from "./pages/TopicLanding";
import AdminLogin from "./pages/admin/Login";
import AdminStoriesIndex from "./pages/admin/StoriesIndex";
import AdminStoryEditor from "./pages/admin/StoryEditor";
import RequireAuth from "./components/RequireAuth";
import NotFound from "./pages/NotFound";
import { captureIncomingUTMs } from "./lib/utm";

// Capture UTM params from the landing URL so they ride along on any subsequent
// lead-capture POST during this session. Safe on SSR (no-op).
captureIncomingUTMs();

const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    children: [
      { index: true, element: <Home /> },
      { path: "about", element: <About /> },
      { path: "archive", element: <Archive /> },
      { path: "speak", element: <Speak /> },
      { path: "speak/:topic", element: <TopicLanding /> },
      { path: "listen", element: <Listen /> },
      { path: "subscribed", element: <Subscribed /> },
      // Canonical essay URL. /archive stays as the listing page.
      { path: "essays/:slug", element: <EssayDetail /> },
      // Legacy alias — inbound links from ads/socials sometimes use /archive/:slug.
      { path: "archive/:slug", element: <EssayDetail /> },
      { path: "essays", element: <Navigate to="/archive" replace /> },
      // Admin — inside the shell so it inherits header/footer chrome. Auth is
      // enforced by RequireAuth, which redirects to /admin/login on miss.
      { path: "admin/login", element: <AdminLogin /> },
      {
        path: "admin/stories",
        element: (
          <RequireAuth>
            <AdminStoriesIndex />
          </RequireAuth>
        ),
      },
      {
        path: "admin/stories/:id/edit",
        element: (
          <RequireAuth>
            <AdminStoryEditor />
          </RequireAuth>
        ),
      },
      { path: "admin", element: <Navigate to="/admin/stories" replace /> },
      // Legacy URL redirects — preserve inbound link equity.
      { path: "newsletter", element: <Navigate to="/" replace /> },
      { path: "press", element: <Navigate to="/archive" replace /> },
      { path: "contact", element: <Navigate to="/speak" replace /> },
      { path: "*", element: <NotFound /> }
    ]
  },
  // /links is a bio-link landing page — no shell chrome, hidden from nav and sitemap.
  { path: "/links", element: <Links /> }
]);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <PostHogProvider
      apiKey={import.meta.env.VITE_PUBLIC_POSTHOG_KEY}
      options={{
        api_host: import.meta.env.VITE_PUBLIC_POSTHOG_HOST,
        defaults: '2025-05-24',
        capture_exceptions: true,
        debug: import.meta.env.MODE === "development",
      }}
    >
      <RouterProvider router={router} />
    </PostHogProvider>
  </React.StrictMode>
);
