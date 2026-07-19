import { useEffect } from "react";

type Props = {
  title: string;
  description: string;
  canonical: string;
  ogImage?: string;
  jsonLd?: unknown[];
  noindex?: boolean;
};

const DEFAULT_OG_IMAGE = "https://theincurablehumanist.com/og-image.svg";
const JSONLD_ID = "tih-jsonld-page";

function setMeta(nameOrProp: string, value: string, byProperty = false) {
  const attr = byProperty ? "property" : "name";
  let el = document.head.querySelector<HTMLMetaElement>(`meta[${attr}="${nameOrProp}"]`);
  if (!el) {
    el = document.createElement("meta");
    el.setAttribute(attr, nameOrProp);
    document.head.appendChild(el);
  }
  el.content = value;
}

function setLink(rel: string, href: string) {
  let el = document.head.querySelector<HTMLLinkElement>(`link[rel="${rel}"]`);
  if (!el) {
    el = document.createElement("link");
    el.rel = rel;
    document.head.appendChild(el);
  }
  el.href = href;
}

export default function SEO({
  title,
  description,
  canonical,
  ogImage = DEFAULT_OG_IMAGE,
  jsonLd,
  noindex = false,
}: Props) {
  useEffect(() => {
    document.title = title;
    setMeta("description", description);
    setMeta("title", title);
    setLink("canonical", canonical);

    setMeta("og:title", title, true);
    setMeta("og:description", description, true);
    setMeta("og:url", canonical, true);
    setMeta("og:image", ogImage, true);

    setMeta("twitter:title", title, true);
    setMeta("twitter:description", description, true);
    setMeta("twitter:url", canonical, true);
    setMeta("twitter:image", ogImage, true);

    // Robots
    setMeta("robots", noindex ? "noindex, nofollow" : "index, follow");

    // JSON-LD @graph
    let script = document.getElementById(JSONLD_ID) as HTMLScriptElement | null;
    if (jsonLd && jsonLd.length > 0) {
      const payload = JSON.stringify({
        "@context": "https://schema.org",
        "@graph": jsonLd,
      });
      if (!script) {
        script = document.createElement("script");
        script.type = "application/ld+json";
        script.id = JSONLD_ID;
        document.head.appendChild(script);
      }
      script.text = payload;
    } else if (script) {
      script.remove();
    }
  }, [title, description, canonical, ogImage, jsonLd, noindex]);

  return null;
}
