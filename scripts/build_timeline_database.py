#!/usr/bin/env python3
"""
Build Timeline Database

This script creates a SQLite database mapping deduplicated document groups to dates.
It combines data from:
1. Deduplicated group markdown files (docs/deduplicated/group_*.md)
2. Date extraction data (output/document_dates.json)

The resulting database enables timeline-based browsing and analysis of documents.

Database: database/timeline.db
"""

import sqlite3
import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DEDUP_DIR = PROJECT_ROOT / "docs" / "deduplicated"
DATES_JSON = PROJECT_ROOT / "output" / "document_dates.json"
TIMELINE_DB = PROJECT_ROOT / "database" / "timeline.db"


def parse_group_markdown(file_path):
    """
    Parse a deduplicated group markdown file.

    Returns:
        dict: {
            'group_id': str,
            'canonical_bates': str,
            'document_count': int,
            'documents': [{'bates': str, 'pages': int, 'date': str}, ...]
        }
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract group number from filename
    group_match = re.search(r'group_(\d+)\.md', file_path.name)
    if not group_match:
        return None

    group_id = f"group_{group_match.group(1).zfill(4)}"

    # Extract canonical document (Most Complete Document)
    canonical_match = re.search(r'\*\*Most Complete Document:\*\* \[HOUSE_OVERSIGHT_(\d+)\]', content)
    if not canonical_match:
        return None

    canonical_bates = f"HOUSE_OVERSIGHT_{canonical_match.group(1)}"

    # Extract document count
    count_match = re.search(r'This group contains \*\*(\d+) related documents\*\*', content)
    document_count = int(count_match.group(1)) if count_match else 0

    # Extract all documents from the table
    documents = []
    table_pattern = r'\| \[HOUSE_OVERSIGHT_(\d+)\]\([^)]+\) \| (\d+) \| ([^|]+) \|'
    for match in re.finditer(table_pattern, content):
        bates_id = f"HOUSE_OVERSIGHT_{match.group(1)}"
        pages = int(match.group(2))
        date_str = match.group(3).strip()

        documents.append({
            'bates': bates_id,
            'pages': pages,
            'date': date_str if date_str != 'Unknown' else None
        })

    return {
        'group_id': group_id,
        'canonical_bates': canonical_bates,
        'document_count': document_count,
        'documents': documents
    }


def load_date_data(dates_json_path):
    """Load document date extraction data."""
    with open(dates_json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def find_group_date(group_data, date_data):
    """
    Find the best date for a group.

    Priority:
    1. Canonical document's date (if available)
    2. First duplicate with a date (if canonical has no date)
    3. None if no dates found

    Returns:
        dict: {
            'date': str (ISO format),
            'time': str or None,
            'source': str,
            'confidence': str,
            'from_bates': str (which document provided the date)
        } or None
    """
    canonical_bates = group_data['canonical_bates']

    # Try canonical document first
    if canonical_bates in date_data:
        date_info = date_data[canonical_bates]
        return {
            'date': date_info['date'],
            'time': date_info.get('time'),
            'source': date_info['source'],
            'confidence': date_info['confidence'],
            'from_bates': canonical_bates
        }

    # Try other documents in the group
    for doc in group_data['documents']:
        bates = doc['bates']
        if bates in date_data:
            date_info = date_data[bates]
            return {
                'date': date_info['date'],
                'time': date_info.get('time'),
                'source': date_info['source'],
                'confidence': date_info['confidence'],
                'from_bates': bates
            }

    return None


def create_timeline_database(db_path):
    """Create the timeline database schema."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Drop existing tables
    cursor.execute('DROP TABLE IF EXISTS timeline_documents')
    cursor.execute('DROP TABLE IF EXISTS timeline_groups')

    # Create timeline_groups table
    cursor.execute('''
        CREATE TABLE timeline_groups (
            group_id TEXT PRIMARY KEY,
            canonical_bates TEXT NOT NULL,
            date TEXT,
            time TEXT,
            date_source TEXT,
            date_from_bates TEXT,
            confidence TEXT,
            document_count INTEGER NOT NULL,
            year INTEGER,
            month INTEGER,
            day INTEGER
        )
    ''')

    # Create timeline_documents table
    cursor.execute('''
        CREATE TABLE timeline_documents (
            bates_id TEXT PRIMARY KEY,
            group_id TEXT NOT NULL,
            is_canonical INTEGER NOT NULL,
            date TEXT,
            time TEXT,
            date_source TEXT,
            confidence TEXT,
            FOREIGN KEY (group_id) REFERENCES timeline_groups(group_id)
        )
    ''')

    # Create indexes
    cursor.execute('CREATE INDEX idx_groups_date ON timeline_groups(date)')
    cursor.execute('CREATE INDEX idx_groups_year ON timeline_groups(year)')
    cursor.execute('CREATE INDEX idx_groups_month ON timeline_groups(month)')
    cursor.execute('CREATE INDEX idx_groups_confidence ON timeline_groups(confidence)')
    cursor.execute('CREATE INDEX idx_docs_group ON timeline_documents(group_id)')
    cursor.execute('CREATE INDEX idx_docs_date ON timeline_documents(date)')

    conn.commit()
    return conn


