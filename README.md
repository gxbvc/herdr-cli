# herdr-cli

Workspace and tab wrapper around [herdr](https://herdr.dev). Create a tab, launch an agent in it, send it work. Prompt text is one argv element so markdown headings and `--` are safe.

Python 3 stdlib only. Requires `herdr` on PATH.

## Setup

```bash
ln -sf ~/tools/herdr-cli/herdr-cli ~/bin/herdr-cli
```

## Usage

```bash
herdr-cli workspaces
herdr-cli tabs --workspace admin
herdr-cli spawn research --workspace admin --cwd ~/projects/admin
cat task.md | herdr-cli send w7:t37 --wait
```

See `AGENTS.md` for the agent-facing cheatsheet.
