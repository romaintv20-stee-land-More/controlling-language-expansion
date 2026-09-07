#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

UPSTREAM_URL = "https://github.com/jaredlll08/Controlling.git"
VERSION_BRANCH = re.compile(r"^\d+(?:\.\d+){1,2}$")
CANDIDATES = (
    "common/src/main/resources/assets/controlling/lang/en_us.json",
    "Common/src/main/resources/assets/controlling/lang/en_us.json",
    "src/main/resources/assets/controlling/lang/en_us.json",
    "src/main/resources/assets/controlling/lang/en_US.json",
    "src/main/resources/assets/controlling/lang/en_us.lang",
    "src/main/resources/assets/controlling/lang/en_US.lang",
)


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def parse_lang(text: str) -> dict[str, str]:
    data: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"Invalid .lang line: {raw!r}")
        key, value = line.split("=", 1)
        if key in data:
            raise ValueError(f"Duplicate .lang key: {key}")
        data[key] = value
    return data


def parse_json(text: str) -> dict[str, str]:
    def hook(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise ValueError(f"Duplicate JSON key: {key}")
            out[key] = value
        return out

    data = json.loads(text, object_pairs_hook=hook)
    if not isinstance(data, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in data.items()
    ):
        raise ValueError("Language JSON must map strings to strings")
    return data


def digest(data: dict[str, str], keys_only: bool = False) -> str:
    payload = (
        "\n".join(sorted(data))
        if keys_only
        else json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def version_key(version: str) -> tuple[int, ...]:
    return tuple(int(x) for x in version.split("."))


def branches(repo: Path) -> list[str]:
    result = git(repo, "for-each-ref", "--format=%(refname:short)", "refs/remotes/origin")
    names = []
    for ref in result.stdout.splitlines():
        if ref.startswith("origin/"):
            name = ref.removeprefix("origin/")
            if VERSION_BRANCH.fullmatch(name):
                names.append(name)
    return sorted(set(names), key=version_key)


def show(repo: Path, branch: str, path: str) -> str | None:
    result = git(repo, "show", f"origin/{branch}:{path}", check=False)
    return result.stdout if result.returncode == 0 else None


def locale_files(repo: Path, branch: str, english_path: str) -> list[str]:
    lang_dir = str(Path(english_path).parent).replace("\\", "/")
    result = git(repo, "ls-tree", "-r", "--name-only", f"origin/{branch}", "--", lang_dir)
    return sorted(
        Path(path).name
        for path in result.stdout.splitlines()
        if path.endswith((".json", ".lang"))
    )


def audit_branch(repo: Path, branch: str) -> dict | None:
    for path in CANDIDATES:
        text = show(repo, branch, path)
        if text is None:
            continue
        fmt = "lang" if path.endswith(".lang") else "json"
        data = parse_lang(text) if fmt == "lang" else parse_json(text)
        files = locale_files(repo, branch, path)
        return {
            "branch": branch,
            "english_path": path,
            "format": fmt,
            "key_count": len(data),
            "keys_sha256": digest(data, keys_only=True),
            "content_sha256": digest(data),
            "official_locale_file_count": len(files),
            "official_locale_files": files,
            "english": data,
        }
    return None


def build_report(repo: Path) -> dict:
    audited: list[dict] = []
    skipped: list[str] = []
    for branch in branches(repo):
        result = audit_branch(repo, branch)
        if result is None:
            skipped.append(branch)
        else:
            audited.append(result)

    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for item in audited:
        grouped[(item["format"], item["content_sha256"])].append(item)

    ordered_groups = sorted(
        grouped.values(),
        key=lambda group: version_key(group[0]["branch"]),
    )
    generations = []
    for index, group in enumerate(ordered_groups, start=1):
        sample = group[0]
        generations.append(
            {
                "id": f"generation_{index:02d}",
                "format": sample["format"],
                "key_count": sample["key_count"],
                "keys_sha256": sample["keys_sha256"],
                "content_sha256": sample["content_sha256"],
                "branches": [item["branch"] for item in group],
                "english": sample["english"],
            }
        )

    return {
        "upstream": UPSTREAM_URL,
        "audited_branch_count": len(audited),
        "skipped_version_branches": skipped,
        "branches": audited,
        "generations": generations,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Controlling localization branches")
    parser.add_argument("--output", default="data/generated/upstream_audit.json")
    args = parser.parse_args()
    output = Path(args.output)

    with tempfile.TemporaryDirectory(prefix="controlling-upstream-") as tmp:
        repo = Path(tmp) / "Controlling"
        subprocess.run(
            ["git", "clone", "--quiet", "--filter=blob:none", "--no-checkout", UPSTREAM_URL, str(repo)],
            check=True,
        )
        report = build_report(repo)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"Audited {report['audited_branch_count']} version branches; "
        f"found {len(report['generations'])} localization generations."
    )
    if report["skipped_version_branches"]:
        print("No English localization found for:", ", ".join(report["skipped_version_branches"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
