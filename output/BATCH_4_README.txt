================================================================================
ENTITY EXTRACTION - BATCH 4 (Documents 2176-2897)
================================================================================

COMPLETION DATE: 2025-11-13
AGENT: Agent 5 - Entity Extractor
STATUS: ✓ COMPLETE

================================================================================
DELIVERABLES
================================================================================

1. PRIMARY OUTPUT (JSON)
   File: /Users/am/Research/Epstein/epstein-wiki/output/entities_batch_4.json
   Size: 4.2 MB
   Format: Structured JSON with entities, mentions, and statistics

2. SUMMARY REPORT (Markdown)
   File: /Users/am/Research/Epstein/epstein-wiki/output/entities_batch_4_report.md
   Contents: Detailed analysis, statistics, and findings

3. EXTRACTION SCRIPT (Python)
   File: /Users/am/Research/Epstein/epstein-wiki/scripts/extract_entities_batch4.py
   Type: Reusable Python script for entity extraction

4. THIS README
   File: /Users/am/Research/Epstein/epstein-wiki/output/BATCH_4_README.txt

================================================================================
PROCESSING SUMMARY
================================================================================

Documents Processed:  722 / 722 (100%)
Documents Skipped:    0
Processing Errors:    0
Success Rate:         100%

Total Unique Entities: 4,602
  - People:           2,249 (48.9%)
  - Organizations:      662 (14.4%)
  - Locations:          353 (7.7%)
  - Events/Dates:     1,338 (29.1%)

================================================================================
KEY FINDINGS
================================================================================

HIGH-PROFILE PEOPLE IDENTIFIED:
  • Jeffrey Epstein: 188 mentions
  • Donald Trump: 87+ mentions
  • Bill Clinton: 38+ mentions
  • Kathy Ruemmler: 90 mentions (Former White House Counsel)
  • Larry Summers: 36 mentions (Former Treasury Secretary)
  • Prince Andrew: 35 mentions
  • Ghislaine Maxwell: 30 mentions
  • Alan Dershowitz: 45 mentions

