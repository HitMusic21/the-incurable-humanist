import SectionTitle from "@/components/SectionTitle";
import Card from "@/components/Card";
import PillButton from "@/components/PillButton";

export default function Newsletter() {
  return (
    <>
      <SectionTitle>Newsletter</SectionTitle>

      <section className="container mt-10 pb-20 md:pb-28 max-w-3xl">
        <Card className="p-8 md:p-10 lg:p-12 text-center">
          <h3 className="font-serif text-accent2 text-[28px] md:text-[32px] mb-6">
            Subscribe to The Incurable Humanist
          </h3>

          <p className="text-[18px] md:text-[19px] mb-6 leading-relaxed">
            Weekly reflections on grief, migration, and art.
          </p>

          <div className="py-8">
            <div className="mx-auto h-[2px] w-[56px] rounded bg-accent" />
          </div>

          <PillButton
            as="button"
            onClick={() => window.open("https://theincurablehumanist.substack.com/?utm_campaign=profile_chips", "_blank")}
          >
            Subscribe on Substack
          </PillButton>

          <p className="mt-6 text-[15px] text-muted-ink">
            Free • Weekly • Unsubscribe anytime
          </p>
        </Card>

        {/* Add context about the founder */}
        <div className="mt-10 text-center">
          <p className="text-[16px] text-muted-ink">
            Written by <a href="/about" className="text-accent hover:text-accent2 underline underline-offset-4 transition">Denise Rodriguez Dao</a>
          </p>
        </div>
      </section>
    </>
  );
}
