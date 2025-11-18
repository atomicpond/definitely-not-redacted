#!/usr/bin/env python3
"""
Generate Timeline by Month Pages

This script creates month-based timeline pages from the timeline database.
Each month with documents gets its own page showing all document groups
chronologically organized by day.

Outputs:
- docs/timeline/by_month/YYYY-MM.md - Individual month pages
- docs/timeline/by_month/index.md - Calendar-style index

Database: database/timeline.db
"""

import sqlite3
from pathlib import Path
from datetime import datetime, date
from collections import defaultdict
import calendar

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
TIMELINE_DB = PROJECT_ROOT / "database" / "timeline.db"
OUTPUT_DIR = PROJECT_ROOT / "docs" / "timeline" / "by_month"

# Confidence badge styles
CONFIDENCE_BADGES = {
    'high': '<span style="background-color: #22c55e; color: white; padding: 2px 8px; border-radius: 3px; font-size: 0.85em;">HIGH</span>',
    'medium': '<span style="background-color: #f59e0b; color: white; padding: 2px 8px; border-radius: 3px; font-size: 0.85em;">MEDIUM</span>',
    'low': '<span style="background-color: #ef4444; color: white; padding: 2px 8px; border-radius: 3px; font-size: 0.85em;">LOW</span>',
    'none': '<span style="background-color: #6b7280; color: white; padding: 2px 8px; border-radius: 3px; font-size: 0.85em;">UNKNOWN</span>'
}


def get_month_statistics(conn):
    """
    Get statistics for all months with documents.

    Returns:
        dict: {(year, month): {'groups': int, 'documents': int, 'confidence': {...}}}
    """
    cursor = conn.cursor()

    month_stats = defaultdict(lambda: {
        'groups': 0,
        'documents': 0,
        'confidence': {'high': 0, 'medium': 0, 'low': 0, 'none': 0}
    })

    # Get groups per month
    cursor.execute('''
        SELECT year, month, confidence, COUNT(*) as groups, SUM(document_count) as docs
        FROM timeline_groups
        WHERE year IS NOT NULL AND month IS NOT NULL
        GROUP BY year, month, confidence
        ORDER BY year, month
    ''')

    for year, month, confidence, groups, docs in cursor.fetchall():
        key = (year, month)
        month_stats[key]['groups'] += groups
        month_stats[key]['documents'] += docs
        month_stats[key]['confidence'][confidence] += groups

    return dict(month_stats)


def get_month_groups(conn, year, month):
    """
    Get all groups for a specific month, organized by day.

    Returns:
        dict: {day: [group_data, ...]}
    """
    cursor = conn.cursor()

    # Get all groups for this month
    cursor.execute('''
        SELECT
            group_id,
            canonical_bates,
            date,
            time,
            date_source,
            date_from_bates,
            confidence,
            document_count,
            day
        FROM timeline_groups
        WHERE year = ? AND month = ?
        ORDER BY day, time, canonical_bates
    ''', (year, month))

    groups_by_day = defaultdict(list)

    for row in cursor.fetchall():
        group_id, canonical_bates, date_str, time_str, source, from_bates, confidence, doc_count, day = row

        # Get duplicate documents for this group
        cursor.execute('''
            SELECT bates_id
            FROM timeline_documents
            WHERE group_id = ? AND is_canonical = 0
            ORDER BY bates_id
        ''', (group_id,))

        duplicates = [row[0] for row in cursor.fetchall()]

        group_data = {
            'group_id': group_id,
            'canonical_bates': canonical_bates,
            'date': date_str,
            'time': time_str,
            'source': source,
            'from_bates': from_bates,
            'confidence': confidence,
            'document_count': doc_count,
            'duplicates': duplicates
        }

        groups_by_day[day].append(group_data)

    return dict(groups_by_day)


def format_datetime(date_str, time_str):
    """Format date and time for display."""
    try:
        date_obj = datetime.fromisoformat(date_str)
        formatted_date = date_obj.strftime('%B %d, %Y')  # e.g., "March 15, 2011"

        if time_str:
            formatted_time = f" at {time_str}"
        else:
            formatted_time = ""

        return formatted_date + formatted_time
    except:
        return date_str


