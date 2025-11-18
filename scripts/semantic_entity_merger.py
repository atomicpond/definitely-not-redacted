#!/usr/bin/env python3
"""
Semantic Entity Merger - Advanced fuzzy matching for entity consolidation.

This script addresses the problem of entity variants that represent the same person/place:
- "Jeffrey Epstein" vs "Epstein" vs "jeff epstein" vs "Mr. Epstein"
- "Donald Trump" vs "Trump" vs "Donald" vs "Donnie" vs "Mr. Trump"
- Intentional misspellings to avoid FOIA (e.g., "Donnie" instead of "Donald")

Strategy:
1. Name component matching (first name, last name, nicknames)
2. Substring/containment matching (e.g., "Epstein" contained in "Jeffrey Epstein")
3. Phonetic matching for misspellings
4. Manual override rules for known aliases
5. Semantic similarity using word embeddings (optional)
"""

import sqlite3
import re
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple, Optional
import Levenshtein

class SemanticEntityMerger:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.conn = None
        self.cursor = None

        # Known aliases and nicknames (can be expanded)
        self.known_aliases = {
            'people': {
                'donald': ['donnie', 'don', 'dt'],
                'hillary': ['hill'],
                'jeffrey': ['jeff', 'jef'],
                'william': ['bill', 'billy'],
                'robert': ['bob', 'bobby', 'rob'],
                'michael': ['mike', 'mikey'],
                'christopher': ['chris'],
                'anthony': ['tony'],
                'joseph': ['joe'],
                'james': ['jim', 'jimmy'],
                'richard': ['rick', 'dick'],
                'thomas': ['tom', 'tommy'],
            }
        }

        # Known entity mergers (high confidence)
        self.manual_merges = {
            'people': [
                # Trump variants
                ['donald-trump', 'trump', 'donald', 'donnie', 'mr-trump', 'president-trump',
                 'donald-j-trump', 'president-donald-trump', 'donald-trumps', 'the-trump',
                 'defendant-trump', 'trump-importance', 'implicated-trump'],

                # Epstein variants
                ['jeffrey-epstein', 'epstein', 'jeff-epstein', 'jeffrey-e-epstein',
                 'jeffrey-edward-epstein', 'mr-epstein', 'epstein-jeffrey', 'jeffrey-epsteins'],

                # Clinton variants
                ['bill-clinton', 'clinton', 'william-clinton', 'president-clinton',
                 'president-bill-clinton', 'mr-clinton'],

                ['hillary-clinton', 'hillary', 'mrs-clinton'],

                # Obama variants
                ['barack-obama', 'obama', 'president-obama', 'barack-h-obama',
                 'barack-hussein-obama', 'mr-obama'],
            ]
        }

        self.stats = {
            'entities_before': 0,
            'entities_after': 0,
            'merges_performed': 0,
            'relationships_updated': 0
        }

    def connect_db(self):
        """Connect to the database."""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def close_db(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def normalize_for_comparison(self, name: str) -> str:
        """Normalize name for comparison (more aggressive than entity_id normalization)."""
        # Convert to lowercase
        normalized = name.lower()

        # Remove common titles and prefixes
        titles = ['mr', 'mrs', 'ms', 'miss', 'dr', 'prof', 'professor', 'hon', 'honorable',
                  'judge', 'president', 'senator', 'sen', 'representative', 'rep',
                  'governor', 'gov', 'mayor', 'the', 'defendant', 'implicated']

        for title in titles:
            # Remove at start with period
            normalized = re.sub(rf'\b{title}\.\s*', '', normalized)
            # Remove at start without period
            normalized = re.sub(rf'\b{title}\s+', '', normalized)

        # Remove possessives
        normalized = re.sub(r"'s\b", '', normalized)

        # Remove special characters except spaces and hyphens
        normalized = re.sub(r'[^\w\s-]', '', normalized)

        # Normalize whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        return normalized

    def extract_name_components(self, name: str) -> Dict[str, List[str]]:
        """Extract first name, last name, and middle components."""
        normalized = self.normalize_for_comparison(name)
        parts = normalized.split()

        components = {
            'first': parts[0] if parts else '',
            'last': parts[-1] if len(parts) > 1 else '',
            'middle': parts[1:-1] if len(parts) > 2 else [],
            'all_parts': parts
        }

        return components

    def is_nickname_match(self, name1: str, name2: str, entity_type: str) -> bool:
        """Check if two names are nickname variants."""
        if entity_type not in self.known_aliases:
            return False

        comp1 = self.extract_name_components(name1)
        comp2 = self.extract_name_components(name2)

        # Check all name parts against all aliases
        for part1 in comp1['all_parts']:
            for part2 in comp2['all_parts']:
                # Check if they're direct aliases
                for canonical, aliases in self.known_aliases[entity_type].items():
                    if (part1 == canonical and part2 in aliases) or \
                       (part2 == canonical and part1 in aliases) or \
                       (part1 in aliases and part2 in aliases):
                        return True

        return False

    def is_substring_match(self, name1: str, name2: str) -> bool:
        """Check if one name is contained in another (accounting for word boundaries)."""
        norm1 = self.normalize_for_comparison(name1)
        norm2 = self.normalize_for_comparison(name2)

        # Skip single word matches if they're too short (avoid false positives)
        if len(norm1.split()) == 1 and len(norm1) < 4:
            return False
        if len(norm2.split()) == 1 and len(norm2) < 4:
            return False

        # Check if one is contained in the other
        if norm1 in norm2 or norm2 in norm1:
            return True

        # Check if last names match and first name is initial or nickname
        comp1 = self.extract_name_components(name1)
        comp2 = self.extract_name_components(name2)

        if comp1['last'] and comp2['last']:
            # Last names must match
            if comp1['last'] == comp2['last']:
                # If one has no first name, match
                if not comp1['first'] or not comp2['first']:
                    return True

                # If first names match on first letter (initial)
                if comp1['first'][0] == comp2['first'][0]:
                    return True

        return False

    def is_fuzzy_match(self, name1: str, name2: str, threshold: float = 0.2) -> bool:
        """Fuzzy string matching using Levenshtein distance."""
        norm1 = self.normalize_for_comparison(name1)
        norm2 = self.normalize_for_comparison(name2)

        if not norm1 or not norm2:
            return False

        distance = Levenshtein.distance(norm1, norm2)
        max_len = max(len(norm1), len(norm2))

        if max_len == 0:
            return True

        ratio = distance / max_len
        return ratio < threshold

    def should_merge(self, entity1: Dict, entity2: Dict) -> bool:
        """
        Determine if two entities should be merged.

        Args:
            entity1: {'id': str, 'name': str, 'type': str}
            entity2: {'id': str, 'name': str, 'type': str}

        Returns:
            True if entities should be merged
        """
        # Must be same type
        if entity1['type'] != entity2['type']:
            return False

        name1 = entity1['name']
        name2 = entity2['name']
        entity_type = entity1['type']

        # Check manual merges first
        for merge_group in self.manual_merges.get(entity_type, []):
            if entity1['id'].split(':')[1] in merge_group and \
               entity2['id'].split(':')[1] in merge_group:
                return True

        # Exact match after normalization
        if self.normalize_for_comparison(name1) == self.normalize_for_comparison(name2):
            return True

        # Nickname/alias match
        if self.is_nickname_match(name1, name2, entity_type):
            return True

        # Substring/containment match
        if self.is_substring_match(name1, name2):
            return True

        # Fuzzy match (typos, misspellings)
        if self.is_fuzzy_match(name1, name2, threshold=0.15):
            return True

        return False

    def get_all_entities(self, entity_type: Optional[str] = None) -> List[Dict]:
        """Fetch entities from database."""
        if entity_type:
            query = "SELECT id, name, type, document_count, mention_count FROM entities WHERE type = ?"
            self.cursor.execute(query, (entity_type,))
        else:
            query = "SELECT id, name, type, document_count, mention_count FROM entities"
            self.cursor.execute(query)

        entities = []
        for row in self.cursor.fetchall():
            entities.append({
                'id': row[0],
                'name': row[1],
                'type': row[2],
                'document_count': row[3],
                'mention_count': row[4]
            })

        return entities

    def find_merge_groups(self, entities: List[Dict]) -> List[List[Dict]]:
        """
        Find groups of entities that should be merged together.
        Uses union-find algorithm to group transitively related entities.
        """
        # Build merge graph using union-find
        parent = {}

        def find(x):
            if x not in parent:
                parent[x] = x
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py

        # Find all pairs that should merge
        print(f"  Comparing {len(entities)} entities for merging...")
        for i in range(len(entities)):
            if i % 100 == 0 and i > 0:
                print(f"    Processed {i}/{len(entities)} entities")

            for j in range(i + 1, len(entities)):
                if self.should_merge(entities[i], entities[j]):
                    union(entities[i]['id'], entities[j]['id'])

        # Group entities by their root parent
        groups = defaultdict(list)
        for entity in entities:
            root = find(entity['id'])
            groups[root].append(entity)

        # Return only groups with more than 1 entity
        merge_groups = [group for group in groups.values() if len(group) > 1]

        return merge_groups

    def choose_canonical_entity(self, group: List[Dict]) -> Dict:
        """
        Choose the best entity from a group to be the canonical representation.
        Prioritizes:
        1. Most mentions
        2. Most documents
        3. Longest name (more complete)
        """
        # Sort by mentions desc, then document_count desc, then name length desc
        sorted_group = sorted(
            group,
            key=lambda e: (e['mention_count'], e['document_count'], len(e['name'])),
            reverse=True
        )

        return sorted_group[0]

    def merge_entity_group(self, group: List[Dict]) -> Tuple[str, List[str], int, int]:
        """
        Merge a group of entities into one canonical entity.

        Returns:
            (canonical_id, merged_ids, total_documents, total_mentions)
        """
        canonical = self.choose_canonical_entity(group)
        merged_ids = [e['id'] for e in group if e['id'] != canonical['id']]

        # Collect all variants
        all_variants = []
        for entity in group:
            # Get existing variants from database
            self.cursor.execute("SELECT variants FROM entities WHERE id = ?", (entity['id'],))
            result = self.cursor.fetchone()
            if result and result[0]:
                # Parse JSON array
                import json
                variants = json.loads(result[0])
                all_variants.extend(variants)
            all_variants.append(entity['name'])

        # Remove duplicates
        unique_variants = list(set(all_variants))

        # Calculate combined stats (we'll recalculate from relationships)
        total_documents = sum(e['document_count'] for e in group)
        total_mentions = sum(e['mention_count'] for e in group)

        return canonical['id'], merged_ids, unique_variants, total_documents, total_mentions

    def execute_merges(self, merge_groups: List[List[Dict]]):
        """Execute the entity merges in the database."""
        print(f"\n  Executing {len(merge_groups)} merge operations...")

        for i, group in enumerate(merge_groups):
            if i % 10 == 0 and i > 0:
                print(f"    Completed {i}/{len(merge_groups)} merges")

            canonical_id, merged_ids, all_variants, total_docs, total_mentions = \
                self.merge_entity_group(group)

            # Update the canonical entity with all variants
            import json
            variants_json = json.dumps(all_variants)
            self.cursor.execute("""
                UPDATE entities
                SET variants = ?
                WHERE id = ?
            """, (variants_json, canonical_id))

            # Update all relationships to point to canonical entity
            for merged_id in merged_ids:
                # Update entity_documents
                self.cursor.execute("""
                    UPDATE entity_documents
                    SET entity_id = ?
                    WHERE entity_id = ?
                """, (canonical_id, merged_id))

                # Update entity_cooccurrence (entity1)
                self.cursor.execute("""
                    UPDATE entity_cooccurrence
                    SET entity1 = ?
                    WHERE entity1 = ?
                """, (canonical_id, merged_id))

                # Update entity_cooccurrence (entity2)
                self.cursor.execute("""
                    UPDATE entity_cooccurrence
                    SET entity2 = ?
                    WHERE entity2 = ?
                """, (canonical_id, merged_id))

                # Delete the merged entity
                self.cursor.execute("DELETE FROM entities WHERE id = ?", (merged_id,))

                self.stats['relationships_updated'] += 1

            self.stats['merges_performed'] += 1

        # Recalculate document_count and mention_count for all entities
        print("  Recalculating entity statistics...")
        self.cursor.execute("""
            UPDATE entities
            SET document_count = (
                SELECT COUNT(DISTINCT document_id)
                FROM entity_documents
                WHERE entity_id = entities.id
            ),
            mention_count = (
                SELECT COALESCE(SUM(mention_count), 0)
                FROM entity_documents
                WHERE entity_id = entities.id
            )
        """)

        self.conn.commit()

    def consolidate_duplicate_relationships(self):
        """
        After merging, there may be duplicate relationships.
        Consolidate them by summing their strengths.
        """
        print("\n  Consolidating duplicate relationships...")

        # Find and merge duplicate entity_documents
        self.cursor.execute("""
            CREATE TEMPORARY TABLE temp_entity_docs AS
            SELECT entity_id, document_id, SUM(mention_count) as total_mentions
            FROM entity_documents
            GROUP BY entity_id, document_id
        """)

        self.cursor.execute("DELETE FROM entity_documents")

        self.cursor.execute("""
            INSERT INTO entity_documents (entity_id, document_id, mention_count)
            SELECT entity_id, document_id, total_mentions
            FROM temp_entity_docs
        """)

        self.cursor.execute("DROP TABLE temp_entity_docs")

        # Find and merge duplicate entity_cooccurrence
        self.cursor.execute("""
            CREATE TEMPORARY TABLE temp_cooccurrence AS
            SELECT
                entity1,
                entity2,
                SUM(strength) as total_strength,
                SUM(document_count) as total_docs
            FROM entity_cooccurrence
            WHERE entity1 < entity2  -- Avoid duplicates
            GROUP BY entity1, entity2
        """)

        self.cursor.execute("DELETE FROM entity_cooccurrence")

        self.cursor.execute("""
            INSERT INTO entity_cooccurrence (entity1, entity2, strength, document_count)
            SELECT entity1, entity2, total_strength, total_docs
            FROM temp_cooccurrence
        """)

        self.cursor.execute("DROP TABLE temp_cooccurrence")

        self.conn.commit()
        print("  Relationship consolidation complete")

    def run_merge(self, entity_type: Optional[str] = None, dry_run: bool = False):
        """
        Run the entity merge process.

        Args:
            entity_type: Specific type to merge (people, organizations, etc.) or None for all
            dry_run: If True, only report what would be merged without making changes
        """
        print("=" * 80)
        print("SEMANTIC ENTITY MERGER")
        print("=" * 80)
        print(f"Database: {self.db_path}")
        print(f"Entity type: {entity_type or 'all'}")
        print(f"Dry run: {dry_run}")
        print()

        self.connect_db()

        try:
            # Get entities
            if entity_type:
                types_to_process = [entity_type]
            else:
                types_to_process = ['people', 'organizations', 'locations', 'events']

            for etype in types_to_process:
                print(f"\nProcessing entity type: {etype}")
                print("-" * 80)

                entities = self.get_all_entities(etype)
                self.stats['entities_before'] = len(entities)
                print(f"  Entities before merge: {len(entities)}")

                # Find merge groups
                merge_groups = self.find_merge_groups(entities)
                print(f"  Found {len(merge_groups)} merge groups")

                if merge_groups:
                    # Show sample merges
                    print("\n  Sample merges (showing first 10):")
                    for i, group in enumerate(merge_groups[:10]):
                        canonical = self.choose_canonical_entity(group)
                        variants = [e['name'] for e in group if e['id'] != canonical['id']]
                        print(f"    {i+1}. {canonical['name']} ← {', '.join(variants)}")

                    if len(merge_groups) > 10:
                        print(f"    ... and {len(merge_groups) - 10} more")

                    if not dry_run:
                        # Execute merges
                        self.execute_merges(merge_groups)

                        # Consolidate duplicate relationships
                        self.consolidate_duplicate_relationships()

                        # Get final count
                        entities_after = self.get_all_entities(etype)
                        self.stats['entities_after'] = len(entities_after)
                        print(f"\n  Entities after merge: {len(entities_after)}")
                        print(f"  Reduction: {self.stats['entities_before'] - self.stats['entities_after']}")
                    else:
                        print("\n  [DRY RUN - No changes made]")

            # Print final statistics
            print("\n" + "=" * 80)
            print("MERGE SUMMARY")
            print("=" * 80)
            if not dry_run:
                print(f"Merge operations performed: {self.stats['merges_performed']}")
                print(f"Relationships updated: {self.stats['relationships_updated']}")
                print(f"Entities reduced by: {self.stats['entities_before'] - self.stats['entities_after']}")
            else:
                print("[DRY RUN - No changes made]")
                print(f"Would perform {len(merge_groups)} merge operations")
            print("=" * 80)

        finally:
            self.close_db()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Semantic Entity Merger for Epstein Wiki')
    parser.add_argument('--db', type=str,
                       default='database/wiki_data.db',
                       help='Path to wiki_data.db database')
    parser.add_argument('--type', type=str,
                       choices=['people', 'organizations', 'locations', 'events'],
                       help='Specific entity type to merge (default: all)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be merged without making changes')

    args = parser.parse_args()

    merger = SemanticEntityMerger(args.db)
    merger.run_merge(entity_type=args.type, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
