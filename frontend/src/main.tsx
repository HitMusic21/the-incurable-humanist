import React from "react";
import ReactDOM from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { PostHogProvider } from "posthog-js/react";
import "./styles/globals.css";
import App from "./shell/App";
import Home from "./pages/Home";
import About from "./pages/About";
import Press from "./pages/Press";
import Contact from "./pages/Contact";
import Newsletter from "./pages/Newsletter";
import NotFound from "./pages/NotFound";

const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    children: [
      { index: true, element: <Home /> },
      { path: "about", element: <About /> },
      { path: "press", element: <Press /> },
      { path: "contact", element: <Contact /> },
      { path: "newsletter", element: <Newsletter /> },
      { path: "*", element: <NotFound /> }
    ]
  }
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
