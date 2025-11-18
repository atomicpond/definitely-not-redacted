================================================================================
DOCUMENT DATES EXTRACTION - README
================================================================================

Generated: 2025-11-17
Script: scripts/extract_dates_timeline.py

================================================================================
OVERVIEW
================================================================================

This extraction processed 2,897 documents and successfully extracted dates from
94.7% of them using a three-tier priority system:

1. Email Headers (High Confidence) - 71.2%
2. Metadata Fields (Medium Confidence) - 8.2%  
3. Content Parsing (Low Confidence) - 15.2%
4. Unknown - 5.3%

================================================================================
OUTPUT FILES
================================================================================

document_dates.json (497 KB)
  - Main output file with dates for all 2,897 documents
  - Structure:
    {
      "HOUSE_OVERSIGHT_XXXXX": {
        "date": "YYYY-MM-DD",
        "time": "HH:MM:SS" or null,
        "source": "email_header|metadata|content_parsed|unknown",
        "raw_date": "original date string from source",
        "confidence": "high|medium|low|none"
      }
    }

document_dates_stats.json (460 B)
  - Summary statistics
  - Total counts by extraction method
  - Date range coverage
  - Generation timestamp

================================================================================
EXTRACTION METHODS
================================================================================

EMAIL HEADERS (High Confidence - 71.2%)
  - Searches first 2000 characters of document OCR text
  - Patterns matched:
    * Sent: M/D/YYYY H:MM:SS AM/PM
    * Date: DayOfWeek, Month D YYYY H:MM AM/PM
    * Date: DayOfWeek, D Month YYYY HH:MM:SS -TZ
    * Received: ... ; DayOfWeek, D Month YYYY HH:MM:SS -TZ
  - Includes precise timestamps (down to the second)
  - Most reliable method

METADATA FIELDS (Medium Confidence - 8.2%)
  - Extracted from documents.db database
  - Priority order:
    1. date_sent
    2. date_received
    3. date_created
    4. date_modified
  - Usually date-only (no time)
  - Reliable but less precise

CONTENT PARSING (Low Confidence - 15.2%)
  - Searches first 5000 characters of document text
  - Patterns matched:
    * DayOfWeek, Month DD, YYYY
    * YYYY-MM-DD (ISO format)
    * MM/DD/YYYY (US format)
  - May include false positives from document content
  - Used as last resort

UNKNOWN (5.3%)
  - No date could be extracted
  - Document may be non-email (images, forms, etc.)
  - OCR text may be missing or corrupted

================================================================================
DATE DISTRIBUTION
================================================================================

Peak Years:
  2017: 567 documents
  2018: 555 documents  
  2016: 534 documents
  2019: 270 documents
  2015: 201 documents

Date Range: 2004 - 2019 (15 years)
  - Earliest: 2004
  - Latest: 2019
  - Note: A few outlier dates (1981, 2038) exist from content parsing errors

================================================================================
USAGE EXAMPLES
================================================================================

Python:
  import json
  
  # Load dates
  with open('output/document_dates.json', 'r') as f:
      dates = json.load(f)
  
  # Get date for a document
  doc_id = 'HOUSE_OVERSIGHT_012722'
  date_info = dates[doc_id]
  print(f"Date: {date_info['date']}")
  print(f"Time: {date_info['time']}")
  print(f"Source: {date_info['source']}")
  print(f"Confidence: {date_info['confidence']}")
  
  # Filter by confidence
  high_conf = {k: v for k, v in dates.items() 
               if v['confidence'] == 'high'}
  
  # Filter by year
  year_2019 = {k: v for k, v in dates.items() 
               if v['date'] and v['date'].startswith('2019')}

SQL (future integration):
  -- Could be imported into documents.db for queries like:
  SELECT * FROM documents 
  WHERE extracted_date BETWEEN '2016-01-01' AND '2016-12-31'
  ORDER BY extracted_date

================================================================================
QUALITY NOTES
================================================================================

STRENGTHS:
  - 94.7% coverage is excellent
  - 71.2% have high-confidence email headers with timestamps
  - Multiple fallback strategies ensure maximum coverage
  - JSON format is easy to integrate with other tools

LIMITATIONS:
  - Content parsing (15.2%) may have false positives
  - Some outlier dates outside reasonable range (1981, 2038)
  - 153 documents (5.3%) have no date
  - Time data only available for email headers (71.2%)

RECOMMENDATIONS:
  - Use high-confidence (email headers) for timeline visualizations
  - Filter dates to reasonable range (2004-2019) for analysis
  - Cross-reference with metadata dates when available
  - Manually verify critical dates if needed

================================================================================
REGENERATION
================================================================================

To regenerate the dates file:
  cd /Users/am/Research/Epstein/epstein-wiki
  python3 scripts/extract_dates_timeline.py

Requirements:
  - Python 3.11+
  - python-dateutil library (pip install python-dateutil)
  - Access to documents.db and OCR text files

Processing Time:
  - ~60 seconds for 2,897 documents
  - Progress updates every 100 documents

================================================================================
