# agents-cli

Thin wrapper around `herdr agent`. Prompt text is one execve argv, never a shell string. Do not patch herdr.

## Commands

```bash
agents-cli list
agents-cli read <target> [--lines N] [--source SOURCE]
agents-cli send <target> [--file PATH] [--wait] [--timeout MS] [--until STATUS] [text...]
cat report.md | agents-cli send <target> --wait
agents-cli wait <target> [--until idle|done|blocked] [--timeout MS]
agents-cli start <name> --kind KIND --pane ID [--retries N] [--retry-delay MS]
agents-cli ask <target> --file task.md --timeout MS
```

JSON envelope: `{"ok":true,"data":...}` or `{"ok":false,"error":"...","code":"..."}`.

## Why this exists

`herdr agent prompt TARGET -- TEXT` treats TEXT as an option. `herdr agent prompt -- "$(cat report.md)"` treats a leading `#` as an option. `herdr agent start` on a new pane can return `agent_pane_busy` until the shell boots.

Use this CLI instead of building a shell string for herdr.

## Notes

- Target is a herdr agent name or pane id (`w7:p1`).
- `start` retries `agent_pane_busy` / `agent_not_ready` (default 10 x 500ms).
- `ask` is `send --wait` then `read --source recent-unwrapped`.
- Session history/restore stays in `herdr-agents-cli`.
