#!/usr/bin/env python3
"""
Fix broken links in entity markdown files.

This script:
1. Scans all entity markdown files
2. Finds all markdown links
3. Checks if target files exist
4. Fixes broken links by:
   - Correcting malformed paths (e.g., ../events/1/20/2017.md -> ../events/1-20-2017.md)
   - Removing links to non-existent files (keeping the text)
   - Fixing malformed entity name slugs
5. Reports statistics on fixes made
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Set
from collections import defaultdict

# Base directory for the docs
DOCS_DIR = Path(__file__).parent.parent / "docs"
ENTITIES_DIR = DOCS_DIR / "entities"

# Statistics
stats = {
    "total_files": 0,
    "files_modified": 0,
    "total_links": 0,
    "broken_links": 0,
    "fixed_links": 0,
    "removed_links": 0,
    "fix_patterns": defaultdict(int)
}

# Cache of existing entity files for fast lookup
existing_files_cache: Set[Path] = set()


def build_file_cache():
    """Build a cache of all existing markdown files."""
    print("Building file cache...")
    for category in ["people", "organizations", "locations", "events"]:
        category_dir = ENTITIES_DIR / category
        if category_dir.exists():
            for file_path in category_dir.glob("*.md"):
                existing_files_cache.add(file_path)

    # Also cache document files
    docs_dir = DOCS_DIR / "documents"
    if docs_dir.exists():
        for file_path in docs_dir.glob("*.md"):
            existing_files_cache.add(file_path)

    print(f"Cached {len(existing_files_cache)} existing files")


def normalize_path(path: str) -> str:
    """Normalize a path for comparison."""
    return str(Path(path).resolve())


def file_exists(base_file: Path, relative_link: str) -> bool:
    """Check if a linked file exists relative to the base file."""
    try:
        # Resolve the absolute path
        target_path = (base_file.parent / relative_link).resolve()
        return target_path in existing_files_cache
    except Exception:
        return False


def fix_malformed_event_path(link: str) -> str:
    """
    Fix malformed event date paths.

    Examples:
    - ../events/1/20/2017.md -> ../events/1-20-2017.md
    - ../events/2/8/2013.md -> ../events/2-8-2013.md
    """
    # Pattern: ../events/X/Y/Z.md where X, Y, Z are numbers
    match = re.match(r'\.\./events/(\d+)/(\d+)/(\d+)\.md', link)
    if match:
        month, day, year = match.groups()
        return f"../events/{month}-{day}-{year}.md"
    return link


def fix_malformed_entity_path(link: str) -> str:
    """
    Fix malformed entity name paths.

    Examples:
    - jr-thomas/inde-xhtml.md -> jr-thomas-inde-xhtml.md
    - jr-thomasinde-xhtml.md -> jr-thomas-inde-xhtml.md (already correct format)
    """
    # Pattern: name/inde-xhtml.md -> name-inde-xhtml.md
    match = re.match(r'([a-z0-9-]+)/inde-xhtml\.md', link)
    if match:
        name = match.group(1)
        return f"{name}-inde-xhtml.md"
    return link


def fix_link(base_file: Path, link_text: str, link_url: str) -> Tuple[str, str, str]:
    """
    Attempt to fix a broken link.

    Returns: (status, fixed_url, fix_type)
    - status: "ok", "fixed", "removed"
    - fixed_url: the corrected URL (if fixed)
    - fix_type: description of the fix applied
    """
    original_url = link_url

    # Skip external links
    if link_url.startswith("http://") or link_url.startswith("https://"):
        return ("ok", link_url, "external")

    # Skip anchor links
    if link_url.startswith("#"):
        return ("ok", link_url, "anchor")

    # Try to fix malformed event paths
    if "/events/" in link_url and re.search(r'/events/\d+/\d+/\d+\.md', link_url):
        fixed_url = fix_malformed_event_path(link_url)
        if file_exists(base_file, fixed_url):
            return ("fixed", fixed_url, "event_date_path")
        link_url = fixed_url  # Try this for further fixes

    # Try to fix malformed entity paths (name/inde-xhtml.md)
    if "inde-xhtml.md" in link_url:
        fixed_url = fix_malformed_entity_path(link_url)
        if file_exists(base_file, fixed_url):
            return ("fixed", fixed_url, "entity_name_path")
        link_url = fixed_url  # Try this for further fixes

    # Check if the link exists as-is
    if file_exists(base_file, link_url):
        return ("ok", link_url, "exists")

    # Try common variations for people links
    if not link_url.startswith("../"):
        # Try adding people prefix
        if file_exists(base_file, f"../people/{link_url}"):
            return ("fixed", f"../people/{link_url}", "added_people_prefix")
        if file_exists(base_file, f"../organizations/{link_url}"):
            return ("fixed", f"../organizations/{link_url}", "added_org_prefix")
        if file_exists(base_file, f"../locations/{link_url}"):
            return ("fixed", f"../locations/{link_url}", "added_location_prefix")
        if file_exists(base_file, f"../events/{link_url}"):
            return ("fixed", f"../events/{link_url}", "added_event_prefix")

    # If nothing worked, remove the link but keep the text
    return ("removed", "", "not_found")


def process_markdown_file(file_path: Path) -> int:
    """
    Process a single markdown file to fix broken links.

    Returns: number of modifications made
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return 0

    original_content = content
    modifications = 0

    # Find all markdown links: [text](url)
    # Use a more robust pattern that handles multi-line link text
    link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'

    def replace_link(match):
        nonlocal modifications
        link_text = match.group(1)
        link_url = match.group(2)

        stats["total_links"] += 1

        status, fixed_url, fix_type = fix_link(file_path, link_text, link_url)

        if status == "ok":
            return match.group(0)  # Return unchanged
        elif status == "fixed":
            stats["broken_links"] += 1
            stats["fixed_links"] += 1
            stats["fix_patterns"][fix_type] += 1
            modifications += 1
            return f"[{link_text}]({fixed_url})"
        elif status == "removed":
            stats["broken_links"] += 1
            stats["removed_links"] += 1
            stats["fix_patterns"][fix_type] += 1
            modifications += 1
            return f"**{link_text}**"  # Keep text but remove link, make it bold

        return match.group(0)

    content = re.sub(link_pattern, replace_link, content)

    # Write back if modified
    if content != original_content:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            stats["files_modified"] += 1
            return modifications
        except Exception as e:
            print(f"Error writing {file_path}: {e}")
            return 0

    return 0


