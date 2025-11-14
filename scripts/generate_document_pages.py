#!/usr/bin/env python3
"""
Generate MkDocs markdown pages for all documents in the Epstein wiki.
Creates individual document pages and index pages organized by date, type, and custodian.
"""

import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import re
from typing import Dict, List, Tuple, Optional

# Configuration
BASE_DIR = Path("/Users/am/Research/Epstein/epstein-wiki")
DOCS_DIR = BASE_DIR / "docs" / "documents"
DATABASE_PATH = BASE_DIR / "database" / "documents.db"
WIKI_DB_PATH = BASE_DIR / "database" / "wiki_data.db"
TEXT_BASE_PATH = Path("/Users/am/Research/Epstein/Epstein Estate Documents - Seventh Production/TEXT")

# Constants
MAX_TEXT_LENGTH = 5000
BATCH_SIZE = 100


def format_file_size(size_bytes: Optional[int]) -> str:
    """Format file size in human-readable format."""
    if not size_bytes:
        return "Unknown"

    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def sanitize_filename(name: str) -> str:
    """Convert entity name to valid filename."""
    # Remove special characters, convert to lowercase
    name = re.sub(r'[^\w\s-]', '', name.lower())
    # Replace spaces and multiple dashes with single dash
    name = re.sub(r'[-\s]+', '-', name)
    return name.strip('-')


def extract_year(date_str: Optional[str]) -> Optional[str]:
    """Extract year from date string."""
    if not date_str:
        return None
    try:
        # Try parsing ISO format
        if '-' in date_str:
            return date_str.split('-')[0]
        # Try other formats
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%Y']:
            try:
                dt = datetime.strptime(date_str, fmt)
                return str(dt.year)
            except:
                continue
    except:
        pass
    return None


def get_text_content(bates_id: str, text_path: Optional[str]) -> Tuple[str, bool]:
    """
    Read text content from file.
    Returns (text_content, is_truncated)
    """
    if not text_path:
        return "", False

    # Try multiple path strategies
    paths_to_try = [
        # Strategy 1: Direct path from database
        TEXT_BASE_PATH / text_path.lstrip('\\').lstrip('/'),
        # Strategy 2: Use bates_id to find in 001 or 002 subdirs
        TEXT_BASE_PATH / "001" / f"{bates_id}.txt",
        TEXT_BASE_PATH / "002" / f"{bates_id}.txt",
    ]

    full_path = None
    for path in paths_to_try:
        if path.exists():
            full_path = path
            break

    if not full_path:
        return "", False  # Silent failure - no text available

    try:
        with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        if len(content) > MAX_TEXT_LENGTH:
            return content[:MAX_TEXT_LENGTH], True
        return content, False
    except Exception as e:
        return "", False  # Silent failure


def get_entity_mentions(doc_id: str, wiki_conn) -> Dict[str, List[Tuple[str, str, int]]]:
    """
    Get all entity mentions for a document, organized by type.
    Returns dict: {entity_type: [(entity_id, entity_name, mention_count), ...]}
    """
    cursor = wiki_conn.cursor()

    query = """
        SELECT e.id, e.name, e.type, ed.mention_count
        FROM entity_documents ed
        JOIN entities e ON ed.entity_id = e.id
        WHERE ed.document_id = ?
        ORDER BY ed.mention_count DESC
    """

    cursor.execute(query, (doc_id,))

    entities_by_type = defaultdict(list)
    for entity_id, entity_name, entity_type, mention_count in cursor.fetchall():
        entities_by_type[entity_type].append((entity_id, entity_name, mention_count))

    return dict(entities_by_type)


def highlight_entities(text: str, entities_by_type: Dict[str, List[Tuple[str, str, int]]]) -> str:
    """
    Highlight entity mentions in text with bold markdown.
    """
    if not text or not entities_by_type:
        return text

    # Collect all entity names
    entity_names = []
    for entities in entities_by_type.values():
        for _, name, _ in entities:
            if name and len(name) > 2:  # Skip very short names to avoid false positives
                entity_names.append(name)

    # Sort by length (longest first) to avoid partial matches
    entity_names.sort(key=len, reverse=True)

    # Replace each entity with bold version (case-insensitive)
    highlighted = text
    for name in entity_names[:50]:  # Limit to top 50 to avoid performance issues
        try:
            # Escape special regex characters
            escaped_name = re.escape(name)
            pattern = re.compile(f'\\b{escaped_name}\\b', re.IGNORECASE)
            highlighted = pattern.sub(f'**{name}**', highlighted)
        except re.error:
            # Skip problematic patterns
            continue

    return highlighted


