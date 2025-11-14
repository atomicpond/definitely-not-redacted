#!/usr/bin/env python3
"""
Generate MkDocs markdown pages for all entities in the wiki database.

This script creates individual entity pages and category index pages
for all entities (people, organizations, locations, events) found in the
wiki_data.db database.
"""

import sqlite3
import json
import os
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

# Configuration
DB_PATH = "/Users/am/Research/Epstein/epstein-wiki/database/wiki_data.db"
DOCS_DB_PATH = "/Users/am/Research/Epstein/epstein-wiki/database/documents.db"
DOCS_DIR = "/Users/am/Research/Epstein/epstein-wiki/docs"
ENTITIES_DIR = f"{DOCS_DIR}/entities"

# Entity type to directory mapping
TYPE_DIRS = {
    'people': 'people',
    'organizations': 'organizations',
    'locations': 'locations',
    'events': 'events'
}

def sanitize_filename(name: str) -> str:
    """Convert entity name to safe filename."""
    # Remove special characters, convert to lowercase, replace spaces with hyphens
    filename = name.lower()
    # Replace slashes with hyphens first
    filename = filename.replace('/', '-')
    # Remove special characters except word chars, spaces, and hyphens
    filename = re.sub(r'[^\w\s-]', '', filename)
    # Replace multiple spaces/hyphens with single hyphen
    filename = re.sub(r'[-\s]+', '-', filename)
    filename = filename.strip('-')

    # Handle excessively long filenames (max 200 chars before .md extension)
    if len(filename) > 200:
        filename = filename[:200].rstrip('-')

    # Ensure we don't have empty filename
    if not filename:
        filename = 'unnamed-entity'

    return filename

def get_entity_filename(entity_id: str, entity_name: str) -> str:
    """Generate filename from entity ID or name."""
    # Extract the suffix from entity_id (after the colon)
    if ':' in entity_id:
        filename = entity_id.split(':', 1)[1]
    else:
        filename = entity_name

    # Sanitize the filename to ensure it's filesystem-safe
    filename = sanitize_filename(filename)

    return f"{filename}.md"

def get_relative_path(from_type: str, to_type: str) -> str:
    """Get relative path from one entity type to another."""
    if from_type == to_type:
        return ""
    else:
        return f"../{TYPE_DIRS[to_type]}/"

def format_variants(variants_json: str) -> List[str]:
    """Parse and format name variants."""
    try:
        variants = json.loads(variants_json)
        return variants if isinstance(variants, list) else [variants]
    except:
        return []

def get_entity_data(conn: sqlite3.Connection) -> List[Dict]:
    """Retrieve all entity data from database."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, type, mention_count, document_count, variants
        FROM entities
        ORDER BY type, mention_count DESC
    """)

    entities = []
    for row in cursor.fetchall():
        entities.append({
            'id': row[0],
            'name': row[1],
            'type': row[2],
            'mention_count': row[3],
            'document_count': row[4],
            'variants': row[5]
        })

    return entities

def get_top_documents(conn: sqlite3.Connection, entity_id: str, limit: int = 10) -> List[Tuple[str, int]]:
    """Get top documents mentioning this entity."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT document_id, mention_count
        FROM entity_documents
        WHERE entity_id = ?
        ORDER BY mention_count DESC
        LIMIT ?
    """, (entity_id, limit))

    return cursor.fetchall()

def get_connections(conn: sqlite3.Connection, entity_id: str, limit: int = 10) -> Dict[str, List[Tuple]]:
    """Get co-occurring entities grouped by type."""
    cursor = conn.cursor()

    # Get connections where entity is entity1
    cursor.execute("""
        SELECT e.id, e.name, e.type, ec.strength
        FROM entity_cooccurrence ec
        JOIN entities e ON ec.entity2 = e.id
        WHERE ec.entity1 = ?
        ORDER BY ec.strength DESC
        LIMIT ?
    """, (entity_id, limit * 4))  # Get more to filter by type

    connections1 = cursor.fetchall()

    # Get connections where entity is entity2
    cursor.execute("""
        SELECT e.id, e.name, e.type, ec.strength
        FROM entity_cooccurrence ec
        JOIN entities e ON ec.entity1 = e.id
        WHERE ec.entity2 = ?
        ORDER BY ec.strength DESC
        LIMIT ?
    """, (entity_id, limit * 4))

    connections2 = cursor.fetchall()

    # Combine and deduplicate
    all_connections = {}
    for conn_id, name, etype, strength in connections1 + connections2:
        if conn_id not in all_connections:
            all_connections[conn_id] = (conn_id, name, etype, strength)
        else:
            # Keep higher strength
            existing = all_connections[conn_id]
            if strength > existing[3]:
                all_connections[conn_id] = (conn_id, name, etype, strength)

    # Group by type
    by_type = defaultdict(list)
    for conn_id, name, etype, strength in all_connections.values():
        by_type[etype].append((conn_id, name, etype, strength))

    # Sort each type by strength and limit
    for etype in by_type:
        by_type[etype] = sorted(by_type[etype], key=lambda x: x[3], reverse=True)[:limit]

    return dict(by_type)

