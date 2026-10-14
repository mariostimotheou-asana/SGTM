# Zoe commands — research notes

Task: identify which file(s) define **Zoe** CLI commands.

## SGTM repository (`mariostimotheou-asana/SGTM`)

A full-text search for `zoe` / `Zoe` in this checkout returned **no matches**. This repo does not define a tool named Zoe.

The closest “commands” in SGTM are setup scripts:

| File | Role |
| --- | --- |
| `scripts/setup.py` | `COMMAND_MAP` maps `state` and `secrets` to handler functions; argparse subparsers wire CLI flags. |
| `scripts/setup_sgtm_tasks_project.py` | Argparse subcommands `create` and `update` for the SGTM Asana project helper. |

## Public “Zoe” CLI (`iamnocodeveloper/zoe-cli`)

If the task refers to the open-source **Zoe** terminal coding assistant, command registration follows the layout documented in that repo’s `ARCHITECTURE.md`:

| Location | Role |
| --- | --- |
| **`src/cli/index.ts`** | Entry point: builds the Commander program, registers subcommands, and handles the default `zoe [prompt]` action. |
| **`src/cli/commands/`** | One module per subcommand (`login`, `logout`, `scan`, `doctor`, `summary`, `resume`, `models`, `use`, etc.). |

In-chat slash commands (e.g. `/model`, `/scan`) are handled in the chat flow rather than as separate Commander subcommands; see `src/cli/commands/chat.ts` and `src/ui/commands.ts` in that repository.

## Asana task comment (intended text)

> **Research:** This SGTM fork contains no “Zoe” references. If you meant the public Zoe CLI, commands are registered in `src/cli/index.ts` with implementations under `src/cli/commands/` ([zoe-cli](https://github.com/iamnocodeveloper/zoe-cli)). If you meant a different internal Zoe tool, please share the repo or doc link so we can point to the right file.
