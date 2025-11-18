#!/usr/bin/env python3
"""
Generate content previews for deduplicated document groups (batch 4: group_0154 to group_0213)
"""

import sqlite3
import json
import os
import re
from pathlib import Path

# Paths
TIMELINE_DB = '/Users/am/Research/Epstein/epstein-wiki/database/timeline.db'
DOCS_DB = '/Users/am/Research/Epstein/epstein-wiki/database/documents.db'
OUTPUT_FILE = '/Users/am/Research/Epstein/epstein-wiki/output/content_previews_batch4.json'

# Group range
START_GROUP = 154
END_GROUP = 213

def get_document_metadata(bates_id, docs_db):
    """Get document metadata from the database"""
    cursor = docs_db.cursor()
    cursor.execute("""
        SELECT email_subject, email_from, email_to, original_filename,
               custodian, date_sent, text_path
        FROM documents
        WHERE bates_id = ?
    """, (bates_id,))

    result = cursor.fetchone()
    if result:
        return {
            'email_subject': result[0],
            'email_from': result[1],
            'email_to': result[2],
            'original_filename': result[3],
            'custodian': result[4],
            'date_sent': result[5],
            'text_path': result[6]
        }
    return None

def generate_summary_from_metadata(bates_id, metadata):
    """Generate a 1-2 sentence summary from document metadata"""
    if not metadata:
        return "Document metadata not available."

    # Clean up metadata values
    def clean_field(field):
        if not field:
            return None
        field = str(field).strip()
        # Remove common OCR artifacts
        field = re.sub(r'[^\x00-\x7F]+', '', field)
        return field if field else None

    email_subject = clean_field(metadata.get('email_subject'))
    email_from = clean_field(metadata.get('email_from'))
    email_to = clean_field(metadata.get('email_to'))
    custodian = clean_field(metadata.get('custodian'))
    original_filename = clean_field(metadata.get('original_filename'))

    # Build summary based on available metadata
    parts = []

    # Check if it's an email (has subject or from/to)
    if email_subject:
        # Clean up subject
        subject = email_subject
        # Truncate if too long
        if len(subject) > 100:
            subject = subject[:97] + "..."
        parts.append(f"Email regarding: {subject}")
    elif email_from or email_to:
        # Email without subject
        if email_from and email_to:
            from_name = email_from.split('@')[0] if '@' in email_from else email_from
            to_name = email_to.split('@')[0] if '@' in email_to else email_to
            # Truncate names if too long
            from_name = from_name[:30]
            to_name = to_name[:30]
            parts.append(f"Email from {from_name} to {to_name}")
        elif email_from:
            from_name = email_from.split('@')[0] if '@' in email_from else email_from
            from_name = from_name[:30]
            parts.append(f"Email from {from_name}")
        else:
            to_name = email_to.split('@')[0] if '@' in email_to else email_to
            to_name = to_name[:30]
            parts.append(f"Email to {to_name}")
    elif original_filename:
        # Use filename to identify document type
        filename = original_filename.lower()
        if '.pdf' in filename:
            parts.append("PDF document")
        elif '.doc' in filename or '.docx' in filename:
            parts.append("Word document")
        elif '.xls' in filename or '.xlsx' in filename:
            parts.append("Excel spreadsheet")
        elif '.ppt' in filename or '.pptx' in filename:
            parts.append("PowerPoint presentation")
        else:
            parts.append("Document")

        # Add filename (truncated)
        fname = original_filename.split('.')[0][:50]
        if fname:
            parts.append(f": {fname}")
    else:
        # Generic document
        if custodian:
            parts.append(f"Document from custodian: {custodian[:50]}")
        else:
            parts.append("Document")

    summary = " ".join(parts)

    # Ensure summary is not too long
    if len(summary) > 200:
        summary = summary[:197] + "..."

    return summary

