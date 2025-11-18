#!/usr/bin/env python3
"""
Generate content previews for deduplicated document groups 101-150.
Creates 1-2 sentence summaries focusing on who/what/purpose.
"""

import sqlite3
import json
import os
import re
from pathlib import Path

# Paths
BASE_DIR = Path("/Users/am/Research/Epstein/epstein-wiki")
TIMELINE_DB = BASE_DIR / "database" / "timeline.db"
DOCS_DB = BASE_DIR / "database" / "documents.db"
OUTPUT_FILE = BASE_DIR / "output" / "content_previews_batch3.json"

def get_document_markdown_path(bates_id):
    """Get the markdown file path for a document."""
    return BASE_DIR / "docs" / "documents" / f"{bates_id}.md"

def extract_document_text_from_markdown(file_path):
    """Extract the document text section from markdown file."""
    if not os.path.exists(file_path):
        return None

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Find the Document Text section
        match = re.search(r'## Document Text\s*```(.*?)```', content, re.DOTALL)
        if match:
            return match.group(1).strip()

        return None
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def extract_metadata_from_markdown(file_path):
    """Extract email metadata from markdown file."""
    if not os.path.exists(file_path):
        return {}

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(2000)  # Just read the beginning

        metadata = {}

        # Extract date sent
        date_match = re.search(r'\*\*Date Sent:\*\*\s*(.+)', content)
        if date_match:
            metadata['date_sent'] = date_match.group(1).strip()

        # Extract email from
        from_match = re.search(r'\*\*Email From:\*\*\s*(.+)', content)
        if from_match:
            metadata['email_from'] = from_match.group(1).strip()

        # Extract email to
        to_match = re.search(r'\*\*Email To:\*\*\s*(.+)', content)
        if to_match:
            metadata['email_to'] = to_match.group(1).strip()

        # Extract email subject
        subject_match = re.search(r'\*\*Email Subject:\*\*\s*(.+)', content)
        if subject_match:
            metadata['email_subject'] = subject_match.group(1).strip()

        # Extract custodian
        custodian_match = re.search(r'\*\*Custodian:\*\*\s*(.+)', content)
        if custodian_match:
            metadata['custodian'] = custodian_match.group(1).strip()

        return metadata
    except Exception as e:
        print(f"Error extracting metadata from {file_path}: {e}")
        return {}

