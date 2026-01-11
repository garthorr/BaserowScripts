#!/usr/bin/env python3
"""
Baserow Contacts Update Script

This script synchronizes contacts from an Excel spreadsheet to a Baserow contacts table.
It adds new contacts and marks contacts not in the spreadsheet as inactive.
"""

import os
import sys
import logging
import argparse
from typing import List, Dict, Any, Set
import requests
import pandas as pd
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BaserowContactsSync:
    """Handles synchronization of contacts between Excel and Baserow."""

    def __init__(self, api_url: str, api_token: str, table_id: int):
        """
        Initialize the Baserow contacts synchronizer.

        Args:
            api_url: Base URL for Baserow API
            api_token: API authentication token
            table_id: ID of the contacts table
        """
        self.api_url = api_url.rstrip('/')
        self.api_token = api_token
        self.table_id = table_id
        self.headers = {
            'Authorization': f'Token {api_token}',
            'Content-Type': 'application/json'
        }

    def read_excel_contacts(
        self,
        file_path: str,
        first_name_col: str = 'first name',
        last_name_col: str = 'last name',
        email_col: str = 'email'
    ) -> List[Dict[str, str]]:
        """
        Read contacts from Excel file.

        Args:
            file_path: Path to Excel file (.xls or .xlsx)
            first_name_col: Column name for first name
            last_name_col: Column name for last name
            email_col: Column name for email

        Returns:
            List of contact dictionaries with normalized data
        """
        logger.info(f"Reading contacts from: {file_path}")

        try:
            # Read Excel file (handles both .xls and .xlsx)
            df = pd.read_excel(file_path)

            # Normalize column names (case-insensitive)
            df.columns = df.columns.str.strip().str.lower()

            # Check required columns exist
            required_cols = {
                first_name_col.lower(),
                last_name_col.lower(),
                email_col.lower()
            }

            missing_cols = required_cols - set(df.columns)
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")

            # Extract contacts
            contacts = []
            for idx, row in df.iterrows():
                email = str(row[email_col.lower()]).strip()
                first_name = str(row[first_name_col.lower()]).strip()
                last_name = str(row[last_name_col.lower()]).strip()

                # Skip rows with missing email
                if not email or email.lower() == 'nan':
                    logger.warning(f"Row {idx + 2} has no email, skipping")
                    continue

                # Skip rows with missing names
                if not first_name or first_name.lower() == 'nan':
                    logger.warning(f"Row {idx + 2} has no first name, skipping")
                    continue

                if not last_name or last_name.lower() == 'nan':
                    logger.warning(f"Row {idx + 2} has no last name, skipping")
                    continue

                contacts.append({
                    'email': email.lower(),  # Normalize for comparison
                    'first_name': first_name,
                    'last_name': last_name
                })

            logger.info(f"Read {len(contacts)} valid contacts from Excel")
            return contacts

        except FileNotFoundError:
            logger.error(f"Excel file not found: {file_path}")
            raise
        except Exception as e:
            logger.error(f"Failed to read Excel file: {e}")
            raise

    def fetch_all_contacts(self) -> List[Dict[str, Any]]:
        """Fetch all contacts from Baserow table."""
        all_contacts = []
        url = f"{self.api_url}/api/database/rows/table/{self.table_id}/"
        params = {'user_field_names': 'true', 'size': 200}

        while url:
            try:
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()

                all_contacts.extend(data['results'])
                url = data.get('next')
                params = {}  # Next URL already includes params

                logger.info(f"Fetched {len(data['results'])} contacts (total: {len(all_contacts)})")

            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to fetch contacts: {e}")
                raise

        logger.info(f"Total contacts in Baserow: {len(all_contacts)}")
        return all_contacts

    def create_contact(self, contact_data: Dict[str, Any]) -> bool:
        """
        Create a new contact in Baserow.

        Args:
            contact_data: Dictionary with contact field values

        Returns:
            True if successful, False otherwise
        """
        url = f"{self.api_url}/api/database/rows/table/{self.table_id}/"
        params = {'user_field_names': 'true'}

        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=contact_data,
                params=params
            )
            response.raise_for_status()
            logger.debug(f"Created contact: {contact_data.get('email')}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create contact {contact_data.get('email')}: {e}")
            return False

    def update_contact(self, row_id: int, updates: Dict[str, Any]) -> bool:
        """
        Update an existing contact in Baserow.

        Args:
            row_id: ID of the contact row to update
            updates: Dictionary of field updates

        Returns:
            True if successful, False otherwise
        """
        if not updates:
            return True

        url = f"{self.api_url}/api/database/rows/table/{self.table_id}/{row_id}/"
        params = {'user_field_names': 'true'}

        try:
            response = requests.patch(
                url,
                headers=self.headers,
                json=updates,
                params=params
            )
            response.raise_for_status()
            logger.debug(f"Updated contact ID {row_id}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update contact {row_id}: {e}")
            return False

    def sync_contacts(
        self,
        excel_file: str,
        first_name_field: str = 'First Name',
        last_name_field: str = 'Last Name',
        email_field: str = 'Email',
        active_field: str = 'Active',
        dry_run: bool = True
    ) -> Dict[str, int]:
        """
        Synchronize contacts from Excel to Baserow.

        Args:
            excel_file: Path to Excel file
            first_name_field: Name of first name field in Baserow
            last_name_field: Name of last name field in Baserow
            email_field: Name of email field in Baserow
            active_field: Name of active checkbox field in Baserow
            dry_run: If True, only report what would be done

        Returns:
            Dictionary with statistics about the operation
        """
        stats = {
            'excel_contacts': 0,
            'baserow_contacts': 0,
            'new_contacts': 0,
            'marked_inactive': 0,
            'marked_active': 0,
            'updated': 0,
            'errors': 0
        }

        logger.info("=" * 60)
        logger.info(f"Starting contacts sync (dry_run={dry_run})")
        logger.info(f"Excel file: {excel_file}")
        logger.info("=" * 60)

        # Read contacts from Excel
        excel_contacts = self.read_excel_contacts(excel_file)
        stats['excel_contacts'] = len(excel_contacts)

        # Create lookup by email
        excel_emails = {c['email']: c for c in excel_contacts}

        # Fetch existing contacts from Baserow
        baserow_contacts = self.fetch_all_contacts()
        stats['baserow_contacts'] = len(baserow_contacts)

        # Create lookup by email (normalized)
        baserow_by_email = {}
        for contact in baserow_contacts:
            email = contact.get(email_field, '').strip().lower()
            if email:
                baserow_by_email[email] = contact

        logger.info("\n" + "=" * 60)
        logger.info("ANALYZING CHANGES")
        logger.info("=" * 60)

        # Process Excel contacts
        for excel_contact in excel_contacts:
            email = excel_contact['email']

            if email in baserow_by_email:
                # Contact exists - ensure it's marked active
                existing = baserow_by_email[email]
                is_active = existing.get(active_field, False)

                if not is_active:
                    logger.info(f"Will mark as active: {email}")
                    stats['marked_active'] += 1

                    if not dry_run:
                        updates = {active_field: True}
                        if self.update_contact(existing['id'], updates):
                            stats['updated'] += 1
                        else:
                            stats['errors'] += 1
                else:
                    logger.debug(f"Already active: {email}")

            else:
                # New contact - add it
                logger.info(f"Will add new contact: {email}")
                stats['new_contacts'] += 1

                if not dry_run:
                    contact_data = {
                        first_name_field: excel_contact['first_name'],
                        last_name_field: excel_contact['last_name'],
                        email_field: excel_contact['email'],
                        active_field: True
                    }
                    if self.create_contact(contact_data):
                        stats['updated'] += 1
                    else:
                        stats['errors'] += 1

        # Mark contacts not in Excel as inactive
        logger.info("\nChecking for contacts to mark inactive...")
        for email, contact in baserow_by_email.items():
            if email not in excel_emails:
                is_active = contact.get(active_field, False)

                if is_active:
                    logger.info(f"Will mark as inactive: {email}")
                    stats['marked_inactive'] += 1

                    if not dry_run:
                        updates = {active_field: False}
                        if self.update_contact(contact['id'], updates):
                            stats['updated'] += 1
                        else:
                            stats['errors'] += 1
                else:
                    logger.debug(f"Already inactive: {email}")

        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("SYNC SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Contacts in Excel: {stats['excel_contacts']}")
        logger.info(f"Contacts in Baserow: {stats['baserow_contacts']}")
        logger.info(f"New contacts to add: {stats['new_contacts']}")
        logger.info(f"Contacts to mark active: {stats['marked_active']}")
        logger.info(f"Contacts to mark inactive: {stats['marked_inactive']}")

        if not dry_run:
            logger.info(f"Updates performed: {stats['updated']}")
            logger.info(f"Errors: {stats['errors']}")
        else:
            logger.info("[DRY RUN] No changes were made")

        logger.info("=" * 60)

        return stats


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Sync contacts from Excel to Baserow contacts table',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to see what would happen
  python update_contacts.py --excel-file enrollment.xlsx --dry-run

  # Actually perform the sync
  python update_contacts.py --excel-file enrollment.xlsx --no-dry-run

  # Use custom field names
  python update_contacts.py --excel-file enrollment.xlsx \\
    --first-name-field "First Name" \\
    --last-name-field "Last Name" \\
    --email-field "Email" \\
    --active-field "Active"
        """
    )

    parser.add_argument(
        '--excel-file',
        required=True,
        help='Path to Excel file (.xls or .xlsx)'
    )
    parser.add_argument(
        '--table-id',
        type=int,
        help='Baserow contacts table ID (overrides .env file)'
    )
    parser.add_argument(
        '--first-name-field',
        default='First Name',
        help='Name of first name field in Baserow (default: "First Name")'
    )
    parser.add_argument(
        '--last-name-field',
        default='Last Name',
        help='Name of last name field in Baserow (default: "Last Name")'
    )
    parser.add_argument(
        '--email-field',
        default='Email',
        help='Name of email field in Baserow (default: "Email")'
    )
    parser.add_argument(
        '--active-field',
        default='Active',
        help='Name of active checkbox field in Baserow (default: "Active")'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        default=True,
        help='Perform a dry run without making changes (default: True)'
    )
    parser.add_argument(
        '--no-dry-run',
        action='store_true',
        help='Actually perform the sync (disables dry run)'
    )
    parser.add_argument(
        '--api-url',
        help='Baserow API URL (overrides .env file)'
    )
    parser.add_argument(
        '--api-token',
        help='Baserow API token (overrides .env file)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose debug logging'
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Load environment variables
    load_dotenv()

    # Get configuration from args or environment
    api_url = args.api_url or os.getenv('BASEROW_API_URL')
    api_token = args.api_token or os.getenv('BASEROW_API_TOKEN')
    table_id = args.table_id or os.getenv('CONTACTS_TABLE_ID') or os.getenv('TABLE_ID')

    # Validate required configuration
    if not api_url:
        logger.error("BASEROW_API_URL not provided (use --api-url or set in .env)")
        sys.exit(1)

    if not api_token:
        logger.error("BASEROW_API_TOKEN not provided (use --api-token or set in .env)")
        sys.exit(1)

    if not table_id:
        logger.error("Table ID not provided (use --table-id or set CONTACTS_TABLE_ID in .env)")
        sys.exit(1)

    try:
        table_id = int(table_id)
    except ValueError:
        logger.error(f"Invalid table ID: {table_id}")
        sys.exit(1)

    # Check Excel file exists
    if not os.path.exists(args.excel_file):
        logger.error(f"Excel file not found: {args.excel_file}")
        sys.exit(1)

    # Determine dry run mode
    dry_run = args.dry_run and not args.no_dry_run

    if not dry_run:
        logger.warning("⚠️  DRY RUN DISABLED - Changes will be permanent!")
        response = input("Are you sure you want to proceed? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("Operation cancelled")
            sys.exit(0)

    # Create sync client and run
    try:
        syncer = BaserowContactsSync(api_url, api_token, table_id)
        stats = syncer.sync_contacts(
            excel_file=args.excel_file,
            first_name_field=args.first_name_field,
            last_name_field=args.last_name_field,
            email_field=args.email_field,
            active_field=args.active_field,
            dry_run=dry_run
        )

        # Exit with error code if there were errors
        if stats['errors'] > 0:
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
