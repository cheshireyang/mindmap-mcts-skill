---
name: mindmap-mcts
description: Run a visible reasoning-tree workflow with lightweight MCTS for complex Codex tasks. Use when a task has multiple plausible hypotheses or designs, needs systematic debugging, requires option tradeoff exploration, involves repeated trial-and-error, or the user asks for a mindmap, reasoning tree, MCTS, visible exploration, branch evaluation, or evidence-backed problem solving.
---

# MindMap-MCTS

Use this skill to keep complex work on a visible, evidence-backed reasoning tree. The bundled CLI owns the JSON truth source, UCB selection, backpropagation, and markdown rendering; the agent owns expansion, real probes, and judgment.

## Command Prefix

Use the bundled CLI through this command prefix:

```bash
"${CODEX_HOME:-$HOME/.codex}/skills/mindmap-mcts/scripts/mindmap" --help
```

For repeated commands in one shell session, define:

```bash
alias mindmap='"${CODEX_HOME:-$HOME/.codex}/skills/mindmap-mcts/scripts/mindmap"'
```

If aliases are not preserved by the current shell call, use the explicit `"${CODEX_HOME:-$HOME/.codex}/skills/mindmap-mcts/scripts/mindmap"` form.

Never hand-edit rendered markdown as the truth source. The `.tree.json` file is the truth source; `.tree.md` is only a view.

## Startup

1. Decide whether this skill applies. Skip it for one-step commands, obvious one-file edits, or direct factual lookups.
2. If no tree exists, create one:

```bash
"${CODEX_HOME:-$HOME/.codex}/skills/mindmap-mcts/scripts/mindmap" init --title "<task title>" --out <task-name>.tree.json
```

3. If a tree exists, inspect it:

```bash
"${CODEX_HOME:-$HOME/.codex}/skills/mindmap-mcts/scripts/mindmap" show <task-name>.tree.json
```

4. Render the readable view:

```bash
"${CODEX_HOME:-$HOME/.codex}/skills/mindmap-mcts/scripts/mindmap" render <task-name>.tree.json --out <task-name>.tree.md
```

## Per-Round Loop

1. Select the next frontier:

```bash
"${CODEX_HOME:-$HOME/.codex}/skills/mindmap-mcts/scripts/mindmap" select <task-name>.tree.json
```

2. Expand the selected node with 2 or 3 child nodes. Children must be mutually exclusive, concrete, and verifiable.

```bash
"${CODEX_HOME:-$HOME/.codex}/skills/mindmap-mcts/scripts/mindmap" add <task-name>.tree.json --parent <node-id> --type hypothesis --content "<specific hypothesis>"
```

3. Evaluate each new child using the cheapest real probe available: read code, grep a symbol, run a focused test, inspect a log, or check a config.

4. Record value and evidence:

```bash
"${CODEX_HOME:-$HOME/.codex}/skills/mindmap-mcts/scripts/mindmap" eval <task-name>.tree.json --id <node-id> --value <0-to-1> --evidence "<short evidence>" --probe-type <test|grep|log|paper|code-read|user-input> --source "<source pointer>" --confidence <low|medium|high>
```

Use `--probe-type`, `--source`, and `--confidence` when a score is backed by a concrete probe. Omit them only when there is no useful structured metadata.

5. Prune disproven branches instead of deleting them:

```bash
"${CODEX_HOME:-$HOME/.codex}/skills/mindmap-mcts/scripts/mindmap" prune <task-name>.tree.json --id <node-id> --evidence "<why this branch is ruled out>" --probe-type <test|grep|log|paper|code-read|user-input> --source "<source pointer>" --confidence <low|medium|high>
```

6. Backpropagate from evaluated nodes:

```bash
"${CODEX_HOME:-$HOME/.codex}/skills/mindmap-mcts/scripts/mindmap" backprop <task-name>.tree.json --from <node-id>
```

7. Render and show the updated state:

```bash
"${CODEX_HOME:-$HOME/.codex}/skills/mindmap-mcts/scripts/mindmap" render <task-name>.tree.json --out <task-name>.tree.md
"${CODEX_HOME:-$HOME/.codex}/skills/mindmap-mcts/scripts/mindmap" render-html <task-name>.tree.json --out <task-name>.tree.html
"${CODEX_HOME:-$HOME/.codex}/skills/mindmap-mcts/scripts/mindmap" show <task-name>.tree.json
"${CODEX_HOME:-$HOME/.codex}/skills/mindmap-mcts/scripts/mindmap" path <task-name>.tree.json
"${CODEX_HOME:-$HOME/.codex}/skills/mindmap-mcts/scripts/mindmap" doctor <task-name>.tree.json
```

## Evaluation Scale

- `0.90` to `1.00`: real evidence verifies this path reaches the target.
- `0.60` to `0.80`: strong signal, still needs confirmation.
- `0.30` to `0.50`: uncertain or neutral signal.
- `0.10` to `0.20`: evidence mostly rules this out.
- `0.00`: confirmed dead branch; prune it.

Prefer real probes over model self-estimates. Evidence such as focused tests, logs, source reads, grep results, or config checks should be recorded directly on the node.

## Stop Conditions

Stop exploring and write an execution plan when one of these is true:

- A root-to-leaf path has value at least `0.85` and key nodes have real evidence.
- The iteration budget is exhausted.
- Several paths remain close in value and no cheap probe can separate them.

When multiple paths remain close, stop and ask the user to choose. Show the best path, close alternatives, and evidence for each.

## Reporting

When reporting progress, include:

- Current selected frontier.
- New child nodes and why they are distinct.
- Probe evidence for each evaluated node.
- Pruned branches and why they should not be retried.
- Updated best path.
- `doctor` output if the tree was edited by hand or imported from another run.
