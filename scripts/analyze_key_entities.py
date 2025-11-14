#!/usr/bin/env python3
"""
Analyze and identify key entities from the extraction results.
"""

import json
import re

INPUT_PATH = "/Users/am/Research/Epstein/epstein-wiki/output/entities_batch_1.json"
OUTPUT_PATH = "/Users/am/Research/Epstein/epstein-wiki/output/key_entities_analysis.md"

# Load data
print("Loading entity data...")
with open(INPUT_PATH, 'r') as f:
    data = json.load(f)

# Known false positive patterns
FALSE_POSITIVE_NAMES = {
    'White House', 'Middle East', 'New Mexico', 'Saudi Arabia', 'San Francisco',
    'Los Angeles', 'New Jersey', 'Vanity Fair', 'Daily News', 'Daily Beast',
    'Rights Act', 'Crime Victims', 'Wealth Management', 'District Court',
    'Central Bank', 'Security Council', 'Asia Pacific', 'Cold War', 'Little St',
    'Harvard Law School', 'Vice President', 'Exchange Act', 'North Korea',
    'United States', 'New York', 'Miami Herald', 'New Year', 'Daily Mail',
    'European Parliament', 'Dear Mr', 'Las Vegas', 'Harvard University',
    'Merrill Lynch', 'America Merrill Lynch', 'Goldman Sachs', 'Merrill Lynch Global',
    'Secret Service'
}

def is_likely_person(name):
    """Check if entity is likely a real person."""
    # Skip false positives
    if any(fp in name for fp in FALSE_POSITIVE_NAMES):
        return False

    # Must have at least first and last name
    parts = name.split()
    if len(parts) < 2:
        return False

    # Skip if contains common org suffixes
    if any(suffix in name for suffix in ['Inc', 'LLC', 'Corp', 'Ltd', 'LP', 'LLP']):
        return False

    # Skip if all caps (likely acronym)
    if name.isupper():
        return False

    return True

def is_likely_org(name):
    """Check if entity is likely a real organization."""
    # Skip single words
    if len(name.split()) == 1 and name not in ['Trump', 'FBI', 'CIA', 'Congress', 'Senate', 'State']:
        return False

    # Include if has org markers
    if any(marker in name for marker in ['Inc', 'LLC', 'Corp', 'Ltd', 'LP', 'LLP', 'Foundation',
                                          'University', 'Institute', 'Bank', 'Group', 'Trust']):
        return True

    # Include known orgs
    known_orgs = {'FBI', 'CIA', 'Congress', 'Senate', 'Treasury', 'Fed', 'Google', 'Twitter',
                  'Facebook', 'Bloomberg', 'Court', 'IRS', 'Supreme Court'}
    if name in known_orgs:
        return True

    return False

# Filter people
print("Filtering people entities...")
real_people = [p for p in data['entities']['people'] if is_likely_person(p['name'])]

# Filter organizations
print("Filtering organization entities...")
real_orgs = [o for o in data['entities']['organizations'] if is_likely_org(o['name'])]

# Create analysis report
report = []
report.append("# Key Entities Analysis - Batch 1")
report.append("")
report.append("## Overview")
report.append(f"- Documents Analyzed: {data['documents_processed']}")
report.append(f"- Total Entities Extracted: {data['statistics']['total_entities']:,}")
report.append(f"- Filtered Real People: {len(real_people):,}")
report.append(f"- Filtered Organizations: {len(real_orgs):,}")
report.append(f"- Locations: {data['statistics']['locations_count']:,}")
report.append("")

# Key People
report.append("## Key People (Top 100)")
report.append("")
report.append("People mentioned 10+ times in the documents:")
report.append("")
report.append("| Rank | Name | Mentions | Documents | Sample Context |")
report.append("|------|------|----------|-----------|----------------|")

for i, person in enumerate(real_people[:100], 1):
    unique_docs = len(set(m['doc_id'] for m in person['mentions']))
    context = ""
    if person['mentions']:
        context = person['mentions'][0]['context'][:80].replace('|', '\\|').replace('\n', ' ')
    report.append(f"| {i} | {person['name']} | {person['mention_count']} | {unique_docs} | {context}... |")

report.append("")
report.append("")

# Key Organizations
report.append("## Key Organizations (Top 50)")
report.append("")
report.append("| Rank | Name | Mentions | Documents |")
report.append("|------|------|----------|-----------|")

for i, org in enumerate(real_orgs[:50], 1):
    unique_docs = len(set(m['doc_id'] for m in org['mentions']))
    report.append(f"| {i} | {org['name']} | {org['mention_count']} | {unique_docs} |")

report.append("")
report.append("")

# Top Locations
report.append("## Key Locations (Top 30)")
report.append("")
report.append("| Rank | Location | Mentions |")
report.append("|------|----------|----------|")

for i, loc in enumerate(data['entities']['locations'][:30], 1):
    report.append(f"| {i} | {loc['name']} | {loc['mention_count']} |")

report.append("")
report.append("")

# Notable Patterns
report.append("## Notable Patterns & Insights")
report.append("")

# Group by categories
attorneys = [p for p in real_people if any(term in p['name'].lower() or
             any(term in m['context'].lower() for m in p['mentions'][:5])
             for term in ['attorney', 'lawyer', 'counsel', 'law', 'esq'])]

politicians = [p for p in real_people if any(term in p['name'].lower() or
               any(term in m['context'].lower() for m in p['mentions'][:5])
               for term in ['president', 'senator', 'congressman', 'prime minister'])]

victims = [p for p in real_people if 'doe' in p['name'].lower()]

report.append(f"### Legal Professionals")
report.append(f"Found {len(attorneys)} legal professionals mentioned:")
report.append("")
for person in attorneys[:20]:
    report.append(f"- **{person['name']}** ({person['mention_count']} mentions)")
report.append("")

report.append(f"### Political Figures")
report.append(f"Found {len(politicians)} political figures mentioned:")
report.append("")
for person in politicians[:20]:
    report.append(f"- **{person['name']}** ({person['mention_count']} mentions)")
report.append("")

report.append(f"### Anonymous References")
report.append(f"Found {len(victims)} 'Jane/John Doe' references (likely victims):")
report.append("")
for person in victims[:10]:
    report.append(f"- **{person['name']}** ({person['mention_count']} mentions)")
report.append("")

# Most cross-referenced entities
report.append("### Most Widely Referenced Entities")
report.append("Entities appearing in 20+ different documents:")
report.append("")

cross_ref = []
for person in real_people:
    unique_docs = len(set(m['doc_id'] for m in person['mentions']))
    if unique_docs >= 20:
        cross_ref.append((person['name'], unique_docs, person['mention_count']))

cross_ref.sort(key=lambda x: x[1], reverse=True)

for name, doc_count, mention_count in cross_ref[:30]:
    report.append(f"- **{name}** - {doc_count} documents, {mention_count} total mentions")

report.append("")

# Save report
print(f"Saving analysis to {OUTPUT_PATH}...")
with open(OUTPUT_PATH, 'w') as f:
    f.write('\\n'.join(report))

print("Analysis complete!")
print()
print(f"Key Statistics:")
print(f"  Real People Identified: {len(real_people)}")
print(f"  Top Person: {real_people[0]['name']} ({real_people[0]['mention_count']} mentions)")
print(f"  Legal Professionals: {len(attorneys)}")
print(f"  Political Figures: {len(politicians)}")
print(f"  Anonymous References: {len(victims)}")
print(f"  Organizations: {len(real_orgs)}")
print()
print(f"Report saved to: {OUTPUT_PATH}")
