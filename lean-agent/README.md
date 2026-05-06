# lean-agent

A Lean Startup Mode-A coach: turn a fresh idea into a pre-filtered hypothesis list, simulate the first round of interviews against a panel of personas, and export a real-interview kit ready for human users.

The agent never validates. Real humans do.

## Quick Start

```bash
# Create a project (idea → hypothesis backlog). Auto-sets it as the current project.
$ lean init "an app that helps remote teams run async standups"

# One-time per project: set current
$ lean use <slug>

# Then operate without retyping the slug
$ lean run R1 H1
$ lean promote H1
$ lean export-kit H1

# Cross-project override anytime
$ lean export-kit H2 --slug some-other-project

# Show / list contexts
$ lean use            # prints current
$ lean use list       # lists available, * marks current
```

## Upgrading from v0

v0.1.0 changes the CLI shape: the project slug moved from a positional argument to the `--slug` option, and is auto-resolved from a stored "current project" when omitted.

| v0 (old)                                  | v0.1.0 (new)                           |
| ----------------------------------------- | -------------------------------------- |
| `lean run R1 <slug> H1`                   | `lean use <slug>` then `lean run R1 H1` |
| `lean promote <slug> H1`                  | `lean promote H1`                      |
| `lean export-kit <slug> H1`               | `lean export-kit H1`                   |
| `lean kill <slug> H1 --note "..."`        | `lean kill H1 --note "..."`            |

`lean init "<idea>"` is unchanged and now auto-sets the new project as current.

## Filesystem layout

Everything lean-agent writes lives under `~/.lean-agent/`:

```
~/.lean-agent/
  state.json    current-project pointer (see "lean use" above). Hand-editable;
                corrupt JSON → hard error with the file path.
  personas/     persona library — bundled starters copied here on first init,
                plus any custom *.md files you add. Survives upgrades.
  projects/     all your projects, one subdirectory per slug. Each project is
                its own git repo.
```

Backup: `tar -czf lean-agent-backup.tgz ~/.lean-agent/`.
Uninstall: `rm -rf ~/.lean-agent/`.

## Upgrading from v0.1.0

**v0.1.1 is a hard breaking change for the home-dir layout.** v0/v0.1.0 used three sibling directories under `$HOME`:

```
~/.lean-personas/    personas
~/lean-projects/     projects
~/.lean-agent/state.json    state
```

v0.1.1 consolidates everything under `~/.lean-agent/`. There is **no auto-migration** in code. After installing v0.1.1, run:

```bash
mv ~/.lean-personas ~/.lean-agent/personas
mv ~/lean-projects ~/.lean-agent/projects
```

If you forget, lean-agent will detect the legacy paths on the next command and print exactly these `mv` commands again.

## Methodology

The agent is one half of a two-half loop: it pre-filters and rehearses; humans validate. See the design docs in [`../docs/lean-startup-agent/`](../docs/lean-startup-agent/) for the underlying Lean Startup Mode-A methodology, the v0 → v0.1.0 design notes, and the per-release roadmap.
