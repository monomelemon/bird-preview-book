#!/usr/bin/env python3
"""Normalize and audit taxonomy claims in species descriptions.

The descriptions are sourced from Wikipedia, while the structured scientific
names come from the project's current eBird/IOC-aligned species data.  This
script keeps the prose aligned without guessing disputed Chinese genus names.
"""

import argparse
import json
import re
from pathlib import Path

from text_utils import normalize_mainland_taxonomy


ROOT = Path(__file__).resolve().parents[1]
SPECIES_PATH = ROOT / "data" / "species.json"

SCIENTIFIC_NAME_RE = re.compile(
    r"(?P<prefix>学名[：:]\s*)(?P<name>[A-Z][a-z]+\s+[a-z][a-z-]+)"
)
FAMILY_GENUS_RE = re.compile(
    r"(?P<family>[\u3400-\u9fff\U00020000-\U0002ffff]{1,8}科)"
    r"[\u3400-\u9fff\U00020000-\U0002ffff]{1,8}属下?"
)


def normalize_description(species):
    description = species.get("description")
    if not description:
        return description, []

    changes = []
    normalized = normalize_mainland_taxonomy(description)
    if normalized != description:
        changes.append("mainland taxonomy wording")

    match = SCIENTIFIC_NAME_RE.search(normalized[:300])
    current_name = species.get("scientificName", "")
    if not match or not current_name or match.group("name") == current_name:
        return normalized, changes

    old_name = match.group("name")
    normalized = normalized[: match.start("name")] + current_name + normalized[match.end("name") :]
    changes.append(f"scientific name: {old_name} -> {current_name}")

    old_genus = old_name.split()[0]
    current_genus = current_name.split()[0]
    if old_genus != current_genus:
        # Wikipedia often retains the Chinese genus belonging to the old Latin
        # name. Remove that unverified assertion from the opening sentence;
        # retaining the family is safer than inventing a Chinese genus label.
        sentence_end_candidates = [
            pos for pos in (normalized.find("。"), normalized.find("\n")) if pos >= 0
        ]
        sentence_end = min(sentence_end_candidates, default=len(normalized))
        opening = normalized[:sentence_end]
        revised_opening = FAMILY_GENUS_RE.sub(r"\g<family>", opening)
        if revised_opening != opening:
            normalized = revised_opening + normalized[sentence_end:]
            changes.append("removed stale Chinese genus claim")

    return normalized, changes


def find_issues(species_rows):
    issues = []
    for species in species_rows:
        description = species.get("description", "")
        if not description:
            continue
        if "真雕属" in description or "真鵰属" in description:
            issues.append((species["birdId"], "regional genus label for Aquila"))
        if "屬" in description:
            issues.append((species["birdId"], "Traditional Chinese taxonomy suffix: 屬"))
        if "属属" in description:
            issues.append((species["birdId"], "duplicated taxonomy suffix: 属属"))
        match = SCIENTIFIC_NAME_RE.search(description[:300])
        if match and match.group("name") != species.get("scientificName"):
            issues.append(
                (
                    species["birdId"],
                    f"scientific name mismatch: {match.group('name')} != "
                    f"{species.get('scientificName')}",
                )
            )
    return issues


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check", action="store_true", help="report remaining issues without writing"
    )
    args = parser.parse_args()

    with SPECIES_PATH.open("r", encoding="utf-8") as handle:
        species_rows = json.load(handle)

    if args.check:
        issues = find_issues(species_rows)
        for bird_id, issue in issues:
            print(f"{bird_id}: {issue}")
        print(f"taxonomy description issues: {len(issues)}")
        raise SystemExit(1 if issues else 0)

    changed_species = 0
    change_count = 0
    for species in species_rows:
        normalized, changes = normalize_description(species)
        if changes:
            species["description"] = normalized
            changed_species += 1
            change_count += len(changes)
            print(f"{species['birdId']}: {'; '.join(changes)}")

    with SPECIES_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(species_rows, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    print(f"updated {changed_species} species ({change_count} changes)")


if __name__ == "__main__":
    main()
