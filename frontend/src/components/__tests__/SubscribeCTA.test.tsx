import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import SubscribeCTA from "@/components/SubscribeCTA";

// PostHogProvider is used by useAnalytics via usePostHog(); the hook tolerates
// a missing provider (returns undefined) — analytics.track() is consent-gated
// and a no-op in tests, so we don't need to mock the provider.

function renderCTA(props: Partial<React.ComponentProps<typeof SubscribeCTA>> = {}) {
  return render(
    <MemoryRouter>
      <SubscribeCTA placement="test-placement" {...props} />
    </MemoryRouter>
  );
}

describe("SubscribeCTA", () => {
  beforeEach(() => {
    window.sessionStorage.clear();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    window.sessionStorage.clear();
  });

  it("POSTs email + UTMs from sessionStorage to /leads/subscribe on submit", async () => {
    window.sessionStorage.setItem(
      "tih_utm",
      JSON.stringify({
        source: "instagram",
        medium: "organic-social",
        campaign: "spring-arc",
        content: null,
        term: null,
      })
    );

    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ status: "pending_confirmation" }), {
        status: 202,
        headers: { "Content-Type": "application/json" },
      })
    );

    renderCTA();
    fireEvent.change(screen.getByPlaceholderText("you@example.com"), {
      target: { value: "reader@example.com" },
    });
    fireEvent.click(screen.getByRole("button", { name: /send me the reader/i }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));

    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toMatch(/\/leads\/subscribe$/);
    const body = JSON.parse(String((init as RequestInit).body));
    expect(body.email).toBe("reader@example.com");
    expect(body.source).toBe("test-placement");
    expect(body.magnet_requested).toBe(true);
    expect(body.utm.source).toBe("instagram");
    expect(body.utm.campaign).toBe("spring-arc");

    // Success view renders.
    await screen.findByText(/check your inbox/i);
  });

  it("shows Substack fallback link when the API errors", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response("boom", { status: 500 })
    );

    renderCTA();
    fireEvent.change(screen.getByPlaceholderText("you@example.com"), {
      target: { value: "reader@example.com" },
    });
    fireEvent.click(screen.getByRole("button", { name: /send me the reader/i }));

    const fallback = await screen.findByRole("link", { name: /open substack/i });
    expect(fallback).toBeInTheDocument();
  });

  it("rejects invalid email locally without hitting the network", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch");

    renderCTA();
    fireEvent.change(screen.getByPlaceholderText("you@example.com"), {
      target: { value: "not-an-email" },
    });
    // Bypass the browser's built-in email validation by submitting the form directly.
    fireEvent.submit(screen.getByPlaceholderText("you@example.com").closest("form")!);

    await screen.findByText(/please enter a valid email/i);
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