def get_bates_number(bates_id):
    """Extract numeric portion of Bates ID."""
    return bates_id.replace('HOUSE_OVERSIGHT_', '')


def generate_month_page(conn, year, month, month_stats, all_months):
    """Generate a markdown page for a specific month."""

    # Get groups for this month
    groups_by_day = get_month_groups(conn, year, month)

    if not groups_by_day:
        return

    # Month name
    month_name = calendar.month_name[month]

    # Find previous and next months
    prev_month = None
    next_month = None

    sorted_months = sorted(all_months)
    current_idx = sorted_months.index((year, month))

    if current_idx > 0:
        prev_year, prev_mon = sorted_months[current_idx - 1]
        prev_month = (prev_year, prev_mon)

    if current_idx < len(sorted_months) - 1:
        next_year, next_mon = sorted_months[current_idx + 1]
        next_month = (next_year, next_mon)

    # Get statistics
    stats = month_stats[(year, month)]

    # Build markdown content
    lines = []
    lines.append(f"# {month_name} {year}")
    lines.append("")

    # Navigation
    nav_parts = []
    if prev_month:
        prev_year, prev_mon = prev_month
        nav_parts.append(f"[← {calendar.month_name[prev_mon]} {prev_year}]({prev_year}-{prev_mon:02d}.md)")
    else:
        nav_parts.append("← Previous")

    nav_parts.append("[📅 Month Index](index.md)")

    if next_month:
        next_year, next_mon = next_month
        nav_parts.append(f"[{calendar.month_name[next_mon]} {next_year} →]({next_year}-{next_mon:02d}.md)")
    else:
        nav_parts.append("Next →")

    lines.append(" | ".join(nav_parts))
    lines.append("")

    # Statistics box
    lines.append('<div style="background-color: #f3f4f6; padding: 15px; border-radius: 5px; margin: 20px 0;">')
    lines.append("")
    lines.append("### Month Overview")
    lines.append("")
    lines.append(f"- **Document Groups:** {stats['groups']:,}")
    lines.append(f"- **Total Documents:** {stats['documents']:,}")
    lines.append("")
    lines.append("**Confidence Distribution:**")
    lines.append("")

    for conf in ['high', 'medium', 'low', 'none']:
        count = stats['confidence'][conf]
        if count > 0:
            pct = (count / stats['groups']) * 100
            lines.append(f"- {CONFIDENCE_BADGES[conf]} {count} groups ({pct:.1f}%)")

    lines.append("")
    lines.append("</div>")
    lines.append("")

    # Document groups by day
    lines.append("---")
    lines.append("")
    lines.append("## Documents by Day")
    lines.append("")

    # Process each day
    sorted_days = sorted(groups_by_day.keys())

    for day in sorted_days:
        groups = groups_by_day[day]

        # Day header
        try:
            day_date = date(year, month, day)
            day_name = day_date.strftime('%A')
            lines.append(f"### {day_name}, {month_name} {day}, {year}")
        except:
            lines.append(f"### {month_name} {day}, {year}")

        lines.append("")
        lines.append(f"**{len(groups)} document group{'s' if len(groups) != 1 else ''}**")
        lines.append("")

        # Each group
        for group in groups:
            lines.append('<div style="border-left: 3px solid #3b82f6; padding-left: 15px; margin: 15px 0;">')
            lines.append("")

            # Date/Time
            datetime_str = format_datetime(group['date'], group['time'])
            lines.append(f"**{datetime_str}**")
            lines.append("")

            # Canonical document
            bates_num = get_bates_number(group['canonical_bates'])
            group_num = group['group_id'].replace('group_', '')
            lines.append(f"📄 **Primary Document:** [{group['canonical_bates']}](../../deduplicated/group_{group_num}.md)")
            lines.append("")

            # Metadata
            lines.append(f"- **Documents in Group:** {group['document_count']}")
            lines.append(f"- **Date Source:** {group['source']}")
            lines.append(f"- **Confidence:** {CONFIDENCE_BADGES[group['confidence']]}")

            if group['from_bates'] != group['canonical_bates']:
                from_bates_num = get_bates_number(group['from_bates'])
                lines.append(f"- **Date From:** {group['from_bates']}")

            lines.append("")

            # Duplicates
            if group['duplicates']:
                lines.append(f"**Duplicate Documents ({len(group['duplicates'])}):**")
                lines.append("")

                # Show up to 10 duplicates inline, rest as expandable
                if len(group['duplicates']) <= 10:
                    dup_links = []
                    for dup in group['duplicates']:
                        dup_num = get_bates_number(dup)
                        dup_links.append(f"[{dup}](../../documents/{dup}.md)")
                    lines.append(", ".join(dup_links))
                else:
                    # Show first 5
                    dup_links = []
                    for dup in group['duplicates'][:5]:
                        dup_num = get_bates_number(dup)
                        dup_links.append(f"[{dup}](../../documents/{dup}.md)")
                    lines.append(", ".join(dup_links))

                    # Expandable for rest
                    lines.append("")
                    lines.append(f"<details><summary>Show {len(group['duplicates']) - 5} more...</summary>")
                    lines.append("")

                    dup_links = []
                    for dup in group['duplicates'][5:]:
                        dup_num = get_bates_number(dup)
                        dup_links.append(f"[{dup}](../../documents/{dup}.md)")
                    lines.append(", ".join(dup_links))

                    lines.append("")
                    lines.append("</details>")

                lines.append("")

            lines.append("</div>")
            lines.append("")

    # Footer navigation
    lines.append("---")
    lines.append("")
    lines.append(" | ".join(nav_parts))
    lines.append("")

    # Write file
    output_file = OUTPUT_DIR / f"{year}-{month:02d}.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    return output_file


