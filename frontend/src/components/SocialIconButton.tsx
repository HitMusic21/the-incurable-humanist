type Props = {
  label: string;
  href: string;
  children: React.ReactNode;
  className?: string;
};

export default function SocialIconButton({ label, href, children, className = "" }: Props) {
  return (
    <a
      aria-label={label}
      href={href}
      className={`inline-flex h-11 w-11 items-center justify-center rounded-full bg-accent2 text-white hover:brightness-110 transition ${className}`}
    >
      {children}
    </a>
  );
}
