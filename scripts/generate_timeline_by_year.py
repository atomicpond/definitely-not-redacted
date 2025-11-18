#!/usr/bin/env python3
"""
Generate year-based timeline pages from timeline database.

Creates:
- docs/timeline/by_year/YYYY.md for each year (2008-2019)
- docs/timeline/by_year/index.md for overview
- docs/timeline/by_year/undated.md for groups without dates
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime

# Paths
DB_PATH = "/Users/am/Research/Epstein/epstein-wiki/database/timeline.db"
OUTPUT_DIR = "/Users/am/Research/Epstein/epstein-wiki/docs/timeline/by_year"

# Confidence badge styles
CONFIDENCE_BADGES = {
    'high': ('success', 'High Confidence'),
    'medium': ('warning', 'Medium Confidence'),
    'low': ('info', 'Low Confidence')
}

# Date source descriptions
DATE_SOURCE_DESC = {
    'email_header': 'Email Header',
    'metadata': 'Document Metadata',
    'content_parsed': 'Parsed from Content',
    'filename': 'Filename',
    'other': 'Other Source'
}


def get_confidence_badge(confidence):
    """Generate Material admonition badge for confidence level."""
    if not confidence:
        return '!!! note "Unknown Confidence"'

    badge_type, label = CONFIDENCE_BADGES.get(confidence.lower(), ('note', 'Unknown Confidence'))
    return f'!!! {badge_type} inline end "{label}"'


def format_time(time_str):
    """Format time string for display."""
    if not time_str:
        return ""

    try:
        # Parse time and format nicely
        parts = time_str.split(':')
        if len(parts) == 3:
            h, m, s = parts
            return f"{h}:{m}:{s}"
        elif len(parts) == 2:
            h, m = parts
            return f"{h}:{m}"
    except:
        pass

    return time_str


def format_date(date_str, time_str=None):
    """Format date string for display."""
    if not date_str:
        return "Undated"

    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        formatted = date_obj.strftime('%B %d, %Y')  # e.g., "January 06, 2014"

        if time_str:
            time_formatted = format_time(time_str)
            if time_formatted:
                return f"{formatted} at {time_formatted}"

        return formatted
    except:
        return date_str


def get_duplicate_bates(conn, group_id, canonical_bates):
    """Get list of duplicate Bates IDs in a group."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT bates_id
        FROM timeline_documents
        WHERE group_id = ? AND is_canonical = 0
        ORDER BY bates_id
    """, (group_id,))

    return [row[0] for row in cursor.fetchall()]


def generate_year_page(conn, year):
    """Generate timeline page for a specific year."""
    cursor = conn.cursor()

    # Get all groups for this year
    cursor.execute("""
        SELECT
            group_id,
            canonical_bates,
            date,
            time,
            date_source,
            date_from_bates,
            confidence,
            document_count,
            month,
            day
        FROM timeline_groups
        WHERE year = ?
        ORDER BY date, time
    """, (year,))

    groups = cursor.fetchall()

    if not groups:
        return None

    # Calculate statistics
    total_groups = len(groups)
    total_docs = sum(g[7] for g in groups)

    # Count by confidence
    confidence_counts = {}
    date_source_counts = {}
    for group in groups:
        conf = group[6] or 'unknown'
        source = group[4] or 'unknown'
        confidence_counts[conf] = confidence_counts.get(conf, 0) + 1
        date_source_counts[source] = date_source_counts.get(source, 0) + 1

    # Build markdown
    md = f"""# {year} Timeline

## Overview

**Year:** {year}
**Document Groups:** {total_groups:,}
**Total Documents:** {total_docs:,}

### Date Confidence Distribution

