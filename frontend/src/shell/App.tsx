import { Outlet, NavLink, Link, useLocation } from "react-router-dom";
import { useEffect } from "react";
import Footer from "@/components/Footer";
import { SITE } from "@/config/site";
import { useAnalytics } from "@/hooks/useAnalytics";

export default function App() {
  const location = useLocation();
  const { track, events } = useAnalytics();

  // Track page views when location changes
  useEffect(() => {
    const pageName = location.pathname === '/' ? 'Home' : 
      location.pathname.slice(1).charAt(0).toUpperCase() + location.pathname.slice(2);
    
    track(events.PAGE_VIEW, {
      page_path: location.pathname,
      page_name: pageName,
    });
  }, [location, track, events]);
  return (
    <div className="min-h-dvh flex flex-col">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-[100] focus:px-6 focus:py-3 focus:bg-accent focus:text-white focus:rounded-lg focus:shadow-lg"
      >
        Skip to main content
      </a>
      <header className="sticky top-0 z-50 backdrop-blur-[2px] border-b border-line bg-bg/80">
        <div className="container flex items-center justify-between py-6">
          <Link
            to="/"
            className="text-[12px] tracking-widecaps uppercase text-muted-ink hover:text-accent transition focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 rounded"
          >
            {SITE.brand}
          </Link>
          <nav className="flex gap-8 text-[12px] tracking-widecaps uppercase text-muted-ink">
            {SITE.nav.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `hover:text-accent transition focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 rounded ${
                    isActive ? "text-accent" : ""
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main id="main-content" className="flex-1">
        <Outlet />
      </main>

      <Footer />
    </div>
  );
}
