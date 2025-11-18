#!/usr/bin/env python3
"""
Fix broken entity links in MkDocs document pages.

This script:
1. Reads the entity alias map to understand which entities were merged
2. Queries the wiki database to find canonical entity IDs
3. Scans all document markdown files
4. Finds broken entity links (links to entities that don't exist)
5. Maps them to correct canonical entities based on the database
6. Fixes the links to point to the correct entity pages

Usage:
    python fix_broken_entity_links.py [--dry-run]
"""

import os
import re
import json
import sqlite3
from pathlib import Path
from typing import Dict, Set, List, Tuple
import argparse


# Paths
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "database" / "wiki_data.db"
ALIAS_MAP_PATH = BASE_DIR / "scripts" / "entity_alias_map.json"
DOCS_DIR = BASE_DIR / "docs" / "documents"
ENTITIES_DIR = BASE_DIR / "docs" / "entities"


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


def load_alias_map() -> Dict[str, Dict[str, str]]:
    """
    Load the entity alias map and create a mapping from aliases to canonical names.

    Returns:
        Dict with structure: {
            'people': {'mr. obama': 'Barack Obama', ...},
            'organizations': {...},
            ...
        }
    """
    with open(ALIAS_MAP_PATH, 'r') as f:
        alias_data = json.load(f)

    alias_to_canonical = {
        'people': {},
        'organizations': {},
        'locations': {},
        'events': {}
    }

    for entity_type in ['people', 'organizations', 'locations', 'events']:
        if entity_type in alias_data:
            for group in alias_data[entity_type]:
                canonical = group['canonical']
                # Map canonical to itself
                alias_to_canonical[entity_type][canonical.lower()] = canonical
                # Map all aliases to canonical
                for alias in group.get('aliases', []):
                    alias_to_canonical[entity_type][alias.lower()] = canonical

    return alias_to_canonical


