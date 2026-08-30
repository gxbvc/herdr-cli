# agents-cli

Wrapper around [herdr](https://herdr.dev) agent panes. Prompt text is passed as one argv element so markdown headings and `--` flags do not hit herdr's option parser. `start` retries while a new pane's shell is still booting.

Python 3 stdlib only. Requires `herdr` on PATH.

## Setup

```bash
ln -sf ~/tools/agents-cli/agents-cli ~/bin/agents-cli
```

## Usage

```bash
agents-cli list
agents-cli send w7:p1 --file report.md --wait
cat report.md | agents-cli send w7:p1
agents-cli start research --kind grok --pane w7:p2
agents-cli ask w7:p1 --file task.md --timeout 60000
```

See `AGENTS.md` for the agent-facing cheatsheet.
