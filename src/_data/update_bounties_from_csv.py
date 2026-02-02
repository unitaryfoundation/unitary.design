#!/usr/bin/env python3

import argparse
import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional
from urllib.parse import urlparse


@dataclass(frozen=True)
class ParsedBounty:
    issue_num: int
    value: int
    repo_key: str
    provider: str


@dataclass(frozen=True)
class ProjectFile:
    path: Path
    title: str
    project_url: str
    repo_key: str
    id: Optional[str]

    @property
    def stem_key(self) -> str:
        return normalize_token(self.path.stem)

    @property
    def title_key(self) -> str:
        return normalize_token(self.title)

    @property
    def id_key(self) -> Optional[str]:
        return normalize_token(self.id) if self.id else None


def normalize_token(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def parse_money(amount: Optional[str]) -> Optional[int]:
    if not amount:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)", amount.replace(",", ""))
    if not match:
        return None
    as_float = float(match.group(1))
    if as_float < 0:
        return None
    return int(as_float)


def parse_repo_key_from_url(url: str) -> Optional[str]:
    parsed = urlparse(url.strip())
    host = parsed.netloc.lower()
    path = parsed.path.strip("/")

    if host.endswith("github.com"):
        parts = [p for p in path.split("/") if p]
        if len(parts) < 2:
            return None
        return f"{parts[0]}/{parts[1]}"

    if host.endswith("gitlab.com"):
        if "/-/" in path:
            return path.split("/-/", 1)[0]
        if path.endswith(".git"):
            path = path[: -len(".git")]
        return path or None

    return None


def parse_provider_from_url(url: str) -> Optional[str]:
    parsed = urlparse(url.strip())
    host = parsed.netloc.lower()
    if host.endswith("github.com"):
        return "github"
    if host.endswith("gitlab.com"):
        return "gitlab"
    return None


def parse_namespace_from_url(url: str) -> Optional[tuple[str, str]]:
    url = url.strip()
    if not url:
        return None

    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.strip("/")
    if "/-/" in path:
        path = path.split("/-/", 1)[0]

    parts = [p for p in path.split("/") if p]
    if not parts:
        return None

    if host.endswith("github.com"):
        return ("github", parts[0])
    if host.endswith("gitlab.com"):
        return ("gitlab", parts[0])
    return None


def canonical_repo_url(provider: str, repo_key: str) -> str:
    if provider == "github":
        return f"https://github.com/{repo_key}"
    if provider == "gitlab":
        return f"https://gitlab.com/{repo_key}"
    raise ValueError(f"Unknown provider: {provider}")


def parse_issue_num_from_url(url: str) -> Optional[int]:
    url = url.strip()
    match = re.search(r"/(?:issues|pull|merge_requests)/(\d+)", url)
    if match:
        return int(match.group(1))
    match = re.search(r"/-/issues/(\d+)", url)
    if match:
        return int(match.group(1))
    return None


def parse_bounty(url: Optional[str], amount: Optional[str]) -> Optional[ParsedBounty]:
    if not url:
        return None
    url = url.strip()
    if not url:
        return None

    issue_num = parse_issue_num_from_url(url)
    if issue_num is None:
        return None

    provider = parse_provider_from_url(url)
    if not provider:
        return None

    repo_key = parse_repo_key_from_url(url)
    if not repo_key:
        return None

    value = parse_money(amount)
    if value is None:
        return None

    return ParsedBounty(issue_num=issue_num, value=value, repo_key=repo_key, provider=provider)


def split_front_matter(text: str) -> tuple[list[str], list[str]]:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise ValueError("file does not start with YAML front matter delimiter '---'")

    end_idx = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_idx = idx
            break
    if end_idx is None:
        raise ValueError("file does not contain closing YAML front matter delimiter '---'")

    return lines[: end_idx + 1], lines[end_idx + 1 :]


def extract_front_matter_value(
    front_matter_lines: list[str], key: str
) -> Optional[str]:
    pattern = re.compile(rf"^{re.escape(key)}:\s*(.*?)\s*$")
    for line in front_matter_lines:
        match = pattern.match(line.rstrip("\r\n"))
        if not match:
            continue
        raw = match.group(1).strip()
        if (raw.startswith('"') and raw.endswith('"')) or (
            raw.startswith("'") and raw.endswith("'")
        ):
            raw = raw[1:-1]
        return raw.strip()
    return None


