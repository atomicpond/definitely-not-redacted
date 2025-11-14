#!/usr/bin/env python3
"""
Query utility for Batch 3 extracted entities
Allows searching and filtering extracted entities from the JSON output
"""

import json
import sys
from typing import List, Dict, Any


class EntityQuerier:
    def __init__(self, json_path: str):
        """Load extracted entities from JSON file."""
        with open(json_path, 'r') as f:
            self.data = json.load(f)
        self.entities = self.data['entities']

    def search_people(self, query: str, min_mentions: int = 1) -> List[Dict[str, Any]]:
        """Search for people by name."""
        query_lower = query.lower()
        results = []
        for person in self.entities['people']:
            if query_lower in person['name'].lower() and person['mention_count'] >= min_mentions:
                results.append(person)
        return sorted(results, key=lambda x: x['mention_count'], reverse=True)

    def search_organizations(self, query: str, min_mentions: int = 1) -> List[Dict[str, Any]]:
        """Search for organizations by name."""
        query_lower = query.lower()
        results = []
        for org in self.entities['organizations']:
            if query_lower in org['name'].lower() and org['mention_count'] >= min_mentions:
                results.append(org)
        return sorted(results, key=lambda x: x['mention_count'], reverse=True)

    def search_locations(self, query: str, min_mentions: int = 1) -> List[Dict[str, Any]]:
        """Search for locations by name."""
        query_lower = query.lower()
        results = []
        for loc in self.entities['locations']:
            if query_lower in loc['name'].lower() and loc['mention_count'] >= min_mentions:
                results.append(loc)
        return sorted(results, key=lambda x: x['mention_count'], reverse=True)

    def get_documents_mentioning(self, entity_normalized: str, category: str = 'people') -> List[str]:
        """Get list of document IDs that mention a specific entity."""
        for entity in self.entities[category]:
            if entity['normalized'] == entity_normalized:
                return list(set([m['doc_id'] for m in entity['mentions']]))
        return []

    def get_co_occurring_entities(self, entity_normalized: str, category: str = 'people',
                                   target_category: str = 'organizations') -> Dict[str, int]:
        """Find entities from target_category that appear in same documents as the given entity."""
        # Get documents mentioning the entity
        docs = self.get_documents_mentioning(entity_normalized, category)

        # Count co-occurrences
        co_occurrences = {}
        for target_entity in self.entities[target_category]:
            for mention in target_entity['mentions']:
                if mention['doc_id'] in docs:
                    name = target_entity['name']
                    co_occurrences[name] = co_occurrences.get(name, 0) + 1

        return dict(sorted(co_occurrences.items(), key=lambda x: x[1], reverse=True))

    def get_statistics(self) -> Dict[str, Any]:
        """Get extraction statistics."""
        return self.data['statistics']

    def print_entity_details(self, entity: Dict[str, Any], max_contexts: int = 5):
        """Pretty print entity details."""
        print(f"\nEntity: {entity['name']}")
        print(f"Normalized: {entity['normalized']}")
        print(f"Total mentions: {entity['mention_count']}")
        print(f"\nSample contexts (showing up to {max_contexts}):")

        for i, mention in enumerate(entity['mentions'][:max_contexts], 1):
            print(f"\n  {i}. Document: {mention['doc_id']}")
            print(f"     Position: {mention['position']}")
            print(f"     Context: {mention['context']}")


def main():
    """Example usage of the entity querier."""
    querier = EntityQuerier('/Users/am/Research/Epstein/epstein-wiki/output/entities_batch_3.json')

    print("=" * 70)
    print("ENTITY QUERIER - BATCH 3")
    print("=" * 70)

    # Example 1: Search for people
    print("\n1. Searching for people named 'Clinton':")
    print("-" * 70)
    clintons = querier.search_people('clinton', min_mentions=5)
    for person in clintons:
        print(f"  - {person['name']:40s} ({person['mention_count']:3d} mentions)")

    # Example 2: Search for organizations
    print("\n2. Searching for organizations containing 'University':")
    print("-" * 70)
    universities = querier.search_organizations('university', min_mentions=3)
    for org in universities[:10]:
        print(f"  - {org['name']:40s} ({org['mention_count']:3d} mentions)")

    # Example 3: Search for locations
    print("\n3. Searching for locations in 'Florida':")
    print("-" * 70)
    florida_locs = querier.search_locations('florida', min_mentions=2)
    for loc in florida_locs:
        print(f"  - {loc['name']:40s} ({loc['mention_count']:3d} mentions)")

    # Example 4: Get documents mentioning specific entity
    print("\n4. Documents mentioning 'Alan Dershowitz':")
    print("-" * 70)
    dershowitz_results = querier.search_people('dershowitz')
    if dershowitz_results:
        docs = querier.get_documents_mentioning(dershowitz_results[0]['normalized'], 'people')
        print(f"  Found in {len(docs)} documents:")
        for doc_id in docs[:10]:
            print(f"    - {doc_id}")
        if len(docs) > 10:
            print(f"    ... and {len(docs) - 10} more")

    # Example 5: Co-occurring entities
    print("\n5. Organizations co-occurring with 'Epstein':")
    print("-" * 70)
    epstein_results = querier.search_people('epstein', min_mentions=100)
    if epstein_results:
        co_orgs = querier.get_co_occurring_entities(
            epstein_results[0]['normalized'],
            'people',
            'organizations'
        )
        for org, count in list(co_orgs.items())[:15]:
            print(f"  - {org:40s} ({count:3d} co-occurrences)")

    # Example 6: Show detailed entity info
    print("\n6. Detailed information for 'Jeffrey Epstein':")
    print("-" * 70)
    if epstein_results:
        querier.print_entity_details(epstein_results[0], max_contexts=3)

    # Statistics
    print("\n\n7. Extraction Statistics:")
    print("-" * 70)
    stats = querier.get_statistics()
    for key, value in stats.items():
        print(f"  {key:25s}: {value:,}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
