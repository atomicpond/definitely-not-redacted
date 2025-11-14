# CLAUDE.md - Project Documentation

## Project: Epstein Estate Documents Wiki

**Repository:** https://github.com/atomicpond/definitely-not-redacted
**Live Site:** https://atomicpond.github.io/definitely-not-redacted/
**Created:** November 13-14, 2025
**Built with:** Claude Code + 10 Specialized Agents

---

## Overview

This project is a comprehensive, searchable wiki with relationship mapping built from the **Epstein Estate Documents - Seventh Production** (House Oversight Committee). The system automatically extracted entities, mapped relationships, and generated a professional static website with interactive visualizations.

### Statistics

- **2,897 documents** (43,351 pages) indexed
- **6,607 significant entities** extracted
- **500,000 relationships** mapped
- **9,907 web pages** generated
- **295 MB** static site
- **~2-3 hours** total processing time

---

## Architecture

### Agent-Based Processing Pipeline

The project used **10 specialized agents** running in parallel to maximize efficiency:

#### **Agent 1: Metadata Parser**
- Parsed Concordance `.dat` and `.opt` files
- Created SQLite database with full document metadata
- Mapped 2,897 documents with Bates numbering

#### **Agents 2-5: Entity Extractors (Parallel)**
- Batch 1-4: Processed 2,897 documents in parallel batches
- Hybrid approach: Pattern matching + spaCy NER (en_core_web_lg)
- Extracted 153,260 raw entities
- Categories: People, Organizations, Locations, Events/Dates

#### **Agent 6B: Relationship Builder**
- Deduplicated 153K → 116K → 6,607 significant entities (95.7% reduction)
- Built 500,000 curated co-occurrence relationships
- Created optimized SQLite database (68 MB)
- Generated graph visualization data (6.7 MB JSON)

#### **Agent 7: Entity Page Generator**
- Created 6,607 entity markdown pages
- 4 category index pages with alphabetical navigation
- Cross-linked to documents and related entities

#### **Agent 8: Document Page Generator**
- Created 2,897 document markdown pages
- Included full OCR text with highlighted entities
- Document metadata and parent/child relationships

#### **Agent 9: Homepage & Graph Generator**
- Homepage with statistics and navigation
- Interactive vis.js network graph
- Search documentation

---

## Technology Stack

### Data Processing
- **Python 3.11** - All data processing and extraction
- **spaCy (en_core_web_lg)** - Named Entity Recognition (NER)
- **SQLite** - Relational database for documents and entities
- **Pandas** - Data manipulation and analysis

### Static Site Generation
- **MkDocs** - Static site generator
- **Material for MkDocs** - Professional theme
- **vis.js** - Interactive network graph visualization
- **GitHub Pages** - Free hosting

### Entity Extraction Strategy
- **Pattern Matching:** Fast regex-based initial extraction
- **AI Validation:** spaCy NER for accuracy
- **Hybrid Approach:** Best of both methods
- **Smart Filtering:** Only significant entities (3+ document mentions)

---

## Project Structure

```
epstein-wiki/
├── docs/                          # MkDocs source
│   ├── index.md                   # Homepage
│   ├── graph.md                   # Interactive network graph
│   ├── search.md                  # Search documentation
│   ├── assets/
│   │   └── graph_viz.json         # Graph data (6.7 MB)
│   ├── entities/
│   │   ├── people/                # 2,195 person entities
│   │   ├── organizations/         # 1,882 organization entities
│   │   ├── locations/             # 565 location entities
│   │   └── events/                # 1,965 event/date entities
│   └── documents/                 # 2,897 document pages
│
├── database/
│   ├── documents.db               # Document metadata (964 KB)
│   └── wiki_data.db               # Entity relationships (68 MB)
│
├── output/
│   ├── entities_batch_1.json      # Entity extraction batch 1 (58 MB)
│   ├── entities_batch_2.json      # Entity extraction batch 2 (37 MB)
│   ├── entities_batch_3.json      # Entity extraction batch 3 (9.6 MB)
│   ├── entities_batch_4.json      # Entity extraction batch 4 (4.2 MB)
│   ├── entity_index.json          # Consolidated index (8.6 MB)
│   ├── graph_viz.json             # Graph visualization data (6.7 MB)
│   └── documents_index.json       # Document statistics
│
├── scripts/
│   ├── parse_metadata.py          # Parse .dat/.opt files
│   ├── extract_entities_batch1.py # Entity extraction (batch 1)
│   ├── extract_entities_batch2.py # Entity extraction (batch 2)
│   ├── extract_entities_batch3.py # Entity extraction (batch 3)
│   ├── extract_entities_batch4.py # Entity extraction (batch 4)
│   ├── build_wiki_data.py         # Build relationship database
│   ├── generate_entity_pages.py   # Generate entity markdown
│   ├── generate_document_pages.py # Generate document markdown
│   ├── generate_homepage.py       # Generate homepage
│   └── query_wiki_data.py         # Query utilities
│
├── site/                          # Generated static website (295 MB)
├── mkdocs.yml                     # Site configuration
├── LICENSE                        # CC BY-NC 4.0
├── PROJECT_COMPLETE.md            # Detailed project summary
└── .gitignore                     # Git ignore rules
```

