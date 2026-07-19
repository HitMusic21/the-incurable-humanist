import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Subscribed from "@/pages/Subscribed";

function renderAt(url: string) {
  return render(
    <MemoryRouter initialEntries={[url]}>
      <Subscribed />
    </MemoryRouter>
  );
}

describe("Subscribed", () => {
  afterEach(() => vi.restoreAllMocks());

  it("hides the referral block before confirmation (?magnet missing)", () => {
    renderAt("/subscribed");
    expect(screen.queryByText(/pass it along/i)).toBeNull();
    // Confirmation copy is what shows here.
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(/check your inbox/i);
  });

  it("shows the referral block after confirmation (?magnet=1)", () => {
    renderAt("/subscribed?magnet=1");
    expect(screen.getByText(/pass it along/i)).toBeInTheDocument();
    // All three share channels render as links.
    expect(screen.getByRole("link", { name: /share on x/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /whatsapp/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /email a friend/i })).toBeInTheDocument();
  });

  it("each share link carries the reader-magnet UTM campaign in its shared URL", () => {
    renderAt("/subscribed?magnet=1");
    const twitter = screen.getByRole("link", { name: /share on x/i }) as HTMLAnchorElement;
    // The tweet-intent URL wraps the shared URL as ?url=…
    const parsed = new URL(twitter.href);
    const shared = new URL(parsed.searchParams.get("url") || "");
    expect(shared.searchParams.get("utm_source")).toBe("website");
    expect(shared.searchParams.get("utm_medium")).toBe("referral");
    expect(shared.searchParams.get("utm_campaign")).toBe("reader-magnet");
    expect(shared.searchParams.get("utm_content")).toBe("thank-you");
  });
});
