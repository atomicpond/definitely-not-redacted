#!/usr/bin/env python3
"""
Generate a single scrollable chronological timeline page.

This script reads the timeline database and creates a single markdown page
with all 201 dated groups organized chronologically with year/month headers.
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Database and output paths
DB_PATH = Path(__file__).parent.parent / "database" / "timeline.db"
OUTPUT_DIR = Path(__file__).parent.parent / "docs" / "timeline"
OUTPUT_FILE = OUTPUT_DIR / "chronological.md"

def get_confidence_badge(confidence):
    """Generate a colored badge for confidence level."""
    colors = {
        'high': '🟢',
        'medium': '🟡',
        'low': '🟠',
        'very_low': '🔴'
    }
    labels = {
        'high': 'High Confidence',
        'medium': 'Medium Confidence',
        'low': 'Low Confidence',
        'very_low': 'Very Low Confidence'
    }
    icon = colors.get(confidence, '⚪')
    label = labels.get(confidence, 'Unknown')
    return f"{icon} {label}"

def format_date_header(date_str):
    """Format date as readable header (e.g., 'January 15, 2015')."""
    if not date_str:
        return "Unknown Date"
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%B %d, %Y')
    except:
        return date_str

def format_month_header(year, month):
    """Format month header (e.g., 'January 2015')."""
    try:
        dt = datetime(year, month, 1)
        return dt.strftime('%B %Y')
    except:
        return f"Month {month}, {year}"

def generate_chronological_timeline():
    """Generate the single chronological timeline page."""

    print("Connecting to timeline database...")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all dated groups sorted chronologically
    print("Fetching dated timeline groups...")
    cursor.execute("""
        SELECT
            group_id,
            canonical_bates,
            date,
            time,
            date_source,
            confidence,
            document_count,
            year,
            month,
            day
        FROM timeline_groups
        WHERE date IS NOT NULL
        ORDER BY date ASC, time ASC NULLS LAST
    """)
    dated_groups = cursor.fetchall()

    # Get undated groups
    print("Fetching undated timeline groups...")
    cursor.execute("""
        SELECT
            group_id,
            canonical_bates,
            date_source,
            confidence,
            document_count
        FROM timeline_groups
        WHERE date IS NULL
        ORDER BY canonical_bates ASC
    """)
    undated_groups = cursor.fetchall()

    # Organize dated groups by year and month
    print("Organizing groups by year and month...")
    groups_by_year = defaultdict(lambda: defaultdict(list))
    years = set()

    for group in dated_groups:
        year = group['year']
        month = group['month']
        years.add(year)
        groups_by_year[year][month].append(group)

    years = sorted(years)

    print(f"Generating timeline page for {len(dated_groups)} dated groups across {len(years)} years...")

    # Start building the markdown content
    content = []

    # Header
    content.append("# Chronological Timeline")
    content.append("")
    content.append("A complete chronological view of all dated documents in the Epstein Estate collection.")
    content.append("")
    content.append(f"**Total Dated Groups:** {len(dated_groups)} | **Undated Groups:** {len(undated_groups)}")
    content.append("")

    # Quick navigation - Year links
    content.append("## Quick Navigation")
    content.append("")
    content.append("**Jump to Year:** ")
    year_links = [f"[{year}](#{year})" for year in years]
    content.append(" | ".join(year_links))
    content.append(" | [Undated](#undated-documents)")
    content.append("")
    content.append("---")
    content.append("")

    # Generate content for each year
    for year in years:
        content.append(f"## {year} {{#{year}}}")
        content.append("")

        months = sorted(groups_by_year[year].keys())

        for month in months:
            month_groups = groups_by_year[year][month]
            month_header = format_month_header(year, month)

            content.append(f"### {month_header}")
            content.append("")

            for group in month_groups:
                # Get duplicate documents for this group
                cursor.execute("""
                    SELECT bates_id, date, time, date_source
                    FROM timeline_documents
                    WHERE group_id = ? AND is_canonical = 0
                    ORDER BY bates_id
                """, (group['group_id'],))
                duplicates = cursor.fetchall()

                # Group header
                date_header = format_date_header(group['date'])
                if group['time']:
                    date_header += f" at {group['time']}"

                content.append(f"#### {date_header}")
                content.append("")

                # Metadata line
                doc_link = f"[{group['canonical_bates']}](../documents/{group['canonical_bates']}.md)"
                confidence_badge = get_confidence_badge(group['confidence'])

                content.append(f"**Document:** {doc_link} | **Count:** {group['document_count']} document(s) | **Confidence:** {confidence_badge}")
                content.append("")

                # Date source info
                if group['date_source']:
                    content.append(f"*Date Source: {group['date_source']}*")
                    content.append("")

                # Content preview placeholder
                content.append("??? info \"Content Preview\"")
                content.append("    *Content preview will be added in future updates.*")
                content.append("")

                # Duplicates section (collapsible)
                if duplicates:
                    content.append(f"??? abstract \"Duplicate Documents ({len(duplicates)})\"")
                    content.append("    | Bates ID | Date | Time | Source |")
                    content.append("    |----------|------|------|--------|")
                    for dup in duplicates:
                        dup_link = f"[{dup['bates_id']}](../documents/{dup['bates_id']}.md)"
                        dup_date = dup['date'] or 'N/A'
                        dup_time = dup['time'] or 'N/A'
                        dup_source = dup['date_source'] or 'N/A'
                        content.append(f"    | {dup_link} | {dup_date} | {dup_time} | {dup_source} |")
                    content.append("")

                content.append("---")
                content.append("")

        # Back to top hint after each year
        content.append("*[Back to top](#quick-navigation)*")
        content.append("")
        content.append("---")
        content.append("")

    # Undated section
    content.append("## Undated Documents {#undated-documents}")
    content.append("")
    content.append(f"The following {len(undated_groups)} document groups do not have extractable dates.")
    content.append("")

    for group in undated_groups:
        # Get duplicate documents for this group
        cursor.execute("""
            SELECT bates_id, date_source
            FROM timeline_documents
            WHERE group_id = ? AND is_canonical = 0
            ORDER BY bates_id
        """, (group['group_id'],))
        duplicates = cursor.fetchall()

        doc_link = f"[{group['canonical_bates']}](../documents/{group['canonical_bates']}.md)"
        confidence_badge = get_confidence_badge(group['confidence'])

        content.append(f"**Document:** {doc_link} | **Count:** {group['document_count']} document(s) | **Confidence:** {confidence_badge}")

        if group['date_source']:
            content.append(f" | *Source: {group['date_source']}*")

        if duplicates:
            content.append("")
            content.append(f"??? abstract \"Duplicate Documents ({len(duplicates)})\"")
            content.append("    | Bates ID | Source |")
            content.append("    |----------|--------|")
            for dup in duplicates:
                dup_link = f"[{dup['bates_id']}](../documents/{dup['bates_id']}.md)"
                dup_source = dup['date_source'] or 'N/A'
                content.append(f"    | {dup_link} | {dup_source} |")

        content.append("")
        content.append("---")
        content.append("")

    # Footer
    content.append("*[Back to top](#quick-navigation)*")
    content.append("")
    content.append("---")
    content.append("")
    content.append("## Performance Notes")
    content.append("")
    content.append("This page contains all dated timeline groups in a single scrollable view.")
    content.append("For better performance on large datasets, consider:")
    content.append("")
    content.append("- Using the year navigation links to jump directly to relevant sections")
    content.append("- Filtering by specific date ranges using the search function")
    content.append("- Viewing individual year pages if they become available")
    content.append("")
    content.append("<!-- Future enhancement: Implement lazy loading for off-screen content -->")
    content.append("<!-- Future enhancement: Add infinite scroll or pagination options -->")
    content.append("<!-- Current page size: ~201 groups optimized for reasonable load time -->")
    content.append("")

    conn.close()

    # Write the markdown file
    print(f"Writing timeline page to {OUTPUT_FILE}...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))

    # Calculate approximate file size
    file_size = OUTPUT_FILE.stat().st_size
    file_size_mb = file_size / (1024 * 1024)

    print(f"✓ Timeline page generated successfully!")
    print(f"  - Dated groups: {len(dated_groups)}")
    print(f"  - Undated groups: {len(undated_groups)}")
    print(f"  - Years covered: {len(years)} ({min(years)}-{max(years)})")
    print(f"  - Output file: {OUTPUT_FILE}")
    print(f"  - File size: {file_size_mb:.2f} MB")

    if file_size_mb > 5:
        print(f"  ⚠ Warning: File size exceeds 5MB. Consider optimization.")

    return OUTPUT_FILE

if __name__ == '__main__':
    generate_chronological_timeline()
