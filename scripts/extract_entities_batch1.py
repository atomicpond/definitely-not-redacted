#!/usr/bin/env python3
"""
Entity Extraction Script - Batch 1
Extracts entities (People, Organizations, Locations, Dates/Events) from documents 1-725
using hybrid pattern-matching + AI (spaCy) approach.
"""

import sqlite3
import json
import re
import os
from collections import defaultdict
from typing import Dict, List, Set, Tuple
import spacy
from pathlib import Path

# Load spaCy model
print("Loading spaCy model...")
nlp = spacy.load("en_core_web_lg")

# Configuration
DB_PATH = "/Users/am/Research/Epstein/epstein-wiki/database/documents.db"
BASE_TEXT_PATH = "/Users/am/Research/Epstein/Epstein Estate Documents - Seventh Production"
OUTPUT_PATH = "/Users/am/Research/Epstein/epstein-wiki/output/entities_batch_1.json"
BATCH_SIZE = 725
CONTEXT_WINDOW = 50
CONFIDENCE_THRESHOLD = 0.7

# Pattern matching regexes
PATTERNS = {
    'name': [
        r'\b(?:Mr|Ms|Mrs|Dr|Prof|Hon)\.\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\b',
        r'\b[A-Z][a-z]+\s+[A-Z]\.\s+[A-Z][a-z]+\b',
        r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b(?:\s+[A-Z][a-z]+)?'
    ],
    'organization': [
        r'\b[A-Z][A-Za-z\s&]+(?:Corp|Corporation|LLC|Inc|Ltd|LLP|LP)\b',
        r'\b[A-Z][A-Za-z\s]+(?:University|College|Foundation|Institute|Trust|Bank|Group|Partners|Associates)\b',
        r'\b(?:The\s+)?[A-Z][A-Za-z\s&]+(?:Company|Firm|Law\s+Firm)\b'
    ],
    'location': [
        r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?,\s+[A-Z]{2}\b',  # City, ST
        r'\b\d+\s+[A-Z][A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln)\b',
        r'\b(?:New York|Los Angeles|Miami|London|Paris|Tokyo|Hong Kong|Singapore|Dubai|Monaco|Switzerland)\b'
    ],
    'date': [
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
        r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
        r'\b\d{4}-\d{2}-\d{2}\b'
    ]
}

# Common words to filter out from names
COMMON_WORDS = {
    'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
    'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after',
    'above', 'below', 'between', 'under', 'again', 'further', 'then', 'once',
    'here', 'there', 'when', 'where', 'why', 'how', 'all', 'both', 'each',
    'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
    'own', 'same', 'so', 'than', 'too', 'very', 'can', 'will', 'just', 'should',
    'now', 'Dear', 'Subject', 'From', 'Sent', 'Received', 'Page', 'Document',
    'Exhibit', 'Attachment', 'Email', 'Date', 'Time', 'File', 'Folder'
}


def normalize_entity(name: str) -> str:
    """Normalize entity name to lowercase with hyphens."""
    # Remove titles
    name = re.sub(r'^(?:Mr|Ms|Mrs|Dr|Prof|Hon)\.\s+', '', name)
    # Clean up whitespace
    name = ' '.join(name.split())
    # Convert to lowercase and replace spaces with hyphens
    return name.lower().replace(' ', '-')


def is_valid_entity(text: str, entity_type: str) -> bool:
    """Filter out invalid entities."""
    text_lower = text.lower()

    # Filter out single words for names
    if entity_type == 'PERSON' and ' ' not in text.strip():
        return False

    # Filter out common words
    if any(word in text_lower for word in COMMON_WORDS):
        if entity_type == 'PERSON':
            return False

    # Filter out very short entities
    if len(text.strip()) < 3:
        return False

    # Filter out all-caps junk
    if text.isupper() and len(text) > 20:
        return False

    return True


def extract_context(text: str, start: int, end: int, window: int = CONTEXT_WINDOW) -> str:
    """Extract context around an entity mention."""
    context_start = max(0, start - window)
    context_end = min(len(text), end + window)
    context = text[context_start:context_end]

    # Clean up context
    context = ' '.join(context.split())
    if context_start > 0:
        context = '...' + context
    if context_end < len(text):
        context = context + '...'

    return context


def extract_with_patterns(text: str, doc_id: str) -> Dict[str, List[Dict]]:
    """Extract entities using pattern matching."""
    entities = {
        'people': [],
        'organizations': [],
        'locations': [],
        'dates': []
    }

    # Names
    for pattern in PATTERNS['name']:
        for match in re.finditer(pattern, text):
            name = match.group()
            if is_valid_entity(name, 'PERSON'):
                entities['people'].append({
                    'text': name,
                    'start': match.start(),
                    'end': match.end(),
                    'method': 'pattern'
                })

    # Organizations
    for pattern in PATTERNS['organization']:
        for match in re.finditer(pattern, text):
            org = match.group()
            if is_valid_entity(org, 'ORG'):
                entities['organizations'].append({
                    'text': org,
                    'start': match.start(),
                    'end': match.end(),
                    'method': 'pattern'
                })

    # Locations
    for pattern in PATTERNS['location']:
        for match in re.finditer(pattern, text):
            loc = match.group()
            if is_valid_entity(loc, 'GPE'):
                entities['locations'].append({
                    'text': loc,
                    'start': match.start(),
                    'end': match.end(),
                    'method': 'pattern'
                })

    # Dates
    for pattern in PATTERNS['date']:
        for match in re.finditer(pattern, text):
            date = match.group()
            entities['dates'].append({
                'text': date,
                'start': match.start(),
                'end': match.end(),
                'method': 'pattern'
            })

    return entities


