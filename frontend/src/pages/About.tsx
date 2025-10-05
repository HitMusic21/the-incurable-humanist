import SectionTitle from "@/components/SectionTitle";
import Card from "@/components/Card";

export default function About() {
  return (
    <>
      <SectionTitle>About</SectionTitle>

      <section className="container mt-10 pb-20 md:pb-28 max-w-4xl">
        {/* Main Content Card */}
        <Card className="p-10 md:p-12 lg:p-14 mb-10 md:mb-14">
          <h2 className="font-serif text-accent2 text-[32px] md:text-[38px] text-center mb-10 md:mb-12 leading-tight">
            The Incurable Humanist
          </h2>

          <div className="space-y-8 text-[17px] md:text-[18px] leading-relaxed max-w-3xl mx-auto">
            <p>
              The Incurable Humanist is a space for grief, migration, and art.
            </p>

            <p>
              Grief is more than mourning the death of a loved one. It is leaving home, it is
              heartbreak, it is losing who we once were, it is navigating trauma.
            </p>

            <p>
              Migration, too, is a form of grief. Each journey carries a weight of love, loss,
              and transformation.
            </p>

            <p>
              Art is our lifesaver. Art in any of its forms, whether it is painting, music,
              writing, cooking, theater, film, photography, etc., is a tool through which we
              process, endure, and transform our grief. Through art, we find resilience.
            </p>

            {/* Visual Break with Accent Line */}
            <div className="py-6 md:py-8">
              <div className="mx-auto h-[2px] w-[56px] rounded bg-accent" />
            </div>

            <p>
              The Incurable Humanist was born from the founder, Denise Rodriguez Dao's, own
              experiences. The profound grief of losing her father, the dislocations of migration
              from Caracas to Mexico City and now New York, her work in the art world, and her
              legal experience helping artists and entrepreneurs find new homes in the United States.
            </p>

            <p>
              The Incurable Humanist is both personal and collective. It begins with Denise's
              storytelling; her experiences are the lens through which this space takes shape.
              Yet it is also collective, because it invites you to share your story.
            </p>
          </div>
        </Card>

        {/* Founder Bio Card */}
        <Card className="p-10 md:p-12 lg:p-14">
          <h2 className="font-serif text-accent2 text-[32px] md:text-[38px] text-center mb-10 md:mb-12 leading-tight">
            The Founder
          </h2>

          {/* Founder Portrait */}
          <div className="mx-auto mb-10 md:mb-12 w-full max-w-[420px] md:max-w-[520px]">
            <img
              src="/founder.jpg"
              alt="Denise Rodriguez Dao, founder of The Incurable Humanist"
              className="w-full h-auto rounded-xl shadow-soft"
            />
          </div>

          <div className="max-w-3xl mx-auto space-y-8 text-[17px] md:text-[18px] leading-relaxed">
            <p>
              Denise Rodriguez Dao writes <em>The Incurable Humanist</em>, a weekly newsletter
              exploring grief, migration, and art.
            </p>

            <p>
              She currently works as a foreign attorney at a boutique immigration law firm in
              Manhattan, where she secures visas for artists, gallerists, entrepreneurs, and
              cultural professionals.
            </p>

            <p>
              She also has a background in the arts, having served as content director, head of
              logistics, and artist liaison at Galería RGR in Mexico City. There, she managed a
              roster that included both iconic figures of Latin American modernism and leading
              contemporary artists.
            </p>

            <p>
              Denise holds a master's degree in Modern and Contemporary Art and the Market from
              Christie's Education in New York and a J.D. from Andrés Bello Catholic University in
              Caracas, Venezuela.
            </p>
          </div>
        </Card>
      </section>
    </>
  );
}
