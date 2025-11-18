#!/usr/bin/env python3
"""
Extract dates from all documents using multiple strategies.
Priority: Email headers > Metadata > Content parsing
"""

import sqlite3
import json
import re
import os
from datetime import datetime
from typing import Dict, Optional, Tuple
from collections import Counter
from pathlib import Path

try:
    from dateutil import parser as date_parser
    DATEUTIL_AVAILABLE = True
except ImportError:
    print("Warning: python-dateutil not installed. Install with: pip install python-dateutil")
    DATEUTIL_AVAILABLE = False


class DateExtractor:
    """Extract dates from documents using multiple strategies."""

    def __init__(self, db_path: str, text_base_path: str):
        self.db_path = db_path
        self.text_base_path = text_base_path
        self.stats = {
            'total': 0,
            'email_header': 0,
            'metadata': 0,
            'content_parsed': 0,
            'unknown': 0,
            'high_confidence': 0,
            'medium_confidence': 0,
            'low_confidence': 0
        }

        # Common date patterns (order matters - most specific first)
        self.email_patterns = [
            # Email header format: "Sent: 8/3/2011 2:11:03 PM"
            (r'Sent:\s*(\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}:\d{2}\s+(?:AM|PM))', 'email_sent'),
            # Email Date header: "Date: Monday, January 6 2014 12:40 PM"
            (r'Date:\s*(\w+,\s+\w+\s+\d{1,2}\s+\d{4}\s+\d{1,2}:\d{2}(?:\s+(?:AM|PM))?)', 'email_date'),
            # Another email format: "Date: Wed, 10 Jul 2019 18:44:28 -0400"
            (r'Date:\s*(\w+,\s+\d{1,2}\s+\w+\s+\d{4}\s+\d{2}:\d{2}:\d{2}\s+[-+]\d{4})', 'email_date_tz'),
            # Received header: "Received: from ... ; Sat, 13 Jul 2019 21:06:06 -0400"
            (r'Received:.*?;\s*(\w+,\s+\d{1,2}\s+\w+\s+\d{4}\s+\d{2}:\d{2}:\d{2}\s+[-+]\d{4})', 'email_received'),
        ]

        self.content_patterns = [
            # Standard date in content: "Wednesday, August 03, 2011"
            (r'(\w+,\s+\w+\s+\d{1,2},\s+\d{4})', 'content_full'),
            # ISO format: "2019-07-13"
            (r'(\d{4}-\d{2}-\d{2})', 'iso_date'),
            # US format: "01/06/2014"
            (r'(\d{1,2}/\d{1,2}/\d{4})', 'us_date'),
        ]

    def connect_db(self):
        """Connect to database."""
        return sqlite3.connect(self.db_path)

    def parse_date_flexible(self, date_str: str) -> Optional[Tuple[str, str]]:
        """
        Parse date string flexibly using dateutil.
        Returns (date, time) tuple or None.
        """
        if not date_str or not DATEUTIL_AVAILABLE:
            return None

        try:
            # Clean the string
            date_str = date_str.strip()

            # Parse with dateutil
            dt = date_parser.parse(date_str, fuzzy=True)

            # Extract date and time
            date_part = dt.strftime('%Y-%m-%d')
            time_part = dt.strftime('%H:%M:%S')

            # Check if time was actually in the string
            has_time = any(c in date_str for c in [':', 'AM', 'PM', 'am', 'pm'])
            if not has_time:
                time_part = None

            return (date_part, time_part)
        except:
            return None

    def extract_from_email_header(self, text: str) -> Optional[Dict]:
        """Extract date from email headers in text."""
        if not text:
            return None

        # Check first 2000 characters for headers
        header_section = text[:2000]

        for pattern, pattern_type in self.email_patterns:
            match = re.search(pattern, header_section, re.IGNORECASE | re.MULTILINE)
            if match:
                date_str = match.group(1)
                parsed = self.parse_date_flexible(date_str)
                if parsed:
                    return {
                        'date': parsed[0],
                        'time': parsed[1],
                        'source': 'email_header',
                        'raw_date': date_str,
                        'confidence': 'high'
                    }

        return None

    def extract_from_metadata(self, doc: Dict) -> Optional[Dict]:
        """Extract date from document metadata."""
        # Priority: date_sent > date_received > date_created > date_modified
        date_fields = [
            ('date_sent', 'metadata_sent'),
            ('date_received', 'metadata_received'),
            ('date_created', 'metadata_created'),
            ('date_modified', 'metadata_modified')
        ]

        for field, source_type in date_fields:
            if doc.get(field):
                date_str = doc[field]
                parsed = self.parse_date_flexible(date_str)
                if parsed:
                    return {
                        'date': parsed[0],
                        'time': parsed[1],
                        'source': 'metadata',
                        'raw_date': date_str,
                        'confidence': 'medium'
                    }

        return None

    def extract_from_content(self, text: str) -> Optional[Dict]:
        """Extract date from document content."""
        if not text:
            return None

        # Search in first 5000 characters
        search_text = text[:5000]

        for pattern, pattern_type in self.content_patterns:
            matches = re.findall(pattern, search_text, re.IGNORECASE)
            if matches:
                # Try to parse the first match
                date_str = matches[0]
                parsed = self.parse_date_flexible(date_str)
                if parsed:
                    return {
                        'date': parsed[0],
                        'time': parsed[1],
                        'source': 'content_parsed',
                        'raw_date': date_str,
                        'confidence': 'low'
                    }

        return None

    def get_text_path(self, doc: Dict) -> Optional[str]:
        """Get full path to document text file."""
        if not doc.get('text_path'):
            return None

        # Convert Windows path to Unix path
        text_path = doc['text_path'].replace('\\', '/')

        # Try different base paths
        # The path in DB is like: \HOUSE_OVERSIGHT_009\TEXT\001\HOUSE_OVERSIGHT_012722.txt
        # But actual structure is: TEXT/001/HOUSE_OVERSIGHT_012722.txt
        possible_paths = []

        # Try extracting just TEXT/... part
        if 'TEXT/' in text_path:
            extracted = text_path.split('TEXT/')[-1]
            possible_paths.append(os.path.join(self.text_base_path, "TEXT", extracted))

        # Try full path
        possible_paths.append(os.path.join(self.text_base_path, text_path.lstrip('/')))

        for path in possible_paths:
            if path and os.path.exists(path):
                return path

        return None

    def read_text_file(self, file_path: str) -> Optional[str]:
        """Read text file content."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            return None

    def extract_date_for_document(self, doc: Dict) -> Dict:
        """Extract date for a single document using all strategies."""
        result = None

        # Strategy 1: Email header (highest priority)
        text_path = self.get_text_path(doc)
        if text_path:
            text = self.read_text_file(text_path)
            if text:
                result = self.extract_from_email_header(text)

                # If no email header, try content parsing
                if not result:
                    result = self.extract_from_content(text)

        # Strategy 2: Metadata (if no email header found)
        if not result:
            result = self.extract_from_metadata(doc)

        # Strategy 3: Unknown
        if not result:
            result = {
                'date': None,
                'time': None,
                'source': 'unknown',
                'raw_date': None,
                'confidence': 'none'
            }

        # Update statistics
        self.stats[result['source']] += 1
        if result['confidence'] != 'none':
            self.stats[f"{result['confidence']}_confidence"] += 1

        return result

    def process_all_documents(self):
        """Process all documents and extract dates."""
        print("=" * 70)
        print("DATE EXTRACTION PIPELINE")
        print("=" * 70)
        print()

        if not DATEUTIL_AVAILABLE:
            print("ERROR: python-dateutil is required. Install with:")
            print("  pip install python-dateutil")
            return None

        conn = self.connect_db()
        cursor = conn.cursor()

        # Get all documents
        print("Loading documents from database...")
        cursor.execute("""
            SELECT bates_id, bates_end, custodian, date_sent, date_received,
                   date_created, date_modified, text_path, email_subject
            FROM documents
        """)

        documents = []
        for row in cursor.fetchall():
            documents.append({
                'bates_id': row[0],
                'bates_end': row[1],
                'custodian': row[2],
                'date_sent': row[3],
                'date_received': row[4],
                'date_created': row[5],
                'date_modified': row[6],
                'text_path': row[7],
                'email_subject': row[8]
            })

        conn.close()

        self.stats['total'] = len(documents)
        print(f"Found {len(documents)} documents")
        print()
        print("Processing documents...")
        print("-" * 70)

        results = {}
        date_list = []  # For timeline analysis

        # Process each document
        for i, doc in enumerate(documents, 1):
            bates_id = doc['bates_id']

            # Extract date
            date_info = self.extract_date_for_document(doc)
            results[bates_id] = date_info

            # Track dates for timeline
            if date_info['date']:
                date_list.append(date_info['date'])

            # Progress indicator
            if i % 100 == 0:
                progress = (i / len(documents)) * 100
                print(f"Progress: {i}/{len(documents)} ({progress:.1f}%) - "
                      f"Found: {self.stats['email_header'] + self.stats['metadata'] + self.stats['content_parsed']}, "
                      f"Unknown: {self.stats['unknown']}")

        print("-" * 70)
        print(f"Completed: {len(documents)} documents processed")
        print()

        # Calculate date range
        date_range = None
        if date_list:
            date_list.sort()
            date_range = {
                'earliest': date_list[0],
                'latest': date_list[-1],
                'span_years': (datetime.strptime(date_list[-1], '%Y-%m-%d').year -
                              datetime.strptime(date_list[0], '%Y-%m-%d').year)
            }

        return results, date_range

    def print_statistics(self, date_range: Optional[Dict]):
        """Print extraction statistics."""
        print()
        print("=" * 70)
        print("EXTRACTION STATISTICS")
        print("=" * 70)
        print()

        print(f"Total Documents: {self.stats['total']:,}")
        print()

        print("Extraction Sources:")
        print(f"  - Email Headers:    {self.stats['email_header']:>6,} ({self.stats['email_header']/self.stats['total']*100:>5.1f}%)")
        print(f"  - Metadata Fields:  {self.stats['metadata']:>6,} ({self.stats['metadata']/self.stats['total']*100:>5.1f}%)")
        print(f"  - Content Parsing:  {self.stats['content_parsed']:>6,} ({self.stats['content_parsed']/self.stats['total']*100:>5.1f}%)")
        print(f"  - Unknown:          {self.stats['unknown']:>6,} ({self.stats['unknown']/self.stats['total']*100:>5.1f}%)")
        print()

        total_found = self.stats['email_header'] + self.stats['metadata'] + self.stats['content_parsed']
        print(f"Total Dates Found:  {total_found:,} ({total_found/self.stats['total']*100:.1f}%)")
        print()

        print("Confidence Levels:")
        print(f"  - High:   {self.stats['high_confidence']:>6,} (email headers)")
        print(f"  - Medium: {self.stats['medium_confidence']:>6,} (metadata)")
        print(f"  - Low:    {self.stats['low_confidence']:>6,} (content parsing)")
        print()

        if date_range:
            print("Date Range Coverage:")
            print(f"  - Earliest: {date_range['earliest']}")
            print(f"  - Latest:   {date_range['latest']}")
            print(f"  - Span:     {date_range['span_years']} years")
        else:
            print("Date Range: No dates found")
        print()
        print("=" * 70)


def main():
    """Main execution function."""
    # Paths
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    db_path = project_dir / "database" / "documents.db"
    output_path = project_dir / "output" / "document_dates.json"
    text_base_path = "/Users/am/Research/Epstein/Epstein Estate Documents - Seventh Production"

    # Verify database exists
    if not db_path.exists():
        print(f"ERROR: Database not found at {db_path}")
        return

    # Create output directory
    output_path.parent.mkdir(exist_ok=True)

    # Initialize extractor
    extractor = DateExtractor(str(db_path), text_base_path)

    # Process documents
    results, date_range = extractor.process_all_documents()

    if results is None:
        return

    # Save results
    print()
    print("Saving results...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Results saved to: {output_path}")

    # Calculate file size
    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"File size: {file_size_mb:.2f} MB")

    # Print statistics
    extractor.print_statistics(date_range)

    # Save statistics
    stats_path = project_dir / "output" / "document_dates_stats.json"
    stats_data = {
        'statistics': extractor.stats,
        'date_range': date_range,
        'output_file': str(output_path),
        'generated_at': datetime.now().isoformat()
    }

    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats_data, f, indent=2)

    print(f"Statistics saved to: {stats_path}")
    print()


if __name__ == "__main__":
    main()
