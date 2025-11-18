#!/usr/bin/env python3
"""
Splink Entity Merger - Use splink for probabilistic entity resolution.

Uses splink (UK Government's record linkage tool) to merge entity variants:
- "Jeffrey Epstein" vs "Epstein" vs "jeff epstein"
- "Donald Trump" vs "Trump" vs "Donnie"
- Handles typos and intentional misspellings
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional
import json

from splink import DuckDBAPI, Linker, SettingsCreator, block_on
from splink.comparison_library import (
    ExactMatch,
    JaroWinklerAtThresholds,
    LevenshteinAtThresholds
)


class SplinkEntityMerger:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.conn = None
        self.cursor = None
        self.db = DuckDBAPI()

        # Known name variations and nicknames
        self.nickname_map = {
            'donald': 'donnie|don|dt',
            'jeffrey': 'jeff|jef',
            'william': 'bill|billy',
            'hillary': 'hill',
            'robert': 'bob|bobby|rob',
            'michael': 'mike|mikey',
            'christopher': 'chris',
            'anthony': 'tony',
            'joseph': 'joe',
            'james': 'jim|jimmy',
            'richard': 'rick|dick',
            'thomas': 'tom|tommy',
        }

        self.stats = {
            'entities_before': 0,
            'entities_after': 0,
            'clusters_found': 0,
            'merges_performed': 0
        }

    def connect_db(self):
        """Connect to SQLite database."""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def close_db(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def load_entities(self, entity_type: str) -> pd.DataFrame:
        """Load entities from SQLite into pandas DataFrame."""
        query = """
            SELECT
                id,
                name,
                type,
                document_count,
                mention_count,
                variants
            FROM entities
            WHERE type = ?
            ORDER BY mention_count DESC
        """

        df = pd.read_sql_query(query, self.conn, params=(entity_type,))

        # Add a unique_id for splink
        df['unique_id'] = df['id']

        # Normalize name for better matching
        df['name_normalized'] = df['name'].str.lower().str.strip()

        return df

    def create_splink_settings(self, entity_type: str):
        """
        Create splink settings optimized for name matching.

        This defines how splink will compare records:
        - Exact matches on normalized names
        - Fuzzy matches using Jaro-Winkler similarity
        - Handles substring matches
        """

        settings = SettingsCreator(
            link_type="dedupe_only",  # We're deduplicating, not linking two datasets
            unique_id_column_name="unique_id",

            # Blocking rules - these create candidate pairs to compare
            # Only compare records that might match (improves performance)
            blocking_rules_to_generate_predictions=[
                # Block on first 3 characters of normalized name
                block_on("substr(name_normalized, 1, 3)"),
                # Block on last word (likely last name)
                block_on("regexp_extract(name_normalized, '\\S+$', 0)"),
            ],

            # Comparison rules - how to score similarity
            comparisons=[
                # Compare full names with Jaro-Winkler similarity
                JaroWinklerAtThresholds(
                    "name",
                    [0.9, 0.85, 0.8],
                ),

                # Also compare with Levenshtein for typos
                LevenshteinAtThresholds(
                    "name",
                    [1, 2, 3],  # Max edit distance
                ),

                # Compare normalized names (exact match on lowercased)
                ExactMatch("name_normalized"),
            ],

            # Retain intermediate columns for debugging
            retain_intermediate_calculation_columns=True,
        )

        return settings

    def find_clusters(self, df: pd.DataFrame, entity_type: str, threshold: float = 0.8):
        """
        Use splink to find clusters of matching entities.

        Args:
            df: DataFrame with entities
            entity_type: Type of entity (people, organizations, etc.)
            threshold: Match probability threshold (0-1, higher = stricter)

        Returns:
            DataFrame with cluster assignments
        """
        print(f"  Running splink on {len(df)} entities...")
        print(f"  Match threshold: {threshold}")

        # Create settings
        settings = self.create_splink_settings(entity_type)

        # Initialize linker
        linker = Linker(df, settings, db_api=self.db)

        # Estimate parameters using expectation maximization
        print("  Training splink model...")
        linker.training.estimate_u_using_random_sampling(max_pairs=1e6)

        # Use blocking rules to estimate m probabilities
        blocking_rule_for_training = block_on("substr(name_normalized, 1, 4)")
        linker.training.estimate_parameters_using_expectation_maximisation(
            blocking_rule_for_training
        )

        # Predict matches
        print("  Finding matches...")
        predictions = linker.inference.predict(threshold_match_probability=threshold)

        # Get clusters
        print("  Clustering entities...")
        clusters = linker.clustering.cluster_pairwise_predictions_at_threshold(
            predictions,
            threshold_match_probability=threshold
        )

        # Convert to pandas
        clusters_df = clusters.as_pandas_dataframe()

        return clusters_df

    def analyze_clusters(self, clusters_df: pd.DataFrame) -> dict:
        """Analyze the cluster results."""
        # Count clusters
        cluster_counts = clusters_df.groupby('cluster_id').size()

        # Only clusters with more than 1 entity are merges
        merge_clusters = cluster_counts[cluster_counts > 1]

        analysis = {
            'total_entities': len(clusters_df),
            'total_clusters': clusters_df['cluster_id'].nunique(),
            'singleton_clusters': (cluster_counts == 1).sum(),
            'merge_clusters': len(merge_clusters),
            'total_merges': (merge_clusters - 1).sum(),  # Each cluster of N entities = N-1 merges
            'largest_cluster': cluster_counts.max(),
        }

        return analysis

    def show_sample_clusters(self, df: pd.DataFrame, clusters_df: pd.DataFrame, n: int = 10):
        """Show sample clusters for review."""
        # Merge cluster info back to original data
        df_with_clusters = df.merge(
            clusters_df[['unique_id', 'cluster_id']],
            on='unique_id',
            how='left'
        )

        # Get clusters with multiple entities
        cluster_sizes = df_with_clusters.groupby('cluster_id').size()
        multi_entity_clusters = cluster_sizes[cluster_sizes > 1].index

        print(f"\n  Sample clusters (showing first {n}):")
        print("  " + "=" * 78)

        for i, cluster_id in enumerate(list(multi_entity_clusters)[:n]):
            cluster_entities = df_with_clusters[
                df_with_clusters['cluster_id'] == cluster_id
            ].sort_values('mention_count', ascending=False)

            # Primary entity (most mentions)
            primary = cluster_entities.iloc[0]
            variants = cluster_entities.iloc[1:]['name'].tolist()

            print(f"\n  {i+1}. Cluster {cluster_id}")
            print(f"     PRIMARY: {primary['name']} ({primary['mention_count']} mentions)")
            print(f"     MERGE ← {', '.join(variants)}")

    def execute_merges(self, df: pd.DataFrame, clusters_df: pd.DataFrame, dry_run: bool = False):
        """
        Execute the entity merges in the database.

        Args:
            df: Original entities DataFrame
            clusters_df: Cluster assignments from splink
            dry_run: If True, don't actually modify database
        """
        # Merge cluster info
        df_with_clusters = df.merge(
            clusters_df[['unique_id', 'cluster_id']],
            on='unique_id',
            how='left'
        )

        # Get clusters with multiple entities
        cluster_sizes = df_with_clusters.groupby('cluster_id').size()
        merge_clusters = cluster_sizes[cluster_sizes > 1].index

        print(f"\n  Executing {len(merge_clusters)} merge operations...")

        if dry_run:
            print("  [DRY RUN - No changes will be made]")
            return

        for i, cluster_id in enumerate(merge_clusters):
            if i % 10 == 0 and i > 0:
                print(f"    Completed {i}/{len(merge_clusters)} merges")

            cluster_entities = df_with_clusters[
                df_with_clusters['cluster_id'] == cluster_id
            ].sort_values('mention_count', ascending=False)

            # Choose canonical entity (most mentions)
            canonical = cluster_entities.iloc[0]
            canonical_id = canonical['unique_id']
            merged_entities = cluster_entities.iloc[1:]

            # Collect all name variants
            all_variants = set()
            for _, entity in cluster_entities.iterrows():
                all_variants.add(entity['name'])
                # Add existing variants if any
                if entity['variants'] and entity['variants'] != 'null':
                    try:
                        existing = json.loads(entity['variants'])
                        all_variants.update(existing)
                    except:
                        pass

            # Update canonical entity with all variants
            variants_json = json.dumps(list(all_variants))
            self.cursor.execute("""
                UPDATE entities
                SET variants = ?
                WHERE id = ?
            """, (variants_json, canonical_id))

            # Merge all other entities into canonical
            for _, merged_entity in merged_entities.iterrows():
                merged_id = merged_entity['unique_id']

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

                # Delete merged entity
                self.cursor.execute("DELETE FROM entities WHERE id = ?", (merged_id,))

                self.stats['merges_performed'] += 1

        # Consolidate duplicate relationships
        print("  Consolidating duplicate relationships...")
        self.consolidate_relationships()

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
        print("  Merge complete!")

    def consolidate_relationships(self):
        """Consolidate duplicate relationships after merging."""
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
                SUM(strength) as total_strength,
                SUM(document_count) as total_docs
            FROM entity_cooccurrence
            WHERE entity1 < entity2
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

    def run_merge(self, entity_type: str = 'people', threshold: float = 0.8,
                  dry_run: bool = False, show_samples: bool = True):
        """
        Run the entity merge process.

        Args:
            entity_type: Type of entity to merge
            threshold: Match probability threshold (0-1, higher = stricter)
            dry_run: If True, show what would be merged without making changes
            show_samples: Show sample clusters
        """
        print("=" * 80)
        print("SPLINK ENTITY MERGER")
        print("=" * 80)
        print(f"Database: {self.db_path}")
        print(f"Entity type: {entity_type}")
        print(f"Match threshold: {threshold}")
        print(f"Dry run: {dry_run}")
        print()

        self.connect_db()

        try:
            # Load entities
            print(f"Loading {entity_type} entities...")
            df = self.load_entities(entity_type)
            self.stats['entities_before'] = len(df)
            print(f"  Loaded {len(df)} entities")

            # Find clusters
            clusters_df = self.find_clusters(df, entity_type, threshold)

            # Analyze results
            analysis = self.analyze_clusters(clusters_df)
            self.stats['clusters_found'] = analysis['merge_clusters']

            print("\n" + "=" * 80)
            print("CLUSTERING RESULTS")
            print("=" * 80)
            print(f"Total entities: {analysis['total_entities']}")
            print(f"Total clusters: {analysis['total_clusters']}")
            print(f"Singleton clusters (no merge needed): {analysis['singleton_clusters']}")
            print(f"Multi-entity clusters (will be merged): {analysis['merge_clusters']}")
            print(f"Total merges to perform: {analysis['total_merges']}")
            print(f"Largest cluster size: {analysis['largest_cluster']}")

            # Show samples
            if show_samples and analysis['merge_clusters'] > 0:
                self.show_sample_clusters(df, clusters_df, n=15)

            # Execute merges
            if not dry_run:
                self.execute_merges(df, clusters_df, dry_run=False)

                # Get final count
                final_df = self.load_entities(entity_type)
                self.stats['entities_after'] = len(final_df)

            # Print summary
            print("\n" + "=" * 80)
            print("MERGE SUMMARY")
            print("=" * 80)
            if not dry_run:
                print(f"Entities before: {self.stats['entities_before']}")
                print(f"Entities after: {self.stats['entities_after']}")
                print(f"Reduction: {self.stats['entities_before'] - self.stats['entities_after']}")
                print(f"Merges performed: {self.stats['merges_performed']}")
            else:
                print("[DRY RUN - No changes made]")
                print(f"Would reduce from {self.stats['entities_before']} to approximately {analysis['total_clusters']} entities")
            print("=" * 80)

        finally:
            self.close_db()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Splink Entity Merger for Epstein Wiki')
    parser.add_argument('--db', type=str,
                       default='database/wiki_data.db',
                       help='Path to wiki_data.db database')
    parser.add_argument('--type', type=str,
                       default='people',
                       choices=['people', 'organizations', 'locations', 'events'],
                       help='Entity type to merge')
    parser.add_argument('--threshold', type=float,
                       default=0.85,
                       help='Match probability threshold (0-1, higher = stricter)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be merged without making changes')
    parser.add_argument('--no-samples', action='store_true',
                       help='Don\'t show sample clusters')

    args = parser.parse_args()

    merger = SplinkEntityMerger(args.db)
    merger.run_merge(
        entity_type=args.type,
        threshold=args.threshold,
        dry_run=args.dry_run,
        show_samples=not args.no_samples
    )


if __name__ == "__main__":
    main()
