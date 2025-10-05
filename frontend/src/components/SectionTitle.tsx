type Props = { children: React.ReactNode };

export default function SectionTitle({ children }: Props) {
  return (
    <div className="container pt-20 md:pt-28">
      <h1 className="text-center font-serif text-accent2 text-[36px] md:text-[42px]">
        {children}
      </h1>
      <div className="mx-auto mt-3 h-[2px] w-[56px] rounded bg-accent" />
    </div>
  );
}
