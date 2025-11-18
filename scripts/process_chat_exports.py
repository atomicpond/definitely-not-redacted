#!/usr/bin/env python3
"""
Process iMessage/chat export files and create readable versions.
Converts technical metadata format into clean, readable conversations.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple

def parse_timestamp(timestamp_str: str) -> Tuple[str, str]:
    """
    Parse timestamp from format like '08/24/18 03:30:17 AM (556799417)'
    Returns (date_str, time_str) tuple
    """
    # Extract the readable part before the parenthesis
    match = re.match(r'(\d{2}/\d{2}/\d{2})\s+(\d{1,2}:\d{2}:\d{2}\s+[AP]M)', timestamp_str)
    if match:
        date_str = match.group(1)
        time_str = match.group(2)

        # Convert to more readable format
        try:
            dt = datetime.strptime(f"{date_str} {time_str}", "%m/%d/%y %I:%M:%S %p")
            date_formatted = dt.strftime("%A, %B %d, %Y")
            time_formatted = dt.strftime("%I:%M %p").lstrip("0")
            return date_formatted, time_formatted
        except:
            return date_str, time_str

    return timestamp_str, ""

def identify_participants(lines: List[str]) -> Dict[str, str]:
    """
    Identify participants from the header and map email addresses to names.
    Returns dict mapping sender IDs to display names.
    """
    participants = {}

    # Look for participants line
    for line in lines[:20]:
        if line.startswith("Participants:"):
            parts = line.split("Participants:")[1].strip().split(",")
            # Clean up participant names
            for i, part in enumerate(parts):
                part = part.strip()
                if part and part != "jee":
                    # Use the participant name as is
                    if i == 0:
                        participants["e:jeeitunes@gmail.com"] = "Jeffrey E."
                    else:
                        # Other participant
                        participants["other"] = part if part else "Contact"

    # Default mappings
    if "e:jeeitunes@gmail.com" not in participants:
        participants["e:jeeitunes@gmail.com"] = "Jeffrey E."

    if "other" not in participants:
        participants["other"] = "Contact"

    return participants

def extract_messages(file_path: Path) -> List[Dict]:
    """
    Extract messages from a chat export file.
    Returns list of message dictionaries.
    """
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    # Identify participants
    participants = identify_participants(lines)

    # Find the actual contact name from the header
    for line in lines[:20]:
        if line.startswith("Participants:"):
            parts = line.split("Participants:")[1].strip().split(",")
            # Get the non-jee participant
            for part in parts:
                part = part.strip()
                if part and part != "jee":
                    participants["other"] = part
                    break

    messages = []
    current_msg = None
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Check for sender line
        if line.startswith("Sender:"):
            if current_msg:
                messages.append(current_msg)

            sender = line.split("Sender:")[1].strip()
            current_msg = {
                'sender': sender,
                'time': '',
                'message': '',
                'date': ''
            }

        # Check for time line
        elif line.startswith("Time:") and current_msg:
            time_str = line.split("Time:")[1].strip()
            date_formatted, time_formatted = parse_timestamp(time_str)
            current_msg['date'] = date_formatted
            current_msg['time'] = time_formatted

        # Check for message line
        elif line.startswith("Message:") and current_msg:
            msg_text = line.split("Message:")[1].strip()

            # Check if message continues on next lines
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                # Stop if we hit next metadata field
                if (next_line.startswith("Sender:") or
                    next_line.startswith("Time:") or
                    next_line.startswith("Flags:") or
                    next_line.startswith("Is Read:") or
                    next_line.startswith("Is Invitation:") or
                    next_line.startswith("GUID:") or
                    next_line.startswith("HOUSE OVERSIGHT") or
                    next_line == ""):
                    break
                msg_text += " " + next_line
                j += 1

            current_msg['message'] = msg_text
            i = j - 1

        i += 1

    # Add last message
    if current_msg:
        messages.append(current_msg)

    # Map senders to display names
    for msg in messages:
        sender = msg['sender']
        if sender == "e:jeeitunes@gmail.com":
            msg['sender_name'] = participants.get("e:jeeitunes@gmail.com", "Jeffrey E.")
        elif sender == "":
            msg['sender_name'] = participants.get("other", "Contact")
        else:
            # Try to extract email or use as-is
            msg['sender_name'] = participants.get("other", "Contact")

    return messages

def format_readable_conversation(messages: List[Dict], original_filename: str) -> str:
    """
    Format messages into a readable conversation.
    """
    output = []
    output.append("=" * 80)
    output.append(f"CHAT CONVERSATION - {original_filename}")
    output.append("=" * 80)
    output.append("")

    if not messages:
        output.append("No messages found in this conversation.")
        return "\n".join(output)

    current_date = None

    for msg in messages:
        # Skip messages without content
        if not msg.get('message') or msg['message'] in ['<Unsupported Message Content>', '']:
            continue

        # Add date header if date changed
        if msg['date'] != current_date:
            current_date = msg['date']
            output.append("")
            output.append("-" * 80)
            output.append(f"  {current_date}")
            output.append("-" * 80)
            output.append("")

        # Add message
        sender_name = msg.get('sender_name', 'Unknown')
        time_str = msg.get('time', '')
        message_text = msg.get('message', '')

        output.append(f"[{time_str}] {sender_name}:")
        output.append(f"  {message_text}")
        output.append("")

    output.append("=" * 80)
    output.append("END OF CONVERSATION")
    output.append("=" * 80)

    return "\n".join(output)

def process_chat_file(file_path: Path) -> bool:
    """
    Process a single chat export file and create readable version.
    Returns True if successful, False otherwise.
    """
    try:
        # Extract messages
        messages = extract_messages(file_path)

        # Format readable version
        readable_content = format_readable_conversation(messages, file_path.name)

        # Create output filename
        output_path = file_path.parent / f"{file_path.stem}_READABLE.txt"

        # Write readable version
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(readable_content)

        return True

    except Exception as e:
        print(f"Error processing {file_path.name}: {e}")
        return False

def main():
    """Main processing function."""
    # Process the 4 identified chat files
    base_dir = Path("/Users/am/Research/Epstein/Epstein Estate Documents - Seventh Production/TEXT/001")

    chat_files = [
        "HOUSE_OVERSIGHT_031042.txt",
        "HOUSE_OVERSIGHT_031045.txt",
        "HOUSE_OVERSIGHT_031054.txt",
        "HOUSE_OVERSIGHT_031173.txt"
    ]

    stats = {
        'total_files': len(chat_files),
        'successful': 0,
        'failed': 0,
        'files_processed': []
    }

    print(f"Processing {len(chat_files)} chat export files...")
    print()

    for filename in chat_files:
        file_path = base_dir / filename

        if not file_path.exists():
            print(f"File not found: {filename}")
            stats['failed'] += 1
            continue

        print(f"Processing: {filename}")

        if process_chat_file(file_path):
            print(f"  ✓ Created: {filename[:-4]}_READABLE.txt")
            stats['successful'] += 1
            stats['files_processed'].append(filename)
        else:
            print(f"  ✗ Failed to process")
            stats['failed'] += 1

        print()

    # Print summary
    print("=" * 80)
    print("PROCESSING SUMMARY")
    print("=" * 80)
    print(f"Total files in batch (1601-2001): 401")
    print(f"Chat export files identified: {stats['total_files']}")
    print(f"Successfully processed: {stats['successful']}")
    print(f"Failed: {stats['failed']}")
    print()
    print("Files processed:")
    for filename in stats['files_processed']:
        print(f"  - {filename}")
    print("=" * 80)

if __name__ == "__main__":
    main()
