# Epstein Wiki Data System

An optimized entity relationship database and visualization system for the Epstein document collection, featuring 6,607 significant entities and 500,000 curated relationships.

## Quick Start

### View Statistics
```bash
python scripts/query_wiki_data.py stats
```

### Search for Entities
```bash
python scripts/query_wiki_data.py search "Jeffrey Epstein"
python scripts/query_wiki_data.py search "Clinton"
```

### Get Entity Connections
```bash
python scripts/query_wiki_data.py connections "people:jeffrey-epstein"
```

### View Top Entities
```bash
python scripts/query_wiki_data.py top people
python scripts/query_wiki_data.py top organizations
python scripts/query_wiki_data.py top locations
```

### Run Examples
```bash
cd scripts
python example_usage.py
```

## System Overview

### Data Files

| File | Size | Description |
|------|------|-------------|
| `database/wiki_data.db` | 68.30 MB | SQLite database with entities and relationships |
| `output/entity_index.json` | 8.60 MB | Entity metadata and top connections |
| `output/graph_viz.json` | 6.74 MB | Graph visualization (top 500 entities) |

### Scripts

| Script | Purpose |
|--------|---------|
| `scripts/build_wiki_data.py` | Build database from entity batches |
| `scripts/query_wiki_data.py` | Query utility and CLI |
| `scripts/example_usage.py` | Usage examples and demonstrations |

### Documentation

| Document | Description |
|----------|-------------|
| `output/WIKI_DATA_REPORT.md` | Detailed technical report |
| `AGENT_6B_SUMMARY.md` | Executive summary |
| `README_WIKI_DATA.md` | This file |

## Database Schema

### Tables

**entities**
- `id` - Unique identifier (type:normalized-name)
- `name` - Display name
- `type` - Entity type (people, organizations, locations, events)
- `mention_count` - Total mentions across all documents
- `document_count` - Number of unique documents
- `variants` - JSON array of name variations

**entity_documents**
- `entity_id` - Foreign key to entities
- `document_id` - Document Bates ID
- `mention_count` - Mentions in this document

**entity_cooccurrence**
- `entity1` - First entity ID
- `entity2` - Second entity ID
- `strength` - Number of shared documents

## Statistics

### Entity Distribution
- **People:** 2,195 (33.2%)
- **Organizations:** 1,882 (28.5%)
- **Events:** 1,965 (29.7%)
- **Locations:** 565 (8.6%)
- **Total:** 6,607 significant entities

### Relationships
- **Total:** 500,000 curated relationships
- **Average Strength:** 7.47 shared documents
- **Maximum Strength:** 597 shared documents
- **Minimum Strength:** 3 shared documents (filtering threshold)

### Processing Performance
- **Processing Time:** 1.93 minutes
- **Entity Reduction:** 95.7% (from 153,260 raw to 6,607 significant)
- **Database Size:** 68.30 MB (86% under 500 MB target)

## Usage Examples

### Python: Load Entity Index
```python
import json

with open('output/entity_index.json') as f:
    entities = json.load(f)

# Access entity data
je = entities['jeffrey-epstein']
print(f"Name: {je['name']}")
print(f"Mentions: {je['mentions']}")
print(f"Documents: {je['documents']}")
print(f"Connections: {len(je['top_cooccurrences'])}")
```

### Python: Query Database
```python
import sqlite3

conn = sqlite3.connect('database/wiki_data.db')
cursor = conn.cursor()

# Find entities
cursor.execute('''
    SELECT name, type, mention_count, document_count
    FROM entities
    WHERE name LIKE '%Epstein%'
    ORDER BY mention_count DESC
''')

for row in cursor.fetchall():
    print(row)
```

### Python: Get Connections
```python
from scripts.query_wiki_data import WikiDataQuery

query = WikiDataQuery()

# Search for entities
results = query.search_entities("Clinton", limit=5)

# Get connections
connections = query.get_connections("people:jeffrey-epstein", limit=20)

# Get shared documents
docs = query.get_shared_documents(
    "people:jeffrey-epstein",
    "people:bill-clinton"
)
```

### JavaScript: Load Graph Data
```javascript
fetch('output/graph_viz.json')
    .then(response => response.json())
    .then(graph => {
        // Use with vis.js
        const container = document.getElementById('network');
        const options = {
            nodes: {
                shape: 'dot',
                scaling: {
                    min: 10,
                    max: 30
                }
            }
        };
        const network = new vis.Network(container, graph, options);
    });
```

### SQL: Direct Queries
```sql
-- Top 10 most mentioned entities
SELECT name, type, mention_count, document_count
FROM entities
ORDER BY mention_count DESC
LIMIT 10;

-- Entities in specific documents
SELECT e.name, e.type, ed.mention_count
FROM entity_documents ed
JOIN entities e ON ed.entity_id = e.id
WHERE ed.document_id = 'HOUSE_OVERSIGHT_030299'
ORDER BY ed.mention_count DESC;

-- Strongest relationships for an entity
SELECT e2.name, c.strength
FROM entity_cooccurrence c
JOIN entities e1 ON c.entity1 = e1.id
JOIN entities e2 ON c.entity2 = e2.id
WHERE e1.name = 'Jeffrey Epstein'
ORDER BY c.strength DESC
LIMIT 20;

-- Find common connections between two entities
SELECT DISTINCT e3.name, e3.type
FROM entity_cooccurrence c1
JOIN entity_cooccurrence c2 ON c1.entity2 = c2.entity2
JOIN entities e3 ON c1.entity2 = e3.id
WHERE c1.entity1 = 'people:jeffrey-epstein'
  AND c2.entity1 = 'people:bill-clinton'
ORDER BY e3.mention_count DESC;
```

