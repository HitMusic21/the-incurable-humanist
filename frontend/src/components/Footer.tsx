import { Link } from "react-router-dom";
import SocialIconRow from "./SocialIconRow";
import { SITE } from "@/config/site";
import { useAnalytics } from '@/hooks/useAnalytics';


export default function Footer() {
  const { track, events } = useAnalytics();
  return (
    <footer className="border-t border-line/60 bg-surface/50">
      <div className="container py-16 md:py-20">
        <div className="grid gap-12 md:grid-cols-3">
          {/* Brand & Tagline */}
          <div>
            <div className="font-serif text-[24px] text-ink mb-4">
              {SITE.hero.title}
            </div>
            <p className="text-muted-ink text-[16px] italic">
              {SITE.hero.tagline}
            </p>
          </div>

          {/* Navigation */}
          <div>
            <div className="font-serif text-[20px] text-ink mb-4">Navigate</div>
            <nav className="flex flex-col gap-3">
              {SITE.nav.map((item) => (
                <Link
                  key={item.to}
                  to={item.to}
                  className="text-muted-ink hover:text-accent transition focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 rounded w-fit"
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>

          {/* Social & Newsletter */}
          <div>
            <div className="font-serif text-[20px] text-ink mb-4">Connect</div>
            <SocialIconRow className="flex flex-wrap gap-3 mb-6" />
            <a
              href={SITE.substackSubscribeUrl}
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => track(events.NEWSLETTER_SIGNUP, { source: 'footer_link' })}
              className="text-accent hover:text-accent2 font-semibold transition focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 rounded inline-block"
            >
              Subscribe to Newsletter →
            </a>
          </div>
        </div>

        {/* Copyright */}
        <div className="mt-12 pt-8 border-t border-line text-center text-[14px] text-muted-ink">
          {/* Privacy sits here rather than in SITE.nav — that array also drives
              the header, and privacy is a footer-tier link, not primary nav. */}
          <p>
            © {new Date().getFullYear()} {SITE.hero.byline.replace('By ', '')}. All rights
            reserved.{' '}
            <span className="mx-1 text-line" aria-hidden="true">·</span>{' '}
            <Link
              to="/privacy"
              className="underline underline-offset-4 hover:text-accent transition focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 rounded"
            >
              Privacy
            </Link>
          </p>
        </div>
      </div>
    </footer>
  );
}
