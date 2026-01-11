# Baserow Scripts

Python scripts for managing Baserow tables, including deduplication and contact synchronization.

## Available Scripts

1. **deduplicate_table.py** - Deduplicate rows in a Baserow table while preserving link fields
2. **update_contacts.py** - Sync contacts from Excel to Baserow, marking inactive contacts

---

# Table Deduplication Script

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

---

# Contacts Sync Script

Synchronize contacts from an Excel spreadsheet to a Baserow contacts table. Adds new contacts from the spreadsheet and marks existing contacts not in the spreadsheet as inactive.

## Features

- **Excel Integration**: Reads contacts from .xls or .xlsx files
- **Smart Sync**: Adds new contacts, reactivates existing ones, deactivates missing ones
- **Email-Based Matching**: Uses email as unique identifier (case-insensitive)
- **Safe by Default**: Runs in dry-run mode by default
- **Comprehensive Logging**: Detailed logging of all sync operations
- **Error Handling**: Robust error handling with detailed error messages

## Setup

The update_contacts.py script uses the same installation as the deduplication script. Just ensure your `.env` file has the contacts table ID:

```env
BASEROW_API_URL=https://api.baserow.io
BASEROW_API_TOKEN=your_api_token_here
CONTACTS_TABLE_ID=67890
```

## Usage

### Dry Run (Preview Changes)

Always start with a dry run:

```bash
python update_contacts.py --excel-file enrollment.xlsx --dry-run
```

This will:
- Read contacts from the Excel file
- Compare with existing Baserow contacts
- Show what would be added, activated, or deactivated
- **Not make any actual changes**

### Perform the Sync

After reviewing the dry run output:

```bash
python update_contacts.py --excel-file enrollment.xlsx --no-dry-run
```

You'll be prompted to confirm before any changes are made.

### Command Line Options

```
--excel-file FILE          (Required) Path to Excel file (.xls or .xlsx)
--table-id ID             Contacts table ID (overrides .env)
--first-name-field FIELD  First name field in Baserow (default: "First Name")
--last-name-field FIELD   Last name field in Baserow (default: "Last Name")
--email-field FIELD       Email field in Baserow (default: "Email")
--active-field FIELD      Active checkbox field in Baserow (default: "Active")
--dry-run                 Preview changes (default: True)
--no-dry-run              Actually perform the sync
--api-url URL             Baserow API URL (overrides .env)
--api-token TOKEN         API token (overrides .env)
--verbose                 Enable detailed debug logging
```

### Examples

**Basic sync with default field names:**
```bash
python update_contacts.py --excel-file current_enrollment.xlsx
```

**Sync with custom field names:**
```bash
python update_contacts.py --excel-file enrollment.xlsx \
  --first-name-field "FirstName" \
  --last-name-field "LastName" \
  --email-field "EmailAddress" \
  --active-field "IsActive"
```

**Use specific table ID:**
```bash
python update_contacts.py --excel-file enrollment.xlsx --table-id 12345
```

## Excel File Format

Your Excel file should have these columns (column names are case-insensitive):

| First Name | Last Name | Email |
|------------|-----------|-------|
| John | Doe | john.doe@example.com |
| Jane | Smith | jane.smith@example.com |

Additional columns (like Unit, Position) are okay but will be ignored.

### Required Columns

The script expects these columns in your Excel file:
- **first name** - Contact's first name
- **last name** - Contact's last name
- **email** - Contact's email address (used as unique identifier)

Rows missing any of these fields will be skipped with a warning.

## How It Works

1. **Read Excel**: Loads contacts from spreadsheet, normalizes email addresses
2. **Fetch Baserow Contacts**: Retrieves all existing contacts from your table
3. **Compare & Analyze**:
   - Contacts in Excel but not in Baserow → **Add as new** (Active = true)
   - Contacts in both with Active = false → **Mark active** (Active = true)
   - Contacts in Baserow but not in Excel with Active = true → **Mark inactive** (Active = false)
   - Contacts in both with Active = true → **No change**
4. **Apply Changes**: Creates, updates contacts as needed
5. **Report Results**: Shows detailed statistics

## Baserow Table Requirements

Your Baserow contacts table should have these fields:

| Field Name | Field Type | Notes |
|------------|------------|-------|
| First Name | Text | Required |
| Last Name | Text | Required |
| Email | Email or Text | Required, used for matching |
| Active | Checkbox | Required, tracks enrollment status |

You can customize field names using command-line options.

## Example Output

```
============================================================
Starting contacts sync (dry_run=True)
Excel file: enrollment.xlsx
============================================================
Reading contacts from: enrollment.xlsx
Read 5 valid contacts from Excel
Fetched 200 contacts (total: 200)
Total contacts in Baserow: 3

============================================================
ANALYZING CHANGES
============================================================
Will mark as active: jane.smith@example.com
Will add new contact: bob.johnson@example.com
Will add new contact: alice.williams@example.com
Will add new contact: charlie.brown@example.com

Checking for contacts to mark inactive...
Will mark as inactive: old.user@example.com

============================================================
SYNC SUMMARY
============================================================
Contacts in Excel: 5
Contacts in Baserow: 3
New contacts to add: 3
Contacts to mark active: 1
Contacts to mark inactive: 1
[DRY RUN] No changes were made
============================================================
```

## Common Scenarios

### Scenario 1: New Enrollment Period
You have a fresh enrollment spreadsheet and want to:
- Add all new enrollees
- Mark previous enrollees who didn't re-enroll as inactive

```bash
python update_contacts.py --excel-file new_enrollment.xlsx --no-dry-run
```

### Scenario 2: Updating Existing Contacts
Some contacts exist but are marked inactive. The sync will:
- Reactivate them if they're in the new spreadsheet
- Add any genuinely new contacts

```bash
python update_contacts.py --excel-file updated_list.xlsx --no-dry-run
```

### Scenario 3: Multiple Enrollment Files
Process multiple spreadsheets by running the script multiple times. The Active field will reflect the most recent run.

## Troubleshooting

### "Excel file not found"
Check the file path. Use absolute paths or ensure you're in the correct directory.

### "Missing required columns: {'email'}"
Your Excel file is missing one of the required columns. Column names should be "First Name", "Last Name", and "Email" (case-insensitive).

### "Row X has no email, skipping"
Some rows in your Excel file have empty email fields. These rows are skipped automatically.

### "Failed to create contact"
Check that:
1. Your API token has write permissions
2. All required fields exist in your Baserow table
3. Field names match (or use --first-name-field etc. to specify)

## Important Notes

- **Email is Unique**: Contacts are matched by email address (case-insensitive)
- **Backup First**: Always backup your table or test on a copy first
- **Active Field**: The script manages the Active checkbox - existing values will be overwritten
- **No Deletion**: Contacts are never deleted, only marked inactive
- **Dry Run Default**: Script defaults to dry-run mode for safety
- **Excel Format**: Supports both .xls and .xlsx files

## Testing

A test suite is included to verify functionality:

```bash
python test_update_contacts.py
```

This runs unit tests with mocked API calls to ensure the sync logic works correctly.

## License

MIT License - Feel free to use and modify as needed.
