#!/usr/bin/env python3
"""
Optimized Wiki Data Builder
Creates filtered entity database with smart co-occurrence relationships
"""

import json
import sqlite3
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Filtering thresholds - OPTIMIZED for manageable dataset
THRESHOLDS = {
    'people': {'doc_count': 5, 'mention_count': 15},
    'organizations': {'doc_count': 5, 'mention_count': 12},
    'locations': {'doc_count': 8, 'mention_count': 20},
    'events': {'doc_count': 5, 'mention_count': 15}
}

MIN_COOCCURRENCE_STRENGTH = 3  # Minimum shared documents for relationship
MAX_RELATIONSHIPS = 500000  # Maximum relationships to keep


class WikiDataBuilder:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.output_path = self.base_path / 'output'
        self.db_path = self.base_path / 'database' / 'wiki_data.db'

        self.entity_batches = [
            self.output_path / f'entities_batch_{i}.json'
            for i in range(1, 5)
        ]

        # Statistics
        self.stats = {
            'total_entities': 0,
            'filtered_entities': 0,
            'relationships': 0,
            'start_time': time.time()
        }

    def create_database(self):
        """Create optimized SQLite database schema"""
        print("Creating database schema...")

        # Remove old database if exists
        if self.db_path.exists():
            self.db_path.unlink()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create tables
        cursor.execute('''
            CREATE TABLE entities (
                id TEXT PRIMARY KEY,
                name TEXT,
                type TEXT,
                mention_count INTEGER,
                document_count INTEGER,
                variants TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE entity_documents (
                entity_id TEXT,
                document_id TEXT,
                mention_count INTEGER,
                PRIMARY KEY (entity_id, document_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE entity_cooccurrence (
                entity1 TEXT,
                entity2 TEXT,
                strength INTEGER,
                PRIMARY KEY (entity1, entity2)
            )
        ''')

        # Create indices
        cursor.execute('CREATE INDEX idx_entity_type ON entities(type)')
        cursor.execute('CREATE INDEX idx_entity_mentions ON entities(mention_count DESC)')
        cursor.execute('CREATE INDEX idx_cooccur_strength ON entity_cooccurrence(strength DESC)')

        conn.commit()
        conn.close()

        print(f"Database created at: {self.db_path}")

    def load_and_filter_entities(self) -> Dict[str, Dict]:
        """Load entities from all batches and apply filtering"""
        print("\nLoading and filtering entities...")

        # Track entities across batches
        entity_map = defaultdict(lambda: {
            'name': None,
            'type': None,
            'normalized': None,
            'variants': set(),
            'documents': defaultdict(int),
            'total_mentions': 0
        })

        for batch_num, batch_file in enumerate(self.entity_batches, 1):
            print(f"  Processing batch {batch_num}...")

            with open(batch_file) as f:
                data = json.load(f)

            for entity_type, entities in data['entities'].items():
                for entity in entities:
                    name = entity['name']
                    normalized = entity['normalized']

                    # Use normalized ID as key
                    entity_id = f"{entity_type}:{normalized}"

                    # Update entity data
                    e = entity_map[entity_id]
                    if e['name'] is None:
                        e['name'] = name
                        e['type'] = entity_type
                        e['normalized'] = normalized

                    # Track variants
                    e['variants'].add(name)

                    # Track document mentions
                    for mention in entity['mentions']:
                        doc_id = mention['doc_id']
                        e['documents'][doc_id] += 1
                        e['total_mentions'] += 1

                self.stats['total_entities'] += len(entities)

        print(f"  Total entities loaded: {len(entity_map)}")
        print(f"  Total mentions across all entities: {self.stats['total_entities']}")

        # Apply filtering
        print("\nApplying significance filters...")
        filtered_entities = {}

        for entity_id, entity_data in entity_map.items():
            entity_type = entity_data['type']
            doc_count = len(entity_data['documents'])
            mention_count = entity_data['total_mentions']

            threshold = THRESHOLDS[entity_type]

            # Check if entity meets significance criteria
            if (doc_count >= threshold['doc_count'] or
                mention_count >= threshold['mention_count']):
                filtered_entities[entity_id] = {
                    'id': entity_id,
                    'name': entity_data['name'],
                    'type': entity_type,
                    'normalized': entity_data['normalized'],
                    'variants': list(entity_data['variants']),
                    'documents': dict(entity_data['documents']),
                    'mention_count': mention_count,
                    'document_count': doc_count
                }

        self.stats['filtered_entities'] = len(filtered_entities)

        print(f"  Significant entities: {len(filtered_entities)}")
        print("\nBreakdown by type:")
        for entity_type in ['people', 'organizations', 'locations', 'events']:
            count = sum(1 for e in filtered_entities.values() if e['type'] == entity_type)
            print(f"    {entity_type}: {count}")

        return filtered_entities

    def insert_entities(self, entities: Dict[str, Dict]):
        """Insert filtered entities into database"""
        print("\nInserting entities into database...")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        entity_rows = []
        doc_rows = []

        for entity_id, entity in entities.items():
            # Prepare entity row
            entity_rows.append((
                entity_id,
                entity['name'],
                entity['type'],
                entity['mention_count'],
                entity['document_count'],
                json.dumps(entity['variants'])
            ))

            # Prepare entity-document relationships
            for doc_id, count in entity['documents'].items():
                doc_rows.append((entity_id, doc_id, count))

        # Batch insert
        cursor.executemany(
            'INSERT INTO entities VALUES (?, ?, ?, ?, ?, ?)',
            entity_rows
        )

        cursor.executemany(
            'INSERT INTO entity_documents VALUES (?, ?, ?)',
            doc_rows
        )

        conn.commit()
        conn.close()

        print(f"  Inserted {len(entity_rows)} entities")
        print(f"  Inserted {len(doc_rows)} entity-document relationships")

    def build_cooccurrence(self, entities: Dict[str, Dict]):
        """Build co-occurrence relationships for filtered entities"""
        print("\nBuilding co-occurrence relationships...")

        # Group entities by document
        doc_entities = defaultdict(set)

        for entity_id, entity in entities.items():
            for doc_id in entity['documents'].keys():
                doc_entities[doc_id].add(entity_id)

        print(f"  Processing {len(doc_entities)} documents...")

        # Count co-occurrences
        cooccurrence = defaultdict(lambda: defaultdict(int))

        for doc_id, entity_ids in doc_entities.items():
            # Create pairs from entities in this document
            entity_list = sorted(entity_ids)
            for i, e1 in enumerate(entity_list):
                for e2 in entity_list[i+1:]:
                    cooccurrence[e1][e2] += 1

        # Filter and prepare for insertion
        relationships = []

        for e1, connections in cooccurrence.items():
            for e2, strength in connections.items():
                if strength >= MIN_COOCCURRENCE_STRENGTH:
                    relationships.append((e1, e2, strength))

        print(f"  Found {len(relationships)} raw relationships (strength >= {MIN_COOCCURRENCE_STRENGTH})")

        # Sort by strength and limit to top relationships
        relationships.sort(key=lambda x: x[2], reverse=True)
        if len(relationships) > MAX_RELATIONSHIPS:
            print(f"  Limiting to top {MAX_RELATIONSHIPS} strongest relationships")
            relationships = relationships[:MAX_RELATIONSHIPS]

        self.stats['relationships'] = len(relationships)

        # Insert into database in batches
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        batch_size = 10000
        for i in range(0, len(relationships), batch_size):
            batch = relationships[i:i+batch_size]
            cursor.executemany(
                'INSERT INTO entity_cooccurrence VALUES (?, ?, ?)',
                batch
            )
            if (i // batch_size + 1) % 10 == 0:
                print(f"    Inserted {i+len(batch):,} / {len(relationships):,} relationships...")

        conn.commit()
        conn.close()

        print(f"  {len(relationships)} relationships inserted into database")

    def generate_entity_index(self, entities: Dict[str, Dict]):
        """Generate consolidated entity index JSON"""
        print("\nGenerating entity index...")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        entity_index = {}

        for entity_id, entity in entities.items():
            # Get top co-occurrences for this entity
            cursor.execute('''
                SELECT entity2, strength FROM entity_cooccurrence
                WHERE entity1 = ?
                ORDER BY strength DESC
                LIMIT 20
            ''', (entity_id,))

            cooccurrences = [
                {'entity': e2, 'strength': strength}
                for e2, strength in cursor.fetchall()
            ]

            # Also check reverse relationships
            cursor.execute('''
                SELECT entity1, strength FROM entity_cooccurrence
                WHERE entity2 = ?
                ORDER BY strength DESC
                LIMIT 20
            ''', (entity_id,))

            for e1, strength in cursor.fetchall():
                cooccurrences.append({'entity': e1, 'strength': strength})

            # Sort by strength and take top 20
            cooccurrences.sort(key=lambda x: x['strength'], reverse=True)
            cooccurrences = cooccurrences[:20]

            entity_index[entity['normalized']] = {
                'name': entity['name'],
                'type': entity['type'],
                'mentions': entity['mention_count'],
                'documents': entity['document_count'],
                'top_cooccurrences': cooccurrences
            }

        conn.close()

        # Write to file
        index_path = self.output_path / 'entity_index.json'
        with open(index_path, 'w') as f:
            json.dump(entity_index, f, indent=2)

        print(f"  Entity index saved to: {index_path}")
        print(f"  Index size: {index_path.stat().st_size / 1024 / 1024:.2f} MB")

    def generate_graph_viz(self, top_n: int = 500):
        """Generate graph visualization data for top N entities"""
        print(f"\nGenerating graph visualization (top {top_n} entities)...")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get top N entities by mention count
        cursor.execute('''
            SELECT id, name, type, mention_count, document_count
            FROM entities
            ORDER BY mention_count DESC
            LIMIT ?
        ''', (top_n,))

        top_entities = cursor.fetchall()
        top_entity_ids = {e[0] for e in top_entities}

        # Create nodes
        nodes = []
        for entity_id, name, entity_type, mention_count, doc_count in top_entities:
            nodes.append({
                'id': entity_id,
                'label': name,
                'group': entity_type,
                'value': mention_count,
                'title': f"{name}\n{entity_type}\n{mention_count} mentions\n{doc_count} documents"
            })

        # Get edges between top entities
        cursor.execute('''
            SELECT entity1, entity2, strength
            FROM entity_cooccurrence
            WHERE entity1 IN ({})
              AND entity2 IN ({})
            ORDER BY strength DESC
        '''.format(
            ','.join('?' * len(top_entity_ids)),
            ','.join('?' * len(top_entity_ids))
        ), list(top_entity_ids) + list(top_entity_ids))

        edges = []
        for e1, e2, strength in cursor.fetchall():
            edges.append({
                'from': e1,
                'to': e2,
                'value': strength,
                'title': f"{strength} shared documents"
            })

        conn.close()

        # Create graph structure
        graph = {
            'nodes': nodes,
            'edges': edges
        }

        # Write to file
        graph_path = self.output_path / 'graph_viz.json'
        with open(graph_path, 'w') as f:
            json.dump(graph, f, indent=2)

        print(f"  Graph saved to: {graph_path}")
        print(f"  Nodes: {len(nodes)}, Edges: {len(edges)}")
        print(f"  File size: {graph_path.stat().st_size / 1024 / 1024:.2f} MB")

    def generate_report(self):
        """Generate summary statistics report"""
        print("\n" + "="*60)
        print("SUMMARY REPORT")
        print("="*60)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Processing time
        elapsed = time.time() - self.stats['start_time']
        print(f"\nProcessing Time: {elapsed:.2f} seconds ({elapsed/60:.2f} minutes)")

        # Entity statistics
        print(f"\nEntity Statistics:")
        print(f"  Total entities (raw): {self.stats['total_entities']:,}")
        print(f"  Significant entities: {self.stats['filtered_entities']:,}")
        print(f"  Reduction: {(1 - self.stats['filtered_entities']/len(set(range(self.stats['total_entities']))))*100:.1f}%")

        # Breakdown by type
        print(f"\nEntities by Type:")
        for entity_type in ['people', 'organizations', 'locations', 'events']:
            cursor.execute('SELECT COUNT(*) FROM entities WHERE type = ?', (entity_type,))
            count = cursor.fetchone()[0]
            print(f"  {entity_type.capitalize()}: {count:,}")

        # Relationship statistics
        print(f"\nRelationship Statistics:")
        print(f"  Total relationships: {self.stats['relationships']:,}")

        cursor.execute('SELECT AVG(strength), MAX(strength) FROM entity_cooccurrence')
        avg_strength, max_strength = cursor.fetchone()
        print(f"  Average strength: {avg_strength:.2f}")
        print(f"  Maximum strength: {max_strength}")

        # Top 20 most connected entities
        print(f"\nTop 20 Most Connected Entities:")
        cursor.execute('''
            SELECT e.name, e.type, e.mention_count, e.document_count, COUNT(c.entity2) as connections
            FROM entities e
            LEFT JOIN entity_cooccurrence c ON e.id = c.entity1
            GROUP BY e.id
            ORDER BY connections DESC, e.mention_count DESC
            LIMIT 20
        ''')

        for i, (name, entity_type, mentions, docs, connections) in enumerate(cursor.fetchall(), 1):
            print(f"  {i:2d}. {name:40s} ({entity_type:15s}) - {connections:4d} connections, {mentions:5d} mentions, {docs:3d} docs")

        # Database sizes
        print(f"\nDatabase Sizes:")
        db_size_mb = self.db_path.stat().st_size / 1024 / 1024
        print(f"  wiki_data.db: {db_size_mb:.2f} MB")

        index_path = self.output_path / 'entity_index.json'
        if index_path.exists():
            index_size_mb = index_path.stat().st_size / 1024 / 1024
            print(f"  entity_index.json: {index_size_mb:.2f} MB")

        graph_path = self.output_path / 'graph_viz.json'
        if graph_path.exists():
            graph_size_mb = graph_path.stat().st_size / 1024 / 1024
            print(f"  graph_viz.json: {graph_size_mb:.2f} MB")

        conn.close()

        print("\n" + "="*60)

    def build(self):
        """Main build process"""
        print("="*60)
        print("OPTIMIZED WIKI DATA BUILDER")
        print("="*60)

        # Step 1: Create database
        self.create_database()

        # Step 2: Load and filter entities
        entities = self.load_and_filter_entities()

        # Step 3: Insert entities
        self.insert_entities(entities)

        # Step 4: Build co-occurrence relationships
        self.build_cooccurrence(entities)

        # Step 5: Generate entity index
        self.generate_entity_index(entities)

        # Step 6: Generate graph visualization
        self.generate_graph_viz(top_n=500)

        # Step 7: Generate report
        self.generate_report()

        print("\n✓ Wiki data build completed successfully!")


if __name__ == '__main__':
    builder = WikiDataBuilder('/Users/am/Research/Epstein/epstein-wiki')
    builder.build()
