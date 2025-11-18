#!/usr/bin/env python3
"""
Integrate READABLE conversation files into existing MkDocs document pages.
Replaces the raw OCR text with the formatted, readable conversation version.
"""

import os
import re
from pathlib import Path
from typing import Optional

def find_readable_file(bates_id: str, text_dir: Path) -> Optional[Path]:
    """
    Find the READABLE.txt file for a given Bates ID.

    Args:
        bates_id: Bates ID like "HOUSE_OVERSIGHT_025363"
        text_dir: Path to TEXT/001 directory

    Returns:
        Path to READABLE file if it exists, None otherwise
    """
    readable_path = text_dir / f"{bates_id}_READABLE.txt"

    if readable_path.exists():
        return readable_path

    return None

def read_readable_content(readable_path: Path) -> str:
    """
    Read the content from a READABLE.txt file.

    Args:
        readable_path: Path to the READABLE file

    Returns:
        Content of the file
    """
    with open(readable_path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()

def update_document_page(doc_path: Path, readable_content: str) -> bool:
    """
    Update a document markdown page with the readable conversation content.
    Replaces the "Document Text" section with the formatted conversation.

    Args:
        doc_path: Path to the document markdown file
        readable_content: The formatted conversation content

    Returns:
        True if updated, False if error
    """
    try:
        # Read the existing document
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find the Document Text section
        # Pattern: ## Document Text\n\n```\n...\n```
        pattern = r'(## Document Text\n\n)```\n.*?\n```'

        # Create the new section with readable conversation
        new_section = f'## Document Text\n\n**Thread-like Conversation View:**\n\n```\n{readable_content}\n```'

        # Replace the old section with the new one
        updated_content = re.sub(
            pattern,
            new_section,
            content,
            flags=re.DOTALL
        )

        # Check if replacement happened
        if updated_content == content:
            print(f"  ⚠ Warning: Could not find Document Text section in {doc_path.name}")
            return False

        # Write the updated content
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        return True

    except Exception as e:
        print(f"  ✗ Error updating {doc_path.name}: {e}")
        return False

def main():
    """Main integration function."""

    # Define paths
    text_dir = Path("/Users/am/Research/Epstein/Epstein Estate Documents - Seventh Production/TEXT/001")
    docs_dir = Path("/Users/am/Research/Epstein/epstein-wiki/docs/documents")

    # Find all READABLE files
    readable_files = list(text_dir.glob("*_READABLE.txt"))

    stats = {
        'total_readable': len(readable_files),
        'updated': 0,
        'not_found': 0,
        'failed': 0,
        'updated_files': []
    }

    print("=" * 80)
    print("INTEGRATING READABLE CONVERSATIONS INTO MKDOCS")
    print("=" * 80)
    print(f"Found {len(readable_files)} READABLE conversation files")
    print()

    for readable_path in sorted(readable_files):
        # Extract Bates ID from filename (remove _READABLE.txt)
        bates_id = readable_path.stem.replace('_READABLE', '')

        # Find corresponding markdown document
        doc_path = docs_dir / f"{bates_id}.md"

        if not doc_path.exists():
            print(f"✗ {bates_id}: Document page not found")
            stats['not_found'] += 1
            continue

        # Read the readable content
        readable_content = read_readable_content(readable_path)

        # Update the document page
        print(f"Processing {bates_id}...", end=" ")

        if update_document_page(doc_path, readable_content):
            print("✓ Updated")
            stats['updated'] += 1
            stats['updated_files'].append(bates_id)
        else:
            print("✗ Failed")
            stats['failed'] += 1

    # Print summary
    print()
    print("=" * 80)
    print("INTEGRATION SUMMARY")
    print("=" * 80)
    print(f"Total READABLE files found: {stats['total_readable']}")
    print(f"Successfully updated: {stats['updated']}")
    print(f"Document pages not found: {stats['not_found']}")
    print(f"Failed to update: {stats['failed']}")
    print()

    if stats['updated'] > 0:
        print(f"Updated {stats['updated']} document pages with readable conversation format")
        print()
        print("Sample updated documents:")
        for bates_id in stats['updated_files'][:5]:
            print(f"  - docs/documents/{bates_id}.md")

    print("=" * 80)

if __name__ == "__main__":
    main()
