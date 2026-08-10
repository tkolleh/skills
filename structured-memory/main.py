import argparse
import re
import sys
from pathlib import Path

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
_NAME_RE = re.compile(r"^name:\s*(.+?)\s*$", re.MULTILINE)
_LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
_INLINE_CODE_RE = re.compile(r"`[^`\n]*`")


def _strip_inline_code(text):
    return _INLINE_CODE_RE.sub("", text)


def _parse_file(path):
    text = path.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(text)
    name = None
    malformed = False
    if match:
        name_match = _NAME_RE.search(match.group(1))
        if name_match:
            name = name_match.group(1).strip()
        else:
            malformed = True
    links = set(_LINK_RE.findall(_strip_inline_code(text)))
    return name, links, malformed


def cmd_check_links(args):
    exit_code = 0
    total_dangling = 0
    total_orphans = 0
    total_malformed = 0

    for dir_arg in args.memory_dir:
        dir_path = Path(dir_arg)
        if not dir_path.is_dir():
            print(f"error: not a directory: {dir_arg}", file=sys.stderr)
            exit_code = 2
            continue

        md_files = sorted(dir_path.glob("*.md"))
        if not md_files:
            print(f"error: no markdown files found in {dir_arg}", file=sys.stderr)
            exit_code = 2
            continue

        names_to_files = {}
        all_links = {}
        malformed_files = []

        for path in md_files:
            try:
                name, links, malformed = _parse_file(path)
            except UnicodeDecodeError as e:
                print(f"error: {path}: not valid UTF-8 ({e})", file=sys.stderr)
                continue
            if malformed:
                malformed_files.append(path)
            if name:
                names_to_files.setdefault(name, []).append(path)
            if links:
                all_links[path] = links

        print(f"# {dir_arg}")

        if malformed_files:
            print(f"  malformed frontmatter ({len(malformed_files)}):")
            for path in malformed_files:
                print(f"    - {path.name}: has a --- frontmatter block but no `name:` field")

        dangling = []
        for path, links in all_links.items():
            for target in links:
                if target not in names_to_files:
                    dangling.append((path, target))

        if dangling:
            print(f"  dangling links ({len(dangling)}):")
            for path, target in dangling:
                print(f"    - {path.name}: [[{target}]] does not match any file's `name:`")

        referenced = {target for links in all_links.values() for target in links}
        orphans = [name for name in names_to_files if name not in referenced]

        if orphans:
            print(f"  orphans, informational ({len(orphans)}):")
            for name in orphans:
                print(f"    - {name}: never referenced by [[link]] from any scanned file")

        if not (malformed_files or dangling or orphans):
            print("  clean: no dangling links, malformed frontmatter, or orphans")

        total_dangling += len(dangling)
        total_orphans += len(orphans)
        total_malformed += len(malformed_files)

    print(f"\n{total_dangling} dangling, {total_orphans} orphans, {total_malformed} malformed")

    if exit_code == 2:
        sys.exit(2)
    if total_dangling or total_malformed:
        sys.exit(1)
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Structured Memory Skill")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_links_parser = subparsers.add_parser(
        "check-links",
        help="Scan markdown memory files for dangling [[links]], malformed frontmatter identity, and orphaned files",
    )
    check_links_parser.add_argument(
        "--memory-dir",
        type=str,
        required=True,
        action="append",
        help="Directory of markdown memory files to scan (repeatable)",
    )
    check_links_parser.set_defaults(func=cmd_check_links)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
