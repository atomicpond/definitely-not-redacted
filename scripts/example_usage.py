#!/usr/bin/env python3
"""
Example usage of the Epstein Wiki Data
Demonstrates common queries and data access patterns
"""

import json
import sqlite3
from pathlib import Path


def example_1_load_entity_index():
    """Example 1: Load and explore the entity index"""
    print("="*70)
    print("EXAMPLE 1: Loading Entity Index")
    print("="*70)

    with open('../output/entity_index.json') as f:
        entities = json.load(f)

    print(f"\nTotal entities in index: {len(entities):,}")

    # Access specific entity
    if 'jeffrey-epstein' in entities:
        je = entities['jeffrey-epstein']
        print(f"\nJeffrey Epstein:")
        print(f"  Name: {je['name']}")
        print(f"  Type: {je['type']}")
        print(f"  Mentions: {je['mentions']:,}")
        print(f"  Documents: {je['documents']}")
        print(f"\n  Top 5 connections:")
        for i, conn in enumerate(je['top_cooccurrences'][:5], 1):
            conn_entity = entities.get(conn['entity'].split(':')[-1], {})
            conn_name = conn_entity.get('name', conn['entity'])
            print(f"    {i}. {conn_name} ({conn['strength']} shared docs)")


def example_2_database_queries():
    """Example 2: Query the SQLite database"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Database Queries")
    print("="*70)

    conn = sqlite3.connect('../database/wiki_data.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Find all entities with "Clinton" in the name
    print("\nEntities with 'Clinton' in name:")
    cursor.execute("""
        SELECT name, type, mention_count, document_count
        FROM entities
        WHERE name LIKE '%Clinton%'
        ORDER BY mention_count DESC
        LIMIT 5
    """)

    for row in cursor.fetchall():
        print(f"  • {row['name']:30s} ({row['type']:12s}) - "
              f"{row['mention_count']:4d} mentions, {row['document_count']:3d} docs")

    # Find strongest relationships
    print("\nStrongest relationships involving Clinton:")
    cursor.execute("""
        SELECT
            e1.name as entity1,
            e2.name as entity2,
            c.strength
        FROM entity_cooccurrence c
        JOIN entities e1 ON c.entity1 = e1.id
        JOIN entities e2 ON c.entity2 = e2.id
        WHERE e1.name LIKE '%Clinton%' OR e2.name LIKE '%Clinton%'
        ORDER BY c.strength DESC
        LIMIT 5
    """)

    for row in cursor.fetchall():
        print(f"  • {row['entity1']:25s} ↔ {row['entity2']:25s} ({row['strength']} docs)")

    conn.close()


def example_3_network_analysis():
    """Example 3: Analyze entity networks"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Network Analysis")
    print("="*70)

    conn = sqlite3.connect('../database/wiki_data.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Find most connected people
    print("\nTop 10 Most Connected People:")
    cursor.execute("""
        SELECT
            e.name,
            e.mention_count,
            e.document_count,
            COUNT(DISTINCT c.entity2) as out_connections,
            COUNT(DISTINCT c2.entity1) as in_connections,
            COUNT(DISTINCT c.entity2) + COUNT(DISTINCT c2.entity1) as total_connections
        FROM entities e
        LEFT JOIN entity_cooccurrence c ON e.id = c.entity1
        LEFT JOIN entity_cooccurrence c2 ON e.id = c2.entity2
        WHERE e.type = 'people'
        GROUP BY e.id
        ORDER BY total_connections DESC
        LIMIT 10
    """)

    for i, row in enumerate(cursor.fetchall(), 1):
        print(f"  {i:2d}. {row['name']:35s} - {row['total_connections']:4d} connections, "
              f"{row['mention_count']:4d} mentions")

    conn.close()


def example_4_shared_documents():
    """Example 4: Find shared documents between entities"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Shared Documents")
    print("="*70)

    conn = sqlite3.connect('../database/wiki_data.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Find entity IDs
    cursor.execute("SELECT id FROM entities WHERE name = 'Jeffrey Epstein'")
    epstein_id = cursor.fetchone()[0]

    cursor.execute("SELECT id FROM entities WHERE name LIKE 'Bill%Clinton'")
    clinton_row = cursor.fetchone()
    if clinton_row:
        clinton_id = clinton_row[0]

        # Get shared documents
        cursor.execute("""
            SELECT ed1.document_id
            FROM entity_documents ed1
            JOIN entity_documents ed2
                ON ed1.document_id = ed2.document_id
            WHERE ed1.entity_id = ? AND ed2.entity_id = ?
            ORDER BY ed1.mention_count DESC
            LIMIT 10
        """, (epstein_id, clinton_id))

        docs = [row[0] for row in cursor.fetchall()]
        print(f"\nJeffrey Epstein and Bill Clinton appear together in {len(docs)} documents:")
        for i, doc_id in enumerate(docs[:5], 1):
            print(f"  {i}. {doc_id}")

    conn.close()


def example_5_graph_visualization_data():
    """Example 5: Load graph visualization data"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Graph Visualization Data")
    print("="*70)

    with open('../output/graph_viz.json') as f:
        graph = json.load(f)

    print(f"\nGraph contains:")
    print(f"  Nodes: {len(graph['nodes']):,}")
    print(f"  Edges: {len(graph['edges']):,}")

    # Group nodes by type
    node_types = {}
    for node in graph['nodes']:
        node_type = node['group']
        node_types[node_type] = node_types.get(node_type, 0) + 1

    print(f"\n  Nodes by type:")
    for node_type, count in sorted(node_types.items(), key=lambda x: x[1], reverse=True):
        print(f"    {node_type}: {count}")

    # Find most connected nodes in graph
    print(f"\n  Top 5 nodes by degree (in graph):")
    node_degrees = {}
    for edge in graph['edges']:
        node_degrees[edge['from']] = node_degrees.get(edge['from'], 0) + 1
        node_degrees[edge['to']] = node_degrees.get(edge['to'], 0) + 1

    for i, (node_id, degree) in enumerate(
        sorted(node_degrees.items(), key=lambda x: x[1], reverse=True)[:5], 1
    ):
        node = next(n for n in graph['nodes'] if n['id'] == node_id)
        print(f"    {i}. {node['label']:35s} - {degree:3d} connections")


