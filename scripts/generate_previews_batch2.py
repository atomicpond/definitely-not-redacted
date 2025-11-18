#!/usr/bin/env python3
"""
Generate content previews for deduplicated document groups 51-100.
"""

import sqlite3
import json
import os
import re
from datetime import datetime

# Database paths
TIMELINE_DB = "/Users/am/Research/Epstein/epstein-wiki/database/timeline.db"
DOCS_DB = "/Users/am/Research/Epstein/epstein-wiki/database/documents.db"
OUTPUT_FILE = "/Users/am/Research/Epstein/epstein-wiki/output/content_previews_batch2.json"

# OCR text directory
OCR_BASE_DIR = "/Users/am/Research/Epstein/Epstein Estate Documents - Seventh Production/TEXT"

def get_canonical_documents():
    """Get canonical documents for groups 51-100 (group_0054 through group_0103)."""
    conn = sqlite3.connect(TIMELINE_DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT group_id, canonical_bates
        FROM timeline_groups
        WHERE CAST(SUBSTR(group_id, 7) AS INTEGER) BETWEEN 54 AND 103
        ORDER BY CAST(SUBSTR(group_id, 7) AS INTEGER)
    """)

    groups = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()

    return groups

def get_ocr_text(bates_id):
    """Get OCR text for a document."""
    # OCR files are organized in subdirectories like TEXT/001/HOUSE_OVERSIGHT_030958.txt
    # Try different subdirectory patterns
    for subdir in ['001', '002', '003', '004', '005', '006', '007', '008', '009', '010']:
        ocr_path = os.path.join(OCR_BASE_DIR, subdir, f"{bates_id}.txt")
        if os.path.exists(ocr_path):
            try:
                with open(ocr_path, 'r', encoding='utf-8', errors='ignore') as f:
                    # Read first 5000 characters (enough for summary)
                    text = f.read(5000)
                return text
            except Exception as e:
                print(f"Error reading {ocr_path}: {e}")
                return None

    return None

def extract_entities(text):
    """Extract basic entities from text using simple patterns."""
    if not text:
        return {"people": [], "orgs": [], "subjects": []}

    # Clean up text
    text = text[:2000]  # First 2000 chars

    # Extract potential names (capitalized words)
    name_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b'
    names = re.findall(name_pattern, text)

    # Extract email subjects
    subject_pattern = r'(?:Subject|Re|Fwd):\s*([^\n]{10,100})'
    subjects = re.findall(subject_pattern, text, re.IGNORECASE)

    # Extract organization mentions
    org_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Inc|LLC|Corp|Foundation|University|Institute|Organization|Committee)))\b'
    orgs = re.findall(org_pattern, text)

    return {
        "people": list(set(names))[:5],
        "orgs": list(set(orgs))[:3],
        "subjects": subjects[:1]
    }

def determine_doc_type(text):
    """Determine document type from text."""
    if not text:
        return "document"

    text_lower = text.lower()[:500]

    if 'from:' in text_lower and 'to:' in text_lower:
        return "email"
    elif 'subject:' in text_lower and '@' in text_lower:
        return "email"
    elif 'memorandum' in text_lower or 'memo to:' in text_lower:
        return "memo"
    elif 'invoice' in text_lower or 'bill to:' in text_lower:
        return "invoice"
    elif 'agreement' in text_lower or 'contract' in text_lower:
        return "agreement"
    elif 'report' in text_lower:
        return "report"
    elif 'letter' in text_lower:
        return "letter"
    elif 'schedule' in text_lower or 'calendar' in text_lower:
        return "schedule"
    else:
        return "document"

def generate_summary(bates_id, text):
    """Generate a concise 1-2 sentence summary."""
    if not text:
        return f"Document {bates_id} - content not available."

    # Extract entities
    entities = extract_entities(text)
    doc_type = determine_doc_type(text)

    # Build summary
    parts = []

    # Get subject if it's an email
    if entities["subjects"]:
        subject = entities["subjects"][0].strip()
        if len(subject) > 80:
            subject = subject[:77] + "..."
        return f"Email regarding: {subject}"

    # Otherwise build from entities
    if entities["people"]:
        # Take first 1-2 names
        people = entities["people"][:2]
        if len(people) == 1:
            parts.append(f"Involves {people[0]}")
        else:
            parts.append(f"Involves {', '.join(people)}")

    if entities["orgs"]:
        parts.append(f"related to {entities['orgs'][0]}")

    # Add document type
    if not parts:
        summary = f"{doc_type.capitalize()}"
    else:
        summary = " ".join(parts)

    # Extract key phrases from first 500 chars
    text_sample = text[:500].lower()

    if 'meeting' in text_sample:
        summary += " - discusses meeting"
    elif 'payment' in text_sample or 'invoice' in text_sample:
        summary += " - payment details"
    elif 'travel' in text_sample or 'flight' in text_sample:
        summary += " - travel arrangements"
    elif 'request' in text_sample:
        summary += " - request"

    # Ensure not too long
    if len(summary) > 200:
        summary = summary[:197] + "..."

    # Make sure it's a proper sentence
    if not summary.endswith('.'):
        summary += "."

    return summary

def main():
    print("Generating content previews for groups 51-100...")
    print(f"Output: {OUTPUT_FILE}")

    # Get canonical documents
    groups = get_canonical_documents()
    print(f"Found {len(groups)} groups to process")

    # Generate previews
    previews = {}
    stats = {
        "total_groups": len(groups),
        "successful": 0,
        "failed": 0,
        "no_ocr": 0,
        "batch": "51-100",
        "timestamp": datetime.now().isoformat()
    }

    for i, (group_id, bates_id) in enumerate(sorted(groups.items()), 1):
        print(f"Processing {i}/{len(groups)}: {group_id} ({bates_id})...")

        # Get OCR text
        text = get_ocr_text(bates_id)

        if text is None:
            print(f"  ⚠️  No OCR text found for {bates_id}")
            stats["no_ocr"] += 1
            previews[group_id] = {
                "canonical_bates": bates_id,
                "summary": f"Document {bates_id} - OCR text not available.",
                "has_content": False
            }
            continue

        # Generate summary
        try:
            summary = generate_summary(bates_id, text)
            previews[group_id] = {
                "canonical_bates": bates_id,
                "summary": summary,
                "has_content": True
            }
            stats["successful"] += 1
            print(f"  ✓ {summary[:80]}...")
        except Exception as e:
            print(f"  ✗ Error generating summary: {e}")
            stats["failed"] += 1
            previews[group_id] = {
                "canonical_bates": bates_id,
                "summary": f"Document {bates_id} - error generating preview.",
                "has_content": False
            }

    # Save output
    output = {
        "previews": previews,
        "statistics": stats,
        "generated_at": datetime.now().isoformat(),
        "batch_range": "groups_51_100",
        "group_id_range": "group_0054 to group_0103"
    }

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print("STATISTICS")
    print(f"{'='*60}")
    print(f"Total groups: {stats['total_groups']}")
    print(f"Successful: {stats['successful']}")
    print(f"No OCR text: {stats['no_ocr']}")
    print(f"Failed: {stats['failed']}")
    print(f"\nOutput saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
