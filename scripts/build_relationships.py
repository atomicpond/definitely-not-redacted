#!/usr/bin/env python3
"""
Relationship Graph Builder
Merges entity batch files, deduplicates entities, and builds relationship database.
"""

import json
import sqlite3
import re
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple
import Levenshtein
from datetime import datetime

class RelationshipGraphBuilder:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.output_path = self.base_path / "output"
        self.db_path = self.base_path / "database"
        self.entities = defaultdict(list)
        self.entity_map = {}  # normalized_name -> entity_id
        self.dedup_stats = {
            "original_count": 0,
            "merged_count": 0,
            "variants_merged": 0
        }

    def normalize_name(self, name: str) -> str:
        """Normalize entity name for deduplication."""
        # Convert to lowercase
        normalized = name.lower()
        # Remove titles
        titles = ['mr.', 'ms.', 'mrs.', 'dr.', 'prof.', 'hon.', 'judge', 'president', 'senator']
        for title in titles:
            if normalized.startswith(title + ' '):
                normalized = normalized[len(title)+1:]
        # Remove special characters except hyphens and spaces
        normalized = re.sub(r'[^\w\s-]', '', normalized)
        # Replace spaces with hyphens
        normalized = re.sub(r'\s+', '-', normalized.strip())
        # Remove multiple consecutive hyphens
        normalized = re.sub(r'-+', '-', normalized)
        # Remove leading/trailing hyphens
        normalized = normalized.strip('-')
        return normalized

    def fuzzy_match(self, name1: str, name2: str, threshold: float = 0.15) -> bool:
        """Check if two names are fuzzy matches using Levenshtein distance."""
        if not name1 or not name2:
            return False
        distance = Levenshtein.distance(name1, name2)
        max_len = max(len(name1), len(name2))
        if max_len == 0:
            return True
        ratio = distance / max_len
        return ratio < threshold

    def load_batch_files(self) -> Dict:
        """Load all entity batch JSON files."""
        print("Loading entity batch files...")
        batch_files = [
            self.output_path / "entities_batch_1.json",
            self.output_path / "entities_batch_2.json",
            self.output_path / "entities_batch_3.json",
            self.output_path / "entities_batch_4.json"
        ]

        all_entities = defaultdict(list)
        total_docs = 0

        for batch_file in batch_files:
            if not batch_file.exists():
                print(f"Warning: {batch_file} not found, skipping...")
                continue

            print(f"  Loading {batch_file.name}...")
            with open(batch_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            batch_num = data.get('batch', 0)
            total_docs += data.get('documents_processed', 0)

            # Merge entities by category
            for category in ['people', 'organizations', 'locations', 'events']:
                if category in data.get('entities', {}):
                    for entity in data['entities'][category]:
                        entity['source_batch'] = batch_num
                        all_entities[category].append(entity)

        print(f"  Loaded {total_docs} documents")
        print(f"  People: {len(all_entities['people'])}")
        print(f"  Organizations: {len(all_entities['organizations'])}")
        print(f"  Locations: {len(all_entities['locations'])}")
        print(f"  Events: {len(all_entities['events'])}")

        self.dedup_stats['original_count'] = sum(len(v) for v in all_entities.values())
        return all_entities

    def deduplicate_entities(self, entities_by_category: Dict) -> Dict:
        """Deduplicate entities using fuzzy matching."""
        print("\nDeduplicating entities...")
        deduplicated = {}

        for category, entities in entities_by_category.items():
            print(f"\n  Processing {category}...")
            print(f"    Original count: {len(entities)}")

            # Group entities by normalized name
            name_groups = defaultdict(list)
            for entity in entities:
                norm_name = self.normalize_name(entity['name'])
                name_groups[norm_name].append(entity)

            # Fuzzy match across different normalized names
            merged_entities = []
            processed = set()
            norm_names = list(name_groups.keys())

            for i, norm_name in enumerate(norm_names):
                if norm_name in processed:
                    continue

                # Find all fuzzy matches
                matches = [norm_name]
                for j in range(i + 1, len(norm_names)):
                    other_norm = norm_names[j]
                    if other_norm in processed:
                        continue
                    if self.fuzzy_match(norm_name, other_norm):
                        matches.append(other_norm)
                        processed.add(other_norm)

                # Merge all matched entities
                all_variants = []
                all_mentions = []
                source_batches = set()

                for match in matches:
                    for entity in name_groups[match]:
                        all_variants.append(entity['name'])
                        all_mentions.extend(entity.get('mentions', []))
                        source_batches.add(entity.get('source_batch', 0))

                # Choose primary name (most common or longest)
                variant_counts = Counter(all_variants)
                primary_name = variant_counts.most_common(1)[0][0]

                # Create merged entity
                merged_entity = {
                    'entity_id': f"{category}_{norm_name}",
                    'entity_type': category,
                    'primary_name': primary_name,
                    'normalized_name': norm_name,
                    'variants': list(set(all_variants)),
                    'mentions': all_mentions,
                    'source_batches': list(source_batches)
                }

                merged_entities.append(merged_entity)
                processed.add(norm_name)

                if len(matches) > 1:
                    self.dedup_stats['variants_merged'] += len(matches) - 1

            deduplicated[category] = merged_entities
            print(f"    After deduplication: {len(merged_entities)}")
            print(f"    Reduction: {len(entities) - len(merged_entities)}")

        self.dedup_stats['merged_count'] = sum(len(v) for v in deduplicated.values())
        return deduplicated

    def create_database(self, deduplicated_entities: Dict):
        """Create SQLite database with entities and relationships."""
        print("\nCreating relationship database...")
        db_file = self.db_path / "relationships.db"

        # Remove existing database
        if db_file.exists():
            db_file.unlink()

        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Create tables
        print("  Creating tables...")
        cursor.execute('''
            CREATE TABLE entities (
                entity_id TEXT PRIMARY KEY,
                entity_type TEXT,
                primary_name TEXT,
                normalized_name TEXT,
                variants TEXT,
                total_mentions INTEGER,
                document_count INTEGER,
                first_seen_doc TEXT,
                last_seen_doc TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE entity_mentions (
                mention_id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id TEXT,
                document_id TEXT,
                context TEXT,
                position INTEGER,
                FOREIGN KEY (entity_id) REFERENCES entities(entity_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE relationships (
                relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity1_id TEXT,
                entity2_id TEXT,
                relationship_type TEXT,
                document_id TEXT,
                context TEXT,
                strength INTEGER,
                FOREIGN KEY (entity1_id) REFERENCES entities(entity_id),
                FOREIGN KEY (entity2_id) REFERENCES entities(entity_id)
            )
        ''')

        # Create indexes
        print("  Creating indexes...")
        cursor.execute('CREATE INDEX idx_entity_type ON entities(entity_type)')
        cursor.execute('CREATE INDEX idx_entity_normalized ON entities(normalized_name)')
        cursor.execute('CREATE INDEX idx_mention_entity ON entity_mentions(entity_id)')
        cursor.execute('CREATE INDEX idx_mention_doc ON entity_mentions(document_id)')
        cursor.execute('CREATE INDEX idx_rel_entity1 ON relationships(entity1_id)')
        cursor.execute('CREATE INDEX idx_rel_entity2 ON relationships(entity2_id)')
        cursor.execute('CREATE INDEX idx_rel_strength ON relationships(strength)')

        # Insert entities
        print("  Inserting entities...")
        entity_count = 0
        mention_count = 0

        for category, entities in deduplicated_entities.items():
            for entity in entities:
                # Get document statistics
                mentions = entity.get('mentions', [])
                doc_ids = [m['doc_id'] for m in mentions]
                unique_docs = list(set(doc_ids))

                cursor.execute('''
                    INSERT INTO entities (
                        entity_id, entity_type, primary_name, normalized_name,
                        variants, total_mentions, document_count,
                        first_seen_doc, last_seen_doc
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    entity['entity_id'],
                    entity['entity_type'],
                    entity['primary_name'],
                    entity['normalized_name'],
                    json.dumps(entity['variants']),
                    len(mentions),
                    len(unique_docs),
                    unique_docs[0] if unique_docs else None,
                    unique_docs[-1] if unique_docs else None
                ))

                # Insert mentions
                for mention in mentions:
                    cursor.execute('''
                        INSERT INTO entity_mentions (
                            entity_id, document_id, context, position
                        ) VALUES (?, ?, ?, ?)
                    ''', (
                        entity['entity_id'],
                        mention['doc_id'],
                        mention.get('context', ''),
                        mention.get('position', 0)
                    ))
                    mention_count += 1

                entity_count += 1

                if entity_count % 1000 == 0:
                    print(f"    Inserted {entity_count} entities, {mention_count} mentions...")

        print(f"  Total entities inserted: {entity_count}")
        print(f"  Total mentions inserted: {mention_count}")

        conn.commit()
        return conn, cursor

    def build_relationships(self, conn, cursor):
        """Build co-occurrence relationships from entity mentions."""
        print("\nBuilding relationships...")

        # Get all documents with their entities
        cursor.execute('''
            SELECT document_id, entity_id
            FROM entity_mentions
            ORDER BY document_id
        ''')

        doc_entities = defaultdict(list)
        for doc_id, entity_id in cursor.fetchall():
            doc_entities[doc_id].append(entity_id)

        print(f"  Processing {len(doc_entities)} documents...")

        # Track relationship strengths
        relationship_strength = defaultdict(int)
        relationship_docs = defaultdict(list)

        processed_docs = 0
        for doc_id, entities in doc_entities.items():
            # Create relationships for all entity pairs in this document
            unique_entities = list(set(entities))

            for i in range(len(unique_entities)):
                for j in range(i + 1, len(unique_entities)):
                    entity1 = unique_entities[i]
                    entity2 = unique_entities[j]

                    # Sort to ensure consistent ordering
                    if entity1 > entity2:
                        entity1, entity2 = entity2, entity1

                    rel_key = (entity1, entity2)
                    relationship_strength[rel_key] += 1
                    relationship_docs[rel_key].append(doc_id)

            processed_docs += 1
            if processed_docs % 100 == 0:
                print(f"    Processed {processed_docs} documents...")

        print(f"  Found {len(relationship_strength)} unique relationships")

        # Filter relationships with strength >= 2
        filtered_rels = {k: v for k, v in relationship_strength.items() if v >= 2}
        print(f"  Filtered to {len(filtered_rels)} relationships with strength >= 2")

        # Insert relationships
        print("  Inserting relationships...")
        rel_count = 0

        for (entity1, entity2), strength in filtered_rels.items():
            # Determine relationship type
            if strength >= 5:
                rel_type = 'frequent-co-mention'
            else:
                rel_type = 'co-mentioned'

            # Get a sample document for context
            sample_doc = relationship_docs[(entity1, entity2)][0]

            cursor.execute('''
                INSERT INTO relationships (
                    entity1_id, entity2_id, relationship_type,
                    document_id, context, strength
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (entity1, entity2, rel_type, sample_doc, '', strength))

            rel_count += 1
            if rel_count % 10000 == 0:
                print(f"    Inserted {rel_count} relationships...")

        print(f"  Total relationships inserted: {rel_count}")
        conn.commit()

        return relationship_strength

    def generate_summary(self, conn, cursor, deduplicated_entities: Dict):
        """Generate summary statistics."""
        print("\nGenerating summary statistics...")

        # Get entity counts by type
        cursor.execute('''
            SELECT entity_type, COUNT(*)
            FROM entities
            GROUP BY entity_type
        ''')
        entities_by_type = dict(cursor.fetchall())

        # Get total relationship count
        cursor.execute('SELECT COUNT(*) FROM relationships')
        total_relationships = cursor.fetchone()[0]

        # Get strongest relationships
        cursor.execute('''
            SELECT e1.primary_name, e2.primary_name, r.strength
            FROM relationships r
            JOIN entities e1 ON r.entity1_id = e1.entity_id
            JOIN entities e2 ON r.entity2_id = e2.entity_id
            ORDER BY r.strength DESC
            LIMIT 50
        ''')
        strongest_relationships = [
            {
                "entity1": row[0],
                "entity2": row[1],
                "strength": row[2]
            }
            for row in cursor.fetchall()
        ]

        # Get most connected entities
        cursor.execute('''
            SELECT entity_id, COUNT(*) as connection_count
            FROM (
                SELECT entity1_id as entity_id FROM relationships
                UNION ALL
                SELECT entity2_id as entity_id FROM relationships
            )
            GROUP BY entity_id
            ORDER BY connection_count DESC
            LIMIT 50
        ''')

        most_connected = []
        for entity_id, count in cursor.fetchall():
            cursor.execute('SELECT primary_name FROM entities WHERE entity_id = ?', (entity_id,))
            name = cursor.fetchone()[0]
            most_connected.append({
                "name": name,
                "entity_id": entity_id,
                "connection_count": count
            })

        # Get most mentioned entities
        cursor.execute('''
            SELECT primary_name, entity_type, total_mentions, document_count
            FROM entities
            ORDER BY total_mentions DESC
            LIMIT 50
        ''')
        most_mentioned = [
            {
                "name": row[0],
                "type": row[1],
                "mentions": row[2],
                "documents": row[3]
            }
            for row in cursor.fetchall()
        ]

        summary = {
            "total_entities": sum(entities_by_type.values()),
            "entities_by_type": entities_by_type,
            "total_relationships": total_relationships,
            "strongest_relationships": strongest_relationships,
            "most_connected_entities": most_connected,
            "most_mentioned_entities": most_mentioned,
            "deduplication_stats": {
                "original_entity_count": self.dedup_stats['original_count'],
                "after_deduplication": self.dedup_stats['merged_count'],
                "variants_merged": self.dedup_stats['variants_merged'],
                "reduction_percentage": round(
                    (1 - self.dedup_stats['merged_count'] / self.dedup_stats['original_count']) * 100, 2
                ) if self.dedup_stats['original_count'] > 0 else 0
            },
            "generated_at": datetime.now().isoformat()
        }

        # Save summary
        summary_file = self.output_path / "relationship_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, indent=2, fp=f)

        print(f"  Summary saved to {summary_file}")
        return summary

    def export_graph_data(self, conn, cursor):
        """Export graph data for visualization."""
        print("\nExporting graph data for visualization...")

        # Get nodes (entities)
        cursor.execute('''
            SELECT entity_id, primary_name, entity_type,
                   total_mentions, document_count
            FROM entities
        ''')

        nodes = [
            {
                "id": row[0],
                "label": row[1],
                "type": row[2],
                "mentions": row[3],
                "documents": row[4]
            }
            for row in cursor.fetchall()
        ]

        # Get edges (relationships) - limit to strength >= 2 for cleaner visualization
        cursor.execute('''
            SELECT entity1_id, entity2_id, strength, relationship_type
            FROM relationships
            WHERE strength >= 2
            ORDER BY strength DESC
        ''')

        edges = [
            {
                "from": row[0],
                "to": row[1],
                "weight": row[2],
                "type": row[3]
            }
            for row in cursor.fetchall()
        ]

        graph_data = {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "generated_at": datetime.now().isoformat()
            }
        }

        graph_file = self.output_path / "graph_data.json"
        with open(graph_file, 'w', encoding='utf-8') as f:
            json.dump(graph_data, indent=2, fp=f)

        print(f"  Graph data saved to {graph_file}")
        print(f"  Nodes: {len(nodes)}, Edges: {len(edges)}")

        return graph_data

    def print_report(self, summary: Dict):
        """Print comprehensive summary report."""
        print("\n" + "="*80)
        print("RELATIONSHIP GRAPH BUILD REPORT")
        print("="*80)

        print("\n📊 ENTITY STATISTICS")
        print("-" * 80)
        print(f"Total entities (before dedup): {summary['deduplication_stats']['original_entity_count']:,}")
        print(f"Total entities (after dedup):  {summary['total_entities']:,}")
        print(f"Variants merged:               {summary['deduplication_stats']['variants_merged']:,}")
        print(f"Reduction:                     {summary['deduplication_stats']['reduction_percentage']}%")

        print("\n📈 ENTITIES BY TYPE")
        print("-" * 80)
        for entity_type, count in summary['entities_by_type'].items():
            print(f"  {entity_type.capitalize():<15} {count:>8,}")

        print(f"\n🔗 RELATIONSHIPS")
        print("-" * 80)
        print(f"Total relationships: {summary['total_relationships']:,}")

        print("\n👥 TOP 20 MOST CONNECTED ENTITIES")
        print("-" * 80)
        for i, entity in enumerate(summary['most_connected_entities'][:20], 1):
            print(f"{i:2}. {entity['name']:<40} {entity['connection_count']:>6} connections")

        print("\n💪 TOP 20 STRONGEST RELATIONSHIPS")
        print("-" * 80)
        for i, rel in enumerate(summary['strongest_relationships'][:20], 1):
            print(f"{i:2}. {rel['entity1']:<30} ↔ {rel['entity2']:<30} ({rel['strength']:>3} co-mentions)")

        print("\n📢 TOP 20 MOST MENTIONED ENTITIES")
        print("-" * 80)
        for i, entity in enumerate(summary['most_mentioned_entities'][:20], 1):
            print(f"{i:2}. {entity['name']:<40} {entity['mentions']:>6} mentions in {entity['documents']:>4} docs")

        print("\n" + "="*80)
        print("✅ Relationship graph build complete!")
        print("="*80)

    def run(self):
        """Run the complete relationship building pipeline."""
        print("Starting Relationship Graph Builder")
        print("="*80)

        # Load batch files
        entities_by_category = self.load_batch_files()

        # Deduplicate entities
        deduplicated_entities = self.deduplicate_entities(entities_by_category)

        # Create database
        conn, cursor = self.create_database(deduplicated_entities)

        # Build relationships
        self.build_relationships(conn, cursor)

        # Generate summary
        summary = self.generate_summary(conn, cursor, deduplicated_entities)

        # Export graph data
        self.export_graph_data(conn, cursor)

        # Close database
        conn.close()

        # Print report
        self.print_report(summary)

        print(f"\n📁 Output files:")
        print(f"  - Database: {self.db_path / 'relationships.db'}")
        print(f"  - Summary:  {self.output_path / 'relationship_summary.json'}")
        print(f"  - Graph:    {self.output_path / 'graph_data.json'}")


if __name__ == "__main__":
    base_path = "/Users/am/Research/Epstein/epstein-wiki"
    builder = RelationshipGraphBuilder(base_path)
    builder.run()
