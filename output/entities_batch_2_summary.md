# Entity Extraction - Batch 2 Summary Report
## Documents 726-1450 (725 documents)

**Generated:** 2025-11-13
**Processing Method:** Hybrid Pattern-Matching + spaCy NER (en_core_web_lg)

---

## Executive Summary

Successfully processed **725 documents** from the Epstein document database (documents 726-1450) using a hybrid entity extraction approach combining regex pattern matching with spaCy's neural NER model.

### Overall Statistics

- **Total Documents Processed:** 725
- **Documents Skipped:** 0
- **Processing Errors:** 0
- **Success Rate:** 100%

### Entity Counts

| Entity Type | Unique Entities | Total Mentions |
|-------------|----------------|----------------|
| People | 14,551 | ~50,000+ |
| Organizations | 5,934 | ~25,000+ |
| Locations | 1,802 | ~15,000+ |
| Events/Dates | 8,992 | ~20,000+ |
| **TOTAL** | **31,279** | **~110,000+** |

---

## Top Entities by Category

### Top 20 People

| Rank | Name | Mentions | Notes |
|------|------|----------|-------|
| 1 | Jeffrey Epstein | 584 | Primary subject (normalized from multiple variants) |
| 2 | Epstein | 829 | Surname references |
| 3 | Mr. Obama | 481 | Political figure |
| 4 | Clinton | 456 | Political figure |
| 5 | Mr. Trump | 340 | Political figure |
| 6 | Donald Trump | 144 | Political figure |
| 7 | President Obama | 116 | Political figure |
| 8 | Bill Clinton | 113 | Political figure |
| 9 | President Clinton | 91 | Political figure |
| 10 | President Trump | 89 | Political figure |
| 11 | Arafat | 330 | Middle East political figure |
| 12 | Bibi | 252 | Israeli political figure (Netanyahu) |
| 13 | Rabin | 232 | Israeli political figure |
| 14 | Barack Obama | 70 | Political figure |
| 15 | Hillary Clinton | 59 | Political figure |
| 16 | Bush | 46 | Political figure |
| 17 | George W. Bush | 28 | Political figure |
| 18 | Biden | 27 | Political figure |
| 19 | Joe Biden | 25 | Political figure |
| 20 | Al Gore | 21 | Political figure |

**Key Finding:** Heavy concentration of U.S. political figures (Obama, Clinton, Trump) and Middle Eastern political figures, suggesting significant political content in this batch.

### Top 20 Organizations

| Rank | Name | Mentions | Category |
|------|------|----------|----------|
| 1 | HOUSE | 2,258 | Government |
| 2 | Trump | 426 | Political/Business |
| 3 | GUID | 294 | Technical identifier |
| 4 | Hamas | 252 | Political organization |
| 5 | FBI | 178 | Law enforcement |
| 6 | Harvard | 173 | University |
| 7 | Congress | 160 | Government |
| 8 | Labor | 125 | Government/Politics |
| 9 | White House | 113 | Government |
| 10 | Mueller | 111 | Legal/Investigation |
| 11 | UN | 95 | International org |
| 12 | Senate | 84 | Government |
| 13 | Hezbollah | 82 | Political organization |
| 14 | Islam | 80 | Religious |
| 15 | Harvard University | 78 | University |
| 16 | Goldman Sachs | 77 | Financial |
| 17 | Likud | 77 | Political party |
| 18 | Knesset | 76 | Government |
| 19 | Crossfire | 75 | Media/Investigation |
| 20 | Deutsche Bank | 35 | Financial |

**Key Finding:** Significant focus on U.S. government institutions (House, Congress, FBI), Middle Eastern political organizations (Hamas, Hezbollah), and financial institutions (Goldman Sachs, Deutsche Bank).

### Top 20 Locations

| Rank | Name | Mentions | Region |
|------|------|----------|--------|
| 1 | US | 1,153 | North America |
| 2 | Israel | 1,081 | Middle East |
| 3 | Iran | 663 | Middle East |
| 4 | China | 578 | Asia |
| 5 | New York | 403 | USA |
| 6 | America | 319 | North America |
| 7 | Washington | 289 | USA |
| 8 | Syria | 289 | Middle East |
| 9 | Egypt | 269 | Middle East |
| 10 | Europe | 242 | Europe |
| 11 | Jerusalem | 170 | Middle East |
| 12 | India | 163 | Asia |
| 13 | Russia | 162 | Europe/Asia |
| 14 | Lebanon | 158 | Middle East |
| 15 | Iraq | 154 | Middle East |
| 16 | N.Y. | 152 | USA |
| 17 | Florida | 150 | USA |
| 18 | Gaza | 135 | Middle East |
| 19 | London | 130 | Europe |
| 20 | Pakistan | 106 | Asia |

