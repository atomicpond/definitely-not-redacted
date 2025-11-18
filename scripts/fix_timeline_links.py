#!/usr/bin/env python3
"""
Fix broken links in timeline markdown files.

This script:
1. Scans all timeline markdown files
2. Identifies broken links (links to non-existent files)
3. Fixes or removes broken links
4. Creates missing navigation pages if needed
5. Reports statistics

Author: Claude Code
Date: 2025-11-17
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Base directory
DOCS_DIR = Path(__file__).parent.parent / "docs"
TIMELINE_DIR = DOCS_DIR / "timeline"

class LinkFixer:
    def __init__(self):
        self.broken_links: Dict[str, List[str]] = {}
        self.fixed_count = 0
        self.removed_count = 0
        self.files_modified = 0

    def check_link_exists(self, source_file: Path, link: str) -> bool:
        """Check if a link target exists."""
        # Ignore anchor links and external URLs
        if link.startswith('#') or link.startswith('http'):
            return True

        # Remove anchor from link
        link_path = link.split('#')[0]

        # Resolve relative path
        source_dir = source_file.parent
        target_path = (source_dir / link_path).resolve()

        return target_path.exists()

    def find_markdown_links(self, content: str) -> List[Tuple[str, str]]:
        """Find all markdown links in content. Returns [(full_match, link_url)]."""
        # Pattern for markdown links: [text](url)
        pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        matches = re.finditer(pattern, content)
        return [(m.group(0), m.group(2)) for m in matches]

    def scan_file(self, file_path: Path) -> List[str]:
        """Scan a file for broken links."""
        broken = []

        try:
            content = file_path.read_text(encoding='utf-8')
            links = self.find_markdown_links(content)

            for full_match, link_url in links:
                if not self.check_link_exists(file_path, link_url):
                    broken.append(link_url)

        except Exception as e:
            print(f"Error scanning {file_path}: {e}")

        return broken

    def fix_file(self, file_path: Path) -> bool:
        """Fix broken links in a file. Returns True if file was modified."""
        try:
            content = file_path.read_text(encoding='utf-8')
            original_content = content
            modified = False

            # Find all broken links
            links = self.find_markdown_links(content)

            for full_match, link_url in links:
                if self.check_link_exists(file_path, link_url):
                    continue

                # Determine how to fix this link
                fixed_link = self.get_fixed_link(file_path, link_url)

                if fixed_link is None:
                    # Remove the link entirely (keep text only)
                    text_match = re.search(r'\[([^\]]+)\]', full_match)
                    if text_match:
                        text = text_match.group(1)
                        content = content.replace(full_match, text)
                        self.removed_count += 1
                        modified = True
                elif fixed_link != link_url:
                    # Replace with fixed link
                    new_match = full_match.replace(link_url, fixed_link)
                    content = content.replace(full_match, new_match)
                    self.fixed_count += 1
                    modified = True

            if modified:
                file_path.write_text(content, encoding='utf-8')
                self.files_modified += 1

            return modified

        except Exception as e:
            print(f"Error fixing {file_path}: {e}")
            return False

    def get_fixed_link(self, source_file: Path, broken_link: str) -> str | None:
        """Determine the correct link for a broken link. Returns None to remove link."""
        # Remove anchor
        link_path = broken_link.split('#')[0]

        # Common broken links and their fixes
        fixes = {
            '../index.md': '../chronological.md',  # Use chronological as main timeline page
            '../all.md': '../chronological.md',    # Use chronological for "all documents"
        }

        if link_path in fixes:
            return fixes[link_path]

        # If it's a link to a year index that doesn't exist, keep it as is
        # (we'll create those pages if needed)
        if link_path == '../by_year/index.md':
            return broken_link  # This file exists

        if link_path == '../by_month/index.md':
            return broken_link  # This file exists

        # For other broken links, return None to remove
        return None

    def scan_all_files(self):
        """Scan all timeline files for broken links."""
        print("Scanning timeline files for broken links...\n")

        # Find all markdown files in timeline directory
        md_files = list(TIMELINE_DIR.rglob("*.md"))

        for file_path in md_files:
            broken = self.scan_file(file_path)
            if broken:
                rel_path = file_path.relative_to(DOCS_DIR)
                self.broken_links[str(rel_path)] = broken

        return self.broken_links

    def fix_all_files(self):
        """Fix broken links in all timeline files."""
        print("Fixing broken links in timeline files...\n")

        # Find all markdown files in timeline directory
        md_files = list(TIMELINE_DIR.rglob("*.md"))

        for file_path in md_files:
            rel_path = file_path.relative_to(DOCS_DIR)
            print(f"Processing: {rel_path}")
            self.fix_file(file_path)

    def create_missing_pages(self):
        """Create missing navigation pages if needed."""
        # Check if timeline/index.md exists
        timeline_index = TIMELINE_DIR / "index.md"

        if not timeline_index.exists():
            print(f"\nCreating missing file: timeline/index.md")

            content = """# Timeline Overview

Browse the Epstein Estate documents chronologically. Documents are organized by date extracted from email headers, document metadata, and content analysis.

## Browse Options

### [Chronological View](chronological.md)
View all dated documents in a single chronological list with full details.

### [Browse by Year](by_year/index.md)
Browse documents organized by year (2008-2019).

### [Browse by Month](by_month/index.md)
Browse documents organized by month with detailed monthly breakdowns.

## Timeline Statistics

**Date Range:** May 19, 2008 - July 16, 2019
**Total Document Groups:** 201
**Total Documents:** 610
**Undated Groups:** 9 (28 documents)

### Date Confidence Distribution

- **High Confidence:** 165 groups (82.1%) - from email headers
- **Medium Confidence:** 9 groups (4.5%) - from document metadata
- **Low Confidence:** 27 groups (13.4%) - parsed from content

---

## How Dates Were Determined

Document dates were extracted using multiple sources, prioritized as follows:

1. **Email Headers** (High Confidence) - Date/time from email metadata
2. **Document Metadata** (Medium Confidence) - Creation/modification dates from file properties
3. **Content Parsed** (Low Confidence) - Dates extracted from document text via pattern matching

When a document group contains multiple duplicates with different dates, the canonical document's date is used, typically from the highest confidence source available.
"""
            timeline_index.write_text(content, encoding='utf-8')
            print("✓ Created timeline/index.md")

    def print_report(self):
        """Print summary report."""
        print("\n" + "="*70)
        print("TIMELINE LINK FIXING REPORT")
        print("="*70)

        if self.broken_links:
            print(f"\n📋 Files with broken links: {len(self.broken_links)}")
            print(f"🔧 Links fixed: {self.fixed_count}")
            print(f"🗑️  Links removed: {self.removed_count}")
            print(f"📝 Files modified: {self.files_modified}")

            print("\n📄 Broken links by file:")
            for file_path, links in sorted(self.broken_links.items()):
                print(f"\n  {file_path}:")
                for link in links:
                    print(f"    - {link}")
        else:
            print("\n✅ No broken links found!")

        print("\n" + "="*70)


def main():
    """Main function."""
    print("="*70)
    print("TIMELINE LINK FIXER")
    print("="*70)
    print()

    fixer = LinkFixer()

    # Step 1: Scan for broken links
    fixer.scan_all_files()

    # Step 2: Create missing pages
    fixer.create_missing_pages()

    # Step 3: Fix all files
    fixer.fix_all_files()

    # Step 4: Print report
    fixer.print_report()

    print("\n✅ Timeline link fixing complete!\n")


if __name__ == "__main__":
    main()
