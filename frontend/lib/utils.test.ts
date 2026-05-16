import { describe, expect, it } from "vitest";
import { cn } from "@/lib/utils";

describe("cn", () => {
  it("joins conditional classes", () => {
    expect(cn("a", false && "b", "c")).toBe("a c");
  });

  it("merges conflicting Tailwind utilities with tailwind-merge", () => {
    expect(cn("px-2 py-1", "px-4")).toBe("py-1 px-4");
  });
});
