# Make Readable Text Conversations

Task an agent to convert raw iMessage/chat export files into readable conversation format.

**Usage:** `/make-readable [directory_path]`

**What it does:**
1. Scans the specified directory for `.txt` files
2. Identifies files that appear to be raw iMessage/chat exports (by checking for metadata like "GUID:", "Sender:", "Time:", etc.)
3. Checks if a `_READABLE.txt` version already exists
4. For files without readable versions, creates formatted conversation threads with:
   - Chronological organization by day
   - Clear speaker identification
   - Readable timestamps
   - Removed technical metadata
   - Conversational format

**Task prompt for agent:**

Please process text conversation files in the directory: {{DIRECTORY_PATH}}

Your task:
1. **Scan the directory** for `.txt` files that appear to be raw iMessage or chat exports
   - Look for files containing metadata like "GUID:", "Sender:", "Time:", "Flags:", "Is Read:"

2. **Check for existing readable versions**
   - Skip files that already have a corresponding `*_READABLE.txt` file

3. **For each raw export file without a readable version:**
   - Read the raw file
   - Extract conversation messages with timestamps and senders
   - Create a reformatted version with:
     - Clear day/date headers
     - Speaker labels (identify from email addresses or participant info)
     - Clean timestamps (e.g., "[2:18 PM]")
     - Message content only (no GUIDs, flags, or technical metadata)
     - Visual separators between days
   - Save as `[original_filename]_READABLE.txt` in the same directory

4. **Report statistics:**
   - Total `.txt` files found
   - Files identified as raw chat exports
   - Files already with readable versions (skipped)
   - New readable versions created
   - Any errors or files that couldn't be processed

**Output format example:**
```
iMessage Conversation
Thread Participants: user1@email.com and user2@email.com
Date Range: [start date] - [end date]
Document: [original filename]

═══════════════════════════════════════════════════════════════

[DAY NAME], [DATE]

[TIME] Sender Name:
Message content here

[TIME] Recipient Name:
Response here

─────────────────────────────────────────────────────────────

[NEXT DAY NAME], [NEXT DATE]

...
```

Make the conversations easy to read while preserving all message content and maintaining chronological order.
