#!/usr/bin/env python3
"""
Entity Extraction Script - Batch 3 (Documents 1451-2175)
Hybrid approach using pattern matching + spaCy NER
"""

import sqlite3
import json
import re
import os
from collections import defaultdict
from pathlib import Path
import spacy
from datetime import datetime

# Configuration
DB_PATH = "/Users/am/Research/Epstein/epstein-wiki/database/documents.db"
TEXT_BASE_PATH = "/Users/am/Research/Epstein/Epstein Estate Documents - Seventh Production/TEXT"
OUTPUT_PATH = "/Users/am/Research/Epstein/epstein-wiki/output/entities_batch_3.json"
BATCH_NUM = 3
START_OFFSET = 1450
BATCH_SIZE = 725
CONTEXT_WINDOW = 50

# Load spaCy model
print("Loading spaCy model...")
nlp = spacy.load("en_core_web_lg")

# Pattern matching regexes
PATTERNS = {
    'person_title': re.compile(r'\b(Mr\.?|Ms\.?|Mrs\.?|Dr\.?|Prof\.?|Hon\.?)\s+([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)', re.MULTILINE),
    'org_suffix': re.compile(r'\b([A-Z][A-Za-z\s&]+(?:Corp\.?|Corporation|LLC|L\.L\.C\.?|Inc\.?|Incorporated|Ltd\.?|Limited|LLP|L\.P\.?|Foundation|University|Institute|Group|Associates|Partners))\b', re.MULTILINE),
    'date_format': re.compile(r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2}|(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+\d{4})\b', re.MULTILINE),
    'email': re.compile(r'\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b'),
}


def normalize_entity(name):
    """Normalize entity name for deduplication."""
    # Remove titles
    name = re.sub(r'\b(Mr\.?|Ms\.?|Mrs\.?|Dr\.?|Prof\.?|Hon\.?)\s+', '', name)
    # Remove extra whitespace
    name = ' '.join(name.split())
    # Convert to lowercase and replace spaces with hyphens
    return name.lower().replace(' ', '-').replace('.', '')


def extract_context(text, position, window=CONTEXT_WINDOW):
    """Extract context around entity mention."""
    start = max(0, position - window)
    end = min(len(text), position + window)
    context = text[start:end]
    # Clean up context
    context = ' '.join(context.split())
    return f"...{context}..."


def pattern_match_entities(text):
    """Fast pattern-based entity extraction."""
    entities = {
        'people': set(),
        'organizations': set(),
        'dates': set(),
        'emails': set()
    }

    # Extract people with titles
    for match in PATTERNS['person_title'].finditer(text):
        entities['people'].add(match.group(0).strip())

    # Extract organizations
    for match in PATTERNS['org_suffix'].finditer(text):
        org = match.group(1).strip()
        if len(org) > 3:  # Avoid short false positives
            entities['organizations'].add(org)

    # Extract dates
    for match in PATTERNS['date_format'].finditer(text):
        entities['dates'].add(match.group(0).strip())

    # Extract emails
    for match in PATTERNS['email'].finditer(text):
        entities['emails'].add(match.group(0).strip())

    return entities


def spacy_extract_entities(text, doc_id):
    """AI-based entity extraction using spaCy."""
    entities_data = {
        'people': [],
        'organizations': [],
        'locations': [],
        'dates': []
    }

    # Process text with spaCy (limit to first 100k chars to avoid memory issues)
    text_sample = text[:100000] if len(text) > 100000 else text

    try:
        doc = nlp(text_sample)

        for ent in doc.ents:
            # Get position in original text
            position = ent.start_char
            entity_text = ent.text.strip()

            # Skip very short or very long entities
            if len(entity_text) < 2 or len(entity_text) > 100:
                continue

            context = extract_context(text_sample, position)

            mention = {
                'doc_id': doc_id,
                'context': context,
                'position': position
            }

            if ent.label_ == 'PERSON':
                entities_data['people'].append({
                    'name': entity_text,
                    'mention': mention
                })
            elif ent.label_ in ['ORG', 'FAC']:
                entities_data['organizations'].append({
                    'name': entity_text,
                    'mention': mention
                })
            elif ent.label_ in ['GPE', 'LOC']:
                entities_data['locations'].append({
                    'name': entity_text,
                    'mention': mention
                })
            elif ent.label_ == 'DATE':
                entities_data['dates'].append({
                    'name': entity_text,
                    'mention': mention
                })
    except Exception as e:
        print(f"  Error processing with spaCy: {e}")

    return entities_data


