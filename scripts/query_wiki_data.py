#!/usr/bin/env python3
"""
Query utility for wiki_data.db
Provides convenient functions to explore entity relationships
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Tuple


class WikiDataQuery:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent / 'database' / 'wiki_data.db'
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def search_entities(self, name_pattern: str, entity_type: str = None, limit: int = 10) -> List[Dict]:
        """Search for entities by name pattern"""
        query = "SELECT * FROM entities WHERE name LIKE ?"
        params = [f"%{name_pattern}%"]

        if entity_type:
            query += " AND type = ?"
            params.append(entity_type)

        query += " ORDER BY mention_count DESC LIMIT ?"
        params.append(limit)

        cursor = self.conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_entity(self, entity_id: str) -> Dict:
        """Get entity by ID"""
        cursor = self.conn.execute(
            "SELECT * FROM entities WHERE id = ?",
            (entity_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_entity_by_name(self, name: str) -> List[Dict]:
        """Get entities by exact name"""
        cursor = self.conn.execute(
            "SELECT * FROM entities WHERE name = ?",
            (name,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_connections(self, entity_id: str, limit: int = 20) -> List[Dict]:
        """Get top connections for an entity"""
        query = """
            SELECT
                e2.id,
                e2.name,
                e2.type,
                e2.mention_count,
                e2.document_count,
                c.strength
            FROM entity_cooccurrence c
            JOIN entities e2 ON c.entity2 = e2.id
            WHERE c.entity1 = ?
            ORDER BY c.strength DESC
            LIMIT ?
        """
        cursor = self.conn.execute(query, (entity_id, limit))
        connections = [dict(row) for row in cursor.fetchall()]

        # Also check reverse relationships
        query_reverse = """
            SELECT
                e1.id,
                e1.name,
                e1.type,
                e1.mention_count,
                e1.document_count,
                c.strength
            FROM entity_cooccurrence c
            JOIN entities e1 ON c.entity1 = e1.id
            WHERE c.entity2 = ?
            ORDER BY c.strength DESC
            LIMIT ?
        """
        cursor = self.conn.execute(query_reverse, (entity_id, limit))
        connections.extend([dict(row) for row in cursor.fetchall()])

        # Sort by strength and deduplicate
        seen = set()
        unique_connections = []
        for conn in sorted(connections, key=lambda x: x['strength'], reverse=True):
            if conn['id'] not in seen:
                seen.add(conn['id'])
                unique_connections.append(conn)

        return unique_connections[:limit]

    def get_shared_documents(self, entity1_id: str, entity2_id: str) -> List[str]:
        """Get document IDs shared between two entities"""
        query = """
            SELECT ed1.document_id
            FROM entity_documents ed1
            JOIN entity_documents ed2
                ON ed1.document_id = ed2.document_id
            WHERE ed1.entity_id = ? AND ed2.entity_id = ?
            ORDER BY ed1.mention_count DESC
        """
        cursor = self.conn.execute(query, (entity1_id, entity2_id))
        return [row[0] for row in cursor.fetchall()]

    def get_top_entities(self, entity_type: str = None, limit: int = 20) -> List[Dict]:
        """Get top entities by mention count"""
        query = "SELECT * FROM entities"
        params = []

        if entity_type:
            query += " WHERE type = ?"
            params.append(entity_type)

        query += " ORDER BY mention_count DESC LIMIT ?"
        params.append(limit)

        cursor = self.conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_entity_network(self, entity_id: str, depth: int = 1) -> Dict:
        """Get entity network up to specified depth"""
        network = {
            'nodes': {},
            'edges': []
        }

        # Get root entity
        root = self.get_entity(entity_id)
        if not root:
            return network

        network['nodes'][entity_id] = root

        # Get direct connections
        connections = self.get_connections(entity_id, limit=50)
        for conn in connections:
            conn_id = conn['id']
            network['nodes'][conn_id] = {
                'id': conn_id,
                'name': conn['name'],
                'type': conn['type'],
                'mention_count': conn['mention_count'],
                'document_count': conn['document_count']
            }
            network['edges'].append({
                'from': entity_id,
                'to': conn_id,
                'strength': conn['strength']
            })

            # Get second-level connections if depth > 1
            if depth > 1:
                second_level = self.get_connections(conn_id, limit=10)
                for conn2 in second_level:
                    conn2_id = conn2['id']
                    if conn2_id not in network['nodes'] and conn2_id != entity_id:
                        network['nodes'][conn2_id] = {
                            'id': conn2_id,
                            'name': conn2['name'],
                            'type': conn2['type'],
                            'mention_count': conn2['mention_count'],
                            'document_count': conn2['document_count']
                        }
                        network['edges'].append({
                            'from': conn_id,
                            'to': conn2_id,
                            'strength': conn2['strength']
                        })

        return network

    def get_statistics(self) -> Dict:
        """Get database statistics"""
        stats = {}

        # Total entities
        cursor = self.conn.execute("SELECT COUNT(*) FROM entities")
        stats['total_entities'] = cursor.fetchone()[0]

        # Entities by type
        cursor = self.conn.execute(
            "SELECT type, COUNT(*) as count FROM entities GROUP BY type"
        )
        stats['entities_by_type'] = {row[0]: row[1] for row in cursor.fetchall()}

        # Total relationships
        cursor = self.conn.execute("SELECT COUNT(*) FROM entity_cooccurrence")
        stats['total_relationships'] = cursor.fetchone()[0]

        # Average relationship strength
        cursor = self.conn.execute(
            "SELECT AVG(strength), MAX(strength), MIN(strength) FROM entity_cooccurrence"
        )
        avg, max_s, min_s = cursor.fetchone()
        stats['relationship_strength'] = {
            'average': avg,
            'maximum': max_s,
            'minimum': min_s
        }

        return stats

    def close(self):
        """Close database connection"""
        self.conn.close()


def main():
    """Command-line interface"""
    import sys

    query = WikiDataQuery()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python query_wiki_data.py search <name>")
        print("  python query_wiki_data.py entity <entity_id>")
        print("  python query_wiki_data.py connections <entity_id>")
        print("  python query_wiki_data.py top [type]")
        print("  python query_wiki_data.py stats")
        return

    command = sys.argv[1]

    if command == "search":
        name = sys.argv[2] if len(sys.argv) > 2 else ""
        results = query.search_entities(name)
        print(f"\nFound {len(results)} entities matching '{name}':\n")
        for entity in results:
            print(f"  {entity['id']}")
            print(f"    Name: {entity['name']}")
            print(f"    Type: {entity['type']}")
            print(f"    Mentions: {entity['mention_count']}")
            print(f"    Documents: {entity['document_count']}")
            print()

    elif command == "entity":
        entity_id = sys.argv[2] if len(sys.argv) > 2 else ""
        entity = query.get_entity(entity_id)
        if entity:
            print(f"\nEntity: {entity['id']}")
            print(f"  Name: {entity['name']}")
            print(f"  Type: {entity['type']}")
            print(f"  Mentions: {entity['mention_count']}")
            print(f"  Documents: {entity['document_count']}")
            variants = json.loads(entity['variants'])
            print(f"  Variants: {', '.join(variants[:5])}")
        else:
            print(f"Entity not found: {entity_id}")

    elif command == "connections":
        entity_id = sys.argv[2] if len(sys.argv) > 2 else ""
        connections = query.get_connections(entity_id, limit=20)
        print(f"\nTop {len(connections)} connections for {entity_id}:\n")
        for i, conn in enumerate(connections, 1):
            print(f"{i:2d}. {conn['name']:40s} ({conn['type']:15s}) - {conn['strength']:3d} shared docs")

    elif command == "top":
        entity_type = sys.argv[2] if len(sys.argv) > 2 else None
        entities = query.get_top_entities(entity_type, limit=20)
        type_str = f" ({entity_type})" if entity_type else ""
        print(f"\nTop {len(entities)} entities{type_str}:\n")
        for i, entity in enumerate(entities, 1):
            print(f"{i:2d}. {entity['name']:40s} ({entity['type']:15s}) - {entity['mention_count']:5d} mentions, {entity['document_count']:3d} docs")

    elif command == "stats":
        stats = query.get_statistics()
        print("\nDatabase Statistics:\n")
        print(f"Total Entities: {stats['total_entities']:,}")
        print(f"\nEntities by Type:")
        for entity_type, count in stats['entities_by_type'].items():
            print(f"  {entity_type.capitalize()}: {count:,}")
        print(f"\nTotal Relationships: {stats['total_relationships']:,}")
        print(f"\nRelationship Strength:")
        print(f"  Average: {stats['relationship_strength']['average']:.2f}")
        print(f"  Maximum: {stats['relationship_strength']['maximum']}")
        print(f"  Minimum: {stats['relationship_strength']['minimum']}")

    else:
        print(f"Unknown command: {command}")

    query.close()


if __name__ == '__main__':
    main()
