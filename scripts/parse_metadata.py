#!/usr/bin/env python3
"""
Metadata Parser for Legal Document Production Files
Parses Opticon (.opt) and Concordance (.dat) files to create a comprehensive document index.
"""

import sqlite3
import json
import csv
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
import re

# File paths
OPT_FILE = "/Users/am/Research/Epstein/Epstein Estate Documents - Seventh Production/DATA/HOUSE_OVERSIGHT_009.opt"
DAT_FILE = "/Users/am/Research/Epstein/Epstein Estate Documents - Seventh Production/DATA/HOUSE_OVERSIGHT_009.dat"
DB_PATH = "/Users/am/Research/Epstein/epstein-wiki/database/documents.db"
JSON_PATH = "/Users/am/Research/Epstein/epstein-wiki/output/documents_index.json"

# Concordance delimiters
FIELD_DELIMITER = 'þ'  # Thorn character
SUBFIELD_DELIMITER = '\x14'  # Ctrl+T (DC4)
RECORD_DELIMITER = '\r\n'

class MetadataParser:
    def __init__(self):
        self.documents = {}
        self.opt_data = {}
        self.parsing_errors = []
        self.stats = {
            'total_documents': 0,
            'total_pages': 0,
            'custodians': Counter(),
            'file_types': Counter(),
            'date_range': {'earliest': None, 'latest': None}
        }

    def parse_opt_file(self):
        """Parse the Opticon (.opt) file to extract page groupings and document breaks."""
        print(f"Parsing OPT file: {OPT_FILE}")

        with open(OPT_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            current_doc = None
            page_count = 0

            for row in reader:
                if len(row) < 7:
                    self.parsing_errors.append(f"Malformed OPT row: {row}")
                    continue

                bates_num = row[0]
                production_set = row[1]
                image_path = row[2]
                is_doc_break = row[3] == 'Y'
                page_count_str = row[6] if len(row) > 6 else ''

                # If this is a document break, start a new document
                if is_doc_break:
                    if current_doc and current_doc in self.opt_data:
                        self.opt_data[current_doc]['page_count'] = page_count

                    current_doc = bates_num
                    page_count = int(page_count_str) if page_count_str else 1

                    self.opt_data[bates_num] = {
                        'bates_id': bates_num,
                        'production_set': production_set,
                        'page_count': page_count,
                        'first_page': image_path
                    }
                else:
                    # Page continues current document
                    if current_doc:
                        page_count += 1

            # Handle last document
            if current_doc and current_doc in self.opt_data:
                self.opt_data[current_doc]['page_count'] = page_count

        print(f"Parsed {len(self.opt_data)} documents from OPT file")
        return len(self.opt_data)

    def parse_dat_file(self):
        """Parse the Concordance (.dat) file to extract metadata."""
        print(f"Parsing DAT file: {DAT_FILE}")

        # Read as binary and split by byte pattern, then decode
        with open(DAT_FILE, 'rb') as f:
            data = f.read()

        # Split by þ\r\nþ pattern in UTF-8 bytes
        record_delimiter = b'\xc3\xbe\x0d\x0a\xc3\xbe'  # þ\r\nþ in UTF-8
        record_parts = data.split(record_delimiter)

        # Decode each part
        records = [part.decode('utf-8-sig') for part in record_parts]

        if len(records) < 2:
            print(f"ERROR: DAT file has fewer than 2 records (found {len(records)})")
            return 0

        print(f"Found {len(records)} records in DAT file")

        # First record is the header (starts with BOM and þ)
        header_row = records[0]
        headers = self._parse_dat_row(header_row)

        print(f"Found {len(headers)} metadata fields: {', '.join(headers[:10])}...")

        # Create field index mapping
        field_map = {header: idx for idx, header in enumerate(headers)}

        # Parse data records
        doc_count = 0
        for i, record in enumerate(records[1:], 1):
            if not record.strip():
                continue

            try:
                # Data records don't start with þ after splitting, so add it back
                record_with_prefix = FIELD_DELIMITER + record
                fields = self._parse_dat_row(record_with_prefix)

                if len(fields) != len(headers):
                    self.parsing_errors.append(
                        f"Row {i}: Field count mismatch. Expected {len(headers)}, got {len(fields)}"
                    )
                    continue

                # Extract key fields
                doc_data = self._extract_document_data(fields, field_map)

                if doc_data['bates_id']:
                    self.documents[doc_data['bates_id']] = doc_data
                    doc_count += 1

                    # Update statistics
                    self._update_stats(doc_data)

            except Exception as e:
                self.parsing_errors.append(f"Row {i}: Error parsing - {str(e)}")

        print(f"Parsed {doc_count} documents from DAT file")
        return doc_count

    def _parse_dat_row(self, row):
        """Parse a single row from the DAT file using Concordance delimiters."""
        # Split by field delimiter and subfield delimiter
        parts = row.split(FIELD_DELIMITER + SUBFIELD_DELIMITER)

        # Clean up parts
        fields = []
        for part in parts:
            # Remove leading field delimiter if present
            cleaned = part.lstrip(FIELD_DELIMITER).strip()
            fields.append(cleaned)

        return fields

    def _extract_document_data(self, fields, field_map):
        """Extract document data from parsed fields."""
        def get_field(field_name):
            idx = field_map.get(field_name, -1)
            if idx >= 0 and idx < len(fields):
                value = fields[idx].strip()
                return value if value else None
            return None

        bates_id = get_field('Bates Begin')

        # Get page count from OPT data if available
        opt_info = self.opt_data.get(bates_id, {})

        doc_data = {
            'bates_id': bates_id,
            'bates_end': get_field('Bates End'),
            'production_set': opt_info.get('production_set'),
            'page_count': opt_info.get('page_count'),
            'custodian': get_field('Custodian/Source'),
            'date_created': get_field('Date Created'),
            'date_modified': get_field('Date Last Modified'),
            'date_sent': get_field('Date Sent'),
            'date_received': get_field('Date Received'),
            'email_from': get_field('Email From'),
            'email_to': get_field('Email To'),
            'email_cc': get_field('Email CC'),
            'email_bcc': get_field('Email BCC'),
            'email_subject': get_field('Email Subject/Title'),
            'original_filename': get_field('Original Filename'),
            'file_extension': get_field('Document Extension'),
            'file_size': self._parse_int(get_field('File Size')),
            'md5_hash': get_field('MD5 Hash'),
            'text_path': get_field('Text Link'),
            'native_path': get_field('Native Link'),
            'parent_doc_id': get_field('Parent Document ID'),
            'is_attachment': 1 if get_field('Attachment Document') else 0,
            'full_text': None  # Will be populated later if needed
        }

        return doc_data

    def _parse_int(self, value):
        """Safely parse integer value."""
        if value:
            try:
                return int(value)
            except ValueError:
                return None
        return None

    def _update_stats(self, doc_data):
        """Update statistics with document data."""
        # Count custodians
        if doc_data['custodian']:
            self.stats['custodians'][doc_data['custodian']] += 1

        # Count file types
        if doc_data['file_extension']:
            self.stats['file_types'][doc_data['file_extension']] += 1

        # Track date range
        for date_field in ['date_created', 'date_sent', 'date_received']:
            date_str = doc_data.get(date_field)
            if date_str:
                try:
                    # Try to parse date (format may vary)
                    # Common formats: MM/DD/YYYY, YYYY-MM-DD
                    date_obj = self._parse_date(date_str)
                    if date_obj:
                        if not self.stats['date_range']['earliest'] or date_obj < self.stats['date_range']['earliest']:
                            self.stats['date_range']['earliest'] = date_obj
                        if not self.stats['date_range']['latest'] or date_obj > self.stats['date_range']['latest']:
                            self.stats['date_range']['latest'] = date_obj
                except:
                    pass

    def _parse_date(self, date_str):
        """Parse date string into datetime object."""
        if not date_str:
            return None

        # Try common date formats
        formats = [
            '%m/%d/%Y',
            '%Y-%m-%d',
            '%m/%d/%y',
            '%Y/%m/%d',
            '%d/%m/%Y',
            '%m-%d-%Y'
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None

    def merge_data(self):
        """Merge OPT and DAT data."""
        print("Merging OPT and DAT data...")

        # Documents in DAT but not in OPT
        dat_only = set(self.documents.keys()) - set(self.opt_data.keys())
        if dat_only:
            print(f"Warning: {len(dat_only)} documents in DAT but not in OPT")

        # Documents in OPT but not in DAT
        opt_only = set(self.opt_data.keys()) - set(self.documents.keys())
        if opt_only:
            print(f"Warning: {len(opt_only)} documents in OPT but not in DAT")
            # Add these to documents with minimal metadata
            for bates_id in opt_only:
                self.documents[bates_id] = {
                    'bates_id': bates_id,
                    'production_set': self.opt_data[bates_id]['production_set'],
                    'page_count': self.opt_data[bates_id]['page_count'],
                    'bates_end': None,
                    'custodian': None,
                    'date_created': None,
                    'date_modified': None,
                    'date_sent': None,
                    'date_received': None,
                    'email_from': None,
                    'email_to': None,
                    'email_cc': None,
                    'email_bcc': None,
                    'email_subject': None,
                    'original_filename': None,
                    'file_extension': None,
                    'file_size': None,
                    'md5_hash': None,
                    'text_path': None,
                    'native_path': None,
                    'parent_doc_id': None,
                    'is_attachment': 0,
                    'full_text': None
                }

        self.stats['total_documents'] = len(self.documents)
        self.stats['total_pages'] = sum(d.get('page_count', 0) or 0 for d in self.documents.values())

        print(f"Total merged documents: {self.stats['total_documents']}")
        print(f"Total pages: {self.stats['total_pages']}")

    def create_database(self):
        """Create SQLite database with parsed data."""
        print(f"Creating database: {DB_PATH}")

        # Remove existing database
        db_path = Path(DB_PATH)
        if db_path.exists():
            db_path.unlink()

        # Create new database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Create table
        cursor.execute('''
            CREATE TABLE documents (
                bates_id TEXT PRIMARY KEY,
                bates_end TEXT,
                production_set TEXT,
                page_count INTEGER,
                custodian TEXT,
                date_created TEXT,
                date_modified TEXT,
                date_sent TEXT,
                date_received TEXT,
                email_from TEXT,
                email_to TEXT,
                email_cc TEXT,
                email_bcc TEXT,
                email_subject TEXT,
                original_filename TEXT,
                file_extension TEXT,
                file_size INTEGER,
                md5_hash TEXT,
                text_path TEXT,
                native_path TEXT,
                parent_doc_id TEXT,
                is_attachment INTEGER,
                full_text TEXT
            )
        ''')

        # Create indices
        cursor.execute('CREATE INDEX idx_custodian ON documents(custodian)')
        cursor.execute('CREATE INDEX idx_date_created ON documents(date_created)')
        cursor.execute('CREATE INDEX idx_bates ON documents(bates_id)')
        cursor.execute('CREATE INDEX idx_parent_doc ON documents(parent_doc_id)')
        cursor.execute('CREATE INDEX idx_email_from ON documents(email_from)')
        cursor.execute('CREATE INDEX idx_date_sent ON documents(date_sent)')

        # Insert data
        insert_count = 0
        for doc_id, doc_data in self.documents.items():
            try:
                cursor.execute('''
                    INSERT INTO documents VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                ''', (
                    doc_data['bates_id'],
                    doc_data['bates_end'],
                    doc_data['production_set'],
                    doc_data['page_count'],
                    doc_data['custodian'],
                    doc_data['date_created'],
                    doc_data['date_modified'],
                    doc_data['date_sent'],
                    doc_data['date_received'],
                    doc_data['email_from'],
                    doc_data['email_to'],
                    doc_data['email_cc'],
                    doc_data['email_bcc'],
                    doc_data['email_subject'],
                    doc_data['original_filename'],
                    doc_data['file_extension'],
                    doc_data['file_size'],
                    doc_data['md5_hash'],
                    doc_data['text_path'],
                    doc_data['native_path'],
                    doc_data['parent_doc_id'],
                    doc_data['is_attachment'],
                    doc_data['full_text']
                ))
                insert_count += 1
            except Exception as e:
                self.parsing_errors.append(f"Error inserting {doc_id}: {str(e)}")

        conn.commit()
        conn.close()

        print(f"Inserted {insert_count} documents into database")
        return insert_count

    def create_json_summary(self):
        """Create JSON summary file."""
        print(f"Creating JSON summary: {JSON_PATH}")

        # Get sample documents (interesting ones with email metadata)
        sample_docs = []
        email_docs = [d for d in self.documents.values() if d.get('email_subject')]
        attachment_docs = [d for d in self.documents.values() if d.get('is_attachment')]

        # Sample variety
        samples_to_get = []
        samples_to_get.extend(email_docs[:3])  # First 3 emails
        samples_to_get.extend(attachment_docs[:2])  # First 2 attachments

        # Add some general documents
        general_docs = [d for d in list(self.documents.values())[:10]
                       if d not in samples_to_get]
        samples_to_get.extend(general_docs[:2])

        for doc in samples_to_get[:5]:
            sample_docs.append({
                'bates_id': doc['bates_id'],
                'custodian': doc['custodian'],
                'date_created': doc['date_created'],
                'email_subject': doc['email_subject'],
                'email_from': doc['email_from'],
                'email_to': doc['email_to'],
                'original_filename': doc['original_filename'],
                'file_extension': doc['file_extension'],
                'page_count': doc['page_count'],
                'is_attachment': bool(doc['is_attachment'])
            })

        summary = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'source_files': {
                    'opt': OPT_FILE,
                    'dat': DAT_FILE
                }
            },
            'statistics': {
                'total_documents': self.stats['total_documents'],
                'total_pages': self.stats['total_pages'],
                'date_range': {
                    'earliest': self.stats['date_range']['earliest'].strftime('%Y-%m-%d') if self.stats['date_range']['earliest'] else None,
                    'latest': self.stats['date_range']['latest'].strftime('%Y-%m-%d') if self.stats['date_range']['latest'] else None
                },
                'top_custodians': dict(self.stats['custodians'].most_common(10)),
                'file_types': dict(self.stats['file_types'].most_common(20)),
                'parsing_errors': len(self.parsing_errors)
            },
            'sample_documents': sample_docs,
            'parsing_errors': self.parsing_errors[:20] if self.parsing_errors else []
        }

        with open(JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"JSON summary created with {len(sample_docs)} sample documents")

    def run(self):
        """Run the complete parsing pipeline."""
        print("=" * 80)
        print("METADATA PARSER - Legal Document Production Files")
        print("=" * 80)
        print()

        # Parse files
        self.parse_opt_file()
        print()

        self.parse_dat_file()
        print()

        # Merge data
        self.merge_data()
        print()

        # Create outputs
        self.create_database()
        print()

        self.create_json_summary()
        print()

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print execution summary."""
        print("=" * 80)
        print("PARSING COMPLETE - SUMMARY")
        print("=" * 80)
        print()
        print(f"Total Documents Parsed: {self.stats['total_documents']}")
        print(f"Total Pages: {self.stats['total_pages']}")
        print()

        if self.stats['date_range']['earliest'] and self.stats['date_range']['latest']:
            print(f"Date Range: {self.stats['date_range']['earliest'].strftime('%Y-%m-%d')} to {self.stats['date_range']['latest'].strftime('%Y-%m-%d')}")
        print()

        print("Top 10 Custodians:")
        for custodian, count in self.stats['custodians'].most_common(10):
            print(f"  - {custodian}: {count} documents")
        print()

        print("Top 10 File Types:")
        for file_type, count in self.stats['file_types'].most_common(10):
            print(f"  - {file_type}: {count} documents")
        print()

        print(f"Database Location: {DB_PATH}")
        print(f"JSON Summary Location: {JSON_PATH}")
        print()

        if self.parsing_errors:
            print(f"Parsing Errors Encountered: {len(self.parsing_errors)}")
            print("(See JSON summary for details)")
        else:
            print("No parsing errors encountered")
        print()

        # Print sample interesting documents
        print("Sample Interesting Documents:")
        print("-" * 80)

        email_docs = [d for d in self.documents.values() if d.get('email_subject')]
        for i, doc in enumerate(email_docs[:5], 1):
            print(f"\n{i}. {doc['bates_id']}")
            print(f"   Custodian: {doc['custodian']}")
            print(f"   Subject: {doc['email_subject']}")
            print(f"   From: {doc['email_from']}")
            print(f"   To: {doc['email_to']}")
            print(f"   Date Sent: {doc['date_sent']}")
            print(f"   Pages: {doc['page_count']}")

        print()
        print("=" * 80)


if __name__ == '__main__':
    parser = MetadataParser()
    parser.run()