"""

    # Add confidence distribution
    for conf in ['high', 'medium', 'low', 'unknown']:
        count = confidence_counts.get(conf, 0)
        if count > 0:
            pct = (count / total_groups) * 100
            md += f"- **{conf.title()}:** {count} groups ({pct:.1f}%)\n"

    md += "\n### Date Sources\n\n"

    # Add source distribution
    for source, count in sorted(date_source_counts.items(), key=lambda x: x[1], reverse=True):
        source_label = DATE_SOURCE_DESC.get(source, source.replace('_', ' ').title())
        pct = (count / total_groups) * 100
        md += f"- **{source_label}:** {count} groups ({pct:.1f}%)\n"

    md += "\n---\n\n## Document Groups\n\n"

    # Add each group
    current_month = None
    for group in groups:
        group_id, canonical_bates, date, time, date_source, date_from_bates, confidence, doc_count, month, day = group

        # Add month header if changed
        if month != current_month:
            current_month = month
            if month:
                month_name = datetime(year, month, 1).strftime('%B')
                md += f"\n### {month_name} {year}\n\n"

        # Format the date/time
        date_display = format_date(date, time)

        # Get duplicate Bates IDs
        duplicates = get_duplicate_bates(conn, group_id, canonical_bates)

        # Build group section
        md += f"#### {date_display}\n\n"

        # Confidence badge
        md += get_confidence_badge(confidence) + "\n\n"

        # Group info
        md += f"**Canonical Document:** [{canonical_bates}](../../documents/{canonical_bates}.md)  \n"
        md += f"**Documents in Group:** {doc_count}  \n"

        # Date source info
        source_label = DATE_SOURCE_DESC.get(date_source, date_source.replace('_', ' ').title() if date_source else 'Unknown')
        md += f"**Date Source:** {source_label}"

        if date_from_bates and date_from_bates != canonical_bates:
            md += f" ([{date_from_bates}](../../documents/{date_from_bates}.md))"

        md += "  \n\n"

        # Placeholder for content preview
        md += "!!! abstract \"Content Preview\"\n"
        md += "    *Content preview will be generated by processing agents*\n\n"

        # Duplicates list
        if duplicates:
            if len(duplicates) <= 5:
                md += "**Duplicate Documents:**\n\n"
                for dup in duplicates:
                    md += f"- [{dup}](../../documents/{dup}.md)\n"
            else:
                md += "??? info \"Duplicate Documents ({} total)\"\n\n".format(len(duplicates))
                for dup in duplicates:
                    md += f"    - [{dup}](../../documents/{dup}.md)\n"

        md += "\n---\n\n"

    return md


def generate_undated_page(conn):
    """Generate page for groups without dates."""
    cursor = conn.cursor()

    # Get all undated groups
    cursor.execute("""
        SELECT
            group_id,
            canonical_bates,
            date_source,
            date_from_bates,
            confidence,
            document_count
        FROM timeline_groups
        WHERE year IS NULL
        ORDER BY group_id
    """)

    groups = cursor.fetchall()

    if not groups:
        return None

    total_groups = len(groups)
    total_docs = sum(g[5] for g in groups)

    # Build markdown
    md = f"""# Undated Document Groups

## Overview

**Document Groups:** {total_groups:,}
**Total Documents:** {total_docs:,}

These document groups could not be assigned a specific date. They may have:

- Insufficient date information in metadata
- Contradictory date information across duplicates
- OCR issues preventing date extraction
- Missing date fields

---

## Groups

"""

    # Add each group
    for group in groups:
        group_id, canonical_bates, date_source, date_from_bates, confidence, doc_count = group

        # Get duplicate Bates IDs
        duplicates = get_duplicate_bates(conn, group_id, canonical_bates)

        # Build group section
        md += f"### Group {group_id}\n\n"

        # Group info
        md += f"**Canonical Document:** [{canonical_bates}](../../documents/{canonical_bates}.md)  \n"
        md += f"**Documents in Group:** {doc_count}  \n"

        if date_source:
            source_label = DATE_SOURCE_DESC.get(date_source, date_source.replace('_', ' ').title())
            md += f"**Date Source Attempted:** {source_label}  \n"

        md += "\n"

        # Placeholder for content preview
        md += "!!! abstract \"Content Preview\"\n"
        md += "    *Content preview will be generated by processing agents*\n\n"

        # Duplicates list
        if duplicates:
            if len(duplicates) <= 5:
                md += "**Duplicate Documents:**\n\n"
                for dup in duplicates:
                    md += f"- [{dup}](../../documents/{dup}.md)\n"
            else:
                md += "??? info \"Duplicate Documents ({} total)\"\n\n".format(len(duplicates))
                for dup in duplicates:
                    md += f"    - [{dup}](../../documents/{dup}.md)\n"

        md += "\n---\n\n"

    return md


def generate_index_page(conn):
    """Generate index page for year-based timeline."""
    cursor = conn.cursor()

    # Get year statistics
    cursor.execute("""
        SELECT
            year,
            COUNT(*) as group_count,
            SUM(document_count) as doc_count,
            MIN(date) as earliest,
            MAX(date) as latest
        FROM timeline_groups
        WHERE year IS NOT NULL
        GROUP BY year
        ORDER BY year
    """)

    year_stats = cursor.fetchall()

    # Get undated count
    cursor.execute("""
        SELECT COUNT(*), SUM(document_count)
        FROM timeline_groups
        WHERE year IS NULL
    """)
    undated_groups, undated_docs = cursor.fetchone()

    # Get overall stats
    cursor.execute("""
        SELECT
            COUNT(*) as total_groups,
            SUM(document_count) as total_docs,
            MIN(date) as earliest_date,
            MAX(date) as latest_date
        FROM timeline_groups
        WHERE year IS NOT NULL
    """)
    total_groups, total_docs, earliest_date, latest_date = cursor.fetchone()

    # Get confidence distribution
    cursor.execute("""
        SELECT confidence, COUNT(*)
        FROM timeline_groups
        WHERE year IS NOT NULL
        GROUP BY confidence
    """)
    confidence_dist = dict(cursor.fetchall())

    # Build markdown
    md = """# Timeline by Year

## Overview

This section organizes the Epstein estate documents chronologically by year, based on dates extracted from email headers, document metadata, and content analysis.

"""

    # Overall statistics
    md += f"""### Timeline Statistics

**Date Range:** {format_date(earliest_date)} - {format_date(latest_date)}
**Total Document Groups:** {total_groups:,}
**Total Documents:** {total_docs:,}
**Undated Groups:** {undated_groups:,} ({undated_docs:,} documents)

