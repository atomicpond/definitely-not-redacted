#!/usr/bin/env python3
"""
Entity Extraction Script - Batch 2 (Documents 726-1450)
Hybrid pattern-matching + AI approach using spaCy
"""

import sqlite3
import json
import re
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Set
import spacy
from datetime import datetime

# Configuration
DB_PATH = "/Users/am/Research/Epstein/epstein-wiki/database/documents.db"
TEXT_BASE_PATH = "/Users/am/Research/Epstein/Epstein Estate Documents - Seventh Production/TEXT"
OUTPUT_PATH = "/Users/am/Research/Epstein/epstein-wiki/output/entities_batch_2.json"
BATCH_NUM = 2
OFFSET = 725
LIMIT = 725
CONTEXT_CHARS = 50

# Load spaCy model
print("Loading spaCy model...")
nlp = spacy.load("en_core_web_lg")
print("spaCy model loaded successfully\n")

class EntityExtractor:
    def __init__(self):
        self.entities = {
            "people": defaultdict(lambda: {"mentions": [], "variants": set()}),
            "organizations": defaultdict(lambda: {"mentions": [], "variants": set()}),
            "locations": defaultdict(lambda: {"mentions": [], "variants": set()}),
            "events": defaultdict(lambda: {"mentions": [], "variants": set()})
        }
        self.stats = {
            "total_docs": 0,
            "processed_docs": 0,
            "skipped_docs": 0,
            "errors": []
        }

        # Pattern definitions
        self.name_titles = r'\b(Mr\.|Ms\.|Mrs\.|Dr\.|Prof\.|Sir|Lady|Hon\.)'
        self.org_suffixes = r'\b(Corp\.?|Corporation|LLC|Inc\.?|Incorporated|Ltd\.?|Limited|LLP|LP|Foundation|University|Institute|College|School|Academy|Association|Society|Trust|Group|Holdings|Partners|Ventures|Capital|Management|Advisors|Consulting)'

    def normalize_entity(self, name: str) -> str:
        """Normalize entity name for deduplication"""
        # Remove titles
        name = re.sub(r'\b(Mr\.|Ms\.|Mrs\.|Dr\.|Prof\.|Sir|Lady|Hon\.)\s+', '', name)
        # Remove middle initials for people
        name = re.sub(r'\b([A-Z])\.\s+', r'\1 ', name)
        # Convert to lowercase and replace spaces with hyphens
        normalized = name.lower().strip()
        normalized = re.sub(r'\s+', '-', normalized)
        normalized = re.sub(r'[^\w\-]', '', normalized)
        return normalized

    def extract_context(self, text: str, start: int, end: int) -> str:
        """Extract context around entity mention"""
        context_start = max(0, start - CONTEXT_CHARS)
        context_end = min(len(text), end + CONTEXT_CHARS)
        context = text[context_start:context_end]
        # Clean up context
        context = ' '.join(context.split())
        return context

    def pattern_match_entities(self, text: str, doc_id: str) -> Dict:
        """Fast pattern matching for entities"""
        matches = {
            "people": [],
            "organizations": [],
            "locations": [],
            "dates": []
        }

        # Match names with titles
        title_pattern = self.name_titles + r'\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})'
        for match in re.finditer(title_pattern, text):
            full_name = match.group(0)
            matches["people"].append({
                "text": full_name,
                "start": match.start(),
                "end": match.end()
            })

        # Match capitalized names (2-3 words)
        name_pattern = r'\b([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b'
        for match in re.finditer(name_pattern, text):
            name = match.group(1)
            # Filter out common false positives
            if not re.match(r'^(The|This|That|Which|When|Where|What|Who|How|Page|Date|Time|From|To|Re|Subject)\s', name):
                matches["people"].append({
                    "text": name,
                    "start": match.start(),
                    "end": match.end()
                })

        # Match organizations
        org_pattern = r'\b([A-Z][A-Za-z\s&]+(?:' + self.org_suffixes + r'))'
        for match in re.finditer(org_pattern, text):
            matches["organizations"].append({
                "text": match.group(1),
                "start": match.start(),
                "end": match.end()
            })

        # Match dates with various formats
        date_patterns = [
            r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',
            r'\b([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})\b',
            r'\b(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})\b',
            r'\b([A-Z][a-z]+\s+\d{4})\b'
        ]
        for pattern in date_patterns:
            for match in re.finditer(pattern, text):
                matches["dates"].append({
                    "text": match.group(1),
                    "start": match.start(),
                    "end": match.end()
                })

        # Match locations (US states, cities with state)
        location_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?,\s+[A-Z]{2})\b'
        for match in re.finditer(location_pattern, text):
            matches["locations"].append({
                "text": match.group(1),
                "start": match.start(),
                "end": match.end()
            })

        return matches

    def spacy_extract(self, text: str, doc_id: str) -> Dict:
        """AI-based entity extraction using spaCy"""
        matches = {
            "people": [],
            "organizations": [],
            "locations": [],
            "dates": []
        }

        # Process text with spaCy (in chunks if too long)
        max_length = 1000000  # spaCy's default limit
        if len(text) > max_length:
            # Process in chunks
            chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
            offset = 0
            for chunk in chunks:
                doc = nlp(chunk)
                self._extract_from_doc(doc, matches, offset)
                offset += len(chunk)
        else:
            doc = nlp(text)
            self._extract_from_doc(doc, matches, 0)

        return matches

    def _extract_from_doc(self, doc, matches, offset):
        """Extract entities from spaCy doc object"""
        for ent in doc.ents:
            # Only include entities with reasonable confidence
            # spaCy doesn't expose confidence directly, but we can filter by label
            if ent.label_ == "PERSON":
                matches["people"].append({
                    "text": ent.text,
                    "start": ent.start_char + offset,
                    "end": ent.end_char + offset,
                    "label": ent.label_
                })
            elif ent.label_ in ["ORG", "PRODUCT"]:
                matches["organizations"].append({
                    "text": ent.text,
                    "start": ent.start_char + offset,
                    "end": ent.end_char + offset,
                    "label": ent.label_
                })
            elif ent.label_ in ["GPE", "LOC", "FAC"]:
                matches["locations"].append({
                    "text": ent.text,
                    "start": ent.start_char + offset,
                    "end": ent.end_char + offset,
                    "label": ent.label_
                })
            elif ent.label_ in ["DATE", "TIME", "EVENT"]:
                matches["dates"].append({
                    "text": ent.text,
                    "start": ent.start_char + offset,
                    "end": ent.end_char + offset,
                    "label": ent.label_
                })

    def merge_entities(self, pattern_matches: Dict, spacy_matches: Dict, text: str, doc_id: str):
        """Merge pattern and spaCy matches, deduplicate"""
        all_matches = {
            "people": pattern_matches["people"] + spacy_matches["people"],
            "organizations": pattern_matches["organizations"] + spacy_matches["organizations"],
            "locations": pattern_matches["locations"] + spacy_matches["locations"],
            "events": pattern_matches["dates"] + spacy_matches["dates"]
        }

        # Process each entity type
        for entity_type, matches in all_matches.items():
            seen_positions = set()

            for match in matches:
                entity_text = match["text"].strip()
                start = match["start"]
                end = match["end"]

                # Skip if too short or at same position as already processed
                if len(entity_text) < 2 or (start, end) in seen_positions:
                    continue

                seen_positions.add((start, end))

                # Normalize entity name
                normalized = self.normalize_entity(entity_text)
                if not normalized:
                    continue

                # Extract context
                context = self.extract_context(text, start, end)

                # Add to entities
                self.entities[entity_type][normalized]["mentions"].append({
                    "doc_id": doc_id,
                    "context": context,
                    "position": start,
                    "original_text": entity_text
                })
                self.entities[entity_type][normalized]["variants"].add(entity_text)

    def process_document(self, doc_id: str, text_path: str) -> bool:
        """Process a single document"""
        try:
            # Construct full path
            if text_path:
                # Extract just the filename part from the path
                # Database has paths like: \HOUSE_OVERSIGHT_009\TEXT\001\HOUSE_OVERSIGHT_026165.txt
                # We need: 001/HOUSE_OVERSIGHT_026165.txt (TEXT_BASE_PATH already has TEXT)
                parts = text_path.replace('\\', '/').split('/')
                # Find 'TEXT' in parts and take everything after it
                if 'TEXT' in parts:
                    text_idx = parts.index('TEXT')
                    relative_path = '/'.join(parts[text_idx+1:])  # Skip TEXT itself
                else:
                    # Fallback: use last two parts (folder/filename.txt)
                    relative_path = '/'.join(parts[-2:])

                full_path = os.path.join(TEXT_BASE_PATH, relative_path)
            else:
                self.stats["skipped_docs"] += 1
                return False

            # Check if file exists
            if not os.path.exists(full_path):
                self.stats["errors"].append(f"File not found: {full_path}")
                self.stats["skipped_docs"] += 1
                return False

            # Read text file
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
            except Exception as e:
                self.stats["errors"].append(f"Error reading {full_path}: {str(e)}")
                self.stats["skipped_docs"] += 1
                return False

            # Skip empty files
            if not text or len(text.strip()) < 10:
                self.stats["skipped_docs"] += 1
                return False

            # Apply pattern matching
            pattern_matches = self.pattern_match_entities(text, doc_id)

            # Apply spaCy NER
            spacy_matches = self.spacy_extract(text, doc_id)

            # Merge and deduplicate
            self.merge_entities(pattern_matches, spacy_matches, text, doc_id)

            self.stats["processed_docs"] += 1
            return True

        except Exception as e:
            self.stats["errors"].append(f"Error processing {doc_id}: {str(e)}")
            self.stats["skipped_docs"] += 1
            return False

    def generate_output(self) -> Dict:
        """Generate final JSON output"""
        output = {
            "batch": BATCH_NUM,
            "documents_processed": self.stats["processed_docs"],
            "entities": {
                "people": [],
                "organizations": [],
                "locations": [],
                "events": []
            },
            "statistics": {
                "total_entities": 0,
                "people_count": 0,
                "orgs_count": 0,
                "locations_count": 0,
                "events_count": 0,
                "total_docs": self.stats["total_docs"],
                "processed_docs": self.stats["processed_docs"],
                "skipped_docs": self.stats["skipped_docs"],
                "error_count": len(self.stats["errors"])
            },
            "processing_info": {
                "start_time": self.start_time,
                "end_time": datetime.now().isoformat(),
                "batch_offset": OFFSET,
                "batch_limit": LIMIT
            }
        }

        # Convert entities to output format
        for entity_type in ["people", "organizations", "locations", "events"]:
            for normalized, data in self.entities[entity_type].items():
                entity_obj = {
                    "name": list(data["variants"])[0] if data["variants"] else normalized,
                    "normalized": normalized,
                    "variants": list(data["variants"]),
                    "mentions": data["mentions"],
                    "mention_count": len(data["mentions"])
                }
                output["entities"][entity_type].append(entity_obj)

            # Sort by mention count
            output["entities"][entity_type].sort(key=lambda x: x["mention_count"], reverse=True)

            # Update statistics with correct keys
            if entity_type == "people":
                count_key = "people_count"
            elif entity_type == "organizations":
                count_key = "orgs_count"
            elif entity_type == "locations":
                count_key = "locations_count"
            elif entity_type == "events":
                count_key = "events_count"

            output["statistics"][count_key] = len(output["entities"][entity_type])
            output["statistics"]["total_entities"] += len(output["entities"][entity_type])

        return output