def extract_with_spacy(text: str, doc_id: str) -> Dict[str, List[Dict]]:
    """Extract entities using spaCy NER."""
    entities = {
        'people': [],
        'organizations': [],
        'locations': [],
        'dates': []
    }

    # Process with spaCy (limit text length for performance)
    max_length = 1000000  # 1M characters max
    if len(text) > max_length:
        text = text[:max_length]

    doc = nlp(text)

    for ent in doc.ents:
        # Use entity confidence if available
        confidence = 1.0  # Default confidence

        if ent.label_ == 'PERSON':
            if is_valid_entity(ent.text, 'PERSON'):
                entities['people'].append({
                    'text': ent.text,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'method': 'spacy',
                    'confidence': confidence
                })
        elif ent.label_ == 'ORG':
            if is_valid_entity(ent.text, 'ORG'):
                entities['organizations'].append({
                    'text': ent.text,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'method': 'spacy',
                    'confidence': confidence
                })
        elif ent.label_ in ['GPE', 'LOC']:
            if is_valid_entity(ent.text, 'GPE'):
                entities['locations'].append({
                    'text': ent.text,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'method': 'spacy',
                    'confidence': confidence
                })
        elif ent.label_ == 'DATE':
            entities['dates'].append({
                'text': ent.text,
                'start': ent.start_char,
                'end': ent.end_char,
                'method': 'spacy',
                'confidence': confidence
            })

    return entities


def merge_entities(pattern_entities: Dict, spacy_entities: Dict) -> Dict:
    """Merge entities from both methods, removing duplicates."""
    merged = {
        'people': [],
        'organizations': [],
        'locations': [],
        'dates': []
    }

    for entity_type in ['people', 'organizations', 'locations', 'dates']:
        seen = set()

        # Add pattern matches
        for ent in pattern_entities[entity_type]:
            normalized = normalize_entity(ent['text'])
            if normalized not in seen:
                seen.add(normalized)
                merged[entity_type].append(ent)

        # Add spaCy matches
        for ent in spacy_entities[entity_type]:
            normalized = normalize_entity(ent['text'])
            # Only add if not already found by patterns
            if normalized not in seen:
                seen.add(normalized)
                merged[entity_type].append(ent)

    return merged


def process_document(doc_id: str, text_path: str, full_text: str) -> Dict:
    """Process a single document and extract entities."""
    # Try to read from text file first, fall back to full_text
    text = None

    if text_path:
        # Convert Windows path to Unix path
        text_path = text_path.replace('\\', '/')
        # Remove leading slash if present
        text_path = text_path.lstrip('/')
        # Remove production set prefix (e.g., HOUSE_OVERSIGHT_009/)
        # The path in DB is like: HOUSE_OVERSIGHT_009/TEXT/001/file.txt
        # But actual path is: TEXT/001/file.txt
        parts = text_path.split('/')
        if len(parts) > 1 and 'TEXT' in parts:
            # Find TEXT and take everything from there
            text_idx = parts.index('TEXT')
            text_path = '/'.join(parts[text_idx:])
        full_path = os.path.join(BASE_TEXT_PATH, text_path)

        if os.path.exists(full_path):
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
            except Exception as e:
                print(f"  Warning: Could not read {full_path}: {e}")

    # Fall back to full_text from database
    if not text and full_text:
        text = full_text

    if not text:
        return None

    # Extract with both methods
    pattern_entities = extract_with_patterns(text, doc_id)
    spacy_entities = extract_with_spacy(text, doc_id)

    # Merge results
    merged = merge_entities(pattern_entities, spacy_entities)

    # Add context to each entity
    for entity_type in merged:
        for ent in merged[entity_type]:
            ent['context'] = extract_context(text, ent['start'], ent['end'])
            ent['doc_id'] = doc_id

    return merged


