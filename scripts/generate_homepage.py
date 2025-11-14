#!/usr/bin/env python3
"""
Generate Homepage for MkDocs Wiki

This script generates the homepage (index.md) for the Epstein Estate Documents wiki
by querying statistics from the databases and creating a formatted markdown file.

Usage:
    python generate_homepage.py

Inputs:
    - database/wiki_data.db (entity and relationship data)
    - database/documents.db (document metadata)

Outputs:
    - docs/index.md (homepage)
"""

import sqlite3
import os
from pathlib import Path


def get_db_path(db_name):
    """Get the absolute path to a database file."""
    base_dir = Path(__file__).parent.parent
    return base_dir / "database" / db_name


def get_document_stats():
    """Get document statistics from documents.db."""
    db_path = get_db_path("documents.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Total documents
    cursor.execute("SELECT COUNT(*) FROM documents")
    total_docs = cursor.fetchone()[0]

    # Total pages
    cursor.execute("SELECT SUM(page_count) FROM documents WHERE page_count IS NOT NULL")
    total_pages = cursor.fetchone()[0] or 0

    # Bates number range
    cursor.execute("SELECT MIN(bates_id), MAX(bates_id) FROM documents WHERE bates_id IS NOT NULL")
    bates_min, bates_max = cursor.fetchone()

    conn.close()

    return {
        'total_docs': total_docs,
        'total_pages': total_pages,
        'bates_min': bates_min,
        'bates_max': bates_max
    }


def get_entity_stats():
    """Get entity statistics from wiki_data.db."""
    db_path = get_db_path("wiki_data.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Total entities
    cursor.execute("SELECT COUNT(*) FROM entities")
    total_entities = cursor.fetchone()[0]

    # Entities by type
    cursor.execute("SELECT type, COUNT(*) FROM entities GROUP BY type ORDER BY COUNT(*) DESC")
    entity_types = dict(cursor.fetchall())

    # Total relationships
    cursor.execute("SELECT COUNT(*) FROM entity_cooccurrence")
    total_relationships = cursor.fetchone()[0]

    # Top mentioned people
    cursor.execute("""
        SELECT name, mention_count
        FROM entities
        WHERE type='people'
        ORDER BY mention_count DESC
        LIMIT 5
    """)
    top_people = cursor.fetchall()

    # Top mentioned organizations
    cursor.execute("""
        SELECT name, mention_count
        FROM entities
        WHERE type='organizations'
        ORDER BY mention_count DESC
        LIMIT 5
    """)
    top_orgs = cursor.fetchall()

    # Most connected entities
    cursor.execute("""
        SELECT entity1, COUNT(*) as connections
        FROM entity_cooccurrence
        GROUP BY entity1
        ORDER BY connections DESC
        LIMIT 5
    """)
    top_connected = cursor.fetchall()

    conn.close()

    return {
        'total_entities': total_entities,
        'entity_types': entity_types,
        'total_relationships': total_relationships,
        'top_people': top_people,
        'top_orgs': top_orgs,
        'top_connected': top_connected
    }


def slugify(text):
    """Convert entity name to URL-friendly slug."""
    return text.lower().replace(' ', '-').replace('/', '-').replace(':', '-')


def format_entity_link(entity_name, entity_type):
    """Format an entity name as a markdown link."""
    slug = slugify(entity_name)
    # Remove type prefix if present
    if ':' in entity_name:
        entity_name = entity_name.split(':', 1)[1]
        entity_type = entity_name.split(':', 1)[0]

    return f"[{entity_name}](entities/{entity_type}/{slug}.md)"


def generate_homepage():
    """Generate the homepage markdown file."""
    print("Gathering statistics...")
    doc_stats = get_document_stats()
    entity_stats = get_entity_stats()

    print(f"Documents: {doc_stats['total_docs']:,}")
    print(f"Pages: {doc_stats['total_pages']:,}")
    print(f"Entities: {entity_stats['total_entities']:,}")
    print(f"Relationships: {entity_stats['total_relationships']:,}")

    # Build the markdown content
    content = f"""# Epstein Estate Documents - Relationship Map

Interactive knowledge graph of **Epstein Estate Documents - Seventh Production**

## Overview

This wiki contains:

- **{doc_stats['total_docs']:,} documents** ({doc_stats['total_pages']:,} pages)
- **{entity_stats['total_entities']:,} significant entities** (people, organizations, locations, events)
- **{entity_stats['total_relationships']:,} relationships** mapping connections between entities

## Quick Navigation

### [📄 Documents](documents/)
Browse all {doc_stats['total_docs']:,} documents with full text and metadata

### [👥 People](entities/people/)
{entity_stats['entity_types'].get('people', 0):,} individuals mentioned in the documents

### [🏢 Organizations](entities/organizations/)
{entity_stats['entity_types'].get('organizations', 0):,} organizations, companies, and institutions

### [📍 Locations](entities/locations/)
{entity_stats['entity_types'].get('locations', 0):,} geographic locations and properties

### [📅 Events & Dates](entities/events/)
{entity_stats['entity_types'].get('events', 0):,} significant dates and events

### [🕸️ Relationship Graph](graph.md)
Interactive network visualization of entity connections

## Key Entities

**Most Mentioned People:**

"""

    # Add top people
    for i, (name, count) in enumerate(entity_stats['top_people'], 1):
        link = format_entity_link(name, 'people')
        content += f"{i}. {link} - {count:,} mentions\n"

    content += "\n**Most Mentioned Organizations:**\n\n"

    # Add top organizations
    for i, (name, count) in enumerate(entity_stats['top_orgs'], 1):
        link = format_entity_link(name, 'organizations')
        content += f"{i}. {link} - {count:,} mentions\n"

    content += "\n**Most Connected Entities:**\n\n"

    # Add most connected
    for i, (entity, connections) in enumerate(entity_stats['top_connected'], 1):
        # Parse entity type from prefix
        if ':' in entity:
            entity_type, entity_name = entity.split(':', 1)
        else:
            entity_type = 'people'
            entity_name = entity

        link = format_entity_link(entity, entity_type)
        content += f"{i}. {link} - {connections:,} connections\n"

    content += f"""
## Search

Use the search bar above to find entities, documents, or keywords across the entire collection.

## About This Collection

**Epstein Estate Documents - Seventh Production** contains legal documents related to the Jeffrey Epstein case, produced to House oversight committees. The collection spans multiple years and includes:

- Legal correspondence and court filings
- Email communications
- Financial documents
- Books and publications
- Government forms and disclosures

**Data Source:** House Oversight Committee
**Bates Numbering:** {doc_stats['bates_min']} - {doc_stats['bates_max']}
**Total Documents:** {doc_stats['total_docs']:,}
**Total Pages:** {doc_stats['total_pages']:,}
**Processing Date:** November 2025

## Features

This wiki provides:

- **Full-text search** across all documents
- **Entity extraction** identifying key people, organizations, locations, and dates
- **Relationship mapping** showing connections between entities
- **Interactive graph visualization** of the knowledge network
- **Document metadata** including dates, custodians, and email headers
- **Cross-references** between related documents and entities

## How to Use This Wiki

1. **Browse by Category:** Use the navigation menu to explore people, organizations, locations, or events
2. **Search:** Use the search bar to find specific terms, names, or topics
3. **Explore Relationships:** Click on entity pages to see all related entities and documents
4. **View the Graph:** Navigate to the [Relationship Graph](graph.md) for a visual network view
5. **Read Documents:** Access full document text and metadata from the [Documents](documents/) section

---

*This wiki was automatically generated from document metadata and OCR text using entity extraction and relationship analysis.*
"""

    # Write to file
    output_path = Path(__file__).parent.parent / "docs" / "index.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\n✓ Homepage generated: {output_path}")
    print(f"  - {doc_stats['total_docs']:,} documents")
    print(f"  - {entity_stats['total_entities']:,} entities")
    print(f"  - {entity_stats['total_relationships']:,} relationships")


def main():
    """Main entry point."""
    try:
        generate_homepage()
        print("\n✓ Homepage generation complete!")
    except Exception as e:
        print(f"\n✗ Error generating homepage: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