def extract_email_parts(content):
    """Extract email subject, from, to from content."""
    if not content:
        return None, None, None

    subject = None
    from_addr = None
    to_addr = None

    # Look for Subject:
    subject_match = re.search(r'Subject:\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
    if subject_match:
        subject = subject_match.group(1).strip()[:100]

    # Look for From:
    from_match = re.search(r'From:\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
    if from_match:
        from_addr = from_match.group(1).strip()[:100]

    # Look for To:
    to_match = re.search(r'To:\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
    if to_match:
        to_addr = to_match.group(1).strip()[:100]

    return subject, from_addr, to_addr

def extract_entities(content):
    """Extract key people and organizations from content."""
    if not content:
        return []

    entities = []

    # Common names to look for
    name_patterns = [
        r'\b(Jeffrey Epstein|Epstein)\b',
        r'\b(Bill Clinton|Clinton)\b',
        r'\b(Prince Andrew|Andrew)\b',
        r'\b(Donald Trump|Trump)\b',
        r'\b(Barack Obama|Obama)\b',
        r'\b(Larry Summers|Summers)\b',
        r'\b(Boris Nikolic|Nikolic)\b',
        r'\b(Ghislaine Maxwell|Maxwell)\b',
    ]

    for pattern in name_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            match = re.search(pattern, content, re.IGNORECASE)
            entities.append(match.group(1))

    return list(set(entities))[:5]  # Top 5 unique

def generate_summary(content, metadata, bates_id):
    """Generate a 1-2 sentence summary of the document."""
    if not content:
        return f"Document content not available."

    # Check if it's an email (from metadata)
    has_email_metadata = any([
        metadata.get('email_from'),
        metadata.get('email_to'),
        metadata.get('email_subject')
    ])

    # Also check content for email markers
    has_email_markers = bool(re.search(r'(From:|To:|Subject:|Sent:)', content[:500]))

    is_email = has_email_metadata or has_email_markers

    # Extract entities from content
    entities = extract_entities(content)

    if is_email:
        # Email summary
        summary_parts = []

        # Use metadata subject if available
        subject = metadata.get('email_subject')
        if not subject:
            # Extract from content
            subject, _, _ = extract_email_parts(content)

        # Use metadata from/to if available
        from_addr = metadata.get('email_from')
        to_addr = metadata.get('email_to')

        if not from_addr or not to_addr:
            _, from_addr, to_addr = extract_email_parts(content)

        # Build summary
        if subject and subject.lower() not in ['re:', 'fwd:', 're', 'fwd', '']:
            # Clean up subject
            subject_clean = re.sub(r'^(re:|fwd:)\s*', '', subject, flags=re.IGNORECASE).strip()
            if len(subject_clean) > 50:
                subject_clean = subject_clean[:50] + "..."
            summary_parts.append(f"Email: {subject_clean}")
        else:
            summary_parts.append("Email correspondence")

        # Add from/to if available
        if from_addr:
            from_name = re.sub(r'<.*?>', '', from_addr).strip()
            from_name = re.sub(r'\[.*?\]', '', from_name).strip()
            if from_name and len(from_name) > 2 and from_name.lower() != 'unknown':
                if len(from_name) > 30:
                    from_name = from_name[:30] + "..."
                summary_parts.append(f"from {from_name}")

        if to_addr and len(summary_parts) < 3:
            to_name = re.sub(r'<.*?>', '', to_addr).strip()
            to_name = re.sub(r'\[.*?\]', '', to_name).strip()
            if to_name and len(to_name) > 2 and to_name.lower() != 'unknown':
                if len(to_name) > 30:
                    to_name = to_name[:30] + "..."
                summary_parts.append(f"to {to_name}")

        summary = " ".join(summary_parts)

        # Add key entity mentions if not too long
        if entities and len(summary) < 120:
            summary += f". Mentions {', '.join(entities[:2])}"

        summary += "."
    else:
        # Non-email document summary
        first_500 = content[:500].lower()

        # Detect document type
        if 'agreement' in first_500 or 'contract' in first_500:
            doc_type = "Legal agreement or contract"
        elif 'schedule' in first_500 or 'flight' in first_500 or 'itinerary' in first_500:
            doc_type = "Schedule or travel document"
        elif 'invoice' in first_500 or 'payment' in first_500 or 'receipt' in first_500:
            doc_type = "Financial document"
        elif 'memo' in first_500 or 'memorandum' in first_500:
            doc_type = "Internal memorandum"
        elif 'article' in first_500 or 'news' in first_500:
            doc_type = "News article or publication"
        elif 'report' in first_500:
            doc_type = "Report"
        else:
            doc_type = "Document"

        summary = doc_type

        # Add entity mentions
        if entities:
            summary += f" involving {', '.join(entities[:3])}"

        summary += "."

    # Truncate to max 200 chars
    if len(summary) > 200:
        summary = summary[:197] + "..."

    return summary

def main():
    """Main processing function."""
    print("Starting content preview generation for groups 101-150...")

    # Connect to databases
    timeline_conn = sqlite3.connect(TIMELINE_DB)
    timeline_cursor = timeline_conn.cursor()

    # Get groups 101-150
    timeline_cursor.execute("""
        SELECT group_id, canonical_bates
        FROM timeline_groups
        WHERE CAST(SUBSTR(group_id, 7) AS INTEGER) BETWEEN 101 AND 150
        ORDER BY group_id
    """)

    groups = timeline_cursor.fetchall()
    print(f"Found {len(groups)} groups to process")

    # Process each group
    previews = {}
    stats = {
        'total_groups': len(groups),
        'successful': 0,
        'failed': 0,
        'no_content': 0
    }

    for group_id, canonical_bates in groups:
        print(f"Processing {group_id} (canonical: {canonical_bates})...")

        # Get markdown path
        md_path = get_document_markdown_path(canonical_bates)

        if not os.path.exists(md_path):
            print(f"  No markdown file found for {canonical_bates}")
            previews[group_id] = {
                'canonical_bates': canonical_bates,
                'summary': f"Document content not available.",
                'has_content': False
            }
            stats['no_content'] += 1
            continue

        # Extract content and metadata
        content = extract_document_text_from_markdown(md_path)
        metadata = extract_metadata_from_markdown(md_path)

        if not content:
            print(f"  No content found in markdown for {canonical_bates}")
            previews[group_id] = {
                'canonical_bates': canonical_bates,
                'summary': f"Document content not available.",
                'has_content': False
            }
            stats['no_content'] += 1
            continue

        # Generate summary
        summary = generate_summary(content, metadata, canonical_bates)

        previews[group_id] = {
            'canonical_bates': canonical_bates,
            'summary': summary,
            'has_content': True,
            'metadata': metadata
        }

        stats['successful'] += 1
        print(f"  Summary: {summary}")

    timeline_conn.close()

    # Save results
    output_data = {
        'batch': 3,
        'group_range': '101-150',
        'generated_at': '2025-11-17',
        'stats': stats,
        'previews': previews
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to {OUTPUT_FILE}")
    print(f"\nStatistics:")
    print(f"  Total groups: {stats['total_groups']}")
    print(f"  Successful: {stats['successful']}")
    print(f"  No content: {stats['no_content']}")
    print(f"  Failed: {stats['failed']}")

if __name__ == '__main__':
    main()
