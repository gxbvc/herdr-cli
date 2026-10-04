# herdr-cli

Talk to herdr in workspaces and tabs. Do not pass pane ids. Do not patch herdr. Formerly `agents-cli` (that name still works as a symlink).

## Commands

```bash
herdr-cli workspaces
herdr-cli tabs --workspace admin
herdr-cli spawn research --workspace admin --cwd ~/projects/admin [--index 1]
herdr-cli start research --tab w7:t37 --kind pi
cat task.md | herdr-cli send w7:t37 --wait
herdr-cli ask research --file task.md --timeout 60000
herdr-cli read w7:t37
herdr-cli wait w7:t37

herdr-cli star w7:t37 [more...]            # adds the star emoji prefix to the label
herdr-cli unstar w7:t37                    # removes it
herdr-cli unstar --all [--workspace bailey]
herdr-cli rename w7:t37 "New label"        # keeps nothing; pass the star yourself if wanted
herdr-cli move w7:t37 --index 0            # 0 = leftmost tab in its workspace
herdr-cli move-workspace hq --index 0      # 0 = first workspace

herdr-cli status [--workspace bailey] [--stale-hours 24] [--questions] [--pretty]
```

Target is a **tab id** (`w7:t37`) or an agent **name**. `--kind` defaults to `pi`. `spawn` creates a tab (`--no-focus`) then starts the agent; `--index` moves it after start.

JSON: `{"ok":true,"data":...}` or `{"ok":false,"error":"...","code":"..."}`. `status --pretty` prints a table instead.

## status

Plain code, no LLM. For each agent tab it reads herdr and the pi session file:
`idle_hours` (session file age), `ends_with_question` (last assistant text ends with `?`),
`last_user_at`, `last_assistant_at`, `context_tokens`, `last_assistant_tail`, `starred`, `index`.
`--questions` keeps only tabs waiting on a question. `--stale-hours N` keeps tabs idle at least N hours.

## Notes

- A tab is the top-bar item in a workspace. The terminal inside it is a pane; this CLI hides that.
- Stars: the label prefix is the star emoji. pios uses the same prefix (`pios/rails/app/models/herdr/tab.rb`).
- `move` and `move-workspace` call the socket API directly (`tab.move`, `workspace.move`), since the herdr CLI has no move command.
- Prompt text is one argv, so leading `#` and `--` are safe. Prefer `--file` or stdin.
- `start` retries `agent_pane_busy` until the new tab's shell is up.
- Snapshots/restore stay in `herdr-agents-cli`.
- Manager system conventions: `~/dotfiles/docs/managers.md`.