def generate_index_page(conn, month_stats):
    """Generate the calendar-style index page."""

    # Get year range
    years = sorted(set(year for year, month in month_stats.keys()))

    if not years:
        return

    lines = []
    lines.append("# Timeline by Month")
    lines.append("")
    lines.append("Browse documents organized by month. Each month page shows document groups chronologically organized by day.")
    lines.append("")

    # Navigation
    lines.append('[📅 Timeline Home](../index.md) | [📆 By Year](../by_year/index.md) | [📋 All Documents](../all.md)')
    lines.append("")

    # Overall statistics
    total_groups = sum(stats['groups'] for stats in month_stats.values())
    total_docs = sum(stats['documents'] for stats in month_stats.values())

    lines.append('<div style="background-color: #f3f4f6; padding: 15px; border-radius: 5px; margin: 20px 0;">')
    lines.append("")
    lines.append("### Overview")
    lines.append("")
    lines.append(f"- **Total Months with Documents:** {len(month_stats)}")
    lines.append(f"- **Total Document Groups:** {total_groups:,}")
    lines.append(f"- **Total Documents:** {total_docs:,}")
    lines.append(f"- **Date Range:** {min(years)} - {max(years)}")
    lines.append("")
    lines.append("</div>")
    lines.append("")

    # Process each year
    for year in years:
        lines.append(f"## {year}")
        lines.append("")

        # Calendar grid
        lines.append('<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px; margin: 20px 0;">')
        lines.append("")

        for month in range(1, 13):
            month_name = calendar.month_name[month]

            if (year, month) in month_stats:
                stats = month_stats[(year, month)]

                # Active month - link
                lines.append('<div style="background-color: #dbeafe; border: 2px solid #3b82f6; padding: 10px; border-radius: 5px;">')
                lines.append("")
                lines.append(f'<a href="{year}-{month:02d}.md" style="text-decoration: none; color: inherit;">')
                lines.append("")
                lines.append(f"**{month_name}**")
                lines.append("")
                lines.append(f"📊 {stats['groups']} groups  ")
                lines.append(f"📄 {stats['documents']} docs")
                lines.append("")

                # Busiest months get a badge
                if stats['groups'] >= 20:
                    lines.append('<span style="background-color: #ef4444; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.75em;">BUSY</span>')
                elif stats['groups'] >= 10:
                    lines.append('<span style="background-color: #f59e0b; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.75em;">ACTIVE</span>')

                lines.append("")
                lines.append("</a>")
                lines.append("")
                lines.append("</div>")
            else:
                # Inactive month - grayed out
                lines.append('<div style="background-color: #f3f4f6; padding: 10px; border-radius: 5px; color: #9ca3af;">')
                lines.append("")
                lines.append(f"**{month_name}**")
                lines.append("")
                lines.append("No documents")
                lines.append("")
                lines.append("</div>")

            lines.append("")

        lines.append("</div>")
        lines.append("")

    # Monthly statistics table
    lines.append("---")
    lines.append("")
    lines.append("## Monthly Statistics")
    lines.append("")
    lines.append("| Month | Groups | Documents | High | Medium | Low | Unknown |")
    lines.append("|-------|--------|-----------|------|--------|-----|---------|")

    # Sort by date (most recent first)
    sorted_months = sorted(month_stats.items(), key=lambda x: (x[0][0], x[0][1]), reverse=True)

    for (year, month), stats in sorted_months:
        month_name = calendar.month_name[month]
        month_link = f"[{month_name} {year}]({year}-{month:02d}.md)"

        conf = stats['confidence']

        lines.append(f"| {month_link} | {stats['groups']} | {stats['documents']} | "
                    f"{conf['high']} | {conf['medium']} | {conf['low']} | {conf['none']} |")

    lines.append("")

    # Top months
    lines.append("---")
    lines.append("")
    lines.append("## Busiest Months")
    lines.append("")

    top_months = sorted(month_stats.items(), key=lambda x: x[1]['groups'], reverse=True)[:10]

    lines.append("| Rank | Month | Groups | Documents |")
    lines.append("|------|-------|--------|-----------|")

    for idx, ((year, month), stats) in enumerate(top_months, 1):
        month_name = calendar.month_name[month]
        month_link = f"[{month_name} {year}]({year}-{month:02d}.md)"
        lines.append(f"| {idx} | {month_link} | {stats['groups']} | {stats['documents']} |")

    lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append('[📅 Timeline Home](../index.md) | [📆 By Year](../by_year/index.md) | [📋 All Documents](../all.md)')
    lines.append("")

    # Write file
    output_file = OUTPUT_DIR / "index.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    return output_file


