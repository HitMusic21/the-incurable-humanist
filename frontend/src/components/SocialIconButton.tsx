import { useAnalytics } from '@/hooks/useAnalytics';
import { withUTM } from '@/lib/utm';

type Props = {
  label: string;
  href: string;
  children: React.ReactNode;
  className?: string;
};

export default function SocialIconButton({ label, href, children, className = "" }: Props) {
  const { track, events } = useAnalytics();

  const taggedHref = withUTM(href, {
    source: "website",
    medium: "referral",
    content: `social-icon-${label.toLowerCase().replace(/\s+/g, "-")}`,
  });

  const handleClick = () => {
    track(events.SOCIAL_LINK_CLICK, {
      platform: label,
      url: taggedHref,
    });
  };

  return (
    <a
      aria-label={label}
      href={taggedHref}
      onClick={handleClick}
      target="_blank"
      rel="noopener noreferrer"
      className={`inline-flex h-11 w-11 items-center justify-center rounded-full bg-accent2 text-white hover:brightness-110 transition ${className}`}
    >
      {children}
    </a>
  );
}
