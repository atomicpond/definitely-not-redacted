#!/usr/bin/env python3
"""
Fix remaining broken links in the MkDocs site.

Issues to fix:
1. docs/deduplicated/navigation.md - Remove links to non-existent groups 0001, 0002, 0003
2. docs/index.md - Fix broken event entity links (wrong paths)
3. docs/search.md - Update .html links to .md (optional)
"""

import re
from pathlib import Path

# Define base path
BASE_DIR = Path("/Users/am/Research/Epstein/epstein-wiki")
DOCS_DIR = BASE_DIR / "docs"

def fix_navigation_md():
    """Fix deduplicated/navigation.md to remove broken group links."""
    nav_file = DOCS_DIR / "deduplicated" / "navigation.md"

    if not nav_file.exists():
        print(f"❌ File not found: {nav_file}")
        return False

    content = nav_file.read_text(encoding='utf-8')
    original_content = content

    # Pattern to match links to group_0001.md, group_0002.md, group_0003.md
    # Match: [Group N](group_000N.md) where N is 1, 2, or 3
    broken_groups = ['group_0001', 'group_0002', 'group_0003']

    changes_made = 0
    for group in broken_groups:
        # Count how many times this appears
        count = content.count(f"]({group}.md)")
        if count > 0:
            print(f"  Found {count} references to {group}.md")
            changes_made += count

    # Replace broken group links with a note that the group doesn't exist
    # We'll remove the link but keep the document reference
    for group_num in ['1', '2', '3']:
        pattern = rf'\[Group {group_num}\]\(group_000{group_num}\.md\)'
        replacement = f'~~Group {group_num}~~ (merged)'
        content = re.sub(pattern, replacement, content)

    if content != original_content:
        nav_file.write_text(content, encoding='utf-8')
        print(f"✅ Fixed {changes_made} broken group links in navigation.md")
        return True
    else:
        print("  No broken group links found in navigation.md")
        return False


def fix_index_md():
    """Fix docs/index.md to correct event entity links."""
    index_file = DOCS_DIR / "index.md"

    if not index_file.exists():
        print(f"❌ File not found: {index_file}")
        return False

    content = index_file.read_text(encoding='utf-8')
    original_content = content

    # Fix event links - they're in wrong paths
    # Wrong: entities/today/events-today.md
    # Right: entities/events/today.md

    link_fixes = {
        'entities/today/events-today.md': 'entities/events/today.md',
        'entities/2008/events-2008.md': 'entities/events/2008.md',
        'entities/2007/events-2007.md': 'entities/events/2007.md',
        'entities/2006/events-2006.md': 'entities/events/2006.md',
        'entities/2009/events-2009.md': 'entities/events/2009.md',
    }

    changes_made = 0
    for wrong_path, correct_path in link_fixes.items():
        if wrong_path in content:
            content = content.replace(wrong_path, correct_path)
            changes_made += 1
            print(f"  Fixed: {wrong_path} → {correct_path}")

    if content != original_content:
        index_file.write_text(content, encoding='utf-8')
        print(f"✅ Fixed {changes_made} broken event links in index.md")
        return True
    else:
        print("  No broken event links found in index.md")
        return False


def fix_search_md():
    """Fix docs/search.md to use .md links instead of .html."""
    search_file = DOCS_DIR / "search.md"

    if not search_file.exists():
        print(f"❌ File not found: {search_file}")
        return False

    content = search_file.read_text(encoding='utf-8')
    original_content = content

    # Replace .html links with appropriate markdown links or remove them
    # These are search links that won't work in markdown anyway
    # Option 1: Comment them out
    # Option 2: Replace with markdown links where possible

    changes_made = 0

    # Replace search.html links - these don't work well in MkDocs
    # Comment them out with a note
    html_search_pattern = r'\[([^\]]+)\]\(\.\./search\.html\?q=([^\)]+)\)'

    def replace_search_link(match):
        nonlocal changes_made
        changes_made += 1
        link_text = match.group(1)
        query = match.group(2).replace('+', ' ')
        # Just make it plain text with a note
        return f'{link_text} <!-- Use search bar above to search for: {query} -->'

    content = re.sub(html_search_pattern, replace_search_link, content)

    # Fix the one events link that's different
    if 'entities/events/2008.md' not in content:
        content = content.replace(
            '[2008 events](entities/events/2008.md)',
            '[2008 events](entities/events/2008.md)'
        )

    if content != original_content:
        search_file.write_text(content, encoding='utf-8')
        print(f"✅ Fixed {changes_made} HTML search links in search.md")
        return True
    else:
        print("  No HTML links found in search.md")
        return False


def main():
    """Main function to fix all broken links."""
    print("=" * 60)
    print("Fixing Remaining Broken Links")
    print("=" * 60)

    total_changes = 0

    print("\n1. Fixing deduplicated/navigation.md...")
    if fix_navigation_md():
        total_changes += 1

    print("\n2. Fixing index.md...")
    if fix_index_md():
        total_changes += 1

    print("\n3. Fixing search.md...")
    if fix_search_md():
        total_changes += 1

    print("\n" + "=" * 60)
    if total_changes > 0:
        print(f"✅ Complete! Fixed links in {total_changes} file(s)")
        print("\nRemaining manual fixes needed:")
        print("  • mkdocs.yml line 51: Change 'All Documents: documents/' to")
        print("    'All Documents: documents/index.md' if needed")
    else:
        print("ℹ️  No changes were needed")
    print("=" * 60)


if __name__ == "__main__":
    main()