def get_related_documents(doc_id: str, entities_by_type: Dict, wiki_conn, limit=5) -> List[Tuple[str, int]]:
    """
    Find related documents based on shared entities.
    Returns list of (document_id, shared_entity_count) tuples.
    """
    if not entities_by_type:
        return []

    # Get all entity IDs for this document
    entity_ids = []
    for entities in entities_by_type.values():
        for entity_id, _, _ in entities:
            entity_ids.append(entity_id)

    if not entity_ids:
        return []

    cursor = wiki_conn.cursor()

    # Find documents sharing the most entities
    placeholders = ','.join('?' * len(entity_ids))
    query = f"""
        SELECT document_id, COUNT(*) as shared_count
        FROM entity_documents
        WHERE entity_id IN ({placeholders})
        AND document_id != ?
        GROUP BY document_id
        ORDER BY shared_count DESC
        LIMIT ?
    """

    cursor.execute(query, entity_ids + [doc_id, limit])
    return cursor.fetchall()


def get_children_documents(doc_id: str, doc_conn) -> List[str]:
    """Get list of child/attachment documents."""
    cursor = doc_conn.cursor()
    cursor.execute(
        "SELECT bates_id FROM documents WHERE parent_doc_id = ? ORDER BY bates_id",
        (doc_id,)
    )
    return [row[0] for row in cursor.fetchall()]


def generate_document_page(doc: Dict, doc_conn, wiki_conn) -> str:
    """Generate markdown content for a single document page."""

    bates_id = doc['bates_id']

    # Get entity mentions
    entities_by_type = get_entity_mentions(bates_id, wiki_conn)

    # Get text content
    text_content, is_truncated = get_text_content(bates_id, doc['text_path'])

    # Highlight entities in text
    highlighted_text = highlight_entities(text_content, entities_by_type)

    # Start building markdown
    md = f"# {bates_id}\n\n"

    # Metadata section
    md += "## Document Metadata\n\n"

    if doc['bates_end'] and doc['bates_end'] != bates_id:
        md += f"**Bates Range:** {bates_id} to {doc['bates_end']}  \n"
    else:
        md += f"**Bates ID:** {bates_id}  \n"

    if doc['page_count']:
        md += f"**Pages:** {doc['page_count']}  \n"

    if doc['custodian']:
        md += f"**Custodian:** {doc['custodian']}  \n"

    if doc['date_created']:
        md += f"**Date Created:** {doc['date_created']}  \n"
    elif doc['date_sent']:
        md += f"**Date Sent:** {doc['date_sent']}  \n"
    elif doc['date_received']:
        md += f"**Date Received:** {doc['date_received']}  \n"

    if doc['original_filename']:
        md += f"**Original Filename:** {doc['original_filename']}  \n"

    if doc['file_extension']:
        md += f"**File Type:** {doc['file_extension'].upper()}  \n"

    if doc['file_size']:
        md += f"**File Size:** {format_file_size(doc['file_size'])}  \n"

    if doc['md5_hash']:
        md += f"**MD5 Hash:** `{doc['md5_hash']}`\n"

    # Email metadata if applicable
    if doc['email_subject']:
        md += f"\n**Subject:** {doc['email_subject']}  \n"
    if doc['email_from']:
        md += f"**From:** {doc['email_from']}  \n"
    if doc['email_to']:
        md += f"**To:** {doc['email_to']}  \n"
    if doc['email_cc']:
        md += f"**CC:** {doc['email_cc']}  \n"

    # Entities section
    if entities_by_type:
        md += "\n## Entities Mentioned\n\n"

        # Map entity types to display names
        type_names = {
            'people': 'People',
            'organizations': 'Organizations',
            'locations': 'Locations',
            'events': 'Events/Dates',
            'other': 'Other'
        }

        for entity_type in ['people', 'organizations', 'locations', 'events']:
            if entity_type in entities_by_type:
                md += f"### {type_names.get(entity_type, entity_type.title())}\n"

                for entity_id, entity_name, mention_count in entities_by_type[entity_type][:10]:
                    # Create entity link
                    entity_file = sanitize_filename(entity_name)
                    entity_link = f"../entities/{entity_type}/{entity_file}.md"

                    mention_text = "mention" if mention_count == 1 else "mentions"
                    md += f"- [{entity_name}]({entity_link}) - {mention_count} {mention_text}\n"

                md += "\n"

    # Document text section
    md += "## Document Text\n\n"

    if highlighted_text:
        md += "```\n"
        md += highlighted_text
        md += "\n```\n"

        if is_truncated:
            md += f"\n*[Text truncated to {MAX_TEXT_LENGTH} characters]*\n"
    else:
        md += "*[No text content available]*\n"

    md += "\n---\n\n"

    # Related documents section
    md += "## Related Documents\n\n"

    # Parent document
    if doc['parent_doc_id']:
        md += f"**Parent Document:** [{doc['parent_doc_id']}]({doc['parent_doc_id']}.md)\n\n"

    # Child documents / attachments
    children = get_children_documents(bates_id, doc_conn)
    if children:
        md += f"**Attachments ({len(children)}):**\n"
        for child_id in children[:10]:
            md += f"- [{child_id}]({child_id}.md)\n"
        if len(children) > 10:
            md += f"- *...and {len(children) - 10} more*\n"
        md += "\n"

    # Similar documents
    related = get_related_documents(bates_id, entities_by_type, wiki_conn, limit=5)
    if related:
        md += "**Similar Documents** (by shared entities):\n"
        for related_id, shared_count in related:
            md += f"- [{related_id}]({related_id}.md) - {shared_count} shared entities\n"

    return md


