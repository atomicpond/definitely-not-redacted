#!/usr/bin/env python3
"""
Generate content previews for deduplicated document groups.
Creates concise 1-2 sentence summaries for timeline display.
"""

import sqlite3
import json
import re
from pathlib import Path
from collections import Counter

# Paths
BASE_DIR = Path(__file__).parent.parent
TIMELINE_DB = BASE_DIR / "database" / "timeline.db"
DOCS_DB = BASE_DIR / "database" / "documents.db"
SOURCE_DIR = Path("/Users/am/Research/Epstein/Epstein Estate Documents - Seventh Production")
OCR_BASE_DIR = SOURCE_DIR / "TEXT"
OUTPUT_FILE = BASE_DIR / "output" / "content_previews_batch1.json"

# Entity patterns for quick extraction
PERSON_PATTERN = re.compile(r'\b(?:Mr\.|Mrs\.|Ms\.|Dr\.)?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b')
ORG_PATTERN = re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:University|Foundation|Corp|Inc|LLC|Institute|Center|Group|Partners|Associates|Law|Firm)))\b')
EMAIL_PATTERN = re.compile(r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Z|a-z]{2,})\b')

def get_canonical_documents(start_group=4, end_group=53):
    """Get canonical document for each group."""
    conn = sqlite3.connect(TIMELINE_DB)
    cursor = conn.cursor()

    group_ids = [f"group_{i:04d}" for i in range(start_group, end_group + 1)]
    placeholders = ','.join('?' * len(group_ids))

    cursor.execute(f"""
        SELECT group_id, canonical_bates
        FROM timeline_groups
        WHERE group_id IN ({placeholders})
        ORDER BY group_id
    """, group_ids)

    results = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()
    return results