def process_all_entity_files():
    """Process all entity markdown files."""
    categories = ["people", "organizations", "locations", "events"]

    for category in categories:
        category_dir = ENTITIES_DIR / category
        if not category_dir.exists():
            print(f"Warning: {category_dir} does not exist")
            continue

        print(f"\nProcessing {category}...")
        files = list(category_dir.glob("*.md"))

        for i, file_path in enumerate(files, 1):
            stats["total_files"] += 1
            mods = process_markdown_file(file_path)

            if mods > 0:
                print(f"  [{i}/{len(files)}] {file_path.name}: {mods} fixes")

            # Progress indicator every 100 files
            if i % 100 == 0:
                print(f"  Progress: {i}/{len(files)} files processed...")


def print_statistics():
    """Print detailed statistics about the fixes."""
    print("\n" + "=" * 80)
    print("LINK FIXING STATISTICS")
    print("=" * 80)
    print(f"\nFiles:")
    print(f"  Total files scanned:     {stats['total_files']:,}")
    print(f"  Files modified:          {stats['files_modified']:,}")

    print(f"\nLinks:")
    print(f"  Total links found:       {stats['total_links']:,}")
    print(f"  Broken links found:      {stats['broken_links']:,}")
    print(f"  Links fixed:             {stats['fixed_links']:,}")
    print(f"  Links removed:           {stats['removed_links']:,}")

    if stats['fix_patterns']:
        print(f"\nFix Patterns:")
        for pattern, count in sorted(stats['fix_patterns'].items(), key=lambda x: -x[1]):
            print(f"  {pattern:30s} {count:,}")

    print("\n" + "=" * 80)


def main():
    """Main entry point."""
    print("Entity Link Fixer")
    print("=" * 80)
    print(f"Entities directory: {ENTITIES_DIR}")
    print()

    if not ENTITIES_DIR.exists():
        print(f"Error: Entities directory not found: {ENTITIES_DIR}")
        return 1

    # Build cache of existing files
    build_file_cache()

    # Process all entity files
    process_all_entity_files()

    # Print statistics
    print_statistics()

    return 0


if __name__ == "__main__":
    exit(main())