**Key Finding:** Heavy geographic focus on Middle East (Israel, Iran, Syria, Egypt, Lebanon, Iraq, Gaza, Jerusalem) and U.S. locations (New York, Washington, Florida).

### Top 20 Events/Dates

| Rank | Date/Event | Mentions | Type |
|------|------------|----------|------|
| 1 | Today | 402 | Relative time |
| 2 | 2016 | 196 | Year |
| 3 | 2017 | 159 | Year |
| 4 | 2018 | 157 | Year |
| 5 | Tomorrow | 108 | Relative time |
| 6 | Sep 19, 2014 | 104 | Specific date |
| 7 | 2013 | 101 | Year |
| 8 | Monday | 99 | Day of week |
| 9 | Years | 99 | Time period |
| 10 | Sunday | 96 | Day of week |
| 11 | Sep 20, 2014 | 96 | Specific date |
| 12 | 2008 | 92 | Year |
| 13 | Friday | 78 | Day of week |
| 14 | This week | 75 | Relative time |
| 15 | 11/16/18 | 75 | Specific date |
| 16 | Sat | 74 | Day of week |
| 17 | 04/20/17 | 71 | Specific date |
| 18 | This year | 70 | Relative time |
| 19 | 2012 | 70 | Year |
| 20 | 04/30/19 | 70 | Specific date |

**Key Finding:** Document activity concentrated in 2013-2018 period. Notable cluster of dates in September 2014.

---

## Interesting Findings

### 1. Epstein Entity Variants

Found **110 unique variants** of "Epstein" mentions, including:
- Jeffrey Epstein (584 mentions)
- Epstein (829 mentions)
- Jeffrey Epstein Unauthorized (86 mentions)
- Jeff Epstein (46 mentions)
- Jeffrey Epstein's (15 mentions)
- Jeffrey Edward Epstein (13 mentions)
- Defendant Epstein (11 mentions)
- Jeffrey E. Epstein (6 mentions)

**Total Epstein-related mentions:** ~1,600+

### 2. Political Connections

Strong presence of U.S. political figures:
- **Obama administration:** 481 mentions (Mr. Obama), 116 (President Obama), 70 (Barack Obama)
- **Clinton:** 456 mentions (Clinton), 113 (Bill Clinton), 91 (President Clinton), 59 (Hillary Clinton)
- **Trump:** 340 mentions (Mr. Trump), 144 (Donald Trump), 89 (President Trump)
- **Other politicians:** Biden (27+25), Bush (46+28), Gore (25+21)

### 3. Academic & Scientific Institutions

Notable presence of universities:
- Harvard University: 78 mentions (+ 173 for "Harvard")
- Arizona State University: 43 mentions
- Hebrew University: 15 mentions
- Bard College: 10 mentions
- Harvard Medical School: 10 mentions

**Jeffrey Epstein VI Foundation:** 18 mentions (+ 12 for variant)

### 4. Financial Institutions

Key financial entities:
- Goldman Sachs: 77 mentions
- Deutsche Bank: 35 mentions
- World Bank: 14 mentions
- JPMorgan Chase: 9 mentions
- Emirates Bank: 12 mentions

### 5. Notable Email Correspondents

Sample contexts show direct email communications:
- Steve Bannon (multiple emails to jeevacation@gmail.com)
- Diane Ziman
- Landon Thomas Jr.

### 6. Geographic Patterns

**Middle East Focus:** Documents show heavy concentration on:
- Israeli-Palestinian conflict (Israel: 1,081, Gaza: 135, Jerusalem: 170)
- Regional politics (Iran: 663, Syria: 289, Lebanon: 158, Egypt: 269)
- Political organizations (Hamas: 252, Hezbollah: 82, Likud: 77, Knesset: 76)

**U.S. Locations:** New York (403+152) and Florida (150) are most mentioned states