def get_document_info(docs_conn: sqlite3.Connection, doc_id: str) -> Dict:
    """Get document metadata."""
    cursor = docs_conn.cursor()
    cursor.execute("""
        SELECT bates_id, email_subject, date_created
        FROM documents
        WHERE bates_id = ?
    """, (doc_id,))

    row = cursor.fetchone()
    if row:
        return {
            'bates_id': row[0],
            'subject': row[1],
            'date': row[2]
        }
    return None

def generate_entity_page(entity: Dict, conn: sqlite3.Connection, docs_conn: sqlite3.Connection) -> str:
    """Generate markdown content for an entity page."""
    name = entity['name']
    entity_type = entity['type']
    entity_id = entity['id']

    # Build markdown
    lines = [
        f"# {name}",
        "",
        f"**Type:** {entity_type.capitalize()}  ",
        f"**Total Mentions:** {entity['mention_count']:,}  ",
        f"**Documents:** {entity['document_count']:,}",
        ""
    ]

    # Name variants
    variants = format_variants(entity['variants'])
    if variants and len(variants) > 0:
        lines.extend([
            "## Name Variants",
            ""
        ])
        for variant in variants:
            lines.append(f"- {variant}")
        lines.append("")

    # Related documents
    lines.extend([
        "## Related Documents",
        ""
    ])

    top_docs = get_top_documents(conn, entity_id, limit=10)
    if top_docs:
        lines.append(f"Top {len(top_docs)} documents by mention frequency:")
        lines.append("")

        for doc_id, mention_count in top_docs:
            # Get document info if available
            doc_info = get_document_info(docs_conn, doc_id)
            if doc_info:
                subject = doc_info.get('subject', '')
                if subject and len(subject) > 60:
                    subject = subject[:57] + "..."
                doc_display = f"{doc_id}"
                if subject:
                    doc_display += f" - {subject}"
                lines.append(f"- [{doc_id}](../../documents/{doc_id}.md) - {mention_count} mention{'s' if mention_count > 1 else ''}")
            else:
                lines.append(f"- [{doc_id}](../../documents/{doc_id}.md) - {mention_count} mention{'s' if mention_count > 1 else ''}")
        lines.append("")
    else:
        lines.append("*No documents found*")
        lines.append("")

    # Connections
    connections = get_connections(conn, entity_id, limit=10)
    if connections:
        lines.extend([
            "## Connections",
            "",
            "### Most Frequently Co-occurring Entities",
            ""
        ])

        for conn_type in ['people', 'organizations', 'locations', 'events']:
            if conn_type in connections and connections[conn_type]:
                lines.append(f"**{conn_type.capitalize()}:**")
                lines.append("")

                for conn_id, conn_name, _, strength in connections[conn_type][:10]:
                    rel_path = get_relative_path(entity_type, conn_type)
                    filename = get_entity_filename(conn_id, conn_name)
                    lines.append(f"- [{conn_name}]({rel_path}{filename}) - {strength} shared document{'s' if strength > 1 else ''}")

                lines.append("")

    # Timeline placeholder
    lines.extend([
        "## Timeline",
        "",
        "*Timeline data will be available when document dates are fully processed.*",
        ""
    ])

    return "\n".join(lines)

