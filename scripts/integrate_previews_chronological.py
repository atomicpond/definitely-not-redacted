#!/usr/bin/env python3
"""
Integrate content previews into the chronological timeline page.
Replaces placeholder text with actual previews from batch JSON files.
"""

import json
import re
from pathlib import Path

def load_all_previews():
    """Load and merge all content preview batch files."""
    base_path = Path(__file__).parent.parent / "output"
    all_previews = {}

    batch_files = [
        "content_previews_batch1.json",
        "content_previews_batch2.json",
        "content_previews_batch3.json",
        "content_previews_batch4.json"
    ]

    for batch_file in batch_files:
        file_path = base_path / batch_file
        if file_path.exists():
            print(f"Loading {batch_file}...")
            with open(file_path, 'r', encoding='utf-8') as f:
                batch_data = json.load(f)
                # Each file has a "previews" key
                if "previews" in batch_data:
                    all_previews.update(batch_data["previews"])
                else:
                    all_previews.update(batch_data)
        else:
            print(f"Warning: {batch_file} not found")

    print(f"Total previews loaded: {len(all_previews)}")
    return all_previews

def build_doc_to_group_mapping(previews):
    """Build a mapping from canonical document ID to group number."""
    doc_to_group = {}

    for group_id, group_data in previews.items():
        if "canonical" in group_data:
            canonical_doc = group_data["canonical"]
            doc_to_group[canonical_doc] = group_id

    print(f"Built mapping for {len(doc_to_group)} canonical documents")
    return doc_to_group

def integrate_previews(timeline_path, previews, doc_to_group):
    """Integrate previews into the chronological timeline."""

    with open(timeline_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Track statistics
    stats = {
        'documents_found': 0,
        'previews_added': 0,
        'previews_missing': 0,
        'placeholders_found': 0
    }

    # Pattern to find document references
    # Looking for: **Document:** [HOUSE_OVERSIGHT_XXXXXX](../documents/HOUSE_OVERSIGHT_XXXXXX.md)
    doc_pattern = r'\*\*Document:\*\* \[(HOUSE_OVERSIGHT_\d+)\]'

    # Split content into lines for easier processing
    lines = content.split('\n')
    new_lines = []
    current_doc_id = None

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check if this line contains a Document reference
        doc_match = re.search(doc_pattern, line)
        if doc_match:
            current_doc_id = doc_match.group(1)
            stats['documents_found'] += 1

        # Check if this line starts a content preview section
        if line.strip().startswith('??? info "Content Preview"'):
            stats['placeholders_found'] += 1

            # Add the preview section header
            new_lines.append(line)

            # Check if we have a preview for this document
            if current_doc_id and current_doc_id in doc_to_group:
                group_id = doc_to_group[current_doc_id]
                if group_id in previews:
                    preview_data = previews[group_id]
                    preview_text = preview_data.get("preview", "No preview available")

                    # Format the preview with proper indentation (4 spaces for collapsible content)
                    new_lines.append(f"    {preview_text}")

                    stats['previews_added'] += 1

                    # Skip the placeholder line(s) - advance to next line and skip indented placeholders
                    i += 1
                    while i < len(lines) and (lines[i].strip().startswith('*') or lines[i].strip() == ''):
                        i += 1
                    i -= 1  # Back up one because the main loop will increment
                else:
                    print(f"Warning: Group {group_id} not in previews for {current_doc_id}")
                    stats['previews_missing'] += 1
            else:
                if current_doc_id:
                    # This is expected - not all documents have dedupe groups
                    stats['previews_missing'] += 1
                else:
                    print(f"Warning: Preview section found without preceding Document ID at line {i}")

        new_lines.append(line)
        i += 1

    # Write the updated content
    updated_content = '\n'.join(new_lines)

    with open(timeline_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)

    return stats

def main():
    """Main execution function."""
    print("=" * 80)
    print("Content Preview Integration for Chronological Timeline")
    print("=" * 80)
    print()

    # Load all preview data
    previews = load_all_previews()
    print()

    # Build document-to-group mapping
    doc_to_group = build_doc_to_group_mapping(previews)
    print()

    # Path to chronological timeline
    timeline_path = Path(__file__).parent.parent / "docs" / "timeline" / "chronological.md"

    if not timeline_path.exists():
        print(f"Error: Timeline file not found at {timeline_path}")
        return

    print(f"Processing timeline: {timeline_path}")
    print()

    # Integrate previews
    stats = integrate_previews(timeline_path, previews, doc_to_group)

    # Report statistics
    print("=" * 80)
    print("INTEGRATION COMPLETE")
    print("=" * 80)
    print(f"Documents found in timeline: {stats['documents_found']}")
    print(f"Preview placeholders found: {stats['placeholders_found']}")
    print(f"Previews successfully added: {stats['previews_added']}")
    print(f"Previews missing (no dedupe group): {stats['previews_missing']}")
    print()

    if stats['previews_added'] > 0:
        coverage = (stats['previews_added'] / stats['placeholders_found'] * 100) if stats['placeholders_found'] > 0 else 0
        print(f"✓ Successfully integrated {stats['previews_added']} content previews ({coverage:.1f}% coverage)")

    if stats['previews_missing'] > 0:
        print(f"ℹ Note: {stats['previews_missing']} documents don't have dedupe groups (expected for unique documents)")

    print()
    print(f"Updated file: {timeline_path}")

if __name__ == "__main__":
    main()
