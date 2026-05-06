import type { ReactElement } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, type RenderOptions, type RenderResult } from "@testing-library/react";

export function renderWithQuery(
  ui: ReactElement,
  options?: RenderOptions,
): RenderResult {
  // Fresh client per test — retries off, stale immediately, gc immediately.
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false, staleTime: 0, gcTime: 0 },
      mutations: { retry: false },
    },
  });
  return render(
    <QueryClientProvider client={client}>{ui}</QueryClientProvider>,
    options,
  );
}
