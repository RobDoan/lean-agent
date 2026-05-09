# lean-agent

> Lean Startup **Mode A** coach — turn a fresh product idea into a pre-filtered hypothesis backlog and rehearse the first interview round against a panel of personas. The agent never validates. Real humans do.

---

## Before you begin

By the end of this tutorial you will have:

- A new project on disk with a hypothesis backlog generated from a one-line idea.
- A completed rehearsal interview (R1) for one of those hypotheses.
- An exportable kit you could take to a real customer interview.
- (Optional) The web UI showing it all in your browser.

You'll need:

- An [Anthropic API key](https://console.anthropic.com/).
- [`uv`](https://github.com/astral-sh/uv) (Python 3.12+ toolchain).
- Optional, for the UI step: Node.js 22+, **or** Docker.

The whole walkthrough takes about 10 minutes. Everything the agent writes lives under `~/.lean-agent/` — you can delete that directory at any time to start over.

---

## 1. Install the CLI

Clone the repo and install the backend (which ships the `lean` CLI):

```bash
git clone https://github.com/SpeedyBite/lean-agent.git
cd lean-agent/lean-agent
uv sync
```

Verify the CLI is on your path:

```bash
uv run lean --version
```

You should see a version number such as `0.0.1`. If you do, the install worked.

---

## 2. Create your first project

Set your API key in the current shell:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

Then create a project from a one-line idea (use your own — this is just an example):

```bash
uv run lean init "an app that helps remote teams run async standups"
```

You'll see progress lines streamed to stderr (`→ generating hypotheses…`) and finally a confirmation:

```text
created: /Users/you/.lean-agent/projects/<your-slug>
```

`<your-slug>` is auto-derived from your idea. The new project is also set as your **current project**, so you don't need to repeat the slug from now on.

Open the directory the CLI just printed to see the generated hypothesis backlog (`H1.md`, `H2.md`, …) under `hypotheses/`.

---

## 3. Run a rehearsal interview (R1)

Pick the first hypothesis and run a rehearsal against the bundled persona panel:

```bash
uv run lean run R1 H1
```

The agent simulates a structured first-round interview against each persona, then writes the result. You'll see:

```text
wrote: /Users/you/.lean-agent/projects/<your-slug>/hypotheses/H1
```

Inside that directory, open `01-problem-validation-sprint.md` to read the rehearsal output.

---

## 4. (Optional) View it in the browser

The CLI is the source of truth, but you can browse what you've made in a web UI.

**Path A — Docker (one command, runs both backend and frontend):**

```bash
cd ..   # back to the repo root
docker compose up --build
```

**Path B — manual frontend dev server (assumes the backend is also running, e.g. `uv run uvicorn lean_agent.api:app --port 8000`):**

```bash
cd lean-agent-ui
npm install
npm run dev
```

Either way, open <http://localhost:5173>, click your project, and you should see the H1 hypothesis with the rehearsal you just generated.

---

## 5. Export the real-interview kit

When you're happy with a hypothesis, promote it and export the kit:

```bash
uv run lean promote H1
uv run lean export-kit H1
```

You'll see:

```text
promoted: H1
kit: /Users/you/.lean-agent/projects/<your-slug>/exports/H1-kit.md
```

Open the file at the printed path. That's the artefact you take to a real customer interview — script, screening questions, notes template.

---

## What you've built

In one sitting you took a one-line idea and produced:

- A pruned hypothesis backlog (`R0`).
- A rehearsed first-round interview (`R1`).
- A real-interview kit ready for a human conversation.

The agent's job ends here. From this point on, the loop is yours: book the interview, run it with a real person, bring the learnings back, and decide what to keep, kill, or revise.

> The agent rehearses. Humans validate.

---

## Where to go next

- **Full CLI reference** — every command, flag, and the home-directory layout: [`lean-agent/README.md`](lean-agent/README.md).
- **Frontend development** — Vite, Tailwind, component layout: [`lean-agent-ui/README.md`](lean-agent-ui/README.md).
- **Running the test suite locally:**
  - Backend: `cd lean-agent && uv run ruff check . && uv run mypy src && uv run pytest`
  - Frontend: `cd lean-agent-ui && npm run lint && npm run typecheck && npm run test -- --run`

### Tech stack at a glance

| Layer    | Stack                                                                    |
| -------- | ------------------------------------------------------------------------ |
| Backend  | Python 3.12+, FastAPI, Typer (CLI), Anthropic SDK, Jinja2, GitPython     |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS 4, TanStack Query, Radix/shadcn |
| Tooling  | uv (Python), npm (JS), Ruff, mypy, pytest, ESLint, Vitest                |
| Runtime  | Docker + docker-compose; GitHub Actions for CI                           |