def generate_index_pages(doc_conn, stats: Dict):
    """Generate index pages organized by various categories."""

    cursor = doc_conn.cursor()

    # Main index page
    print("Generating main index page...")

    # Get counts and stats
    cursor.execute("SELECT COUNT(*) FROM documents")
    total_docs = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(page_count) FROM documents WHERE page_count IS NOT NULL")
    total_pages = cursor.fetchone()[0] or 0

    cursor.execute("SELECT MIN(date_created), MAX(date_created) FROM documents WHERE date_created IS NOT NULL")
    min_date, max_date = cursor.fetchone()

    # Main index
    md = "# Documents\n\n"
    md += f"**Total documents:** {total_docs:,}  \n"
    md += f"**Total pages:** {total_pages:,}  \n"
    if min_date and max_date:
        md += f"**Date range:** {min_date} to {max_date}  \n"
    md += "\n"

    md += "## Browse\n\n"
    md += "- [By Date](#by-date)\n"
    md += "- [By Type](#by-type)\n"
    md += "- [By Custodian](#by-custodian)\n"
    md += "- [Recent Documents](#recent-documents)\n"
    md += "\n---\n\n"

    # By Date
    md += "## By Date\n\n"
    cursor.execute("""
        SELECT SUBSTR(date_created, 1, 4) as year, COUNT(*) as count
        FROM documents
        WHERE date_created IS NOT NULL
        GROUP BY year
        ORDER BY year DESC
    """)

    for year, count in cursor.fetchall():
        if year and year != '':
            md += f"### {year} ({count} documents)\n\n"

            # Get sample documents from this year
            cursor.execute("""
                SELECT bates_id, original_filename, date_created
                FROM documents
                WHERE date_created LIKE ?
                ORDER BY date_created DESC
                LIMIT 10
            """, (f"{year}%",))

            for bates_id, filename, date in cursor.fetchall():
                display_name = filename if filename else bates_id
                md += f"- [{bates_id}]({bates_id}.md) - {display_name}"
                if date:
                    md += f" ({date})"
                md += "\n"

            md += "\n"

    md += "---\n\n"

    # By Type
    md += "## By Type\n\n"
    cursor.execute("""
        SELECT UPPER(file_extension) as ext, COUNT(*) as count
        FROM documents
        WHERE file_extension IS NOT NULL AND file_extension != ''
        GROUP BY ext
        ORDER BY count DESC
    """)

    for ext, count in cursor.fetchall():
        if ext:
            md += f"- **{ext}** ({count:,} documents)\n"

    md += "\n---\n\n"

    # By Custodian
    md += "## By Custodian\n\n"
    cursor.execute("""
        SELECT custodian, COUNT(*) as count
        FROM documents
        WHERE custodian IS NOT NULL AND custodian != ''
        GROUP BY custodian
        ORDER BY count DESC
    """)

    for custodian, count in cursor.fetchall():
        if custodian:
            md += f"### {custodian} ({count:,} documents)\n\n"

            # Get sample documents
            cursor.execute("""
                SELECT bates_id, original_filename, date_created
                FROM documents
                WHERE custodian = ?
                ORDER BY date_created DESC
                LIMIT 5
            """, (custodian,))

            for bates_id, filename, date in cursor.fetchall():
                display_name = filename if filename else bates_id
                md += f"- [{bates_id}]({bates_id}.md) - {display_name}\n"

            md += "\n"

    md += "---\n\n"

    # Recent documents
    md += "## Recent Documents\n\n"
    cursor.execute("""
        SELECT bates_id, original_filename, date_created, custodian
        FROM documents
        WHERE date_created IS NOT NULL
        ORDER BY date_created DESC
        LIMIT 50
    """)

    for bates_id, filename, date, custodian in cursor.fetchall():
        display_name = filename if filename else bates_id
        md += f"- [{bates_id}]({bates_id}.md) - {display_name}"
        if custodian:
            md += f" ({custodian})"
        if date:
            md += f" - {date}"
        md += "\n"

    # Write index
    index_path = DOCS_DIR / "index.md"
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(md)

    print(f"✓ Created index page: {index_path}")


