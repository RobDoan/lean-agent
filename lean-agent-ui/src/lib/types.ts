// Mirrors lean-agent/src/lean_agent/api_schemas.py.
// Keep in sync — backend Pydantic models are the source of truth.

export interface ProjectSummary {
  slug: string;
  idea: string | null;
  hypothesis_count: number;
  run_count: number;
  with_synthesis_count: number;
  created_at: string;
}

export interface HypothesisListItem {
  id: string;
  title: string;
  has_run: boolean;
  has_synthesis: boolean;
  interview_count: number;
}

export interface ProjectDetail {
  slug: string;
  idea: string | null;
  idea_triage: string[];
  hypotheses: HypothesisListItem[];
}

export interface InterviewMeta {
  name: string;
  filename: string;
}

export interface HypothesisDetail {
  id: string;
  title: string;
  synthesis_markdown: string | null;
  sprint_markdown: string | null;
  interviews: InterviewMeta[];
}

export interface InterviewContent {
  name: string;
  markdown: string;
}

export interface ApiError {
  detail: string;
}

// v0.3 — persona library
export type PersonaSummary = {
  id: string;
  name: string;
  role: string | null;
};

export type PersonaDetail = {
  id: string;
  name: string;
  metadata: Record<string, string>;
  backstory: string;
  beliefs: string;
  biases: string;
  how_she_answers: string;
  raw_content: string;
};

// v0.3 — panel-presets
export type PresetSummary = {
  name: string;
  persona_count: number;
};

export type PresetDetail = {
  name: string;
  persona_ids: string[];
  raw_content: string;
};

// v0.3.2 — preset auto-generation
export type PresetPlanPersona = {
  slug: string;
  name: string;
  description: string;
};

export type PresetPlan = {
  description: string;
  reuse: string[];
  create: PresetPlanPersona[];
};

// v0.3.2 -- preset history
export type PresetHistoryEntry = {
  sha: string;
  message: string;
  date: string;
};

export type PresetVersionContent = {
  sha: string;
  content: string;
};
