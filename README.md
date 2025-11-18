# Epstein Estate Documents Wiki

Searchable wiki and relationship map of **Epstein Estate Documents - Seventh Production** (House Oversight Committee).

**Live Site:** [https://atomicpond.github.io/definitely-not-redacted/](https://atomicpond.github.io/definitely-not-redacted/)

## Overview

- **2,897 documents** (43,351 pages) fully indexed
- **2,099 people** entities with relationship mapping
- **1,882 organizations** mentioned across documents
- **565 locations** referenced
- **1,965 events/dates** tracked
- **77 chat conversations** formatted in thread-like view for readability

## Entity Consolidation & FOIA Awareness

Many documents contain **intentional misspellings and variant names** to evade FOIA (Freedom of Information Act) requests. This wiki consolidates entity aliases into canonical pages:

### Examples of Consolidated Entities

| Canonical Entity | Aliases Merged |
|-----------------|----------------|
| **Jeffrey Epstein** | Epstein, jeff epstein, Jeffrey E. Epstein, Mr. Epstein, Epstein Jeffrey, and 8 more variants |
| **Donald Trump** | Trump, Donald, Donnie, Mr. Trump, President Trump, Defendant Trump, and 20 more variants |
| **Bill Clinton** | Clinton, CLINTON, President Clinton, William Clinton, Clintons, and 3 more |
| **Barack Obama** | Obama, Barak, President Obama, Mr. Obama, Senator Barack Obama, and 5 more |
| **Steve Bannon** | Mr. Bannon, Stephen K. Bannon |
| **Alan Dershowitz** | Mr. Dershowitz, Alan M. Dershowitz |
| **Ghislaine Maxwell** | Maxwell, Ms Maxwell, Ms. Maxwell, Miss Maxwell, S Maxwell, and 2 more |
| **Bibi (Netanyahu)** | Benjamin Netanyahu, Netanyahu, Bibi Netanyahu, Binyamin Netanyahu |
| **Kathy Ruemmler** | Kathy, Kathryn Ruemmler, Ms. Ruemmler |
| **James Comey** | Director James Comey, Mr. Comey |
| **Robert Mueller** | mueller, Robert Mueller's |

**Total: 102 entity merges** performed to consolidate fragmented mentions.

### Why This Matters

FOIA evasion tactics include:
- Using nicknames instead of full names ("Donnie" vs "Donald Trump")
- Inconsistent capitalization ("CLINTON" vs "Clinton")
- Formal titles ("Mr. Obama" vs "Barack Obama")
- Partial names ("Bibi" vs "Benjamin Netanyahu")
- Misspellings and typos

This wiki **attempts to unify variants** so searches and relationship mapping capture the complete picture, not just fragments.

## Features

### 📄 Searchable Documents
- Full OCR text from all 2,897 documents
- Metadata including Bates IDs, custodians, dates
- **Thread-like conversation views** for 77 chat exports (formatted for readability)

### 👥 Entity Pages
- Deduplicated entity pages with **all name variants** listed
- Document mentions with frequency counts
- Related entities and co-occurrence relationships

### 🔗 Relationship Mapping
- Co-occurrence analysis showing entity connections
- Document-based relationship strength
- Cross-referenced entity networks

## Technical Details

**Built with:**
- Entity extraction: spaCy NER + pattern matching
- Entity merging: Hybrid approach (manual alias map + fuzzy matching)
- Deduplication: Levenshtein distance + semantic matching
- Site generation: MkDocs Material theme
- Database: SQLite (entities + relationships)
- Hosting: GitHub Pages

**Scripts:**
- `scripts/hybrid_entity_merger.py` - Entity consolidation
- `scripts/entity_alias_map.json` - Manual FOIA evasion mappings
- `scripts/integrate_readable_conversations.py` - Chat formatting
- `scripts/fix_broken_entity_links.py` - Link resolution after merging

## Usage

### Local Development
```bash
# Install dependencies
pip install mkdocs-material

# Serve locally
mkdocs serve

# Visit http://127.0.0.1:8000
```

### Search
Use the search bar to find entities, documents, or keywords. All entity variants are searchable and link to the canonical entity page.

### Browse
- Navigate by entity type (People, Organizations, Locations, Events)
- View document pages for full text and metadata
- Explore entity connections through relationship links

## Data Source

**Epstein Estate Documents - Seventh Production**
Released to: House Oversight Committee
Bates Range: HOUSE_OVERSIGHT_010477 - HOUSE_OVERSIGHT_033599
Format: Concordance load file (legal discovery standard)

## License

**Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)**

You are free to share and adapt this material for non-commercial purposes with attribution.
Media outlets and commercial entities require explicit permission.

See [LICENSE](LICENSE) for details.

## Contact

**Repository:** https://github.com/atomicpond/definitely-not-redacted
**Issues:** https://github.com/atomicpond/definitely-not-redacted/issues

---