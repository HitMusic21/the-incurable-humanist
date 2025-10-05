import PillButton from "@/components/PillButton";
import SocialIconButton from "@/components/SocialIconButton";
import { SITE } from "@/config/site";

function HeroBlock() {
  return (
    <section className="min-h-screen bg-bg relative overflow-hidden">
      {/* Desktop: Asymmetric Editorial Layout with Sophisticated Overlap */}
      {/* Mobile: Full-bleed vertical scroll with card floating over portrait */}
      <div className="relative min-h-screen lg:grid lg:grid-cols-[1.5fr_1fr] lg:items-stretch">

        {/* Portrait Column - Full impact, Rembrandt lighting showcase */}
        <div className="relative h-screen lg:h-screen lg:z-10">
          {/* Image Container - Let the beautiful lighting shine */}
          <div className="relative h-full overflow-hidden">
            <img
              src="/denisehome.jpeg"
              alt="Denise Rodriguez Dao, author of The Incurable Humanist, in burgundy blouse with books creating an intimate literary atmosphere"
              className="h-full w-full object-cover object-[center_-7%] sm:object-[center_-2%] lg:object-[center_3%]"
            />

            {/* Sophisticated gradient overlays - warm and subtle */}
            {/* Bottom gradient for mobile content overlap */}
            <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-bg/95 lg:to-transparent" />

            {/* Right-side gradient for desktop content transition - enhanced for overlap */}
            <div className="hidden lg:block absolute inset-0 bg-gradient-to-r from-transparent via-transparent via-60% to-bg/40" />

            {/* Subtle warm glow to enhance the portrait */}
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center_35%,transparent_0%,transparent_50%,rgba(249,247,243,0.1)_100%)]" />
          </div>

          {/* Decorative accent - burgundy echo from her blouse */}
          <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-accent2 to-transparent opacity-60" />
        </div>

        {/* Content Column - Floating editorial card with sophisticated overlap */}
        <div className="relative -mt-[50vh] sm:-mt-[52vh] md:-mt-[55vh] lg:mt-0 z-30 lg:flex lg:items-center lg:justify-start lg:-ml-28 xl:-ml-32">
          <div className="px-5 sm:px-10 lg:px-8 xl:px-10 pb-12 lg:pb-0">

            {/* Floating content card - Editorial sophistication with enhanced depth */}
            <div className="bg-surface rounded-[32px] shadow-[0_24px_48px_rgba(154,122,137,0.2)] lg:shadow-[0_40px_80px_rgba(154,122,137,0.35),0_16px_32px_rgba(0,0,0,0.12)] p-7 sm:p-10 lg:p-12 xl:p-14 border border-line/30 lg:border-line/50 max-w-xl lg:max-w-none">

              {/* Decorative opening accent - burgundy from portrait */}
              <div className="w-20 h-1 bg-gradient-to-r from-accent2 via-accent to-accent2/80 rounded-full mb-7 sm:mb-8 lg:mb-10" />

              {/* Main heading - Book cover typography */}
              <h1 className="font-serif text-accent font-medium leading-[0.92] tracking-tight">
                <span className="block text-[42px] sm:text-[56px] lg:text-[52px] xl:text-[64px]">
                  The Incurable
                </span>
                <span className="block text-[42px] sm:text-[56px] lg:text-[52px] xl:text-[64px] mt-1 lg:mt-0.5">
                  Humanist
                </span>
              </h1>

              {/* Byline - refined, literary */}
              <div className="mt-6 sm:mt-7 lg:mt-8 text-[13px] sm:text-[14px] uppercase tracking-[0.18em] text-muted-ink font-medium">
                {SITE.hero.byline}
              </div>

              {/* Elegant divider */}
              <div className="mt-4 sm:mt-5 mb-4 sm:mb-5 w-16 h-px bg-gradient-to-r from-line to-transparent" />

              {/* Tagline - intimate and personal */}
              <p className="text-[17px] sm:text-[21px] lg:text-[20px] xl:text-[22px] italic text-ink/70 leading-relaxed font-light max-w-md">
                {SITE.hero.tagline}
              </p>

              {/* Subscribe CTA - warm invitation */}
              <div className="mt-8 sm:mt-9 lg:mt-10">
                <PillButton
                  as="link"
                  to="/newsletter"
                  className="text-[15px] sm:text-[16px] font-medium tracking-wide shadow-[0_12px_32px_rgba(154,122,137,0.3)] hover:shadow-[0_16px_40px_rgba(154,122,137,0.4)] hover:scale-[1.02] transition-all duration-300"
                >
                  Subscribe to Newsletter
                </PillButton>
              </div>

              {/* Social links - sophisticated connection points */}
              <div className="mt-8 sm:mt-9 lg:mt-10 pt-6 sm:pt-7 border-t border-line/40">
                <div className="text-[11px] sm:text-[12px] uppercase tracking-[0.14em] text-muted-ink mb-4 font-medium">
                  Connect
                </div>
                <div className="flex flex-wrap items-center gap-3">
                  <SocialIconButton
                    label="Instagram"
                    href={SITE.socials.instagram}
                    className="hover:scale-110 hover:bg-accent2/90 transition-all duration-300"
                  >
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
                    </svg>
                  </SocialIconButton>

                  <SocialIconButton
                    label="TikTok"
                    href={SITE.socials.tiktok}
                    className="hover:scale-110 hover:bg-accent2/90 transition-all duration-300"
                  >
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z"/>
                    </svg>
                  </SocialIconButton>

                  <SocialIconButton
                    label="Facebook"
                    href={SITE.socials.facebook}
                    className="hover:scale-110 hover:bg-accent2/90 transition-all duration-300"
                  >
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                    </svg>
                  </SocialIconButton>

                  <SocialIconButton
                    label="LinkedIn"
                    href={SITE.socials.linkedin}
                    className="hover:scale-110 hover:bg-accent2/90 transition-all duration-300"
                  >
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                    </svg>
                  </SocialIconButton>

                  <SocialIconButton
                    label="X (Twitter)"
                    href={SITE.socials.x}
                    className="hover:scale-110 hover:bg-accent2/90 transition-all duration-300"
                  >
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                    </svg>
                  </SocialIconButton>
                </div>
              </div>

            </div>
          </div>
        </div>

      </div>
    </section>
  );
}

export default function Home() {
  return <HeroBlock />;
}