def main():
    print("=" * 80)
    print("ENTITY EXTRACTION - BATCH 2")
    print("Documents 726-1450")
    print("=" * 80)
    print()

    # Initialize extractor
    extractor = EntityExtractor()
    extractor.start_time = datetime.now().isoformat()

    # Connect to database
    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Query documents for batch 2
    query = """
        SELECT bates_id, text_path
        FROM documents
        ORDER BY bates_id
        LIMIT ? OFFSET ?
    """
    cursor.execute(query, (LIMIT, OFFSET))
    documents = cursor.fetchall()

    extractor.stats["total_docs"] = len(documents)
    print(f"Found {len(documents)} documents in batch 2\n")

    # Process documents
    for idx, (bates_id, text_path) in enumerate(documents, 1):
        if idx % 100 == 0 or idx == 1:
            print(f"Processing document {idx}/{len(documents)}: {bates_id}")

        extractor.process_document(bates_id, text_path)

        if idx % 100 == 0:
            print(f"  Progress: {extractor.stats['processed_docs']} processed, "
                  f"{extractor.stats['skipped_docs']} skipped")
            print(f"  Entities so far: "
                  f"{len(extractor.entities['people'])} people, "
                  f"{len(extractor.entities['organizations'])} orgs, "
                  f"{len(extractor.entities['locations'])} locations, "
                  f"{len(extractor.entities['events'])} events")
            print()

    # Close database
    conn.close()

    # Generate output
    print("\nGenerating output...")
    output = extractor.generate_output()

    # Save to JSON
    print(f"Saving to: {OUTPUT_PATH}")
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print("EXTRACTION COMPLETE")
    print("=" * 80)
    print(f"Total documents: {output['statistics']['total_docs']}")
    print(f"Processed: {output['statistics']['processed_docs']}")
    print(f"Skipped: {output['statistics']['skipped_docs']}")
    print(f"Errors: {output['statistics']['error_count']}")
    print()
    print("ENTITY STATISTICS:")
    print(f"  People: {output['statistics']['people_count']}")
    print(f"  Organizations: {output['statistics']['orgs_count']}")
    print(f"  Locations: {output['statistics']['locations_count']}")
    print(f"  Events/Dates: {output['statistics']['events_count']}")
    print(f"  Total unique entities: {output['statistics']['total_entities']}")
    print()

    # Show top entities
    print("TOP 10 MOST MENTIONED ENTITIES:")
    print("\nPeople:")
    for entity in output['entities']['people'][:10]:
        print(f"  - {entity['name']}: {entity['mention_count']} mentions")

    print("\nOrganizations:")
    for entity in output['entities']['organizations'][:10]:
        print(f"  - {entity['name']}: {entity['mention_count']} mentions")

    print("\nLocations:")
    for entity in output['entities']['locations'][:10]:
        print(f"  - {entity['name']}: {entity['mention_count']} mentions")

    print("\n" + "=" * 80)

    # Print errors if any
    if extractor.stats["errors"]:
        print(f"\nFirst 10 errors:")
        for error in extractor.stats["errors"][:10]:
            print(f"  - {error}")

    return output


if __name__ == "__main__":
    main()
