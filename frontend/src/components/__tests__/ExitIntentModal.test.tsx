import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import ExitIntentModal from "@/components/ExitIntentModal";

function fireExitIntent() {
  const evt = new MouseEvent("mouseout", {
    bubbles: true,
    cancelable: true,
    clientY: 0,
  });
  // relatedTarget defaults to null, which our handler wants (means the pointer
  // truly left the viewport, not just moved between children).
  document.dispatchEvent(evt);
}

describe("ExitIntentModal", () => {
  beforeEach(() => {
    window.sessionStorage.clear();
  });
  afterEach(() => {
    window.sessionStorage.clear();
  });

  it("does NOT open before the 8s dwell threshold", () => {
    render(
      <MemoryRouter>
        <ExitIntentModal />
      </MemoryRouter>
    );
    // Fire immediately — should be suppressed by the dwell check.
    act(() => fireExitIntent());
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("opens once after the dwell, then stays suppressed for the session", async () => {
    // Stub Date.now() so mount reads t=0 and the mouseout handler reads t=9000
    // (past MIN_DWELL_MS). Avoids fake timers — they break screen.findBy*.
    const t0 = 1_000_000;
    let advanced = false;
    const spy = vi.spyOn(Date, "now").mockImplementation(() => (advanced ? t0 + 9000 : t0));
    try {
      render(
        <MemoryRouter>
          <ExitIntentModal />
        </MemoryRouter>
      );
      advanced = true;
      act(() => fireExitIntent());

      expect(await screen.findByRole("dialog")).toBeInTheDocument();
      expect(window.sessionStorage.getItem("tih_exit_shown")).toBe("1");
    } finally {
      spy.mockRestore();
    }
  });

  it("stays closed on mount when the session flag is already set", () => {
    window.sessionStorage.setItem("tih_exit_shown", "1");
    render(
      <MemoryRouter>
        <ExitIntentModal />
      </MemoryRouter>
    );
    act(() => fireExitIntent());
    expect(screen.queryByRole("dialog")).toBeNull();
  });
});
