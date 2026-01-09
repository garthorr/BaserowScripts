# Baserow Deduplication Script

A Python script to deduplicate rows in a Baserow table based on a specified identifying field, while intelligently preserving and merging link fields from duplicate records.

## Features

- **Smart Duplicate Detection**: Identifies duplicate rows based on any field you specify
- **Link Field Preservation**: Automatically merges link-to-table fields from all duplicates into the kept record
- **Safe by Default**: Runs in dry-run mode by default to preview changes before applying them
- **Flexible Keep Strategy**: Choose to keep either the first or last occurrence of duplicates
- **Comprehensive Logging**: Detailed logging of all operations and changes
- **Pagination Support**: Handles large tables with automatic pagination
- **Error Handling**: Robust error handling with detailed error messages

## Requirements

- Python 3.7+
- Baserow account with API access
- API token with read/write permissions for your table

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd BaserowScripts
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your environment:
```bash
cp .env.example .env
```

4. Edit `.env` and add your Baserow credentials:
```env
BASEROW_API_URL=https://api.baserow.io
BASEROW_API_TOKEN=your_api_token_here
TABLE_ID=12345
IDENTIFYING_FIELD=Email
```

### Getting Your Baserow API Token

1. Log in to your Baserow account
2. Click on your profile icon in the top-right corner
3. Select "Settings" or "Account settings"
4. Navigate to the "API tokens" section
5. Click "Create new token"
6. Give it a name and appropriate permissions
7. Copy the token and paste it into your `.env` file

### Finding Your Table ID

1. Open your table in Baserow
2. Look at the URL in your browser: `https://baserow.io/database/<database_id>/table/<table_id>`
3. The number after `/table/` is your table ID

## Usage

### Dry Run (Recommended First Step)

Always start with a dry run to see what changes would be made:

```bash
python deduplicate_table.py --identifying-field Email --dry-run
```

This will:
- Fetch all rows from your table
- Identify duplicate groups
- Show you what would be updated and deleted
- **Not make any actual changes**

### Actually Perform Deduplication

Once you've reviewed the dry run output and are satisfied:

```bash
python deduplicate_table.py --identifying-field Email --no-dry-run
```

You'll be prompted to confirm before any changes are made.

### Command Line Options

```
--identifying-field FIELD   (Required) Field name to use for identifying duplicates
--table-id ID              Table ID (overrides .env file)
--dry-run                  Preview changes without applying them (default: True)
--no-dry-run              Actually perform the deduplication
--keep-strategy {first|last}  Which duplicate to keep (default: first)
--api-url URL             Baserow API URL (overrides .env)
--api-token TOKEN         API token (overrides .env)
--verbose                 Enable detailed debug logging
```

### Examples

**Deduplicate by email, keeping first occurrence:**
```bash
python deduplicate_table.py --identifying-field Email
```

**Deduplicate by username, keeping last occurrence:**
```bash
python deduplicate_table.py --identifying-field Username --keep-strategy last
```

**Use custom table ID:**
```bash
python deduplicate_table.py --table-id 54321 --identifying-field Email
```

**Enable verbose logging:**
```bash
python deduplicate_table.py --identifying-field Email --verbose
```

## How It Works

1. **Fetch Table Metadata**: Retrieves all field definitions to identify link fields
2. **Fetch All Rows**: Downloads all rows from the table (handles pagination automatically)
3. **Group Duplicates**: Groups rows by the identifying field value (case-insensitive for text)
4. **Process Each Group**:
   - Selects one row to keep (based on keep-strategy)
   - Merges all link field values from duplicates into the keeper
   - Updates the keeper row with merged link fields
   - Deletes the duplicate rows
5. **Report Results**: Provides detailed statistics about the operation

## Link Field Handling

The script automatically detects all "link to table" fields in your table and intelligently merges them:

- **Before Deduplication**:
  - Row 1 (Email: john@example.com) → Links to Projects: [A, B]
  - Row 2 (Email: john@example.com) → Links to Projects: [C, D]
  - Row 3 (Email: john@example.com) → Links to Projects: [B, E]

