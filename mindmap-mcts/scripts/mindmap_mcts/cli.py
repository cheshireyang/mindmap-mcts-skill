from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .engine import add_node, backpropagate, evaluate_node, frontier_nodes, init_tree, prune_node, select_frontier
from .model import MindMapError, load_tree, save_tree
from .render import render_html, render_markdown, render_next, render_path, render_summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mindmap", description="MindMap-MCTS tree engine")
    subcommands = parser.add_subparsers(dest="command", required=True)

    init_parser = subcommands.add_parser("init", help="create a new tree")
    init_parser.add_argument("--title", required=True)
    init_parser.add_argument("--out", required=True)
    init_parser.set_defaults(func=cmd_init)

    add_parser = subcommands.add_parser("add", help="add a child node")
    add_parser.add_argument("tree")
    add_parser.add_argument("--parent", required=True)
    add_parser.add_argument("--type", required=True)
    add_parser.add_argument("--content", required=True)
    add_parser.add_argument("--force", action="store_true")
    add_parser.set_defaults(func=cmd_add)

    eval_parser = subcommands.add_parser("eval", help="evaluate a node")
    eval_parser.add_argument("tree")
    eval_parser.add_argument("--id", required=True)
    eval_parser.add_argument("--value", required=True, type=float)
    eval_parser.add_argument("--evidence", required=True)
    eval_parser.add_argument("--probe-type", default="")
    eval_parser.add_argument("--source", default="")
    eval_parser.add_argument("--confidence", default="")
    eval_parser.add_argument("--state", choices=["frontier", "exploring", "verified", "pruned", "selected"])
    eval_parser.set_defaults(func=cmd_eval)

    prune_parser = subcommands.add_parser("prune", help="prune a node")
    prune_parser.add_argument("tree")
    prune_parser.add_argument("--id", required=True)
    prune_parser.add_argument("--evidence", required=True)
    prune_parser.add_argument("--probe-type", default="")
    prune_parser.add_argument("--source", default="")
    prune_parser.add_argument("--confidence", default="")
    prune_parser.set_defaults(func=cmd_prune)

    select_parser = subcommands.add_parser("select", help="select the next frontier")
    select_parser.add_argument("tree")
    select_parser.set_defaults(func=cmd_select)

    backprop_parser = subcommands.add_parser("backprop", help="backpropagate from a node")
    backprop_parser.add_argument("tree")
    backprop_parser.add_argument("--from", dest="from_id", required=True)
    backprop_parser.set_defaults(func=cmd_backprop)

    render_parser = subcommands.add_parser("render", help="render tree markdown")
    render_parser.add_argument("tree")
    render_parser.add_argument("--out", required=True)
    render_parser.set_defaults(func=cmd_render)

    render_html_parser = subcommands.add_parser("render-html", help="render static tree HTML")
    render_html_parser.add_argument("tree")
    render_html_parser.add_argument("--out", required=True)
    render_html_parser.set_defaults(func=cmd_render_html)

    show_parser = subcommands.add_parser("show", help="show tree summary")
    show_parser.add_argument("tree")
    show_parser.set_defaults(func=cmd_show)

    path_parser = subcommands.add_parser("path", help="show best path and evidence")
    path_parser.add_argument("tree")
    path_parser.set_defaults(func=cmd_path)

    doctor_parser = subcommands.add_parser("doctor", help="validate tree health")
    doctor_parser.add_argument("tree")
    doctor_parser.set_defaults(func=cmd_doctor)

    next_parser = subcommands.add_parser("next", help="recommend the next tree action")
    next_parser.add_argument("tree")
    next_parser.set_defaults(func=cmd_next)

    return parser


def cmd_init(args: argparse.Namespace) -> int:
    tree = init_tree(args.title)
    save_tree(args.out, tree)
    print(f"Created {args.out}")
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    tree_path = Path(args.tree)
    tree = load_tree(tree_path)
    tree, node = add_node(tree, args.parent, args.content, args.type, force=args.force)
    save_tree(tree_path, tree)
    print(f"Added {node.id}")
    return 0


def cmd_eval(args: argparse.Namespace) -> int:
    tree_path = Path(args.tree)
    tree = load_tree(tree_path)
    tree = evaluate_node(
        tree,
        args.id,
        args.value,
        args.evidence,
        state=args.state,
        probe_type=args.probe_type,
        source=args.source,
        confidence=args.confidence,
    )
    save_tree(tree_path, tree)
    print(f"Evaluated {args.id}")
    return 0


def cmd_prune(args: argparse.Namespace) -> int:
    tree_path = Path(args.tree)
    tree = load_tree(tree_path)
    tree = prune_node(
        tree,
        args.id,
        args.evidence,
        probe_type=args.probe_type,
        source=args.source,
        confidence=args.confidence,
    )
    save_tree(tree_path, tree)
    print(f"Pruned {args.id}")
    return 0


def cmd_select(args: argparse.Namespace) -> int:
    tree = load_tree(args.tree)
    node = select_frontier(tree)
    print(f"Selected {node.id}: {node.content}")
    return 0


def cmd_backprop(args: argparse.Namespace) -> int:
    tree_path = Path(args.tree)
    tree = load_tree(tree_path)
    tree = backpropagate(tree, args.from_id)
    save_tree(tree_path, tree)
    print(f"Backpropagated from {args.from_id}")
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    tree = load_tree(args.tree)
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_markdown(tree), encoding="utf-8")
    print(f"Rendered {args.out}")
    return 0


def cmd_render_html(args: argparse.Namespace) -> int:
    tree = load_tree(args.tree)
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_html(tree), encoding="utf-8")
    print(f"Rendered {args.out}")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    tree = load_tree(args.tree)
    print(render_summary(tree), end="")
    return 0


def cmd_path(args: argparse.Namespace) -> int:
    tree = load_tree(args.tree)
    print(render_path(tree), end="")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    tree = load_tree(args.tree)
    frontiers = frontier_nodes(tree)
    print("Tree OK")
    print(f"title={tree.title}")
    print(f"nodes={len(tree.nodes)}")
    print(f"frontiers={', '.join(node.id for node in frontiers) if frontiers else '(none)'}")
    return 0


def cmd_next(args: argparse.Namespace) -> int:
    tree = load_tree(args.tree)
    print(render_next(tree), end="")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except MindMapError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
