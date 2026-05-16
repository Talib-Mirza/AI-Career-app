import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { Button } from "@/components/ui/button";

describe("Button", () => {
  it("renders accessible label", () => {
    render(<Button type="button">Continue</Button>);
    expect(
      screen.getByRole("button", { name: /continue/i }),
    ).toBeInTheDocument();
  });

  it("forwards click handler", async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    render(
      <Button type="button" onClick={onClick}>
        Tap
      </Button>,
    );
    await user.click(screen.getByRole("button", { name: /tap/i }));
    expect(onClick).toHaveBeenCalledTimes(1);
  });
});
