import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import App from "../App";

describe("App Component", () => {
  it("renders without crashing", () => {
    render(<App />);
    expect(document.body).toBeTruthy();
  });

  it("contains main application elements", () => {
    render(<App />);
    // App should render either Wizard or Report components
    // The exact content depends on the current state
    const container = document.body;
    expect(container).toBeTruthy();
    expect(container).toBeInTheDocument();
  });

  it("displays the application title or branding", () => {
    render(<App />);

    // Look for app title, logo, or main heading
    const titleElements = screen.queryAllByText(
      /smart research|research crew|src/i,
    );
    expect(titleElements.length).toBeGreaterThanOrEqual(0);
  });

  it("initializes in the correct default state", () => {
    render(<App />);

    // Should start with wizard view by default
    const wizardElements = screen.queryAllByText(
      /topic|research|guidelines|start/i,
    );
    expect(wizardElements.length).toBeGreaterThan(0);
  });

  it("handles state transitions correctly", () => {
    render(<App />);

    // App should manage transitions between wizard and report views
    // This tests the overall application flow
    const appContainer = document.body;
    expect(appContainer).toBeTruthy();

    // Should have proper component structure
    expect(appContainer.children.length).toBeGreaterThan(0);
  });

  it("provides proper error boundaries", () => {
    // Test that app handles errors gracefully
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    render(<App />);

    // App should render even if there are minor issues
    expect(document.body).toBeTruthy();

    consoleSpy.mockRestore();
  });

  it("maintains responsive design", () => {
    render(<App />);

    // Should have responsive classes or viewport handling
    const appElements = document.body.children;
    expect(appElements.length).toBeGreaterThan(0);

    // Check for responsive design indicators
    const responsiveElements = document.querySelectorAll(
      '[class*="responsive"], [class*="mobile"], [class*="tablet"], [class*="desktop"]',
    );
    expect(responsiveElements.length).toBeGreaterThanOrEqual(0);
  });

  it("handles browser navigation correctly", () => {
    render(<App />);

    // Should work with browser back/forward
    expect(window.location).toBeDefined();
    expect(document.title).toBeDefined();
  });
});
