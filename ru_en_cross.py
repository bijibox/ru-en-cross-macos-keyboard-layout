#!/usr/bin/env python3
"""Small build/install helper for the ru-en-cross keyboard layout bundle."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import List, Optional


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_BUILD_DIR = PROJECT_ROOT / "build"
ORIGINAL_BUNDLE = DEFAULT_BUILD_DIR / "original" / "ru-en-cross.bundle"
BUNDLE_NAME = "ru-en-cross.bundle"


def remove_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif path.exists() or path.is_symlink():
        path.unlink()


def build_bundle(output_dir: Path = DEFAULT_BUILD_DIR) -> Path:
    """Create the installable bundle by copying the checked-in reference."""
    output_dir = output_dir.expanduser().resolve()
    source = ORIGINAL_BUNDLE.resolve()
    target = output_dir / BUNDLE_NAME

    if not source.is_dir():
        raise FileNotFoundError(f"reference bundle not found: {source}")
    if target == source or source in target.parents:
        raise ValueError("output bundle must not overwrite the reference bundle")

    output_dir.mkdir(parents=True, exist_ok=True)
    remove_path(target)
    shutil.copytree(source, target, copy_function=shutil.copy2)
    return target


def install_bundle(output_dir: Path = DEFAULT_BUILD_DIR) -> Path:
    bundle = build_bundle(output_dir)
    install_dir = Path.home() / "Library" / "Keyboard Layouts"
    target = install_dir / BUNDLE_NAME

    install_dir.mkdir(parents=True, exist_ok=True)
    remove_path(target)
    shutil.copytree(bundle, target, copy_function=shutil.copy2)
    return target


def clean(output_dir: Path = DEFAULT_BUILD_DIR) -> Path:
    output_dir = output_dir.expanduser().resolve()
    target = output_dir / BUNDLE_NAME
    remove_path(target)
    return target


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ru_en_cross.py",
        description="Build and install the ru-en-cross macOS keyboard layout bundle.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    build = subcommands.add_parser("build", help="create build/ru-en-cross.bundle")
    build.add_argument(
        "output_dir",
        nargs="?",
        type=Path,
        default=DEFAULT_BUILD_DIR,
        help="directory for the generated bundle (default: build)",
    )

    install = subcommands.add_parser(
        "install",
        help="build and install the bundle into ~/Library/Keyboard Layouts",
    )
    install.add_argument(
        "output_dir",
        nargs="?",
        type=Path,
        default=DEFAULT_BUILD_DIR,
        help="temporary build directory (default: build)",
    )

    clean_command = subcommands.add_parser("clean", help="remove the generated bundle")
    clean_command.add_argument(
        "output_dir",
        nargs="?",
        type=Path,
        default=DEFAULT_BUILD_DIR,
        help="directory containing the generated bundle (default: build)",
    )

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = make_parser().parse_args(argv)

    try:
        if args.command == "build":
            path = build_bundle(args.output_dir)
            print(path)
        elif args.command == "install":
            path = install_bundle(args.output_dir)
            print(path)
        elif args.command == "clean":
            path = clean(args.output_dir)
            print(path)
        else:
            raise ValueError(f"unknown command: {args.command}")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