def merge_entities(pattern_entities, spacy_entities, doc_id):
    """Merge pattern-matched and spaCy entities."""
    merged = {
        'people': [],
        'organizations': [],
        'locations': [],
        'dates': []
    }

    # Add spaCy entities (they have context)
    for person_data in spacy_entities['people']:
        merged['people'].append(person_data)

    for org_data in spacy_entities['organizations']:
        merged['organizations'].append(org_data)

    for loc_data in spacy_entities['locations']:
        merged['locations'].append(loc_data)

    for date_data in spacy_entities['dates']:
        merged['dates'].append(date_data)

    # Add pattern-matched entities that weren't caught by spaCy
    # (without detailed context, but still valuable)
    spacy_people_names = {e['name'].lower() for e in spacy_entities['people']}
    for name in pattern_entities['people']:
        if name.lower() not in spacy_people_names:
            merged['people'].append({
                'name': name,
                'mention': {
                    'doc_id': doc_id,
                    'context': f'Pattern match: {name}',
                    'position': -1
                }
            })

    spacy_org_names = {e['name'].lower() for e in spacy_entities['organizations']}
    for org in pattern_entities['organizations']:
        if org.lower() not in spacy_org_names:
            merged['organizations'].append({
                'name': org,
                'mention': {
                    'doc_id': doc_id,
                    'context': f'Pattern match: {org}',
                    'position': -1
                }
            })

    return merged


def aggregate_entities(all_document_entities):
    """Aggregate entities across all documents."""
    aggregated = {
        'people': defaultdict(lambda: {'mentions': [], 'mention_count': 0}),
        'organizations': defaultdict(lambda: {'mentions': [], 'mention_count': 0}),
        'locations': defaultdict(lambda: {'mentions': [], 'mention_count': 0}),
        'events': defaultdict(lambda: {'mentions': [], 'mention_count': 0})
    }

    for doc_entities in all_document_entities:
        # People
        for person_data in doc_entities['people']:
            normalized = normalize_entity(person_data['name'])
            aggregated['people'][normalized]['mentions'].append(person_data['mention'])
            aggregated['people'][normalized]['mention_count'] += 1
            # Store original name (use first occurrence)
            if 'name' not in aggregated['people'][normalized]:
                aggregated['people'][normalized]['name'] = person_data['name']

        # Organizations
        for org_data in doc_entities['organizations']:
            normalized = normalize_entity(org_data['name'])
            aggregated['organizations'][normalized]['mentions'].append(org_data['mention'])
            aggregated['organizations'][normalized]['mention_count'] += 1
            if 'name' not in aggregated['organizations'][normalized]:
                aggregated['organizations'][normalized]['name'] = org_data['name']

        # Locations
        for loc_data in doc_entities['locations']:
            normalized = normalize_entity(loc_data['name'])
            aggregated['locations'][normalized]['mentions'].append(loc_data['mention'])
            aggregated['locations'][normalized]['mention_count'] += 1
            if 'name' not in aggregated['locations'][normalized]:
                aggregated['locations'][normalized]['name'] = loc_data['name']

        # Events (dates with context)
        for date_data in doc_entities['dates']:
            normalized = normalize_entity(date_data['name'])
            aggregated['events'][normalized]['mentions'].append(date_data['mention'])
            aggregated['events'][normalized]['mention_count'] += 1
            if 'name' not in aggregated['events'][normalized]:
                aggregated['events'][normalized]['name'] = date_data['name']

    # Convert to final format
    final = {
        'people': [],
        'organizations': [],
        'locations': [],
        'events': []
    }

    for normalized, data in aggregated['people'].items():
        final['people'].append({
            'name': data['name'],
            'normalized': normalized,
            'mentions': data['mentions'],
            'mention_count': data['mention_count']
        })

    for normalized, data in aggregated['organizations'].items():
        final['organizations'].append({
            'name': data['name'],
            'normalized': normalized,
            'mentions': data['mentions'],
            'mention_count': data['mention_count']
        })

    for normalized, data in aggregated['locations'].items():
        final['locations'].append({
            'name': data['name'],
            'normalized': normalized,
            'mentions': data['mentions'],
            'mention_count': data['mention_count']
        })

    for normalized, data in aggregated['events'].items():
        final['events'].append({
            'name': data['name'],
            'normalized': normalized,
            'mentions': data['mentions'],
            'mention_count': data['mention_count']
        })

    # Sort by mention count (most mentioned first)
    for category in final:
        final[category].sort(key=lambda x: x['mention_count'], reverse=True)

    return final