def parse_date_components(date_str):
    """Parse ISO date string into year, month, day components."""
    if not date_str:
        return None, None, None

    try:
        date_obj = datetime.fromisoformat(date_str)
        return date_obj.year, date_obj.month, date_obj.day
    except:
        return None, None, None


def populate_timeline_database(conn, groups_data, date_data):
    """Populate the timeline database with group and document data."""
    cursor = conn.cursor()

    groups_inserted = 0
    docs_inserted = 0

    for group_data in groups_data:
        group_id = group_data['group_id']
        canonical_bates = group_data['canonical_bates']
        document_count = group_data['document_count']

        # Find the best date for this group
        group_date_info = find_group_date(group_data, date_data)

        # Extract date components
        date_str = group_date_info['date'] if group_date_info else None
        time_str = group_date_info['time'] if group_date_info else None
        source = group_date_info['source'] if group_date_info else 'unknown'
        confidence = group_date_info['confidence'] if group_date_info else 'none'
        from_bates = group_date_info['from_bates'] if group_date_info else None

        year, month, day = parse_date_components(date_str)

        # Insert group record
        cursor.execute('''
            INSERT INTO timeline_groups
            (group_id, canonical_bates, date, time, date_source, date_from_bates,
             confidence, document_count, year, month, day)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            group_id, canonical_bates, date_str, time_str, source, from_bates,
            confidence, document_count, year, month, day
        ))
        groups_inserted += 1

        # Insert document records
        for doc in group_data['documents']:
            bates = doc['bates']
            is_canonical = 1 if bates == canonical_bates else 0

            # Get individual document date if available
            doc_date_info = date_data.get(bates)
            doc_date = doc_date_info['date'] if doc_date_info else None
            doc_time = doc_date_info.get('time') if doc_date_info else None
            doc_source = doc_date_info['source'] if doc_date_info else 'unknown'
            doc_confidence = doc_date_info['confidence'] if doc_date_info else 'none'

            cursor.execute('''
                INSERT INTO timeline_documents
                (bates_id, group_id, is_canonical, date, time, date_source, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                bates, group_id, is_canonical, doc_date, doc_time, doc_source, doc_confidence
            ))
            docs_inserted += 1

    conn.commit()
    return groups_inserted, docs_inserted


def generate_statistics(conn):
    """Generate statistics about the timeline database."""
    cursor = conn.cursor()

    stats = {}

    # Total groups and documents
    cursor.execute('SELECT COUNT(*) FROM timeline_groups')
    stats['total_groups'] = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM timeline_documents')
    stats['total_documents'] = cursor.fetchone()[0]

    # Groups by confidence level
    cursor.execute('''
        SELECT confidence, COUNT(*)
        FROM timeline_groups
        GROUP BY confidence
        ORDER BY
            CASE confidence
                WHEN 'high' THEN 1
                WHEN 'medium' THEN 2
                WHEN 'low' THEN 3
                WHEN 'none' THEN 4
                ELSE 5
            END
    ''')
    stats['by_confidence'] = dict(cursor.fetchall())

    # Groups by year
    cursor.execute('''
        SELECT year, COUNT(*)
        FROM timeline_groups
        WHERE year IS NOT NULL
        GROUP BY year
        ORDER BY year
    ''')
    stats['by_year'] = dict(cursor.fetchall())

    # Groups by source
    cursor.execute('''
        SELECT date_source, COUNT(*)
        FROM timeline_groups
        GROUP BY date_source
        ORDER BY COUNT(*) DESC
    ''')
    stats['by_source'] = dict(cursor.fetchall())

    # Date range
    cursor.execute('SELECT MIN(date), MAX(date) FROM timeline_groups WHERE date IS NOT NULL')
    min_date, max_date = cursor.fetchone()
    stats['date_range'] = {'min': min_date, 'max': max_date}

    # Groups without dates
    cursor.execute('SELECT COUNT(*) FROM timeline_groups WHERE date IS NULL')
    stats['groups_without_date'] = cursor.fetchone()[0]

    # Documents without dates
    cursor.execute('SELECT COUNT(*) FROM timeline_documents WHERE date IS NULL')
    stats['documents_without_date'] = cursor.fetchone()[0]

    # Average documents per group
    cursor.execute('SELECT AVG(document_count) FROM timeline_groups')
    stats['avg_documents_per_group'] = round(cursor.fetchone()[0], 2)

    return stats