---

## Key Features

### 🔍 Full-Text Search
- Built-in MkDocs search across all 2,897 documents
- Search entities, dates, keywords
- Instant results with highlighting

### 👥 Entity Pages
Each of 6,607 entity pages includes:
- Name variants and statistics
- Top 10 related documents with mention counts
- Co-occurring entities grouped by type
- Proper cross-linking throughout

### 📄 Document Pages
Each of 2,897 document pages includes:
- Complete metadata (Bates ID, custodian, dates, file info)
- Up to 5,000 characters of OCR text
- **Highlighted entities** (bold in text)
- Related documents (parent/child, similar)
- All mentioned entities grouped by type

### 🕸️ Interactive Network Graph
- vis.js force-directed graph
- Top 500 most-mentioned entities
- 51,154 relationships visualized
- Color-coded by type:
  - 🔵 Blue: People
  - 🟢 Green: Organizations
  - 🔴 Red: Locations
  - 🟡 Yellow: Events/Dates
- Click nodes to navigate to entity pages
- Filter by entity type
- Physics disabled after load (performance optimization)

### 📊 Databases
**documents.db:**
```sql
- 2,897 document records
- Full metadata from Concordance .dat file
- Indexed for fast queries
- 964 KB
```

**wiki_data.db:**
```sql
- 6,607 entities
- 100,667 entity-document relationships
- 500,000 co-occurrence relationships
- Indexed for performance
- 68 MB
```

---

## Data Sources

### Input Files
**Epstein Estate Documents - Seventh Production**
- Source: House Oversight Committee
- Format: Standard e-discovery (Concordance)
- Bates Range: HOUSE_OVERSIGHT_010477 - HOUSE_OVERSIGHT_033599
- Date Range: 2005-2025

**File Types:**
- `.dat` - Concordance metadata database
- `.opt` - Opticon image load file
- `.txt` - OCR extracted text (2,897 files)
- `.jpg` - Document scans (23,124 images, 300 DPI)
- Native files - Original documents (11 files)

---

## Entity Extraction Methodology

### Hybrid Approach

**1. Pattern Matching (Fast Pass)**
```python
- Names: Capitalized 2-3 word phrases, titles (Mr./Ms./Dr.)
- Organizations: Corp/LLC/Inc/Ltd/Foundation/University
- Locations: City, State, Country patterns
- Dates: Various formats with context
```

**2. AI Validation (Accuracy Pass)**
```python
- Model: spaCy en_core_web_lg
- Entity types: PERSON, ORG, GPE, LOC, DATE
- Confidence threshold: 0.7
- Context extraction: 50 chars before/after
```

**3. Smart Filtering**
```python
Significance thresholds:
- People: 3+ documents OR 10+ mentions
- Organizations: 3+ documents OR 8+ mentions
- Locations: 5+ documents OR 15+ mentions
- Events: 3+ documents OR 10+ mentions

Result: 95.7% reduction (153K → 6,607)
```

**4. Deduplication**
```python
- Name normalization (lowercase, hyphens)
- Fuzzy matching (Levenshtein distance)
- Variant tracking
- Example: "Jeffrey Epstein" + "Epstein" + "Jeffrey E. Epstein" → merged
```

---

## Performance Optimizations