def main():
    """Main extraction process."""
    print(f"Starting entity extraction for Batch {BATCH_NUM}")
    print(f"Documents: {START_OFFSET + 1} to {START_OFFSET + BATCH_SIZE}")
    print("=" * 60)

    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Query documents for this batch
    query = """
        SELECT bates_id, text_path, full_text, email_from, email_to, email_subject
        FROM documents
        ORDER BY bates_id
        LIMIT ? OFFSET ?
    """
    cursor.execute(query, (BATCH_SIZE, START_OFFSET))
    documents = cursor.fetchall()

    print(f"Retrieved {len(documents)} documents from database")
    print()

    all_document_entities = []
    processed_count = 0
    error_count = 0

    for idx, doc in enumerate(documents):
        doc_id = doc['bates_id']
        text_path = doc['text_path']
        full_text = doc['full_text']

        # Progress reporting
        if (idx + 1) % 100 == 0:
            print(f"Progress: {idx + 1}/{len(documents)} documents processed")

        # Get text content
        text = None

        # Try full_text field first
        if full_text:
            text = full_text
        # Try reading from text file
        elif text_path:
            # The text_path format is like: \HOUSE_OVERSIGHT_009\TEXT\001\HOUSE_OVERSIGHT_030311.txt
            # We need to extract just the filename and folder from the end
            # Extract the part after TEXT\ (e.g., 001\filename.txt)
            text_path_clean = text_path.replace('\\', '/')

            # Try to extract the last two parts (folder/filename.txt)
            parts = text_path_clean.split('/')
            if len(parts) >= 2:
                # Get the last two parts (e.g., 001 and HOUSE_OVERSIGHT_030311.txt)
                folder_and_file = '/'.join(parts[-2:])
                full_path = os.path.join(TEXT_BASE_PATH, folder_and_file)
            else:
                # Fallback: just use the bates_id
                full_path = os.path.join(TEXT_BASE_PATH, '001', f"{doc_id}.txt")

            try:
                if os.path.exists(full_path):
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        text = f.read()
                else:
                    # Try alternate path in folder 002
                    alt_path = os.path.join(TEXT_BASE_PATH, '002', f"{doc_id}.txt")
                    if os.path.exists(alt_path):
                        with open(alt_path, 'r', encoding='utf-8', errors='ignore') as f:
                            text = f.read()
            except Exception as e:
                print(f"  Error reading {doc_id}: {e}")
                error_count += 1
                continue

        # Skip if no text available
        if not text or len(text.strip()) < 10:
            continue

        try:
            # Extract entities using both methods
            pattern_entities = pattern_match_entities(text)
            spacy_entities = spacy_extract_entities(text, doc_id)

            # Merge results
            merged_entities = merge_entities(pattern_entities, spacy_entities, doc_id)
            all_document_entities.append(merged_entities)

            processed_count += 1

        except Exception as e:
            print(f"  Error processing {doc_id}: {e}")
            error_count += 1
            continue

    print()
    print(f"Processed {processed_count} documents successfully")
    print(f"Errors: {error_count}")
    print()
    print("Aggregating entities...")

    # Aggregate entities
    aggregated_entities = aggregate_entities(all_document_entities)

    # Calculate statistics
    stats = {
        'total_entities': sum(len(aggregated_entities[cat]) for cat in aggregated_entities),
        'people_count': len(aggregated_entities['people']),
        'orgs_count': len(aggregated_entities['organizations']),
        'locations_count': len(aggregated_entities['locations']),
        'events_count': len(aggregated_entities['events']),
        'total_mentions': sum(
            sum(e['mention_count'] for e in aggregated_entities[cat])
            for cat in aggregated_entities
        )
    }

    # Create output
    output = {
        'batch': BATCH_NUM,
        'documents_processed': processed_count,
        'documents_with_errors': error_count,
        'extraction_date': datetime.now().isoformat(),
        'entities': aggregated_entities,
        'statistics': stats
    }

    # Write output
    print(f"Writing results to {OUTPUT_PATH}")
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Print summary
    print()
    print("=" * 60)
    print("EXTRACTION COMPLETE")
    print("=" * 60)
    print(f"Documents processed: {processed_count}")
    print(f"Total unique entities: {stats['total_entities']}")
    print(f"  - People: {stats['people_count']}")
    print(f"  - Organizations: {stats['orgs_count']}")
    print(f"  - Locations: {stats['locations_count']}")
    print(f"  - Events/Dates: {stats['events_count']}")
    print(f"Total mentions: {stats['total_mentions']}")
    print()

    # Show top entities
    print("Top 10 People (by mentions):")
    for i, person in enumerate(aggregated_entities['people'][:10], 1):
        print(f"  {i}. {person['name']} ({person['mention_count']} mentions)")
    print()

    print("Top 10 Organizations (by mentions):")
    for i, org in enumerate(aggregated_entities['organizations'][:10], 1):
        print(f"  {i}. {org['name']} ({org['mention_count']} mentions)")
    print()

    print("Top 10 Locations (by mentions):")
    for i, loc in enumerate(aggregated_entities['locations'][:10], 1):
        print(f"  {i}. {loc['name']} ({loc['mention_count']} mentions)")
    print()

    conn.close()
    print(f"Results saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
