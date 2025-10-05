import { Outlet, NavLink, Link } from "react-router-dom";
import Footer from "@/components/Footer";
import { SITE } from "@/config/site";

export default function App() {
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