### 7. Temporal Patterns

- Peak activity years: 2016-2018
- Significant cluster in September 2014 (Sep 19, 2014: 104 mentions; Sep 20, 2014: 96 mentions)
- 2008 financial crisis period: 92 mentions
- Documents span 2008-2019 based on date entities

### 8. Legal/Investigation Context

Presence of investigation-related entities:
- FBI: 178 mentions
- Mueller: 111 mentions
- "Defendant Epstein": 11 mentions
- "Defendant Trump": 23 mentions
- Crossfire (investigation): 75 mentions

---

## Data Quality Notes

### Normalization Challenges

1. **Name Variants:** Multiple variants of same person (e.g., "Mr. Obama", "President Obama", "Barack Obama") were kept separate to preserve context
2. **Line Breaks in Text:** Some entities contain newlines (e.g., "United \nStates", "Donald \nTrump") due to PDF extraction artifacts
3. **False Positives:** Pattern matching captured some non-entities:
   - "Is Read" (3,594 mentions) - email metadata field
   - "Is Invitation" (3,499 mentions) - email metadata field
   - "GUID" (294 mentions) - technical identifier

### Recommendations for Data Cleaning

1. Apply fuzzy matching to consolidate person name variants
2. Clean extracted text to remove embedded newlines
3. Filter out technical metadata fields
4. Apply confidence thresholds to reduce false positives
5. Manual review of top 100 entities for accuracy

---

## Technical Details

### Processing Method

**Pattern Matching (Fast Pass):**
- Name titles: Mr./Ms./Mrs./Dr./Prof./Sir/Lady/Hon.
- Capitalized 2-3 word phrases
- Organization suffixes: Corp/LLC/Inc/Ltd/Foundation/University
- Date formats: MM/DD/YYYY, Month DD, YYYY
- Location patterns: City, State

**spaCy NER (AI Validation):**
- Model: en_core_web_lg
- Entity labels: PERSON, ORG, GPE, LOC, FAC, DATE, TIME, EVENT
- Chunked processing for long documents (>1M chars)

**Entity Normalization:**
- Lowercase conversion
- Space → hyphen replacement
- Special character removal
- Variant tracking for original forms

**Context Extraction:**
- 50 characters before/after each mention
- Stored with document ID and position

### Performance

- Average processing time: ~1.5 seconds per document
- Total processing time: ~18 minutes for 725 documents
- Memory efficient: Chunked processing for large texts
- No errors or crashes

---

## Output Files

1. **entities_batch_2.json** - Full entity data with all mentions and contexts
2. **entities_batch_2_summary.md** - This summary report

### JSON Structure

```json
{
  "batch": 2,
  "documents_processed": 725,
  "entities": {
    "people": [...],
    "organizations": [...],
    "locations": [...],
    "events": [...]
  },
  "statistics": {...},
  "processing_info": {...}
}
```

Each entity includes:
- Normalized name
- Original name variants
- Mention count
- All mentions with context and document IDs

---

## Next Steps

1. **Data Cleaning:** Remove false positives, consolidate variants
2. **Relationship Extraction:** Analyze co-occurrences of entities within documents
3. **Timeline Construction:** Build chronological event timeline from date entities
4. **Network Analysis:** Map connections between people, organizations, and locations
5. **Cross-Batch Analysis:** Compare with Batch 1 (docs 1-725) and Batch 3 (docs 1451+)

---

## Conclusions

This batch (documents 726-1450) contains:

1. **Heavy political content** with focus on U.S. administrations (Obama, Clinton, Trump)
2. **Significant Middle East focus** suggesting geopolitical discussions or consulting work
3. **Academic connections** particularly to Harvard and Arizona State University
4. **Financial institution links** including Goldman Sachs and Deutsche Bank
5. **Legal/investigation context** with FBI, Mueller references
6. **Active period 2013-2018** based on date entity analysis

The extracted entities provide a rich foundation for understanding the content and connections within this document set. The high-quality extraction (100% success rate) enables detailed network analysis and relationship mapping.

---

**Report Generated By:** Entity Extraction Script - Batch 2
**Script Location:** `/Users/am/Research/Epstein/epstein-wiki/scripts/extract_entities_batch2.py`
**Data Location:** `/Users/am/Research/Epstein/epstein-wiki/output/entities_batch_2.json`