### Processing
- **Parallel agent execution** - 4 concurrent entity extractors
- **Batch processing** - 725 documents per agent
- **Smart filtering** - 95.7% entity reduction
- **Database indexing** - Fast queries
- **Chunked text processing** - Memory efficient

### Website
- **Static site generation** - Instant page loads
- **Graph physics disabled** - Stops after stabilization
- **Filtered initial view** - Loads "People Only" by default
- **Lazy loading** - Images and large content
- **Minimal dependencies** - Fast CDN delivery

---

## Usage

### Local Development

```bash
# Clone repository
git clone https://github.com/atomicpond/definitely-not-redacted.git
cd definitely-not-redacted

# Install dependencies
pip install mkdocs-material spacy pandas
python -m spacy download en_core_web_lg

# Run local server
mkdocs serve
# Visit http://127.0.0.1:8000

# Build static site
mkdocs build
# Output in site/ directory
```

### Query Database

```python
import sqlite3

# Connect to databases
docs_db = sqlite3.connect('database/documents.db')
wiki_db = sqlite3.connect('database/wiki_data.db')

# Example: Find all entities related to Jeffrey Epstein
cursor = wiki_db.cursor()
cursor.execute("""
    SELECT e2.name, c.strength
    FROM entity_cooccurrence c
    JOIN entities e2 ON c.entity2 = e2.id
    WHERE c.entity1 = 'people:jeffrey-epstein'
    ORDER BY c.strength DESC
    LIMIT 20
""")

for name, strength in cursor.fetchall():
    print(f"{name}: {strength} shared documents")
```

Or use the provided query tool:
```bash
cd scripts
python query_wiki_data.py search "Jeffrey Epstein"
python query_wiki_data.py connections "people:jeffrey-epstein"
python query_wiki_data.py stats
```

### Regenerate Content

```bash
# Regenerate entity pages
python scripts/generate_entity_pages.py

# Regenerate document pages
python scripts/generate_document_pages.py

# Regenerate homepage
python scripts/generate_homepage.py

# Rebuild entire site
mkdocs build
```

### Deploy Updates

```bash
# Make changes to docs/
# Commit changes
git add .
git commit -m "Update content"
git push

# Deploy to GitHub Pages
mkdocs gh-deploy
```

---

## Top Entities Discovered

### Most Mentioned People
1. Jeffrey Epstein - 1,538 mentions (625 documents)
2. Epstein - 1,741 mentions (205 documents)
3. Bill Clinton - ~1,000 combined mentions
4. Barack Obama - 740+ combined mentions
5. Donald Trump - 765+ combined mentions

### Most Mentioned Organizations
1. HOUSE - 3,931 mentions
2. Trump - 999 mentions
3. FBI - 424 mentions (156 documents)
4. Congress - Multiple variants
5. Harvard University - 173+ mentions

### Most Mentioned Locations
1. New York - 1,083 mentions
2. United States - 753 mentions
3. Israel - 420 mentions
4. Palm Beach - 355 mentions (221 documents)
5. China - Multiple variants

### Most Connected Entities
1. events:today - 2,294 connections
2. events:2008 - 2,183 connections
3. events:2007 - 2,170 connections

---

## License

**Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)**

### You are free to:
- ✅ **Share** - Copy and redistribute the material
- ✅ **Adapt** - Remix, transform, and build upon the material

### Under these terms:
- **Attribution** - You must give appropriate credit
- **NonCommercial** - You may not use for commercial purposes
- **Media outlets require permission** - News media, publishers, documentaries, etc. must request explicit written permission for commercial use

### Source Documents
The underlying government documents are **public records** (public domain). This license applies to the compilation, organization, extracted data, and software.

**For commercial licensing inquiries:** Contact repository maintainers

Full license: https://creativecommons.org/licenses/by-nc/4.0/legalcode

---

## Known Issues & Limitations

### Entity Extraction
- Some false positives from email metadata (e.g., "Is Read")
- Name variant proliferation (same person, multiple entries)
- OCR artifacts in some documents
- Generic terms captured as entities (e.g., "HOUSE", "University")

### Data Quality
- Not all documents have complete metadata
- OCR accuracy varies (85-95%)
- Some multi-page documents may have formatting issues
- A few broken entity links due to special characters in filenames

### Graph Visualization
- Limited to top 500 entities for performance
- Full 6,607 entity graph would be too slow
- Some edge cases with entity name normalization