def main():
    print("="*80)
    print("Content Preview Generator - Batch 4")
    print(f"Processing groups {START_GROUP:04d} to {END_GROUP:04d}")
    print("="*80)

    # Connect to databases
    timeline_db = sqlite3.connect(TIMELINE_DB)
    docs_db = sqlite3.connect(DOCS_DB)

    # Get groups in range
    cursor = timeline_db.cursor()
    cursor.execute("""
        SELECT group_id, canonical_bates, document_count
        FROM timeline_groups
        WHERE group_id >= ? AND group_id <= ?
        ORDER BY group_id
    """, (f'group_{START_GROUP:04d}', f'group_{END_GROUP:04d}'))

    groups = cursor.fetchall()
    print(f"\nFound {len(groups)} groups to process")

    # Process each group
    previews = {}
    stats = {
        'total_groups': len(groups),
        'successful': 0,
        'failed': 0,
        'no_metadata': 0
    }

    for i, (group_id, canonical_bates, doc_count) in enumerate(groups, 1):
        print(f"\n[{i}/{len(groups)}] Processing {group_id} ({canonical_bates})...", end=' ')

        try:
            # Get metadata
            metadata = get_document_metadata(canonical_bates, docs_db)

            if not metadata:
                print("❌ No metadata found")
                stats['failed'] += 1
                previews[group_id] = {
                    'canonical_bates': canonical_bates,
                    'summary': "Document metadata not available.",
                    'has_content': False
                }
                continue

            # Generate summary from metadata
            summary = generate_summary_from_metadata(canonical_bates, metadata)

            # Check if we have any meaningful content
            has_content = bool(metadata.get('email_subject') or
                             metadata.get('email_from') or
                             metadata.get('email_to') or
                             metadata.get('original_filename'))

            if not has_content:
                stats['no_metadata'] += 1
            else:
                stats['successful'] += 1

            previews[group_id] = {
                'canonical_bates': canonical_bates,
                'summary': summary,
                'has_content': has_content
            }

            print(f"✓ ({len(summary)} chars)")
            print(f"   Preview: {summary[:80]}...")

        except Exception as e:
            print(f"❌ Error: {e}")
            stats['failed'] += 1
            previews[group_id] = {
                'canonical_bates': canonical_bates,
                'summary': f"Error generating preview: {str(e)}",
                'has_content': False
            }

    # Close databases
    timeline_db.close()
    docs_db.close()

    # Save output (match batch 2/3 format)
    from datetime import datetime
    output_data = {
        'previews': previews,
        'statistics': {
            'total_groups': stats['total_groups'],
            'successful': stats['successful'],
            'failed': stats['failed'],
            'no_metadata': stats['no_metadata'],
            'batch': f'{START_GROUP}-{END_GROUP}',
            'timestamp': datetime.now().isoformat()
        },
        'generated_at': datetime.now().isoformat(),
        'batch_range': f'groups_{START_GROUP}_{END_GROUP}',
        'group_id_range': f'group_{START_GROUP:04d} to group_{END_GROUP:04d}'
    }

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)

    print("\n" + "="*80)
    print("PROCESSING COMPLETE")
    print("="*80)
    print(f"\nStatistics:")
    print(f"  Total groups: {stats['total_groups']}")
    print(f"  Successfully processed: {stats['successful']}")
    print(f"  No metadata: {stats['no_metadata']}")
    print(f"  Failed: {stats['failed']}")
    print(f"\nOutput saved to: {OUTPUT_FILE}")
    print(f"File size: {os.path.getsize(OUTPUT_FILE):,} bytes")

    # Show some sample previews
    print("\n" + "="*80)
    print("SAMPLE PREVIEWS")
    print("="*80)
    sample_groups = list(previews.keys())[:5]
    for group_id in sample_groups:
        preview = previews[group_id]
        print(f"\n{group_id} ({preview['canonical_bates']}):")
        print(f"  {preview['summary']}")

if __name__ == '__main__':
    main()