def print_statistics(stats):
    """Print formatted statistics."""
    print("\n" + "="*80)
    print("TIMELINE DATABASE STATISTICS")
    print("="*80)

    print(f"\n📊 OVERVIEW")
    print(f"  Total Groups:              {stats['total_groups']:,}")
    print(f"  Total Documents:           {stats['total_documents']:,}")
    print(f"  Avg Documents per Group:   {stats['avg_documents_per_group']}")

    print(f"\n📅 DATE COVERAGE")
    if stats['date_range']['min'] and stats['date_range']['max']:
        print(f"  Date Range:                {stats['date_range']['min']} to {stats['date_range']['max']}")
    print(f"  Groups with Dates:         {stats['total_groups'] - stats['groups_without_date']:,}")
    print(f"  Groups without Dates:      {stats['groups_without_date']:,}")
    print(f"  Documents without Dates:   {stats['documents_without_date']:,}")

    print(f"\n🎯 CONFIDENCE LEVELS")
    for confidence, count in stats['by_confidence'].items():
        pct = (count / stats['total_groups']) * 100
        print(f"  {confidence.capitalize():12} {count:5,} ({pct:5.1f}%)")

    print(f"\n📰 DATE SOURCES")
    for source, count in stats['by_source'].items():
        pct = (count / stats['total_groups']) * 100
        print(f"  {source:20} {count:5,} ({pct:5.1f}%)")

    print(f"\n📆 GROUPS BY YEAR")
    if stats['by_year']:
        # Show top 15 years and summarize the rest
        years = list(stats['by_year'].items())
        for year, count in years[:15]:
            pct = (count / stats['total_groups']) * 100
            print(f"  {year:6} {count:5,} ({pct:5.1f}%)")

        if len(years) > 15:
            remaining = sum(count for _, count in years[15:])
            print(f"  {'Other':6} {remaining:5,} ({(remaining/stats['total_groups'])*100:5.1f}%)")

    print("\n" + "="*80)


def main():
    """Main execution function."""
    print("Building Timeline Database...")
    print(f"  Dedup Directory: {DEDUP_DIR}")
    print(f"  Dates JSON:      {DATES_JSON}")
    print(f"  Output DB:       {TIMELINE_DB}")

    # Ensure database directory exists
    TIMELINE_DB.parent.mkdir(exist_ok=True)

    # Load date data
    print("\n[1/5] Loading date extraction data...")
    date_data = load_date_data(DATES_JSON)
    print(f"  Loaded {len(date_data):,} document dates")

    # Parse all group markdown files
    print("\n[2/5] Parsing deduplicated group files...")
    group_files = sorted(DEDUP_DIR.glob("group_*.md"))
    groups_data = []

    for group_file in group_files:
        group_data = parse_group_markdown(group_file)
        if group_data:
            groups_data.append(group_data)

    print(f"  Parsed {len(groups_data):,} groups")

    # Create database
    print("\n[3/5] Creating timeline database...")
    conn = create_timeline_database(TIMELINE_DB)
    print(f"  Created database: {TIMELINE_DB}")

    # Populate database
    print("\n[4/5] Populating timeline database...")
    groups_inserted, docs_inserted = populate_timeline_database(conn, groups_data, date_data)
    print(f"  Inserted {groups_inserted:,} groups")
    print(f"  Inserted {docs_inserted:,} documents")

    # Generate statistics
    print("\n[5/5] Generating statistics...")
    stats = generate_statistics(conn)

    # Close database
    conn.close()

    # Print statistics
    print_statistics(stats)

    # Save statistics to JSON
    stats_file = PROJECT_ROOT / "output" / "timeline_stats.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    print(f"\n✅ Statistics saved to: {stats_file}")

    print(f"\n✅ Timeline database created successfully!")
    print(f"   Database file: {TIMELINE_DB}")
    print(f"   Size: {TIMELINE_DB.stat().st_size / (1024*1024):.2f} MB")


if __name__ == '__main__':
    main()