### Recommendations for Improvement
1. Manual review of top 100 entities for accuracy
2. Enhanced fuzzy matching for name deduplication
3. Filter out common false positives
4. Add document image viewer integration
5. Implement advanced search with filters
6. Add timeline visualization
7. Export functionality (CSV/JSON)

---

## Future Enhancements

### Potential Features
- **Timeline View** - Chronological document browser
- **Advanced Search** - Faceted search by type, date, custodian
- **Network Analysis** - Centrality, clustering coefficients
- **Document Viewer** - Inline image viewing
- **Export Tools** - CSV/JSON export of data
- **API** - REST API for programmatic access
- **Authentication** - Optional password protection
- **Entity Disambiguation** - Better variant merging
- **Sentiment Analysis** - Context sentiment around entities
- **PDF Generation** - Export documents as PDFs

### Technical Improvements
- Git LFS for large files (wiki_data.db, batch JSONs)
- Automated CI/CD pipeline
- Database migrations system
- Unit tests for extraction scripts
- Performance monitoring
- Incremental processing for updates

---

## Development Notes

### Agent Coordination
All 10 agents were coordinated to:
- Use existing tools (no reinventing the wheel)
- Save context by working independently
- Report comprehensive results
- Create reusable, documented scripts

### Key Decisions
1. **Hybrid NER** - Pattern matching + AI for speed + accuracy
2. **Smart Filtering** - 95.7% reduction to focus on significant entities
3. **Static Site** - Fast, free, no backend required
4. **MkDocs + Material** - Professional, searchable, mobile-friendly
5. **SQLite** - Portable, no server, queryable
6. **GitHub Pages** - Free hosting, automatic deployment

### Challenges Overcome
1. **102M relationships** - Initial approach too large, optimized to 500K
2. **Graph performance** - Physics disabled after load, filtered view
3. **Large files** - GitHub warnings on 68MB database (acceptable)
4. **Entity variants** - Fuzzy matching with Levenshtein distance
5. **Git authentication** - Switched to gh CLI for deployment

---

## Acknowledgments

**Built with:**
- Claude Code (Anthropic)
- 10 specialized autonomous agents
- spaCy NLP library
- MkDocs + Material theme
- vis.js network visualization
- GitHub Pages hosting

**Data Source:**
- Epstein Estate Documents - Seventh Production
- House Oversight Committee
- Public records

**Created:** November 13-14, 2025
**Processing Time:** ~2-3 hours
**Total Effort:** Fully automated with AI agents

---

## Contact & Contributing

**Repository:** https://github.com/atomicpond/definitely-not-redacted
**Issues:** https://github.com/atomicpond/definitely-not-redacted/issues

### Commercial Use
For commercial licensing inquiries (media, publishing, etc.), please contact the repository maintainers through GitHub.

### Contributing
This is a completed project, but suggestions and improvements are welcome via GitHub issues.

---

## Technical Specifications

**System Requirements:**
- Python 3.11+
- 4GB RAM minimum (8GB recommended for processing)
- 2GB disk space for source data
- 500MB for generated site

**Dependencies:**
```txt
mkdocs>=1.5.0
mkdocs-material>=9.0.0
spacy>=3.7.0
pandas>=2.0.0
jinja2>=3.1.0
```

**Browser Compatibility:**
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers supported

---

## Project Timeline

**November 13, 2025**
- 17:00-19:00: Extracted and organized 19 zip files (36 GB)
- 19:00-20:00: Setup infrastructure, installed dependencies
- 20:00-21:00: Agent 1 parsed metadata (2,897 documents)
- 21:00-22:30: Agents 2-5 extracted entities (parallel, 153K entities)

**November 14, 2025**
- 00:00-00:30: Agent 6B built optimized relationships (500K)
- 00:30-01:30: Agents 7-9 generated all markdown pages (parallel)
- 01:30-02:00: Built and tested MkDocs site
- 02:00-02:30: Deployed to GitHub Pages
- 02:30-03:00: Fixed graph performance, cleanup

**Total Time:** ~8-9 hours (mostly autonomous agent processing)

---

*This wiki was automatically generated from legal discovery documents using AI-powered entity extraction and relationship mapping. All processing, analysis, and website generation was performed by autonomous agents coordinated through Claude Code.*
