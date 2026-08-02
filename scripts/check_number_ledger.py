#!/usr/bin/env python3
"""Pre-commit gate: block staged manuscript prose that states a number not
present anywhere in the evidence ledger.

The ledger lives in a sibling repo (structural-vision-research), not this
one — this repo holds the manuscript, that repo holds the evidence base.
Heuristic, not a proof-checker. Only looks at manuscript prose
(manuscript/drafts/, manuscript/submission/) and only at *added* lines in
the staged diff, so editing figures/tables/generated output never triggers
it. False positives are expected for figure/table/section references and
citation years; use the escape hatches below rather than weakening the
check.

Escape hatches for a flagged line:
  - Add the number to the ledger (in structural-vision-research/evidence/)
    with a source, or
  - Mark the line with `LEDGER-EXEMPT: <reason>` (e.g. a figure/section
    number, not a factual claim) anywhere on the same line.
"""

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(
    subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True
    ).stdout.strip()
)

# Evidence ledger lives in a sibling repo, not this one.
LEDGER_REPO = REPO_ROOT.parent / "structural-vision-research"

# Only these extensions are treated as manuscript prose.
MANUSCRIPT_EXTENSIONS = {".md", ".tex"}

# Only these directories hold manuscript prose. manuscript/figures,
# manuscript/generated, manuscript/results, manuscript/tables are outputs/
# data, not prose making claims, and are excluded even though they sit
# under manuscript/.
MANUSCRIPT_DIR_PREFIXES = ["manuscript/drafts/", "manuscript/submission/"]

EXEMPT_MARKER = "LEDGER-EXEMPT:"

# Number directly preceded by one of these words is a structural reference
# (figure/table/section/equation number), not a factual claim.
STRUCTURAL_REF_RE = re.compile(
    r"(?:figure|fig\.?|table|tbl\.?|equation|eq\.?|section|sec\.?|§|chapter|appendix|item|step|phase)\s*$",
    re.IGNORECASE,
)

# A 4-digit number in a citation-year position: (Smith, 2023) / [12] / et al. 2023
CITATION_YEAR_RE = re.compile(r"(\(|,\s*|et al\.?\s+)\d{4}\)?")

NUMBER_RE = re.compile(r"\d[\d,]*\.?\d*")


def is_manuscript_file(rel_path: str) -> bool:
    if Path(rel_path).suffix not in MANUSCRIPT_EXTENSIONS:
        return False
    return any(rel_path.startswith(p) for p in MANUSCRIPT_DIR_PREFIXES)


def load_ledger_numbers(ledger_repo: Path) -> set[str]:
    evidence_dir = ledger_repo / "evidence"
    ledger_files = sorted(evidence_dir.glob("*LEDGER*.md")) + sorted(
        evidence_dir.glob("*ledger*.md")
    )
    numbers: set[str] = set()
    for ledger_file in ledger_files:
        text = ledger_file.read_text(errors="ignore")
        for match in NUMBER_RE.finditer(text):
            numbers.add(match.group().replace(",", ""))
    return numbers


def added_lines(rel_path: str) -> list[tuple[int, str]]:
    """Return (line_number, content) for lines added in the staged diff."""
    diff = subprocess.run(
        ["git", "diff", "--cached", "-U0", "--", rel_path],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=True,
    ).stdout
    result = []
    current_line = None
    for line in diff.splitlines():
        if line.startswith("@@"):
            m = re.search(r"\+(\d+)", line)
            current_line = int(m.group(1)) if m else None
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            if current_line is None:
                continue
            result.append((current_line, line[1:]))
            current_line += 1
        elif not line.startswith("-"):
            if current_line is not None:
                current_line += 1
    return result


def flagged_numbers(line: str, ledger_numbers: set[str]) -> list[str]:
    if EXEMPT_MARKER in line:
        return []
    flagged = []
    for match in NUMBER_RE.finditer(line):
        raw = match.group()
        normalized = raw.replace(",", "")
        if len(normalized.replace(".", "")) < 2:
            continue  # single digits: almost never a claim worth gating
        prefix = line[: match.start()]
        if STRUCTURAL_REF_RE.search(prefix):
            continue
        if CITATION_YEAR_RE.search(line[max(0, match.start() - 15) : match.end() + 1]):
            continue
        if normalized in ledger_numbers:
            continue
        flagged.append(raw)
    return flagged


def main() -> int:
    staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=True,
    ).stdout.splitlines()

    manuscript_files = [f for f in staged if is_manuscript_file(f)]
    if not manuscript_files:
        return 0

    if not LEDGER_REPO.is_dir():
        print(
            f"check_number_ledger: sibling repo not found at {LEDGER_REPO} — "
            "cannot verify numbers in staged manuscript files. Fix the path "
            "or bypass with --no-verify only after confirming with the project owner.",
            file=sys.stderr,
        )
        return 1

    ledger_numbers = load_ledger_numbers(LEDGER_REPO)
    if not ledger_numbers:
        print(
            f"check_number_ledger: no evidence/*LEDGER*.md found under {LEDGER_REPO} — "
            "cannot verify numbers in staged manuscript files. Fix the ledger path "
            "or bypass with --no-verify only after confirming with the project owner.",
            file=sys.stderr,
        )
        return 1

    violations: list[tuple[str, int, str]] = []
    for rel_path in manuscript_files:
        for line_no, content in added_lines(rel_path):
            for number in flagged_numbers(content, ledger_numbers):
                violations.append((rel_path, line_no, number))

    if not violations:
        return 0

    print(
        f"check_number_ledger: numbers not found in {LEDGER_REPO}/evidence/*LEDGER*.md:\n",
        file=sys.stderr,
    )
    for rel_path, line_no, number in violations:
        print(f"  {rel_path}:{line_no}: `{number}`", file=sys.stderr)
    print(
        "\nAdd each number to the ledger with a source, or mark the line with "
        f"`{EXEMPT_MARKER} <reason>` if it isn't a factual claim (figure/table/"
        "section number, citation year, etc).",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
