import SectionTitle from "@/components/SectionTitle";
import PressItemCard from "@/components/PressItemCard";
import { SITE } from "@/config/site";

export default function Press() {
  return (
    <>
      <SectionTitle>Press</SectionTitle>

      <section className="container mt-10 pb-20 md:pb-28 space-y-10 md:space-y-12">
        {SITE.press.map((p) => (
          <PressItemCard key={p.title} {...p} />
        ))}
      </section>
    </>
  );
}