def load_project_files(projects_dir: Path) -> list[ProjectFile]:
    project_files: list[ProjectFile] = []
    for path in sorted(projects_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        front, _ = split_front_matter(text)
        # front includes the opening and closing '---' lines; metadata is between them.
        front_matter_lines = front[1:-1]

        title = extract_front_matter_value(front_matter_lines, "title") or ""
        project_url = extract_front_matter_value(front_matter_lines, "project_url") or ""
        project_id = extract_front_matter_value(front_matter_lines, "id")
        repo_key = parse_repo_key_from_url(project_url) or ""
        if not title or not project_url or not repo_key:
            # Skip malformed project files rather than crashing.
            continue
        project_files.append(
            ProjectFile(
                path=path,
                title=title,
                project_url=project_url,
                repo_key=repo_key,
                id=project_id,
            )
        )
    return project_files


def choose_project_file(
    row_project_name: str,
    row_project_repo_url: Optional[str],
    project_files: Iterable[ProjectFile],
    repo_key_to_project: dict[str, ProjectFile],
) -> Optional[ProjectFile]:
    row_repo_key = (
        parse_repo_key_from_url(row_project_repo_url) if row_project_repo_url else None
    )
    if row_repo_key:
        matched = repo_key_to_project.get(row_repo_key.lower())
        if matched:
            return matched

    row_key = normalize_token(row_project_name)
    if not row_key:
        return None

    exact_matches: list[ProjectFile] = []
    substring_matches: list[ProjectFile] = []
    for project in project_files:
        if row_key in {project.stem_key, project.title_key, project.id_key}:
            exact_matches.append(project)
            continue

        keys = {project.stem_key, project.title_key}
        if project.id_key:
            keys.add(project.id_key)
        if any(k and k in row_key for k in keys):
            substring_matches.append(project)

    if len(exact_matches) == 1:
        return exact_matches[0]
    if len(exact_matches) > 1:
        return None

    if len(substring_matches) == 1:
        return substring_matches[0]
    return None


def render_bounties_yaml(
    bounties: list[ParsedBounty], *, main_repo_key: str
) -> list[str]:
    lines: list[str] = []
    if not bounties:
        return ["bounties: []\n"]

    lines.append("bounties:\n")
    for bounty in bounties:
        lines.append(f"  - issue_num: {bounty.issue_num}\n")
        lines.append(f"    value: {bounty.value}\n")
        if bounty.repo_key.lower() != main_repo_key.lower():
            lines.append(f"    repo: {bounty.repo_key}\n")
    return lines


def update_bounties_in_markdown(
    text: str, bounties: list[ParsedBounty], *, project_url_override: Optional[str] = None
) -> str:
    front, body = split_front_matter(text)
    front_matter_lines = front[1:-1]

    project_url = extract_front_matter_value(front_matter_lines, "project_url")
    if not project_url:
        raise ValueError("project_url not found in front matter")

    effective_project_url = (project_url_override or project_url).strip()
    main_repo_key = parse_repo_key_from_url(effective_project_url)
    if not main_repo_key:
        raise ValueError(
            f"could not parse repo key from project_url: {effective_project_url}"
        )

    if project_url_override:
        updated_project_url_line = f"project_url: {effective_project_url}\n"
        replaced = False
        for idx, line in enumerate(front_matter_lines):
            if line.startswith("project_url:"):
                front_matter_lines[idx] = updated_project_url_line
                replaced = True
                break
        if not replaced:
            front_matter_lines.append(updated_project_url_line)

    bounty_block = render_bounties_yaml(bounties, main_repo_key=main_repo_key)

    start_idx = None
    for idx, line in enumerate(front_matter_lines):
        if line.rstrip("\r\n") == "bounties:":
            start_idx = idx
            break

    if start_idx is None:
        front_matter_lines.extend(bounty_block)
    else:
        # Replace existing block lines following `bounties:` until the next
        # non-indented, non-empty line (i.e., the next top-level YAML key).
        end_idx = start_idx + 1
        while end_idx < len(front_matter_lines):
            candidate = front_matter_lines[end_idx]
            if candidate.strip() == "":
                end_idx += 1
                continue
            if candidate.startswith((" ", "\t")):
                end_idx += 1
                continue
            break

        front_matter_lines[start_idx:end_idx] = bounty_block

    updated_front = ["---\n", *front_matter_lines, "---\n"]
    return "".join(updated_front + body)


def parse_csv_bounties(row: dict[str, str]) -> list[ParsedBounty]:
    bounties: list[ParsedBounty] = []
    for i in range(1, 7):
        url_col = "Bounty URL" if i == 1 else f"Bounty {i} URL"
        amt_col = "Bounty Amount" if i == 1 else f"Bounty {i} Amount"
        bounty = parse_bounty(row.get(url_col), row.get(amt_col))
        if bounty:
            bounties.append(bounty)
    return bounties


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Populate per-project `bounties:` front matter from a CSV export."
    )
    repo_root = Path(__file__).resolve().parents[2]
    parser.add_argument(
        "--csv",
        default=str(repo_root / "Bounties-Veena's view.csv"),
        help="Path to the CSV export (default: repo root CSV).",
    )
    parser.add_argument(
        "--projects-dir",
        default=str(repo_root / "src" / "projects"),
        help="Directory containing project markdown files (default: src/projects).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would change without writing files.",
    )
    parser.add_argument(
        "--sync-project-url",
        action="store_true",
        help="If the CSV project URL points to a different repo than the markdown `project_url`, update the markdown to match.",
    )
    parser.add_argument(
        "--strict-project-url-match",
        action="store_true",
        help="Fail (non-zero exit) when a CSV row does not match the markdown `project_url`.",
    )
    args = parser.parse_args(argv)

    csv_path = Path(args.csv)
    projects_dir = Path(args.projects_dir)
    if not csv_path.exists():
        print(f"CSV not found: {csv_path}", file=sys.stderr)
        return 2
    if not projects_dir.exists():
        print(f"Projects dir not found: {projects_dir}", file=sys.stderr)
        return 2

    project_files = load_project_files(projects_dir)
    repo_key_to_project = {p.repo_key.lower(): p for p in project_files}

    unmatched_rows: list[str] = []
    updated_files: list[Path] = []
    mismatched_project_urls: list[str] = []
    synced_project_urls: list[str] = []
    strict_failed = False

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_name = (row.get("Participating Project") or "").strip()
            if not row_name:
                continue

            bounties = parse_csv_bounties(row)
            if not bounties:
                continue

            project = choose_project_file(
                row_project_name=row_name,
                row_project_repo_url=(row.get("Project Repo URL") or "").strip() or None,
                project_files=project_files,
                repo_key_to_project=repo_key_to_project,
            )
            if not project:
                unmatched_rows.append(row_name)
                continue

            row_project_repo_url = (row.get("Project Repo URL") or "").strip() or None
            row_project_repo_key = (
                parse_repo_key_from_url(row_project_repo_url)
                if row_project_repo_url
                else None
            )
            row_project_provider = (
                parse_provider_from_url(row_project_repo_url)
                if row_project_repo_url
                else None
            )

            project_provider = parse_provider_from_url(project.project_url) or "unknown"
            matched = True
            if row_project_repo_key:
                matched = row_project_repo_key.lower() == project.repo_key.lower()
            elif row_project_repo_url:
                namespace = parse_namespace_from_url(row_project_repo_url)
                if namespace:
                    ns_provider, ns_value = namespace
                    matched = (
                        ns_provider == project_provider
                        and project.repo_key.split("/", 1)[0].lower() == ns_value.lower()
                    )

            project_url_override = None
            if not matched:
                mismatch_msg = (
                    f"{row_name}: CSV Project Repo URL '{row_project_repo_url}' vs {project.path} project_url '{project.project_url}'"
                )
                if args.sync_project_url and row_project_repo_key and row_project_provider:
                    project_url_override = canonical_repo_url(
                        row_project_provider, row_project_repo_key
                    )
                    synced_project_urls.append(
                        f"{row_name}: {project.path} project_url -> {project_url_override}"
                    )
                else:
                    mismatched_project_urls.append(mismatch_msg)
                    if args.strict_project_url_match:
                        strict_failed = True
                        continue

            original = project.path.read_text(encoding="utf-8")
            updated = update_bounties_in_markdown(
                original, bounties, project_url_override=project_url_override
            )
            if updated != original:
                updated_files.append(project.path)
                if not args.dry_run:
                    project.path.write_text(updated, encoding="utf-8")

    if args.dry_run:
        for path in updated_files:
            print(f"Would update: {path}")
    else:
        for path in updated_files:
            print(f"Updated: {path}")

    if unmatched_rows:
        print(
            "Unmatched CSV rows (could not map to a project markdown file):",
            file=sys.stderr,
        )
        for name in unmatched_rows:
            print(f"  - {name}", file=sys.stderr)

    if mismatched_project_urls:
        header = "Project URL mismatches (CSV vs markdown `project_url`):"
        if args.strict_project_url_match:
            header += " (strict)"
        print(header, file=sys.stderr)
        for item in mismatched_project_urls:
            print(f"  - {item}", file=sys.stderr)

    if synced_project_urls:
        print("Synced markdown `project_url` from CSV:", file=sys.stderr)
        for item in synced_project_urls:
            print(f"  - {item}", file=sys.stderr)

    if strict_failed:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