### Date Confidence Distribution

"""

    # Confidence distribution
    for conf in ['high', 'medium', 'low']:
        count = confidence_dist.get(conf, 0)
        if count > 0:
            pct = (count / total_groups) * 100
            badge_type, label = CONFIDENCE_BADGES[conf]
            md += f"- {get_confidence_badge(conf).replace('inline end ', '').strip()} **{count:,} groups ({pct:.1f}%)**\n"

    md += "\n---\n\n## Browse by Year\n\n"

    # Year links with statistics
    for year_data in year_stats:
        year, group_count, doc_count, earliest, latest = year_data

        md += f"### [{year}]({year}.md)\n\n"
        md += f"**Document Groups:** {group_count:,}  \n"
        md += f"**Total Documents:** {doc_count:,}  \n"
        md += f"**Date Range:** {format_date(earliest)} - {format_date(latest)}  \n\n"

    # Undated section
    if undated_groups > 0:
        md += f"### [Undated Groups](undated.md)\n\n"
        md += f"**Document Groups:** {undated_groups:,}  \n"
        md += f"**Total Documents:** {undated_docs:,}  \n\n"

    md += """---

## How Dates Were Determined

Document dates were extracted using multiple sources, prioritized as follows:

1. **Email Headers** (High Confidence) - Date/time from email metadata
2. **Document Metadata** (Medium Confidence) - Creation/modification dates from file properties
3. **Content Parsed** (Low Confidence) - Dates extracted from document text via pattern matching

When a document group contains multiple duplicates with different dates, the canonical document's date is used, typically from the highest confidence source available.

## Navigation Tips

- Use the year pages to browse documents chronologically
- Each group shows the canonical document and all duplicates
- Confidence badges indicate date reliability
- Content previews will be added by processing agents
- Use site search to find specific dates or documents

"""

    return md


def main():
    """Main execution function."""
    print("=" * 80)
    print("TIMELINE BY YEAR PAGE GENERATOR")
    print("=" * 80)
    print()

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    # Connect to database
    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)

    try:
        # Get available years
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT year
            FROM timeline_groups
            WHERE year IS NOT NULL
            ORDER BY year
        """)
        years = [row[0] for row in cursor.fetchall()]

        print(f"Found {len(years)} years: {min(years)}-{max(years)}")
        print()

        # Generate year pages
        print("Generating year pages...")
        stats = {
            'years_generated': 0,
            'total_groups': 0,
            'total_docs': 0
        }

        for year in years:
            print(f"  - Generating {year}.md...", end=" ")
            md_content = generate_year_page(conn, year)

            if md_content:
                output_path = os.path.join(OUTPUT_DIR, f"{year}.md")
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(md_content)

                # Count groups and docs
                cursor.execute("""
                    SELECT COUNT(*), SUM(document_count)
                    FROM timeline_groups
                    WHERE year = ?
                """, (year,))
                groups, docs = cursor.fetchone()

                stats['years_generated'] += 1
                stats['total_groups'] += groups
                stats['total_docs'] += docs

                print(f"✓ ({groups} groups, {docs} docs)")
            else:
                print("✗ (no data)")

        print()

        # Generate undated page
        print("Generating undated.md...", end=" ")
        md_content = generate_undated_page(conn)

        if md_content:
            output_path = os.path.join(OUTPUT_DIR, "undated.md")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(md_content)

            # Count groups and docs
            cursor.execute("""
                SELECT COUNT(*), SUM(document_count)
                FROM timeline_groups
                WHERE year IS NULL
            """)
            groups, docs = cursor.fetchone()

            print(f"✓ ({groups} groups, {docs} docs)")
            stats['undated_groups'] = groups
            stats['undated_docs'] = docs
        else:
            print("✗ (no data)")
            stats['undated_groups'] = 0
            stats['undated_docs'] = 0

        print()

        # Generate index page
        print("Generating index.md...", end=" ")
        md_content = generate_index_page(conn)

        if md_content:
            output_path = os.path.join(OUTPUT_DIR, "index.md")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            print("✓")
        else:
            print("✗")

        print()
        print("=" * 80)
        print("GENERATION COMPLETE")
        print("=" * 80)
        print()
        print(f"Year pages generated: {stats['years_generated']}")
        print(f"Total dated groups: {stats['total_groups']:,}")
        print(f"Total dated documents: {stats['total_docs']:,}")
        print(f"Undated groups: {stats['undated_groups']:,}")
        print(f"Undated documents: {stats['undated_docs']:,}")
        print()
        print(f"Pages created in: {OUTPUT_DIR}")
        print()

        # List generated files
        generated_files = sorted(os.listdir(OUTPUT_DIR))
        print(f"Generated files ({len(generated_files)}):")
        for filename in generated_files:
            file_path = os.path.join(OUTPUT_DIR, filename)
            file_size = os.path.getsize(file_path)
            print(f"  - {filename} ({file_size:,} bytes)")

        print()

    finally:
        conn.close()
        print("Database connection closed.")

    print()
    print("✓ Timeline by year pages generated successfully!")
    print()


if __name__ == "__main__":
    main()
