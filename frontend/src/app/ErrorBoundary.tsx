import { Component, type ErrorInfo, type PropsWithChildren, type ReactNode } from "react";

interface ErrorBoundaryState {
  error: Error | null;
}

// React error boundaries must be class components; there is no hook equivalent.
// Without this, an uncaught render error anywhere in the tree produces a blank
// white screen with no indication anything went wrong.
export class ErrorBoundary extends Component<PropsWithChildren, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Unhandled render error", error, info.componentStack);
  }

  render(): ReactNode {
    if (this.state.error) {
      return (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            minHeight: "100vh",
            gap: 12,
            padding: 24,
            textAlign: "center",
            fontFamily: "var(--font-sans, sans-serif)",
          }}
        >
          <h1 style={{ fontSize: 18, fontWeight: 650 }}>Something went wrong</h1>
          <p style={{ fontSize: 13.5, color: "var(--color-text-secondary, #4a5568)", maxWidth: 420 }}>
            An unexpected error occurred while rendering this page. Reloading usually fixes it.
          </p>
          <button
            onClick={() => window.location.reload()}
            style={{
              padding: "8px 16px",
              borderRadius: 6,
              border: "1px solid var(--color-primary, #1d4ed8)",
              background: "var(--color-primary, #1d4ed8)",
              color: "#fff",
              cursor: "pointer",
              fontSize: 13,
            }}
          >
            Reload page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