def main():
    """Main execution function."""

    print("=" * 80)
    print("EPSTEIN WIKI - DOCUMENT PAGE GENERATOR")
    print("=" * 80)
    print()

    # Create output directory
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # Connect to databases
    print("Connecting to databases...")
    doc_conn = sqlite3.connect(DATABASE_PATH)
    doc_conn.row_factory = sqlite3.Row

    wiki_conn = sqlite3.connect(WIKI_DB_PATH)
    wiki_conn.row_factory = sqlite3.Row

    # Get all documents
    cursor = doc_conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM documents")
    total_docs = cursor.fetchone()[0]

    print(f"Found {total_docs:,} documents to process")
    print()

    # Statistics
    stats = {
        'total': 0,
        'success': 0,
        'errors': 0,
        'no_text': 0,
        'with_entities': 0
    }

    # Process documents in batches
    print("Generating document pages...")
    print("-" * 80)

    cursor.execute("""
        SELECT * FROM documents
        ORDER BY bates_id
    """)

    batch_num = 0
    while True:
        batch = cursor.fetchmany(BATCH_SIZE)
        if not batch:
            break

        batch_num += 1

        for row in batch:
            doc = dict(row)
            bates_id = doc['bates_id']
            stats['total'] += 1

            try:
                # Generate page content
                md_content = generate_document_page(doc, doc_conn, wiki_conn)

                # Write to file
                output_path = DOCS_DIR / f"{bates_id}.md"
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(md_content)

                stats['success'] += 1

                # Track stats
                if not doc['text_path']:
                    stats['no_text'] += 1

                # Progress update
                if stats['total'] % 100 == 0:
                    pct = (stats['total'] / total_docs) * 100
                    print(f"Progress: {stats['total']:,}/{total_docs:,} ({pct:.1f}%) - "
                          f"Last: {bates_id}")

            except Exception as e:
                print(f"ERROR processing {bates_id}: {e}")
                stats['errors'] += 1

    print()
    print("-" * 80)
    print(f"✓ Generated {stats['success']:,} document pages")
    print()

    # Generate index pages
    print("Generating index pages...")
    generate_index_pages(doc_conn, stats)
    print()

    # Close connections
    doc_conn.close()
    wiki_conn.close()

    # Print summary
    print("=" * 80)
    print("SUMMARY REPORT")
    print("=" * 80)
    print()
    print(f"Total documents processed:    {stats['total']:,}")
    print(f"Successfully generated:       {stats['success']:,}")
    print(f"Errors:                       {stats['errors']:,}")
    print(f"Documents without text:       {stats['no_text']:,}")
    print()
    print(f"Output directory: {DOCS_DIR}")
    print()

    # List sample files
    print("Sample generated files:")
    files = sorted(DOCS_DIR.glob("*.md"))[:5]
    for f in files:
        size = f.stat().st_size
        print(f"  - {f.name} ({size:,} bytes)")

    print()
    print("✓ Document page generation complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
