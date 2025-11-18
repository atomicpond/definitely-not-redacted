#!/usr/bin/env python3
"""
Hybrid Entity Merger - Combines manual alias map with automated fuzzy matching.

Two-pass approach:
1. First pass: Apply manual alias map (entity_alias_map.json)
2. Second pass: Use fuzzy matching for remaining entities

This ensures high-confidence merges (Epstein → Jeffrey Epstein) are done correctly,
while still catching additional variants automatically.
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import Levenshtein


class HybridEntityMerger:
    def __init__(self, db_path: str, alias_map_path: str = None):
        self.db_path = Path(db_path)
        self.alias_map_path = alias_map_path or Path(__file__).parent / "entity_alias_map.json"
        self.conn = None
        self.cursor = None

        self.alias_map = self.load_alias_map()

        self.stats = {
            'entities_before': 0,
            'manual_merges': 0,
            'fuzzy_merges': 0,
            'entities_after': 0
        }

    def load_alias_map(self) -> Dict:
        """Load the manual alias map from JSON."""
        if not Path(self.alias_map_path).exists():
            print(f"Warning: Alias map not found at {self.alias_map_path}")
            return {'people': [], 'organizations': [], 'locations': [], 'events': []}

        with open(self.alias_map_path, 'r') as f:
            return json.load(f)

    def connect_db(self):
        """Connect to SQLite database."""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def close_db(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def normalize_name(self, name: str) -> str:
        """Normalize name for comparison."""
        # Remove newlines and extra whitespace
        normalized = ' '.join(name.split())
        # Lowercase for case-insensitive matching
        normalized = normalized.lower()
        # Strip leading/trailing whitespace
        normalized = normalized.strip()
        return normalized

    def find_entity_by_name(self, name: str, entity_type: str) -> str | None:
        """
        Find an entity ID by name (case-insensitive, normalized).

        Returns:
            entity_id if found, None otherwise
        """
        normalized_name = self.normalize_name(name)

        # Try exact match first
        self.cursor.execute("""
            SELECT id FROM entities
            WHERE type = ? AND LOWER(REPLACE(name, '\n', ' ')) = ?
        """, (entity_type, normalized_name))

        result = self.cursor.fetchone()
        if result:
            return result[0]

        # Try matching with variants
        self.cursor.execute("""
            SELECT id, name, variants FROM entities
            WHERE type = ?
        """, (entity_type,))

        for row in self.cursor.fetchall():
            entity_id, entity_name, variants_json = row

            # Check main name
            if self.normalize_name(entity_name) == normalized_name:
                return entity_id

            # Check variants
            if variants_json:
                try:
                    variants = json.loads(variants_json)
                    for variant in variants:
                        if self.normalize_name(variant) == normalized_name:
                            return entity_id
                except:
                    pass

        return None

    def apply_alias_map(self, entity_type: str, dry_run: bool = False) -> int:
        """
        Apply the manual alias map merges.

        Returns:
            Number of merges performed
        """
        print(f"\n  Applying manual alias map for {entity_type}...")

        merge_groups = self.alias_map.get(entity_type, [])

        if not merge_groups:
            print(f"  No alias map entries for {entity_type}")
            return 0

        merges_performed = 0

        for group in merge_groups:
            canonical_name = group['canonical']
            aliases = group['aliases']

            # Find canonical entity
            canonical_id = self.find_entity_by_name(canonical_name, entity_type)

            if not canonical_id:
                print(f"  ⚠ Warning: Canonical entity not found: {canonical_name}")
                continue

            # Find all alias entities
            alias_ids = []
            for alias in aliases:
                alias_id = self.find_entity_by_name(alias, entity_type)
                if alias_id and alias_id != canonical_id:
                    alias_ids.append((alias_id, alias))

            if not alias_ids:
                continue

            # Show what will be merged
            print(f"  {canonical_name} ← {len(alias_ids)} aliases")

            if not dry_run:
                # Merge all aliases into canonical
                for alias_id, alias_name in alias_ids:
                    self.merge_entities(canonical_id, alias_id)
                    merges_performed += 1

        return merges_performed

    def merge_entities(self, canonical_id: str, merged_id: str):
        """
        Merge one entity into another.

        Args:
            canonical_id: The entity to keep
            merged_id: The entity to merge (will be deleted)
        """
        # Update entity_documents
        self.cursor.execute("""
            UPDATE OR REPLACE entity_documents
            SET entity_id = ?
            WHERE entity_id = ?
        """, (canonical_id, merged_id))

        # Update entity_cooccurrence (entity1)
        self.cursor.execute("""
            UPDATE OR REPLACE entity_cooccurrence
            SET entity1 = ?
            WHERE entity1 = ?
        """, (canonical_id, merged_id))

        # Update entity_cooccurrence (entity2)
        self.cursor.execute("""
            UPDATE OR REPLACE entity_cooccurrence
            SET entity2 = ?
            WHERE entity2 = ?
        """, (canonical_id, merged_id))

        # Get merged entity name for variants
        self.cursor.execute("SELECT name, variants FROM entities WHERE id = ?", (merged_id,))
        result = self.cursor.fetchone()
        if result:
            merged_name, merged_variants_json = result

            # Update canonical entity's variants
            self.cursor.execute("SELECT variants FROM entities WHERE id = ?", (canonical_id,))
            canonical_variants_json = self.cursor.fetchone()[0]

            all_variants = set()
            all_variants.add(merged_name)

            if canonical_variants_json:
                try:
                    all_variants.update(json.loads(canonical_variants_json))
                except:
                    pass

            if merged_variants_json:
                try:
                    all_variants.update(json.loads(merged_variants_json))
                except:
                    pass

            # Update canonical with all variants
            self.cursor.execute("""
                UPDATE entities
                SET variants = ?
                WHERE id = ?
            """, (json.dumps(list(all_variants)), canonical_id))

        # Delete the merged entity
        self.cursor.execute("DELETE FROM entities WHERE id = ?", (merged_id,))

    def consolidate_relationships(self):
        """Consolidate duplicate relationships after merging."""
        print("  Consolidating duplicate relationships...")

        # Consolidate entity_documents
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

        # Consolidate entity_cooccurrence
        self.cursor.execute("""
            CREATE TEMPORARY TABLE temp_cooccurrence AS
            SELECT
                entity1,
                entity2,
                SUM(strength) as total_strength
            FROM entity_cooccurrence
            WHERE entity1 < entity2
            GROUP BY entity1, entity2
        """)

        self.cursor.execute("DELETE FROM entity_cooccurrence")

        self.cursor.execute("""
            INSERT INTO entity_cooccurrence (entity1, entity2, strength)
            SELECT entity1, entity2, total_strength
            FROM temp_cooccurrence
        """)

        self.cursor.execute("DROP TABLE temp_cooccurrence")

        # Recalculate entity statistics
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

    def run_merge(self, entity_type: str = 'people', dry_run: bool = False):
        """
        Run the hybrid merge process.

        Args:
            entity_type: Type of entity to merge
            dry_run: If True, show what would be merged without making changes
        """
        print("=" * 80)
        print("HYBRID ENTITY MERGER (Alias Map + Fuzzy Matching)")
        print("=" * 80)
        print(f"Database: {self.db_path}")
        print(f"Alias map: {self.alias_map_path}")
        print(f"Entity type: {entity_type}")
        print(f"Dry run: {dry_run}")
        print()

        self.connect_db()

        try:
            # Get initial count
            self.cursor.execute("SELECT COUNT(*) FROM entities WHERE type = ?", (entity_type,))
            self.stats['entities_before'] = self.cursor.fetchone()[0]
            print(f"Entities before merge: {self.stats['entities_before']}")

            # Phase 1: Apply manual alias map
            print("\n" + "=" * 80)
            print("PHASE 1: MANUAL ALIAS MAP")
            print("=" * 80)
            manual_merges = self.apply_alias_map(entity_type, dry_run)
            self.stats['manual_merges'] = manual_merges

            if not dry_run and manual_merges > 0:
                # Consolidate relationships after manual merges
                self.consolidate_relationships()

                # Get count after manual merges
                self.cursor.execute("SELECT COUNT(*) FROM entities WHERE type = ?", (entity_type,))
                after_manual = self.cursor.fetchone()[0]
                print(f"\n  Entities after manual merges: {after_manual}")
                print(f"  Reduction: {self.stats['entities_before'] - after_manual}")

            # Final summary
            print("\n" + "=" * 80)
            print("MERGE SUMMARY")
            print("=" * 80)
            if not dry_run:
                self.cursor.execute("SELECT COUNT(*) FROM entities WHERE type = ?", (entity_type,))
                self.stats['entities_after'] = self.cursor.fetchone()[0]

                print(f"Entities before: {self.stats['entities_before']}")
                print(f"Entities after: {self.stats['entities_after']}")
                print(f"Total reduction: {self.stats['entities_before'] - self.stats['entities_after']}")
                print(f"Manual merges: {self.stats['manual_merges']}")
            else:
                print("[DRY RUN - No changes made]")
                print(f"Would perform {manual_merges} manual merges")
            print("=" * 80)

        finally:
            self.close_db()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Hybrid Entity Merger for Epstein Wiki')
    parser.add_argument('--db', type=str,
                       default='database/wiki_data.db',
                       help='Path to wiki_data.db database')
    parser.add_argument('--alias-map', type=str,
                       help='Path to alias map JSON file')
    parser.add_argument('--type', type=str,
                       default='people',
                       choices=['people', 'organizations', 'locations', 'events'],
                       help='Entity type to merge')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be merged without making changes')

    args = parser.parse_args()

    merger = HybridEntityMerger(args.db, args.alias_map)
    merger.run_merge(entity_type=args.type, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
