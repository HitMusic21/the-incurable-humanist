type Props = {
  substackUrl: string;
  className?: string;
};

export default function SubstackEmbed({ substackUrl, className = "" }: Props) {
  // Extract the subdomain from the Substack URL
  // e.g., "https://yourname.substack.com" -> "yourname"
  const getSubstackSubdomain = (url: string) => {
    try {
      const urlObj = new URL(url);
      const hostname = urlObj.hostname;
      // Handle both yourname.substack.com and custom domains
      if (hostname.includes('.substack.com')) {
        return hostname.split('.')[0];
      }
      return hostname;
    } catch {
      return 'yourname'; // fallback
    }
  };

  const subdomain = getSubstackSubdomain(substackUrl);
  const embedUrl = `https://${subdomain}.substack.com/embed`;

  return (
    <div className={className}>
      <iframe
        src={embedUrl}
        width="100%"
        height="320"
        style={{ border: '1px solid #EEE', background: 'white' }}
        frameBorder="0"
        scrolling="no"
        title="Substack Newsletter Signup"
      />
    </div>
  );
}