ORGANIZATIONS:
  • HBRK Associates Inc.: 67 mentions (Epstein's company)
  • New York Times: 78 mentions
  • Boeing: 46 mentions
  • Tech companies (Google, Facebook, Twitter): 33-82 mentions

INTERNATIONAL SCOPE:
  • China: 103 mentions
  • Paris: 49 mentions
  • Israel: 24 mentions
  • Other: London, Russia, Japan (12-22 mentions each)

DOCUMENT CHARACTERISTICS:
  • Primarily email correspondence
  • Timeframe: Late 2016 (post-election period)
  • Focus: Financial/business communications, media interactions
  • Geographic scope: Global (US, Europe, Asia)

================================================================================
METHODOLOGY
================================================================================

EXTRACTION METHOD: Hybrid Pattern-Matching + AI (spaCy NER)

PATTERN MATCHING (Fast Layer):
  - Names with titles (Mr./Ms./Dr./Prof.)
  - Organizations (Corp/LLC/Inc/Foundation/University)
  - Locations (City, State patterns, addresses)
  - Dates (Multiple formats: MDY, numeric, ISO)

AI VALIDATION (spaCy Layer):
  - Model: en_core_web_lg (large English model)
  - Entity types: PERSON, ORG, GPE, LOC, FAC, DATE, EVENT
  - Confidence threshold: 0.7

POST-PROCESSING:
  - Entity normalization (lowercase, hyphenated IDs)
  - Variant merging (e.g., "Jeffrey E. Epstein" → "jeffrey-epstein")
  - Context extraction (50 characters before/after)
  - False positive filtering (email artifacts, generic terms)
  - Mention limiting (top 100 per entity for file size)

================================================================================
HOW TO USE THE OUTPUT
================================================================================

LOADING THE JSON DATA (Python):

  import json

  # Load the entity data
  with open('/Users/am/Research/Epstein/epstein-wiki/output/entities_batch_4.json') as f:
      data = json.load(f)

  # Access statistics
  print(f"Total entities: {data['statistics']['total_entities']}")

  # Get all people
  people = data['entities']['people']

  # Find a specific person
  for person in people:
      if 'epstein' in person['normalized']:
          print(f"Name: {person['name']}")
          print(f"Mentions: {person['mention_count']}")
          for mention in person['mentions'][:5]:
              print(f"  Doc: {mention['doc_id']}")
              print(f"  Context: {mention['context']}")

SEARCHING FOR ENTITIES:

  # Find all political figures
  political = [p for p in data['entities']['people']
               if any(term in p['name'].lower()
                      for term in ['trump', 'clinton', 'president'])]

  # Find tech companies
  tech = [o for o in data['entities']['organizations']
          if any(term in o['name'].lower()
                 for term in ['google', 'facebook', 'apple'])]

  # Find international locations
  intl = [l for l in data['entities']['locations']
          if l['name'].lower() in ['china', 'paris', 'london', 'israel']]

EXPORTING TO OTHER FORMATS:

  # Export to CSV
  import csv

  with open('people.csv', 'w') as f:
      writer = csv.writer(f)
      writer.writerow(['Name', 'Normalized', 'Mentions'])
      for person in data['entities']['people']:
          writer.writerow([person['name'],
                          person['normalized'],
                          person['mention_count']])

================================================================================
RE-RUNNING THE EXTRACTION
================================================================================

To re-run the extraction with modified parameters:

  cd /Users/am/Research/Epstein/epstein-wiki
  python3 scripts/extract_entities_batch4.py

Modify the script to change:
  - BATCH_START / BATCH_END: Document range
  - CONTEXT_CHARS: Context window size
  - CONFIDENCE_THRESHOLD: AI confidence level
  - EXCLUDE_NAMES: Add more false positives to filter
  - PATTERNS: Adjust regex patterns

================================================================================
NEXT STEPS / RECOMMENDATIONS
================================================================================

1. ENTITY RESOLUTION
   - Merge variant forms of the same entity
   - Example: "trump", "Donald Trump", "President Trump" → single entity

2. RELATIONSHIP EXTRACTION
   - Analyze co-occurrences within documents
   - Build entity relationship graphs
   - Identify frequently connected entities

3. TIMELINE CONSTRUCTION
   - Use date entities to create chronological timelines
   - Map events to specific dates
   - Track entity mentions over time

4. CROSS-BATCH ANALYSIS
   - Compare entities across different document batches
   - Identify patterns and trends
   - Track entity frequency changes

5. NETWORK VISUALIZATION
   - Create network graphs of entity relationships
   - Visualize connections between people, orgs, locations
   - Identify central/influential entities

6. TOPIC MODELING
   - Combine entity extraction with topic analysis
   - Identify themes and subjects
   - Group documents by topic + entities

7. DATA CLEANUP
   - Remove remaining email artifacts
   - Consolidate address variants
   - Filter document metadata (HOUSE, OVERSIGHT)
   - Improve normalization rules

================================================================================
TECHNICAL NOTES
================================================================================

DATABASE SCHEMA:
  The source database (documents.db) contains:
    - bates_id: Document identifier
    - text_path: Path to extracted text file
    - (Other metadata fields)

TEXT FILE STRUCTURE:
  Location: /Users/am/Research/Epstein/Epstein Estate Documents - Seventh Production/TEXT/
  Subdirectories: 001/, 002/
  Format: Plain text (.txt files)
  Encoding: UTF-8 with error handling

PATH HANDLING:
  Database paths use Windows format: \HOUSE_OVERSIGHT_009\TEXT\002\file.txt
  Script converts to Unix format: TEXT/002/file.txt
  Full path: {TEXT_BASE_PATH}/TEXT/002/file.txt

PERFORMANCE:
  - Processing time: ~10-15 minutes for 722 documents
  - Memory usage: Moderate (spaCy model loaded once)
  - spaCy processing: ~1MB text limit per document
  - Output size: 4.2 MB JSON (with mention limiting)

================================================================================
SUPPORT / QUESTIONS
================================================================================

For questions about:
  - Data format: See entities_batch_4_report.md
  - Script usage: Read comments in extract_entities_batch4.py
  - Entity definitions: Refer to spaCy documentation
  - Batch processing: Check database query logic in script

================================================================================
VERSION HISTORY
================================================================================

Version 1.0 (2025-11-13)
  - Initial extraction of documents 2176-2897
  - Hybrid pattern-matching + spaCy NER
  - 4,602 entities extracted
  - 100% processing success rate

================================================================================