def main():
    """Main execution function."""
    print("Generating Timeline by Month Pages...")
    print(f"  Database:    {TIMELINE_DB}")
    print(f"  Output Dir:  {OUTPUT_DIR}")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Connect to database
    print("\n[1/3] Loading month statistics...")
    conn = sqlite3.connect(TIMELINE_DB)
    month_stats = get_month_statistics(conn)

    print(f"  Found {len(month_stats)} months with documents")

    # Generate individual month pages
    print("\n[2/3] Generating month pages...")
    all_months = sorted(month_stats.keys())

    month_files = []
    for year, month in all_months:
        month_name = calendar.month_name[month]
        print(f"  {month_name} {year}...")

        month_file = generate_month_page(conn, year, month, month_stats, all_months)
        if month_file:
            month_files.append(month_file)

    print(f"  Generated {len(month_files)} month pages")

    # Generate index page
    print("\n[3/3] Generating index page...")
    index_file = generate_index_page(conn, month_stats)
    print(f"  Created: {index_file}")

    # Close database
    conn.close()

    # Summary
    print("\n" + "="*80)
    print("GENERATION COMPLETE")
    print("="*80)
    print(f"\n📁 Output Directory: {OUTPUT_DIR}")
    print(f"   Month Pages:      {len(month_files)}")
    print(f"   Index Page:       {index_file.name}")

    # Calculate total size
    total_size = sum(f.stat().st_size for f in month_files) + index_file.stat().st_size
    print(f"   Total Size:       {total_size / 1024:.1f} KB")

    # Show year distribution
    years = sorted(set(year for year, month in month_stats.keys()))
    print(f"\n📅 Years Covered:    {min(years)} - {max(years)}")

    for year in years:
        year_months = [m for y, m in month_stats.keys() if y == year]
        year_groups = sum(month_stats[(year, m)]['groups'] for m in year_months)
        print(f"   {year}: {len(year_months):2d} months, {year_groups:3d} groups")

    print("\n✅ All month-based timeline pages generated successfully!")


if __name__ == '__main__':
    main()