def get_all_entities_from_db() -> Dict[str, Tuple[str, str]]:
    """
    Get all entities from the database.

    Returns:
        Dict mapping entity_id to (name, type)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, type FROM entities")
    entities = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}

    conn.close()
    return entities


def find_canonical_entity_id(
    entity_name: str,
    entity_type: str,
    alias_map: Dict[str, Dict[str, str]],
    db_entities: Dict[str, Tuple[str, str]]
) -> str | None:
    """
    Find the canonical entity ID for a given entity name.

    Args:
        entity_name: The entity name (e.g., "Mr. Obama")
        entity_type: The entity type (e.g., "people")
        alias_map: The alias to canonical mapping
        db_entities: All entities from the database

    Returns:
        The canonical entity_id or None if not found
    """
    # Normalize whitespace (handle newlines in entity names)
    entity_name_normalized = ' '.join(entity_name.split())

    # Check alias map first
    name_lower = entity_name_normalized.lower()
    if entity_type in alias_map and name_lower in alias_map[entity_type]:
        canonical_name = alias_map[entity_type][name_lower]
        canonical_id = f"{entity_type}:{slugify(canonical_name)}"

        # Verify it exists in database
        if canonical_id in db_entities:
            return canonical_id

    # Check if the entity exists as-is in the database
    direct_id = f"{entity_type}:{slugify(entity_name_normalized)}"
    if direct_id in db_entities:
        return direct_id

    # Try fuzzy matching by checking if any entity name matches
    for entity_id, (db_name, db_type) in db_entities.items():
        if db_type == entity_type and db_name.lower() == name_lower:
            return entity_id

    return None


def extract_entity_links(content: str) -> List[Tuple[str, str, str]]:
    """
    Extract entity links from markdown content.

    Args:
        content: The markdown content

    Returns:
        List of tuples: (full_match, entity_type, entity_slug)
    """
    # Pattern: [Entity Name](../entities/{type}/{slug}.md)
    pattern = r'\[([^\]]+)\]\(\.\./entities/(people|organizations|locations|events)/([^)]+)\.md\)'
    matches = re.findall(pattern, content)

    results = []
    for match in matches:
        entity_name, entity_type, entity_slug = match
        # Reconstruct the full match for replacement
        full_match = f"[{entity_name}](../entities/{entity_type}/{entity_slug}.md)"
        results.append((full_match, entity_type, entity_slug, entity_name))

    return results


def check_entity_file_exists(entity_type: str, entity_slug: str) -> bool:
    """Check if an entity markdown file exists."""
    # Replace slashes with hyphens for file path (dates use / in ID but - in filename)
    file_slug = entity_slug.replace('/', '-')
    file_path = ENTITIES_DIR / entity_type / f"{file_slug}.md"
    return file_path.exists()


def fix_document_links(
    doc_path: Path,
    alias_map: Dict[str, Dict[str, str]],
    db_entities: Dict[str, Tuple[str, str]],
    dry_run: bool = False
) -> Tuple[int, List[str]]:
    """
    Fix broken entity links in a single document.

    Args:
        doc_path: Path to the document
        alias_map: The alias to canonical mapping
        db_entities: All entities from the database
        dry_run: If True, don't modify files

    Returns:
        Tuple of (num_fixes, list of fixes made)
    """
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    fixes_made = []

    # Extract all entity links
    entity_links = extract_entity_links(content)

    for full_match, entity_type, entity_slug, entity_name in entity_links:
        # Check if the link slug needs fixing (has slashes that should be hyphens)
        needs_fixing = False
        canonical_id = None

        # If the slug contains slashes, it needs to be fixed for proper file linking
        if '/' in entity_slug:
            needs_fixing = True
            # Try to find the entity in database
            canonical_id = find_canonical_entity_id(entity_name, entity_type, alias_map, db_entities)
        # Otherwise, check if the file exists
        elif not check_entity_file_exists(entity_type, entity_slug):
            needs_fixing = True
            # Try to find the canonical entity
            canonical_id = find_canonical_entity_id(entity_name, entity_type, alias_map, db_entities)

        if needs_fixing:

            if canonical_id:
                # Extract canonical slug from ID
                canonical_slug = canonical_id.split(':', 1)[1]
                canonical_name = db_entities[canonical_id][0]

                # Convert slug for file path (replace / with - for dates)
                canonical_file_slug = canonical_slug.replace('/', '-')

                # Create the fixed link
                new_match = f"[{entity_name}](../entities/{entity_type}/{canonical_file_slug}.md)"

                # Replace in content
                content = content.replace(full_match, new_match)

                # Normalize entity name for reporting (handle newlines)
                entity_name_display = ' '.join(entity_name.split())
                fix_info = f"{entity_slug} -> {canonical_file_slug} ({entity_name_display})"
                fixes_made.append(fix_info)

    # Write back if changes were made
    if content != original_content and not dry_run:
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(content)

    return len(fixes_made), fixes_made


def main():
    parser = argparse.ArgumentParser(description='Fix broken entity links in document pages')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be fixed without modifying files')
    args = parser.parse_args()

    print("=" * 80)
    print("FIXING BROKEN ENTITY LINKS IN MKDOCS DOCUMENT PAGES")
    print("=" * 80)
    print()

    # Load data
    print("Loading alias map...")
    alias_map = load_alias_map()
    print(f"  Loaded {sum(len(v) for v in alias_map.values())} alias mappings")

    print("\nLoading entities from database...")
    db_entities = get_all_entities_from_db()
    print(f"  Loaded {len(db_entities)} entities from database")

    # Get all document files
    print("\nScanning document files...")
    doc_files = list(DOCS_DIR.glob("*.md"))
    print(f"  Found {len(doc_files)} document files")

    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No files will be modified")

    print("\nProcessing documents...")
    print("-" * 80)

    total_fixes = 0
    docs_with_fixes = 0
    all_fixes = {}

    for doc_path in doc_files:
        num_fixes, fixes = fix_document_links(doc_path, alias_map, db_entities, dry_run=args.dry_run)

        if num_fixes > 0:
            docs_with_fixes += 1
            total_fixes += num_fixes
            all_fixes[doc_path.name] = fixes

            print(f"\n{doc_path.name}: {num_fixes} fix(es)")
            for fix in fixes:
                print(f"  - {fix}")

    # Summary
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Documents processed: {len(doc_files)}")
    print(f"Documents with fixes: {docs_with_fixes}")
    print(f"Total links fixed: {total_fixes}")

    if args.dry_run:
        print("\n⚠️  This was a dry run. Run without --dry-run to apply fixes.")
    else:
        print("\n✓ All broken entity links have been fixed!")

    # Show most common fixes
    if total_fixes > 0:
        print("\nMost common fixes:")
        fix_counts = {}
        for fixes in all_fixes.values():
            for fix in fixes:
                # Extract the slug mapping (before ->)
                slug_mapping = fix.split(' (')[0]
                fix_counts[slug_mapping] = fix_counts.get(slug_mapping, 0) + 1

        for slug_mapping, count in sorted(fix_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {count}x: {slug_mapping}")


if __name__ == '__main__':
    main()