## Top Entities

### Most Connected People
1. Bill Clinton (271 connections)
2. Barack Obama (270 connections)
3. Jeffrey Epstein (230 connections)
4. Jeffrey E (216 connections)
5. Donald Trump (156 connections)

### Most Connected Organizations
1. HOUSE (1,965 connections)
2. Congress (1,092 connections)
3. Harvard (923 connections)
4. FBI (791 connections)
5. Trump (575 connections)

### Most Connected Locations
1. America (1,780 connections)
2. Europe (1,698 connections)
3. China (1,576 connections)
4. New York (1,541 connections)
5. London (1,523 connections)

## Jeffrey Epstein Network

**Entity:** Jeffrey Epstein
- **Mentions:** 1,538
- **Documents:** 625
- **Connections:** 230 direct, 1,025 total

### Top Connections
1. HOUSE (481 shared documents)
2. Epstein variant (176 shared documents)
3. New York (138 shared documents)
4. Trump organization (118 shared documents)
5. US (114 shared documents)
6. Jeffrey variant (112 shared documents)
7. Bill Clinton (105 shared documents)
8. Today (97 shared documents)
9. Obama (93 shared documents)
10. Donald Trump (92 shared documents)

## Rebuilding the Database

To rebuild the database from scratch:

```bash
python scripts/build_wiki_data.py
```

This will:
1. Load all entity batch files
2. Apply significance filtering
3. Calculate co-occurrence relationships
4. Generate database and JSON outputs
5. Create summary report

Processing takes approximately 2 minutes.

### Configuration

Edit thresholds in `scripts/build_wiki_data.py`:

```python
THRESHOLDS = {
    'people': {'doc_count': 5, 'mention_count': 15},
    'organizations': {'doc_count': 5, 'mention_count': 12},
    'locations': {'doc_count': 8, 'mention_count': 20},
    'events': {'doc_count': 5, 'mention_count': 15}
}

MIN_COOCCURRENCE_STRENGTH = 3  # Minimum shared documents
MAX_RELATIONSHIPS = 500000  # Maximum relationships to keep
```

## Web Application Integration

### Backend (Python/Flask)
```python
from flask import Flask, jsonify
from scripts.query_wiki_data import WikiDataQuery

app = Flask(__name__)
query = WikiDataQuery()

@app.route('/api/entity/<entity_id>')
def get_entity(entity_id):
    entity = query.get_entity(entity_id)
    connections = query.get_connections(entity_id)
    return jsonify({
        'entity': entity,
        'connections': connections
    })

@app.route('/api/search/<name>')
def search(name):
    results = query.search_entities(name)
    return jsonify(results)
```

### Frontend (React)
```javascript
// Load entity index on app start
const [entities, setEntities] = useState({});

useEffect(() => {
    fetch('/output/entity_index.json')
        .then(r => r.json())
        .then(data => setEntities(data));
}, []);

// Display entity
function EntityView({ entityId }) {
    const entity = entities[entityId];
    return (
        <div>
            <h2>{entity.name}</h2>
            <p>Type: {entity.type}</p>
            <p>Mentions: {entity.mentions}</p>
            <p>Documents: {entity.documents}</p>
            <h3>Connections:</h3>
            <ul>
                {entity.top_cooccurrences.map(conn => (
                    <li key={conn.entity}>
                        {conn.entity} ({conn.strength} docs)
                    </li>
                ))}
            </ul>
        </div>
    );
}
```

## Analysis Recommendations

### Network Analysis
- Use NetworkX, igraph, or Gephi for advanced analysis
- Calculate centrality metrics (degree, betweenness, PageRank)
- Detect communities/clusters
- Analyze network evolution over time

### Visualization
- Interactive graph with vis.js or D3.js
- Force-directed layout for relationship visualization
- Filter by entity type, mention count, or strength
- Zoom and pan capabilities
- Node tooltips with entity details

### Data Mining
- Topic modeling on document clusters
- Sentiment analysis of entity mentions
- Named entity disambiguation
- Relationship type classification
- Temporal pattern analysis

## Limitations

### Data Quality
- Entity extraction is automated (may have errors)
- Some entities may be over-split (variants not merged)
- Context may be needed to disambiguate names
- Event entities include many dates and time references

### Coverage
- Only includes significant entities (95.7% filtered out)
- Relationships limited to top 500K strongest connections
- Graph visualization shows only top 500 entities
- Some rare but important entities may be excluded

### Entity Types
- Some misclassifications may occur
- Boundary cases between types (e.g., "Trump" as person vs organization)
- Generic terms may be included (e.g., "today", "daily")

## Support

For detailed documentation:
- **Technical Report:** `output/WIKI_DATA_REPORT.md`
- **Agent Summary:** `AGENT_6B_SUMMARY.md`
- **Example Code:** `scripts/example_usage.py`

For issues or questions, review the build script: `scripts/build_wiki_data.py`

## License

This is analysis data derived from the Epstein document collection. Refer to the original data source for licensing information.

---

**Last Updated:** 2025-11-14
**System Version:** 1.0
**Agent:** 6B - Optimized Relationship Builder