def aggregate_entities(all_entities: List[Dict]) -> Dict:
    """Aggregate entities across all documents."""
    aggregated = {
        'people': defaultdict(lambda: {'normalized': '', 'mentions': [], 'mention_count': 0}),
        'organizations': defaultdict(lambda: {'normalized': '', 'mentions': [], 'mention_count': 0}),
        'locations': defaultdict(lambda: {'normalized': '', 'mentions': [], 'mention_count': 0}),
        'events': defaultdict(lambda: {'normalized': '', 'mentions': [], 'mention_count': 0})
    }

    for doc_entities in all_entities:
        if not doc_entities:
            continue

        # Process people
        for ent in doc_entities.get('people', []):
            name = ent['text']
            normalized = normalize_entity(name)
            aggregated['people'][name]['normalized'] = normalized
            aggregated['people'][name]['mentions'].append({
                'doc_id': ent['doc_id'],
                'context': ent['context'],
                'position': ent['start']
            })
            aggregated['people'][name]['mention_count'] += 1

        # Process organizations
        for ent in doc_entities.get('organizations', []):
            org = ent['text']
            normalized = normalize_entity(org)
            aggregated['organizations'][org]['normalized'] = normalized
            aggregated['organizations'][org]['mentions'].append({
                'doc_id': ent['doc_id'],
                'context': ent['context'],
                'position': ent['start']
            })
            aggregated['organizations'][org]['mention_count'] += 1

        # Process locations
        for ent in doc_entities.get('locations', []):
            loc = ent['text']
            normalized = normalize_entity(loc)
            aggregated['locations'][loc]['normalized'] = normalized
            aggregated['locations'][loc]['mentions'].append({
                'doc_id': ent['doc_id'],
                'context': ent['context'],
                'position': ent['start']
            })
            aggregated['locations'][loc]['mention_count'] += 1

        # Process dates/events
        for ent in doc_entities.get('dates', []):
            date = ent['text']
            normalized = normalize_entity(date)
            aggregated['events'][date]['normalized'] = normalized
            aggregated['events'][date]['mentions'].append({
                'doc_id': ent['doc_id'],
                'context': ent['context'],
                'position': ent['start']
            })
            aggregated['events'][date]['mention_count'] += 1

    # Convert to final format
    result = {
        'people': [],
        'organizations': [],
        'locations': [],
        'events': []
    }

    for entity_type in ['people', 'organizations', 'locations', 'events']:
        for name, data in aggregated[entity_type].items():
            result[entity_type].append({
                'name': name,
                'normalized': data['normalized'],
                'mentions': data['mentions'][:100],  # Limit to first 100 mentions
                'mention_count': data['mention_count']
            })

    # Sort by mention count
    for entity_type in result:
        result[entity_type].sort(key=lambda x: x['mention_count'], reverse=True)

    return result


def main():
    """Main processing function."""
    print(f"Starting entity extraction for batch 1 (documents 1-{BATCH_SIZE})")
    print(f"Database: {DB_PATH}")
    print(f"Output: {OUTPUT_PATH}")
    print()

    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get first 725 documents
    print(f"Fetching first {BATCH_SIZE} documents...")
    cursor.execute("""
        SELECT bates_id, text_path, full_text
        FROM documents
        ORDER BY bates_id
        LIMIT ?
    """, (BATCH_SIZE,))

    documents = cursor.fetchall()
    print(f"Retrieved {len(documents)} documents")
    print()

    # Process documents
    all_entities = []
    processed = 0
    errors = 0

    for idx, (doc_id, text_path, full_text) in enumerate(documents, 1):
        try:
            entities = process_document(doc_id, text_path, full_text)
            if entities:
                all_entities.append(entities)
                processed += 1

            # Progress report every 100 documents
            if idx % 100 == 0:
                print(f"Progress: {idx}/{len(documents)} documents processed ({processed} successful, {errors} errors)")

        except Exception as e:
            errors += 1
            print(f"  Error processing {doc_id}: {e}")

    print()
    print(f"Processing complete: {processed} documents, {errors} errors")
    print()

    # Aggregate entities
    print("Aggregating entities...")
    aggregated = aggregate_entities(all_entities)

    # Calculate statistics
    statistics = {
        'total_entities': sum(len(aggregated[t]) for t in aggregated),
        'people_count': len(aggregated['people']),
        'orgs_count': len(aggregated['organizations']),
        'locations_count': len(aggregated['locations']),
        'events_count': len(aggregated['events'])
    }

    # Create output
    output = {
        'batch': 1,
        'documents_processed': processed,
        'entities': aggregated,
        'statistics': statistics
    }

    # Save to JSON
    print(f"Saving results to {OUTPUT_PATH}...")
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print()
    print("=" * 60)
    print("ENTITY EXTRACTION COMPLETE")
    print("=" * 60)
    print(f"Documents processed: {processed}")
    print(f"Errors: {errors}")
    print(f"Total unique entities: {statistics['total_entities']}")
    print(f"  - People: {statistics['people_count']}")
    print(f"  - Organizations: {statistics['orgs_count']}")
    print(f"  - Locations: {statistics['locations_count']}")
    print(f"  - Events/Dates: {statistics['events_count']}")
    print()

    # Show top entities
    print("Top 10 Most Mentioned People:")
    for i, person in enumerate(aggregated['people'][:10], 1):
        print(f"  {i}. {person['name']} ({person['mention_count']} mentions)")
    print()

    print("Top 10 Most Mentioned Organizations:")
    for i, org in enumerate(aggregated['organizations'][:10], 1):
        print(f"  {i}. {org['name']} ({org['mention_count']} mentions)")
    print()

    print("Top 10 Most Mentioned Locations:")
    for i, loc in enumerate(aggregated['locations'][:10], 1):
        print(f"  {i}. {loc['name']} ({loc['mention_count']} mentions)")
    print()

    conn.close()


if __name__ == '__main__':
    main()
