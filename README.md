# agents-cli

Workspace and tab wrapper around [herdr](https://herdr.dev). Create a tab, launch an agent in it, send it work. Prompt text is one argv element so markdown headings and `--` are safe.

Python 3 stdlib only. Requires `herdr` on PATH.

## Setup

```bash
ln -sf ~/tools/agents-cli/agents-cli ~/bin/agents-cli
```

## Usage

```bash
agents-cli workspaces
agents-cli tabs --workspace admin
agents-cli spawn research --workspace admin --cwd ~/projects/admin
cat task.md | agents-cli send w7:t37 --wait
```

See `AGENTS.md` for the agent-facing cheatsheet.
