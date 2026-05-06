import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import "@fontsource-variable/geist";
import "./index.css";
import Dashboard from "./pages/Dashboard";
import ProjectDetail from "./pages/ProjectDetail";
import NotFound from "./pages/NotFound";
import { RootLayout } from "./components/RootLayout";
import PersonasList from "./pages/PersonasList";
import PresetsList from "./pages/PresetsList";
import EditorPage from "./pages/EditorPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false, staleTime: 5_000 },
  },
});

const router = createBrowserRouter([
  {
    element: <RootLayout />,
    errorElement: <NotFound />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: "p/:slug", element: <ProjectDetail /> },
      { path: "p/:slug/h/:hid", element: <ProjectDetail /> },
      { path: "personas", element: <PersonasList /> },
      { path: "personas/new", element: <EditorPage target="persona" mode="create" /> },
      { path: "personas/:id", element: <EditorPage target="persona" mode="edit" /> },
      { path: "panel-presets", element: <PresetsList /> },
      { path: "panel-presets/new", element: <EditorPage target="preset" mode="create" /> },
      { path: "panel-presets/:name", element: <EditorPage target="preset" mode="edit" /> },
      { path: "*", element: <NotFound /> },
    ],
  },
]);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </StrictMode>,
);
