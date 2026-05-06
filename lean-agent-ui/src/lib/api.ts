import type {
  HypothesisDetail,
  InterviewContent,
  PersonaDetail,
  PersonaSummary,
  PresetDetail,
  PresetSummary,
  ProjectDetail,
  ProjectSummary,
} from "@/lib/types";

export class ApiClientError extends Error {
  readonly status: number;
  readonly detail: string;
  referencedBy?: string[];

  constructor(status: number, detail: string) {
    super(`API ${status}: ${detail}`);
    this.name = "ApiClientError";
    this.status = status;
    this.detail = detail;
  }
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path);
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body && typeof body.detail === "string") detail = body.detail;
    } catch {
      // body wasn't JSON; keep statusText.
    }
    throw new ApiClientError(response.status, detail);
  }
  return (await response.json()) as T;
}

export function listProjects(): Promise<ProjectSummary[]> {
  return getJson<ProjectSummary[]>("/api/projects");
}

export function getProject(slug: string): Promise<ProjectDetail> {
  return getJson<ProjectDetail>(`/api/projects/${slug}`);
}

export function getHypothesis(slug: string, hid: string): Promise<HypothesisDetail> {
  return getJson<HypothesisDetail>(`/api/projects/${slug}/hypotheses/${hid}`);
}

export function getInterview(slug: string, hid: string, name: string): Promise<InterviewContent> {
  return getJson<InterviewContent>(`/api/projects/${slug}/hypotheses/${hid}/interviews/${name}`);
}

export function listPersonas(): Promise<PersonaSummary[]> {
  return getJson<PersonaSummary[]>("/api/personas");
}

export function getPersona(id: string): Promise<PersonaDetail> {
  return getJson<PersonaDetail>(`/api/personas/${id}`);
}

export function listPresets(): Promise<PresetSummary[]> {
  return getJson<PresetSummary[]>("/api/panel-presets");
}

export function getPreset(name: string): Promise<PresetDetail> {
  return getJson<PresetDetail>(`/api/panel-presets/${name}`);
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(path, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw await apiError(r);
  return (await r.json()) as T;
}

async function putJson<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(path, {
    method: "PUT",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw await apiError(r);
  return (await r.json()) as T;
}

async function del(path: string): Promise<void> {
  const r = await fetch(path, { method: "DELETE" });
  if (!r.ok) throw await apiError(r);
}

async function apiError(r: Response): Promise<ApiClientError> {
  let detail = r.statusText;
  let referenced_by: string[] | undefined;
  try {
    const body = (await r.json()) as { detail?: string; referenced_by?: string[] };
    if (body && typeof body.detail === "string") detail = body.detail;
    if (Array.isArray(body?.referenced_by)) referenced_by = body.referenced_by.map(String);
  } catch { /* keep statusText */ }
  const e = new ApiClientError(r.status, detail);
  if (referenced_by) (e as ApiClientError & { referencedBy: string[] }).referencedBy = referenced_by;
  return e;
}

// v0.3 commit + delete

export function createPersona(body: { id: string; content: string }): Promise<PersonaDetail> {
  return postJson<PersonaDetail>("/api/personas", body);
}

export function editPersona(id: string, content: string): Promise<PersonaDetail> {
  return putJson<PersonaDetail>(`/api/personas/${id}`, { content });
}

export function deletePersona(id: string): Promise<void> {
  return del(`/api/personas/${id}`);
}

export function createPreset(body: { name: string; content: string }): Promise<PresetDetail> {
  return postJson<PresetDetail>("/api/panel-presets", body);
}

export function editPreset(name: string, content: string): Promise<PresetDetail> {
  return putJson<PresetDetail>(`/api/panel-presets/${name}`, { content });
}

export function deletePreset(name: string): Promise<void> {
  return del(`/api/panel-presets/${name}`);
}