- **After Deduplication**:
  - Row 1 (Email: john@example.com) → Links to Projects: [A, B, C, D, E]
  - Row 2 → Deleted
  - Row 3 → Deleted

All unique links are preserved and consolidated into the kept record.

## Safety Features

1. **Dry Run Default**: Script runs in dry-run mode by default
2. **Confirmation Prompt**: Asks for confirmation before making actual changes
3. **Skip Empty Values**: Rows with empty/null identifying fields are skipped
4. **Error Handling**: If updating a keeper row fails, its duplicates won't be deleted
5. **Detailed Logging**: Every operation is logged for audit trail

## Example Output

```
2026-01-09 12:00:00 - INFO - ============================================================
2026-01-09 12:00:00 - INFO - Starting deduplication (dry_run=True)
2026-01-09 12:00:00 - INFO - Identifying field: Email
2026-01-09 12:00:00 - INFO - Keep strategy: first
2026-01-09 12:00:00 - INFO - ============================================================
2026-01-09 12:00:00 - INFO - Found link field: Projects
2026-01-09 12:00:00 - INFO - Found link field: Teams
2026-01-09 12:00:00 - INFO - Fetched 200 rows (total: 200)
2026-01-09 12:00:00 - INFO - Total rows fetched: 200
2026-01-09 12:00:00 - INFO - Found 15 groups of duplicates
2026-01-09 12:00:00 - INFO - Total duplicate rows to remove: 23
2026-01-09 12:00:00 - INFO -
Processing group: john@example.com (3 duplicates)
2026-01-09 12:00:00 - INFO -   Keeping row 101
2026-01-09 12:00:00 - INFO -   Removing 2 duplicate(s): [102, 103]
2026-01-09 12:00:00 - INFO -   [DRY RUN] Would update 2 link fields
2026-01-09 12:00:00 - INFO -     Projects: 5 links
2026-01-09 12:00:00 - INFO -     Teams: 2 links
2026-01-09 12:00:00 - INFO -   [DRY RUN] Would delete 2 row(s)
...
2026-01-09 12:00:00 - INFO - ============================================================
2026-01-09 12:00:00 - INFO - DEDUPLICATION SUMMARY
2026-01-09 12:00:00 - INFO - ============================================================
2026-01-09 12:00:00 - INFO - Total rows fetched: 200
2026-01-09 12:00:00 - INFO - Duplicate groups found: 15
2026-01-09 12:00:00 - INFO - Would update: 15 rows
2026-01-09 12:00:00 - INFO - Would delete: 23 rows
2026-01-09 12:00:00 - INFO - ============================================================
```

## Troubleshooting

### "BASEROW_API_TOKEN not provided"
Make sure you've created a `.env` file with your API token, or pass it via `--api-token`.

### "Failed to fetch table fields: 401"
Your API token is invalid or expired. Generate a new one in Baserow settings.

### "Failed to fetch table fields: 404"
The table ID is incorrect. Double-check the table ID in your Baserow URL.

### "Row X has empty identifying field, skipping"
Some rows have empty values in the identifying field. These rows are skipped and won't be deduplicated. You may want to clean these up manually.

### Rate Limiting
If you're deduplicating a very large table, you might hit Baserow's rate limits. The script will show error messages. Wait a few minutes and try again.

## Important Notes

- **Backup First**: Always backup your table before running deduplication with `--no-dry-run`
- **Test on Copy**: Consider testing on a copy of your table first
- **Review Dry Run**: Always review the dry-run output carefully before proceeding
- **Link Fields Only**: Only "link to table" fields are merged; other field types in duplicates are discarded
- **Case Insensitive**: Text field matching is case-insensitive (e.g., "john@example.com" = "John@Example.com")
- **ID-Based Ordering**: "First" and "last" are determined by row ID, not creation date

## License

MIT License - Feel free to use and modify as needed.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the example output to understand expected behavior
3. Run with `--verbose` flag for detailed debugging information
4. Create an issue in this repository with the error message and context
