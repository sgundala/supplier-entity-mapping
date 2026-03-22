import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";

import App from "./App";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("App", () => {
  it("renders vendor results including location metadata", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({
        results: [
          {
            rank: 1,
            vendor_name: "ABC Chemicals",
            summary: "Industrial chemicals supplier",
            metadata: {
              category: "Industrial Chemicals",
              location: "Houston, TX",
            },
            score: 0.98,
          },
        ],
      }),
    });

    render(<App />);

    fireEvent.change(screen.getByLabelText(/search suppliers/i), {
      target: { value: "industrial chemicals supplier" },
    });
    fireEvent.click(screen.getByRole("button", { name: /search/i }));

    await waitFor(() => {
      expect(screen.getByText("ABC Chemicals")).toBeInTheDocument();
    });

    expect(screen.getByText("Houston, TX")).toBeInTheDocument();
  });
});
