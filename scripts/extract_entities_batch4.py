#!/usr/bin/env python3
"""
Entity Extraction Script - Batch 4 (Documents 2176-2897)
Hybrid approach: Pattern matching + spaCy NER
"""

import sqlite3
import json
import re
import os
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple
import spacy
from datetime import datetime

# Configuration
DB_PATH = "/Users/am/Research/Epstein/epstein-wiki/database/documents.db"
TEXT_BASE_PATH = "/Users/am/Research/Epstein/Epstein Estate Documents - Seventh Production"
OUTPUT_PATH = "/Users/am/Research/Epstein/epstein-wiki/output/entities_batch_4.json"
BATCH_START = 2176
BATCH_END = 2897
CONTEXT_CHARS = 50
CONFIDENCE_THRESHOLD = 0.7

# Pattern matching regexes
PATTERNS = {
    'name_with_title': re.compile(r'\b(Mr\.|Ms\.|Mrs\.|Dr\.|Prof\.|Hon\.)\s+([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)', re.MULTILINE),
    'capitalized_name': re.compile(r'\b([A-Z][a-z]+\s+(?:[A-Z]\.?\s+)?[A-Z][a-z]+)\b', re.MULTILINE),
    'organization': re.compile(r'\b([A-Z][A-Za-z\s&]+(?:Corp\.|Corporation|LLC|Inc\.|Incorporated|Ltd\.|Limited|LLP|Foundation|University|Institute|Associates|Partners|Group))', re.MULTILINE),
    'location_city_state': re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s+([A-Z]{2})\b', re.MULTILINE),
    'address': re.compile(r'\b\d+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Street|St\.|Avenue|Ave\.|Road|Rd\.|Boulevard|Blvd\.|Drive|Dr\.|Lane|Ln\.)', re.MULTILINE),
    'date_mdy': re.compile(r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b', re.MULTILINE),
    'date_numeric': re.compile(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', re.MULTILINE),
    'date_iso': re.compile(r'\b\d{4}-\d{2}-\d{2}\b', re.MULTILINE),
}

# Common false positives to filter
EXCLUDE_NAMES = {
    'United States', 'New York', 'Los Angeles', 'San Francisco', 'Palm Beach',
    'The Court', 'The Government', 'The Plaintiff', 'The Defendant',
    'Subject Matter', 'Dear Sir', 'Yours Truly', 'Best Regards',
    'Page Number', 'Document Number', 'Case Number', 'Email Address',
    # Email artifacts
    'On Mon', 'On Tue', 'On Wed', 'On Thu', 'On Fri', 'On Sat', 'On Sun',
    'On Jan', 'On Feb', 'On Mar', 'On Apr', 'On May', 'On Jun', 'On Jul', 'On Aug', 'On Sep', 'On Oct', 'On Nov', 'On Dec',
    # Generic terms
    'Subject Re', 'Subject Fw', 'Re Subject', 'Fw Subject', 'Reid Subject',
    'From Sent', 'To Cc', 'Best Regards', 'Thank You', 'Thanks You',
    # Single names that are too generic
    'Reid', 'Thomas', 'Larry', 'Jeffrey', 'Donald',
}

# Name normalization variants
NAME_VARIANTS = {
    'Jeffrey E. Epstein': 'jeffrey-epstein',
    'Jeffrey Edward Epstein': 'jeffrey-epstein',
    'Jeffrey Epstein': 'jeffrey-epstein',
    'Ghislaine Maxwell': 'ghislaine-maxwell',
    'Ghislaine Noelle Marion Maxwell': 'ghislaine-maxwell',
    'Bill Clinton': 'bill-clinton',
    'William J. Clinton': 'bill-clinton',
    'William Jefferson Clinton': 'bill-clinton',
    'Donald Trump': 'donald-trump',
    'Donald J. Trump': 'donald-trump',
    'Prince Andrew': 'prince-andrew',
    'Andrew Albert Christian Edward': 'prince-andrew',
}


class EntityExtractor:
    """Hybrid entity extractor using pattern matching and spaCy NER"""

    def __init__(self):
        print("Loading spaCy model...")
        self.nlp = spacy.load('en_core_web_lg')
        print("Model loaded successfully")

        self.entities = {
            'people': defaultdict(lambda: {'name': '', 'normalized': '', 'mentions': [], 'mention_count': 0}),
            'organizations': defaultdict(lambda: {'name': '', 'normalized': '', 'mentions': [], 'mention_count': 0}),
            'locations': defaultdict(lambda: {'name': '', 'normalized': '', 'mentions': [], 'mention_count': 0}),
            'events': defaultdict(lambda: {'name': '', 'normalized': '', 'mentions': [], 'mention_count': 0}),
        }

        self.stats = {
            'documents_processed': 0,
            'documents_skipped': 0,
            'errors': [],
            'total_entities': 0,
        }

    def normalize_entity(self, name: str) -> str:
        """Normalize entity name for deduplication"""
        # Check predefined variants
        if name in NAME_VARIANTS:
            return NAME_VARIANTS[name]

        # Default normalization: lowercase, replace spaces with hyphens
        normalized = name.lower().strip()
        normalized = re.sub(r'\s+', '-', normalized)
        normalized = re.sub(r'[^\w\-]', '', normalized)
        return normalized

    def extract_context(self, text: str, position: int, entity: str) -> str:
        """Extract context around entity mention"""
        start = max(0, position - CONTEXT_CHARS)
        end = min(len(text), position + len(entity) + CONTEXT_CHARS)
        context = text[start:end]
        # Clean up whitespace
        context = ' '.join(context.split())
        return context

    def pattern_match_entities(self, text: str, doc_id: str) -> Dict[str, Set[Tuple[str, int]]]:
        """Fast pattern matching for common entity types"""
        matches = {
            'people': set(),
            'organizations': set(),
            'locations': set(),
            'events': set(),
        }

        # Match names with titles
        for match in PATTERNS['name_with_title'].finditer(text):
            full_name = match.group(0).strip()
            if full_name not in EXCLUDE_NAMES:
                matches['people'].add((full_name, match.start()))

        # Match capitalized names (2-3 words)
        for match in PATTERNS['capitalized_name'].finditer(text):
            name = match.group(1).strip()
            # Filter out single names and common false positives
            if name not in EXCLUDE_NAMES and len(name.split()) >= 2:
                matches['people'].add((name, match.start()))

        # Match organizations
        for match in PATTERNS['organization'].finditer(text):
            org = match.group(1).strip()
            matches['organizations'].add((org, match.start()))

        # Match locations (city, state)
        for match in PATTERNS['location_city_state'].finditer(text):
            location = match.group(0).strip()
            matches['locations'].add((location, match.start()))

        # Match addresses
        for match in PATTERNS['address'].finditer(text):
            address = match.group(0).strip()
            matches['locations'].add((address, match.start()))

        # Match dates (as events)
        for pattern_name in ['date_mdy', 'date_numeric', 'date_iso']:
            for match in PATTERNS[pattern_name].finditer(text):
                date = match.group(0).strip()
                matches['events'].add((date, match.start()))

        return matches

    def spacy_extract_entities(self, text: str, doc_id: str) -> Dict[str, Set[Tuple[str, int]]]:
        """Use spaCy NER for entity extraction"""
        matches = {
            'people': set(),
            'organizations': set(),
            'locations': set(),
            'events': set(),
        }

        # Limit text length for spaCy processing (1MB max)
        if len(text) > 1_000_000:
            text = text[:1_000_000]

        try:
            doc = self.nlp(text)

            for ent in doc.ents:
                # Filter by confidence (if available)
                # Note: spaCy doesn't expose confidence directly, but we can use entity type as proxy

                if ent.label_ == 'PERSON':
                    matches['people'].add((ent.text.strip(), ent.start_char))
                elif ent.label_ == 'ORG':
                    matches['organizations'].add((ent.text.strip(), ent.start_char))
                elif ent.label_ in ['GPE', 'LOC', 'FAC']:
                    matches['locations'].add((ent.text.strip(), ent.start_char))
                elif ent.label_ == 'DATE':
                    matches['events'].add((ent.text.strip(), ent.start_char))
                elif ent.label_ == 'EVENT':
                    matches['events'].add((ent.text.strip(), ent.start_char))

        except Exception as e:
            print(f"  Warning: spaCy NER failed for {doc_id}: {e}")
            self.stats['errors'].append({
                'doc_id': doc_id,
                'error': f'spaCy NER failed: {e}'
            })

        return matches

    def merge_entities(self, pattern_matches: Dict, spacy_matches: Dict) -> Dict:
        """Merge and deduplicate entities from both sources"""
        merged = {
            'people': set(),
            'organizations': set(),
            'locations': set(),
            'events': set(),
        }

        for category in merged.keys():
            # Combine both sources
            all_matches = pattern_matches.get(category, set()) | spacy_matches.get(category, set())
            merged[category] = all_matches

        return merged

    def add_entity(self, category: str, entity: str, doc_id: str, position: int, text: str):
        """Add entity to the collection"""
        # Filter out excluded names
        if entity in EXCLUDE_NAMES or entity.strip() in EXCLUDE_NAMES:
            return

        # Filter email artifacts
        if entity.startswith('On ') or entity.endswith(' <'):
            return

        # Filter very short entities (single characters, etc)
        if len(entity.strip()) < 3:
            return

        normalized = self.normalize_entity(entity)

        # Skip very short or invalid entities after normalization
        if len(normalized) < 3:
            return

        entity_dict = self.entities[category][normalized]

        if not entity_dict['name']:
            entity_dict['name'] = entity
            entity_dict['normalized'] = normalized

        # Extract context
        context = self.extract_context(text, position, entity)

        # Add mention
        entity_dict['mentions'].append({
            'doc_id': doc_id,
            'context': context,
            'position': position
        })
        entity_dict['mention_count'] += 1

    def process_document(self, doc_id: str, text_path: str) -> bool:
        """Process a single document"""
        # Extract just the filename from the database path
        # Database has paths like: \HOUSE_OVERSIGHT_009\TEXT\002\HOUSE_OVERSIGHT_032350.txt
        # But we need: TEXT/002/HOUSE_OVERSIGHT_032350.txt
        parts = text_path.replace('\\', '/').split('/')

        # Find TEXT directory and construct path from there
        if 'TEXT' in parts:
            text_idx = parts.index('TEXT')
            relative_path = '/'.join(parts[text_idx:])
            full_path = os.path.join(TEXT_BASE_PATH, relative_path)
        else:
            # Fallback: just use the filename
            filename = parts[-1]
            # Try both subdirectories
            full_path = None
            for subdir in ['001', '002']:
                test_path = os.path.join(TEXT_BASE_PATH, 'TEXT', subdir, filename)
                if os.path.exists(test_path):
                    full_path = test_path
                    break

            if not full_path:
                print(f"  Warning: File not found: {text_path}")
                self.stats['documents_skipped'] += 1
                self.stats['errors'].append({
                    'doc_id': doc_id,
                    'error': 'File not found'
                })
                return False

        if not os.path.exists(full_path):
            print(f"  Warning: File not found: {full_path}")
            self.stats['documents_skipped'] += 1
            self.stats['errors'].append({
                'doc_id': doc_id,
                'error': 'File not found'
            })
            return False

        try:
            # Read text file with encoding handling
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                text = f.read()

            # Skip empty files
            if not text.strip():
                self.stats['documents_skipped'] += 1
                return False

            # Step 1: Pattern matching (fast)
            pattern_matches = self.pattern_match_entities(text, doc_id)

            # Step 2: spaCy NER (slower but more accurate)
            spacy_matches = self.spacy_extract_entities(text, doc_id)

            # Step 3: Merge results
            merged = self.merge_entities(pattern_matches, spacy_matches)

            # Step 4: Add to entity collection
            for category, entities in merged.items():
                for entity, position in entities:
                    self.add_entity(category, entity, doc_id, position, text)

            self.stats['documents_processed'] += 1
            return True

        except Exception as e:
            print(f"  Error processing {doc_id}: {e}")
            self.stats['documents_skipped'] += 1
            self.stats['errors'].append({
                'doc_id': doc_id,
                'error': str(e)
            })
            return False

    def get_documents_from_db(self):
        """Query database for batch 4 documents"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get documents in range (using OFFSET and LIMIT)
        query = """
            SELECT bates_id, text_path
            FROM documents
            ORDER BY bates_id
            LIMIT ? OFFSET ?
        """

        # Calculate limit: from position 2176 to 2897 (722 documents)
        limit = BATCH_END - BATCH_START + 1
        offset = BATCH_START - 1

        cursor.execute(query, (limit, offset))
        documents = cursor.fetchall()
        conn.close()

        return documents

    def run(self):
        """Main extraction process"""
        print(f"\n{'='*80}")
        print(f"Entity Extraction - Batch 4")
        print(f"Documents: {BATCH_START}-{BATCH_END}")
        print(f"{'='*80}\n")

        # Get documents
        print("Querying database...")
        documents = self.get_documents_from_db()
        print(f"Found {len(documents)} documents to process\n")

        # Process each document
        for idx, (doc_id, text_path) in enumerate(documents, 1):
            if idx % 100 == 0:
                print(f"\n[Progress] Processed {idx}/{len(documents)} documents")
                print(f"  People: {len(self.entities['people'])}")
                print(f"  Organizations: {len(self.entities['organizations'])}")
                print(f"  Locations: {len(self.entities['locations'])}")
                print(f"  Events: {len(self.entities['events'])}\n")

            if idx % 10 == 0:
                print(f"  Processing [{idx}/{len(documents)}]: {doc_id}", end='\r')

            self.process_document(doc_id, text_path)

        print(f"\n\nProcessing complete!")
        print(f"  Processed: {self.stats['documents_processed']}")
        print(f"  Skipped: {self.stats['documents_skipped']}")
        print(f"  Errors: {len(self.stats['errors'])}")

    def generate_output(self):
        """Generate JSON output"""
        print("\nGenerating output JSON...")

        # Convert defaultdicts to regular dicts and sort by mention count
        output = {
            'batch': 4,
            'batch_range': f'{BATCH_START}-{BATCH_END}',
            'documents_processed': self.stats['documents_processed'],
            'entities': {
                'people': [],
                'organizations': [],
                'locations': [],
                'events': []
            },
            'statistics': {
                'total_entities': 0,
                'people_count': 0,
                'orgs_count': 0,
                'locations_count': 0,
                'events_count': 0,
                'documents_skipped': self.stats['documents_skipped'],
                'errors': len(self.stats['errors'])
            },
            'processing_info': {
                'timestamp': datetime.now().isoformat(),
                'confidence_threshold': CONFIDENCE_THRESHOLD,
                'context_chars': CONTEXT_CHARS,
                'method': 'hybrid_pattern_spacy'
            }
        }

        # Sort and add entities
        for category in ['people', 'organizations', 'locations', 'events']:
            entities_list = []
            for normalized, data in self.entities[category].items():
                # Limit mentions to top 100 per entity to reduce file size
                mentions = sorted(data['mentions'], key=lambda x: x['doc_id'])[:100]

                entities_list.append({
                    'name': data['name'],
                    'normalized': data['normalized'],
                    'mentions': mentions,
                    'mention_count': data['mention_count']
                })

            # Sort by mention count descending
            entities_list.sort(key=lambda x: x['mention_count'], reverse=True)
            output['entities'][category] = entities_list

            # Update statistics with correct key names
            if category == 'people':
                count_key = 'people_count'
            elif category == 'organizations':
                count_key = 'orgs_count'
            elif category == 'locations':
                count_key = 'locations_count'
            elif category == 'events':
                count_key = 'events_count'

            output['statistics'][count_key] = len(entities_list)
            output['statistics']['total_entities'] += len(entities_list)

        # Add error log (limit to first 100 errors)
        if self.stats['errors']:
            output['errors'] = self.stats['errors'][:100]

        # Write to file
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"Output saved to: {OUTPUT_PATH}")
        return output

    def print_summary(self, output: Dict):
        """Print summary report"""
        print(f"\n{'='*80}")
        print("SUMMARY REPORT - Batch 4 Entity Extraction")
        print(f"{'='*80}\n")

        stats = output['statistics']
        print(f"Documents Processed: {output['documents_processed']}")
        print(f"Documents Skipped: {stats['documents_skipped']}")
        print(f"Errors: {stats['errors']}\n")

        print(f"Total Unique Entities: {stats['total_entities']}")
        print(f"  - People: {stats['people_count']}")
        print(f"  - Organizations: {stats['orgs_count']}")
        print(f"  - Locations: {stats['locations_count']}")
        print(f"  - Events/Dates: {stats['events_count']}\n")

        # Top entities
        print("TOP ENTITIES BY MENTIONS:\n")

        print("People (Top 10):")
        for i, entity in enumerate(output['entities']['people'][:10], 1):
            print(f"  {i:2d}. {entity['name']:<40s} ({entity['mention_count']} mentions)")

        print("\nOrganizations (Top 10):")
        for i, entity in enumerate(output['entities']['organizations'][:10], 1):
            print(f"  {i:2d}. {entity['name']:<40s} ({entity['mention_count']} mentions)")

        print("\nLocations (Top 10):")
        for i, entity in enumerate(output['entities']['locations'][:10], 1):
            print(f"  {i:2d}. {entity['name']:<40s} ({entity['mention_count']} mentions)")

        print(f"\n{'='*80}\n")


def main():
    """Main entry point"""
    extractor = EntityExtractor()

    try:
        # Run extraction
        extractor.run()

        # Generate output
        output = extractor.generate_output()

        # Print summary
        extractor.print_summary(output)

        print("✓ Entity extraction complete!")
        return 0

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 1
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
