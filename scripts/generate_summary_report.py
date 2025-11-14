#!/usr/bin/env python3
"""
Generate a summary report and interesting findings from entity extraction results.
"""

import json
from collections import defaultdict

INPUT_PATH = "/Users/am/Research/Epstein/epstein-wiki/output/entities_batch_1.json"
OUTPUT_PATH = "/Users/am/Research/Epstein/epstein-wiki/output/entities_batch_1_summary.md"

# Load data
print("Loading entity data...")
with open(INPUT_PATH, 'r') as f:
    data = json.load(f)

# Create summary report
print("Generating summary report...")

report = []
report.append("# Entity Extraction Summary - Batch 1")
report.append("")
report.append("## Overview")
report.append(f"- **Batch Number:** {data['batch']}")
report.append(f"- **Documents Processed:** {data['documents_processed']}")
report.append(f"- **Total Unique Entities:** {data['statistics']['total_entities']:,}")
report.append("")

report.append("## Entity Counts by Type")
report.append(f"- **People:** {data['statistics']['people_count']:,}")
report.append(f"- **Organizations:** {data['statistics']['orgs_count']:,}")
report.append(f"- **Locations:** {data['statistics']['locations_count']:,}")
report.append(f"- **Events/Dates:** {data['statistics']['events_count']:,}")
report.append("")

# Top people
report.append("## Top 50 Most Mentioned People")
report.append("")
report.append("| Rank | Name | Mentions | Sample Context |")
report.append("|------|------|----------|----------------|")
for i, person in enumerate(data['entities']['people'][:50], 1):
    name = person['name'].replace('|', '\\|')
    context = ""
    if person['mentions']:
        context = person['mentions'][0]['context'][:100].replace('|', '\\|').replace('\n', ' ')
    report.append(f"| {i} | {name} | {person['mention_count']} | {context}... |")
report.append("")

# Top organizations
report.append("## Top 50 Most Mentioned Organizations")
report.append("")
report.append("| Rank | Name | Mentions | Sample Context |")
report.append("|------|------|----------|----------------|")
for i, org in enumerate(data['entities']['organizations'][:50], 1):
    name = org['name'].replace('|', '\\|')
    context = ""
    if org['mentions']:
        context = org['mentions'][0]['context'][:100].replace('|', '\\|').replace('\n', ' ')
    report.append(f"| {i} | {name} | {person['mention_count']} | {context}... |")
report.append("")

# Top locations
report.append("## Top 50 Most Mentioned Locations")
report.append("")
report.append("| Rank | Name | Mentions |")
report.append("|------|------|----------|")
for i, loc in enumerate(data['entities']['locations'][:50], 1):
    name = loc['name'].replace('|', '\\|')
    report.append(f"| {i} | {name} | {loc['mention_count']} |")
report.append("")

# Interesting patterns
report.append("## Interesting Findings")
report.append("")

# Find entities with highest document spread
doc_spread = {}
for entity_type in ['people', 'organizations', 'locations']:
    for entity in data['entities'][entity_type]:
        unique_docs = len(set(m['doc_id'] for m in entity['mentions']))
        if unique_docs > 10:  # Mentioned in 10+ documents
            doc_spread[entity['name']] = {
                'type': entity_type,
                'mentions': entity['mention_count'],
                'documents': unique_docs
            }

# Sort by document spread
sorted_spread = sorted(doc_spread.items(), key=lambda x: x[1]['documents'], reverse=True)

report.append("### Entities Mentioned Across Most Documents")
report.append("These entities appear in many different documents, suggesting central importance:")
report.append("")
report.append("| Entity | Type | Unique Documents | Total Mentions |")
report.append("|--------|------|------------------|----------------|")
for name, info in sorted_spread[:20]:
    report.append(f"| {name} | {info['type']} | {info['documents']} | {info['mentions']} |")
report.append("")

# Find potential key people (mentioned frequently)
report.append("### Potential Key Figures")
report.append("People mentioned 20+ times across the documents:")
report.append("")
key_people = [p for p in data['entities']['people'] if p['mention_count'] >= 20]
report.append(f"Found {len(key_people)} people mentioned 20+ times:")
report.append("")
for person in key_people[:30]:
    report.append(f"- **{person['name']}** ({person['mention_count']} mentions)")
report.append("")

# Organizations mentioned frequently
report.append("### Key Organizations")
report.append("Organizations mentioned 20+ times:")
report.append("")
key_orgs = [o for o in data['entities']['organizations'] if o['mention_count'] >= 20]
report.append(f"Found {len(key_orgs)} organizations mentioned 20+ times:")
report.append("")
for org in key_orgs[:30]:
    report.append(f"- **{org['name']}** ({org['mention_count']} mentions)")
report.append("")

# Geographic spread
report.append("### Geographic Distribution")
report.append("Most frequently mentioned locations:")
report.append("")
for i, loc in enumerate(data['entities']['locations'][:20], 1):
    report.append(f"{i}. **{loc['name']}** - {loc['mention_count']} mentions")
report.append("")

# Date/event patterns
report.append("### Temporal Patterns")
report.append("Most frequently mentioned dates/time periods:")
report.append("")
for i, event in enumerate(data['entities']['events'][:20], 1):
    report.append(f"{i}. {event['name']} ({event['mention_count']} mentions)")
report.append("")

# Save report
print(f"Saving report to {OUTPUT_PATH}...")
with open(OUTPUT_PATH, 'w') as f:
    f.write('\n'.join(report))

print("Summary report generated successfully!")
print(f"Report saved to: {OUTPUT_PATH}")