def example_6_entity_stats():
    """Example 6: Entity statistics and distributions"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Entity Statistics")
    print("="*70)

    conn = sqlite3.connect('../database/wiki_data.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Distribution of mentions
    print("\nMention count distribution:")
    cursor.execute("""
        SELECT
            CASE
                WHEN mention_count < 20 THEN '< 20'
                WHEN mention_count < 50 THEN '20-49'
                WHEN mention_count < 100 THEN '50-99'
                WHEN mention_count < 200 THEN '100-199'
                WHEN mention_count < 500 THEN '200-499'
                ELSE '500+'
            END as bucket,
            COUNT(*) as count
        FROM entities
        GROUP BY bucket
        ORDER BY MIN(mention_count)
    """)

    for row in cursor.fetchall():
        bar = '█' * (row['count'] // 100)
        print(f"  {row['bucket']:10s}: {row['count']:5d} entities {bar}")

    # Top entities by document coverage
    print("\nEntities appearing in most documents:")
    cursor.execute("""
        SELECT name, type, document_count, mention_count
        FROM entities
        ORDER BY document_count DESC
        LIMIT 5
    """)

    for i, row in enumerate(cursor.fetchall(), 1):
        print(f"  {i}. {row['name']:35s} - {row['document_count']:4d} docs, "
              f"{row['mention_count']:5d} mentions")

    conn.close()


def main():
    """Run all examples"""
    print("\n" + "╔" + "═"*68 + "╗")
    print("║" + " "*20 + "EPSTEIN WIKI DATA EXAMPLES" + " "*22 + "║")
    print("╚" + "═"*68 + "╝\n")

    try:
        example_1_load_entity_index()
        example_2_database_queries()
        example_3_network_analysis()
        example_4_shared_documents()
        example_5_graph_visualization_data()
        example_6_entity_stats()

        print("\n" + "="*70)
        print("All examples completed successfully!")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
