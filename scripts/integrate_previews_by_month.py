#!/usr/bin/env python3
"""
Integrate content previews into timeline by-month pages.

This script:
1. Loads all content preview batch files
2. Updates month timeline pages to include previews
3. Matches group IDs correctly
4. Reports statistics on integration
"""

import json
import re
import os
from pathlib import Path
from typing import Dict, Set


def load_all_previews(base_dir: Path) -> Dict[str, dict]:
    """Load and merge all content preview batch files."""
    all_previews = {}

    for batch_num in range(1, 5):
        batch_file = base_dir / f"content_previews_batch{batch_num}.json"
        if not batch_file.exists():
            print(f"Warning: {batch_file} not found")
            continue

        with open(batch_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            previews = data.get('previews', {})
            all_previews.update(previews)
            print(f"Loaded {len(previews)} previews from batch {batch_num}")

    return all_previews


def extract_group_id(line: str) -> str | None:
    """Extract group ID from a markdown link."""
    # Match patterns like: [HOUSE_OVERSIGHT_029684](../../deduplicated/group_0011.md)
    match = re.search(r'\(\.\.\/\.\.\/deduplicated\/(group_\d+)\.md\)', line)
    if match:
        return match.group(1)
    return None


def process_month_file(file_path: Path, previews: Dict[str, dict]) -> Dict[str, int]:
    """Process a single month file and add previews."""
    stats = {
        'groups_found': 0,
        'previews_added': 0,
        'previews_missing': 0
    }

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)

        # Check if this line contains a group reference
        group_id = extract_group_id(line)
        if group_id:
            stats['groups_found'] += 1

            # Check if we have a preview for this group
            if group_id in previews:
                preview_data = previews[group_id]
                preview_text = preview_data.get('preview', '')

                # Look ahead to see if preview already exists
                has_preview = False
                if i + 1 < len(lines) and '**Preview:**' in lines[i + 1]:
                    has_preview = True

                if not has_preview and preview_text:
                    # Add preview on next line
                    new_lines.append(f"\n**Preview:** {preview_text}\n")
                    stats['previews_added'] += 1
            else:
                stats['previews_missing'] += 1

        i += 1

    # Write updated content back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    return stats


def main():
    """Main function."""
    # Set up paths
    base_dir = Path(__file__).parent.parent
    output_dir = base_dir / "output"
    month_dir = base_dir / "docs" / "timeline" / "by_month"

    print("=" * 80)
    print("Content Preview Integration for Month Timeline Pages")
    print("=" * 80)
    print()

    # Load all previews
    print("Step 1: Loading content previews...")
    print("-" * 80)
    previews = load_all_previews(output_dir)
    print(f"\nTotal previews loaded: {len(previews)}")
    print()

    # Process all month files
    print("Step 2: Processing month timeline pages...")
    print("-" * 80)

    total_stats = {
        'files_processed': 0,
        'groups_found': 0,
        'previews_added': 0,
        'previews_missing': 0
    }

    month_files = sorted(month_dir.glob("*.md"))
    month_files = [f for f in month_files if f.name != 'index.md']

    for month_file in month_files:
        stats = process_month_file(month_file, previews)
        total_stats['files_processed'] += 1
        total_stats['groups_found'] += stats['groups_found']
        total_stats['previews_added'] += stats['previews_added']
        total_stats['previews_missing'] += stats['previews_missing']

        if stats['previews_added'] > 0:
            print(f"✓ {month_file.name}: {stats['previews_added']} previews added "
                  f"({stats['previews_missing']} missing)")

    print()
    print("=" * 80)
    print("Summary Statistics")
    print("=" * 80)
    print(f"Month files processed:    {total_stats['files_processed']}")
    print(f"Document groups found:    {total_stats['groups_found']}")
    print(f"Previews added:           {total_stats['previews_added']}")
    print(f"Previews missing:         {total_stats['previews_missing']}")
    print()

    if total_stats['previews_added'] > 0:
        success_rate = (total_stats['previews_added'] / total_stats['groups_found']) * 100
        print(f"Success rate: {success_rate:.1f}%")
        print()
        print("✓ Preview integration complete!")
    else:
        print("⚠ No previews were added. Check that preview files exist and contain data.")

    print()


if __name__ == "__main__":
    main()