def get_ocr_text_path(bates_id):
    """Find the OCR text file for a given Bates ID."""
    # Get text_path from database
    conn = sqlite3.connect(DOCS_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT text_path FROM documents WHERE bates_id = ?", (bates_id,))
    row = cursor.fetchone()
    conn.close()

    if not row or not row[0]:
        return None

    # text_path is like: \HOUSE_OVERSIGHT_009\TEXT\001\HOUSE_OVERSIGHT_023621.txt
    text_path = row[0].replace('\\', '/').lstrip('/')
    # Extract the subdirectory and filename
    # Format: HOUSE_OVERSIGHT_009/TEXT/001/HOUSE_OVERSIGHT_023621.txt
    parts = text_path.split('/')
    if len(parts) >= 3 and parts[1] == 'TEXT':
        # Reconstruct as: SOURCE_DIR/TEXT/001/filename.txt
        text_file = OCR_BASE_DIR / parts[2] / parts[3]
        if text_file.exists():
            return text_file

    # Fallback: try to find file in any TEXT subdirectory
    for subdir in OCR_BASE_DIR.glob('*'):
        if subdir.is_dir():
            text_file = subdir / f"{bates_id}.txt"
            if text_file.exists():
                return text_file

    return None

def read_document_content(text_file, max_chars=3000):
    """Read document content, limited to first N characters."""
    try:
        with open(text_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(max_chars)
        return content
    except Exception as e:
        print(f"Error reading {text_file}: {e}")
        return None

def extract_entities(text):
    """Quick entity extraction using patterns."""
    entities = set()

    # Extract person names
    for match in PERSON_PATTERN.finditer(text[:1500]):  # First 1500 chars
        name = match.group(1).strip()
        if len(name.split()) >= 2:  # At least first and last name
            entities.add(name)

    # Extract organizations
    for match in ORG_PATTERN.finditer(text[:1500]):
        org = match.group(1).strip()
        entities.add(org)

    return list(entities)[:10]  # Limit to top 10

def identify_document_type(text):
    """Identify document type from content."""
    text_lower = text.lower()

    # Email indicators
    if any(word in text_lower[:500] for word in ['from:', 'to:', 'subject:', 're:', 'sent:']):
        return 'email'

    # Letter indicators
    if any(word in text_lower[:300] for word in ['dear ', 'sincerely', 'regards']):
        return 'letter'

    # Report/document indicators
    if any(word in text_lower[:500] for word in ['report', 'summary', 'analysis', 'findings']):
        return 'report'

    # Meeting/calendar indicators
    if any(word in text_lower[:500] for word in ['meeting', 'agenda', 'minutes', 'attendees']):
        return 'meeting'

    # Invoice/financial
    if any(word in text_lower[:500] for word in ['invoice', 'payment', 'amount due', '$']):
        return 'financial'

    return 'document'

def extract_key_info(text):
    """Extract key information snippets from document."""
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    info = {
        'subject': None,
        'from': None,
        'to': None,
        'topic': None
    }

    for i, line in enumerate(lines[:20]):  # First 20 lines
        line_lower = line.lower()

        if line_lower.startswith('subject:'):
            info['subject'] = line.split(':', 1)[1].strip()[:100]
        elif line_lower.startswith('from:'):
            info['from'] = line.split(':', 1)[1].strip()[:100]
        elif line_lower.startswith('to:'):
            info['to'] = line.split(':', 1)[1].strip()[:100]
        elif line_lower.startswith('re:'):
            info['subject'] = line.split(':', 1)[1].strip()[:100]

    return info

def generate_summary(text, bates_id):
    """Generate a concise 1-2 sentence summary."""
    doc_type = identify_document_type(text)
    key_info = extract_key_info(text)
    entities = extract_entities(text)

    # Build summary based on document type
    summary_parts = []

    if doc_type == 'email':
        if key_info['from'] and key_info['subject']:
            summary_parts.append(f"Email from {key_info['from'][:50]}")
            summary_parts.append(f"regarding {key_info['subject'][:80]}")
        elif key_info['subject']:
            summary_parts.append(f"Email thread regarding {key_info['subject'][:100]}")
        else:
            summary_parts.append("Email correspondence")
    elif doc_type == 'letter':
        summary_parts.append("Letter")
        if entities:
            summary_parts.append(f"involving {', '.join(entities[:2])}")
    elif doc_type == 'report':
        summary_parts.append("Report or analysis")
    elif doc_type == 'meeting':
        summary_parts.append("Meeting notes or agenda")
    else:
        summary_parts.append("Document")

    # Add entity context if available
    if entities and not summary_parts[-1].startswith('involving'):
        if len(entities) == 1:
            summary_parts.append(f"mentioning {entities[0]}")
        elif len(entities) > 1:
            summary_parts.append(f"mentioning {entities[0]} and {entities[1]}")

    summary = ' '.join(summary_parts).strip()

    # Ensure it ends with a period
    if not summary.endswith('.'):
        summary += '.'

    # Truncate if too long
    if len(summary) > 200:
        summary = summary[:197] + '...'

    return summary

def process_groups():
    """Process all groups and generate previews."""
    print("Fetching canonical documents from timeline database...")
    canonical_docs = get_canonical_documents(4, 53)
    print(f"Found {len(canonical_docs)} groups to process")

    previews = {}
    stats = {
        'processed': 0,
        'failed': 0,
        'total_chars': 0,
        'entity_counts': Counter()
    }

    for group_id in sorted(canonical_docs.keys()):
        bates_id = canonical_docs[group_id]
        print(f"\nProcessing {group_id}: {bates_id}")

        # Find OCR text file
        text_file = get_ocr_text_path(bates_id)
        if not text_file:
            print(f"  ⚠️  Text file not found for {bates_id}")
            previews[group_id] = {
                'canonical': bates_id,
                'preview': 'Document text not available.',
                'char_count': 30,
                'entities_mentioned': []
            }
            stats['failed'] += 1
            continue

        # Read content
        content = read_document_content(text_file)
        if not content or len(content.strip()) < 50:
            print(f"  ⚠️  Insufficient content in {bates_id}")
            previews[group_id] = {
                'canonical': bates_id,
                'preview': 'Document content too short to summarize.',
                'char_count': 42,
                'entities_mentioned': []
            }
            stats['failed'] += 1
            continue

        # Generate summary
        try:
            summary = generate_summary(content, bates_id)
            entities = extract_entities(content)

            previews[group_id] = {
                'canonical': bates_id,
                'preview': summary,
                'char_count': len(summary),
                'entities_mentioned': entities[:5]
            }

            stats['processed'] += 1
            stats['total_chars'] += len(summary)
            for entity in entities:
                stats['entity_counts'][entity] += 1

            print(f"  ✓ Generated preview ({len(summary)} chars)")
            print(f"    Preview: {summary[:80]}...")

        except Exception as e:
            print(f"  ⚠️  Error generating summary: {e}")
            previews[group_id] = {
                'canonical': bates_id,
                'preview': 'Error generating preview.',
                'char_count': 27,
                'entities_mentioned': []
            }
            stats['failed'] += 1

    # Calculate statistics
    avg_length = stats['total_chars'] / stats['processed'] if stats['processed'] > 0 else 0
    most_common_entities = stats['entity_counts'].most_common(10)

    output = {
        'previews': previews,
        'statistics': {
            'groups_processed': stats['processed'],
            'groups_failed': stats['failed'],
            'total_groups': len(canonical_docs),
            'average_preview_length': round(avg_length, 1),
            'most_common_entities': [
                {'entity': entity, 'count': count}
                for entity, count in most_common_entities
            ]
        }
    }

    # Write output
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Groups processed successfully: {stats['processed']}")
    print(f"Groups failed: {stats['failed']}")
    print(f"Average preview length: {avg_length:.1f} characters")
    print(f"\nMost common entities:")
    for entity, count in most_common_entities[:5]:
        print(f"  - {entity}: {count}")
    print(f"\nOutput saved to: {OUTPUT_FILE}")

if __name__ == '__main__':
    process_groups()
