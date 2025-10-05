import Card from "./Card";

type Item = { outlet: string; title: string; dek: string; href: string };

export default function PressItemCard({ outlet, title, dek, href }: Item) {
  return (
    <Card className="group relative p-8 md:p-10 hover:shadow-[0_12px_32px_rgba(110,85,128,0.08)] transition-all duration-500 border border-line/60 hover:border-accent/15">

      {/* Decorative quotation mark - editorial touch */}
      <div
        className="absolute top-6 right-6 md:top-8 md:right-8 text-[48px] md:text-[64px] font-serif text-accent/5 leading-none select-none pointer-events-none"
        aria-hidden="true"
      >
        "
      </div>

      {/* Content layer */}
      <div className="relative z-10">
        {/* Publication name - italicized, muted accent */}
        <div className="font-serif text-[18px] md:text-[20px] italic text-accent2 mb-3 transition-colors group-hover:text-accent">
          {outlet}
        </div>

        {/* Article title - hero element */}
        <a
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="block mb-3 -ml-1 pl-1 rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-4"
        >
          <h3 className="font-serif text-[22px] md:text-[26px] lg:text-[28px] font-semibold text-ink leading-tight transition-colors group-hover:text-accent2">
            {title}
          </h3>
        </a>

        {/* Description - constrained width for readability */}
        <p className="text-[16px] md:text-[17px] text-muted-ink leading-relaxed mb-8 max-w-3xl">
          {dek}
        </p>

        {/* CTA section with separator */}
        <div className="pt-6 border-t border-line/40 group-hover:border-accent/30 transition-colors">
          <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            aria-label={`Read "${title}" on ${outlet}`}
            className="inline-flex items-center gap-2 text-[16px] font-medium text-accent hover:text-accent transition-all group/link px-2 -mx-2 rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2"
          >
            <span className="underline decoration-2 decoration-accent/30 group-hover/link:decoration-accent underline-offset-4 transition-colors">
              Read Article
            </span>
            <svg
              className="w-4 h-4 transition-transform group-hover/link:translate-x-1"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2.5}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </a>
        </div>
      </div>
    </Card>
  );
}
