# agents-cli

Talk to herdr in workspaces and tabs. Do not pass pane ids. Do not patch herdr.

## Commands

```bash
agents-cli workspaces
agents-cli tabs --workspace admin
agents-cli spawn research --workspace admin --cwd ~/projects/admin
agents-cli start research --tab w7:t37 --kind pi
cat task.md | agents-cli send w7:t37 --wait
agents-cli ask research --file task.md --timeout 60000
agents-cli read w7:t37
agents-cli wait w7:t37
```

Target is a **tab id** (`w7:t37`) or an agent **name**. `--kind` defaults to `pi`. `spawn` creates a tab (`--no-focus`) then starts the agent.

JSON: `{"ok":true,"data":...}` or `{"ok":false,"error":"...","code":"..."}`.

## Notes

- A tab is the top-bar item in a workspace. The terminal inside it is a pane; this CLI hides that.
- Prompt text is one argv, so leading `#` and `--` are safe. Prefer `--file` or stdin.
- `start` retries `agent_pane_busy` until the new tab's shell is up.
- Snapshots/restore stay in `herdr-agents-cli`.