def generate_index_page(entities: List[Dict], entity_type: str) -> str:
    """Generate index page for an entity type."""
    type_name = entity_type.capitalize()

    # Filter entities by type
    type_entities = [e for e in entities if e['type'] == entity_type]

    lines = [
        f"# {type_name}",
        "",
        f"Total {entity_type} entities: {len(type_entities):,}",
        ""
    ]

    # Most mentioned
    if type_entities:
        lines.extend([
            "## Most Mentioned",
            ""
        ])

        top_entities = sorted(type_entities, key=lambda x: x['mention_count'], reverse=True)[:50]
        for i, entity in enumerate(top_entities, 1):
            filename = get_entity_filename(entity['id'], entity['name'])
            lines.append(f"{i}. [{entity['name']}]({filename}) - {entity['mention_count']:,} mentions")

        lines.append("")

        # Alphabetical index
        lines.extend([
            "## Browse All",
            ""
        ])

        # Group by first letter
        by_letter = defaultdict(list)
        for entity in sorted(type_entities, key=lambda x: x['name'].lower()):
            first_letter = entity['name'][0].upper()
            if first_letter.isalpha():
                by_letter[first_letter].append(entity)
            else:
                by_letter['#'].append(entity)

        # Create letter navigation
        letters = sorted([k for k in by_letter.keys() if k != '#'])
        if '#' in by_letter:
            letters = ['#'] + letters

        nav_links = [f"[{letter}](#{letter.lower() if letter != '#' else 'other'})" for letter in letters]
        lines.append(" | ".join(nav_links))
        lines.append("")

        # List entities by letter
        for letter in letters:
            anchor = letter.lower() if letter != '#' else 'other'
            header = letter if letter != '#' else 'Other'
            lines.extend([
                f"### {header} {{#{anchor}}}",
                ""
            ])

            for entity in by_letter[letter]:
                filename = get_entity_filename(entity['id'], entity['name'])
                lines.append(f"- [{entity['name']}]({filename}) - {entity['mention_count']:,} mentions")

            lines.append("")

    return "\n".join(lines)

def main():
    """Main execution function."""
    print("Entity Page Generator")
    print("=" * 60)

    # Connect to databases
    print("\nConnecting to databases...")
    conn = sqlite3.connect(DB_PATH)
    docs_conn = sqlite3.connect(DOCS_DB_PATH)

    # Get all entities
    print("Loading entity data...")
    entities = get_entity_data(conn)
    print(f"Found {len(entities)} entities")

    # Count by type
    type_counts = defaultdict(int)
    for entity in entities:
        type_counts[entity['type']] += 1

    print("\nEntity counts by type:")
    for etype, count in sorted(type_counts.items()):
        print(f"  {etype}: {count:,}")

    # Generate entity pages
    print("\nGenerating entity pages...")
    pages_created = 0
    errors = []

    for i, entity in enumerate(entities, 1):
        try:
            entity_type = entity['type']
            entity_dir = os.path.join(ENTITIES_DIR, TYPE_DIRS[entity_type])

            # Ensure directory exists
            os.makedirs(entity_dir, exist_ok=True)

            # Generate filename
            filename = get_entity_filename(entity['id'], entity['name'])
            filepath = os.path.join(entity_dir, filename)

            # Generate content
            content = generate_entity_page(entity, conn, docs_conn)

            # Write file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            pages_created += 1

            # Progress indicator
            if i % 100 == 0:
                print(f"  Progress: {i}/{len(entities)} ({pages_created} pages created)")

        except Exception as e:
            error_msg = f"Error generating page for {entity['name']} ({entity['id']}): {str(e)}"
            errors.append(error_msg)
            print(f"  ERROR: {error_msg}")

    print(f"\nGenerated {pages_created} entity pages")

    # Generate index pages
    print("\nGenerating index pages...")
    index_pages_created = 0

    for entity_type, dir_name in TYPE_DIRS.items():
        try:
            index_dir = os.path.join(ENTITIES_DIR, dir_name)
            index_path = os.path.join(index_dir, "index.md")

            content = generate_index_page(entities, entity_type)

            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(content)

            index_pages_created += 1
            print(f"  Created {entity_type}/index.md")

        except Exception as e:
            error_msg = f"Error generating index for {entity_type}: {str(e)}"
            errors.append(error_msg)
            print(f"  ERROR: {error_msg}")

    print(f"\nGenerated {index_pages_created} index pages")

    # Generate summary report
    print("\nGenerating summary report...")
    report_path = os.path.join(DOCS_DIR, "entity_generation_report.txt")

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("Entity Page Generation Report\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Total entities: {len(entities):,}\n\n")

        f.write("Entities by type:\n")
        for etype, count in sorted(type_counts.items()):
            f.write(f"  {etype}: {count:,}\n")
        f.write("\n")

        f.write(f"Entity pages created: {pages_created:,}\n")
        f.write(f"Index pages created: {index_pages_created}\n\n")

        if errors:
            f.write(f"Errors encountered: {len(errors)}\n\n")
            f.write("Error details:\n")
            for error in errors:
                f.write(f"  - {error}\n")
        else:
            f.write("No errors encountered!\n")

    print(f"Summary report saved to: {report_path}")

    # Close connections
    conn.close()
    docs_conn.close()

    print("\n" + "=" * 60)
    print("Generation complete!")
    print(f"  Entity pages: {pages_created:,}")
    print(f"  Index pages: {index_pages_created}")
    if errors:
        print(f"  Errors: {len(errors)}")
    print("=" * 60)

if __name__ == "__main__":
    main()
