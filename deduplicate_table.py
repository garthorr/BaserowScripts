#!/usr/bin/env python3
"""
Baserow Table Deduplication Script

This script identifies and removes duplicate rows in a Baserow table based on a
specified identifying field, while preserving and merging link fields from duplicates.
"""

import os
import sys
import logging
import argparse
from collections import defaultdict
from typing import List, Dict, Any, Set
import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BaserowDeduplicator:
    """Handles deduplication of Baserow table rows."""

    def __init__(self, api_url: str, api_token: str, table_id: int):
        """
        Initialize the Baserow deduplicator.

        Args:
            api_url: Base URL for Baserow API
            api_token: API authentication token
            table_id: ID of the table to deduplicate
        """
        self.api_url = api_url.rstrip('/')
        self.api_token = api_token
        self.table_id = table_id
        self.headers = {
            'Authorization': f'Token {api_token}',
            'Content-Type': 'application/json'
        }

    def get_table_fields(self) -> List[Dict[str, Any]]:
        """Fetch table field metadata to identify link fields."""
        url = f"{self.api_url}/api/database/fields/table/{self.table_id}/"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch table fields: {e}")
            raise

    def get_link_fields(self) -> Set[str]:
        """Identify all link-to-table fields in the table."""
        fields = self.get_table_fields()
        link_fields = set()

        for field in fields:
            if field['type'] == 'link_row':
                link_fields.add(field['name'])
                logger.info(f"Found link field: {field['name']}")

        return link_fields

    def fetch_all_rows(self) -> List[Dict[str, Any]]:
        """Fetch all rows from the table with pagination support."""
        all_rows = []
        url = f"{self.api_url}/api/database/rows/table/{self.table_id}/"
        params = {'user_field_names': 'true', 'size': 200}

        while url:
            try:
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()

                all_rows.extend(data['results'])
                url = data.get('next')
                params = {}  # Next URL already includes params

                logger.info(f"Fetched {len(data['results'])} rows (total: {len(all_rows)})")

            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to fetch rows: {e}")
                raise

        logger.info(f"Total rows fetched: {len(all_rows)}")
        return all_rows

    def identify_duplicates(
        self,
        rows: List[Dict[str, Any]],
        identifying_field: str
    ) -> Dict[Any, List[Dict[str, Any]]]:
        """
        Group rows by the identifying field value.

        Args:
            rows: List of all rows from the table
            identifying_field: Field name to use for identifying duplicates

        Returns:
            Dictionary mapping identifying field values to lists of duplicate rows
        """
        grouped = defaultdict(list)

        for row in rows:
            key = row.get(identifying_field)

            # Skip rows with empty/null identifying field
            if key is None or key == '':
                logger.warning(f"Row {row.get('id')} has empty identifying field, skipping")
                continue

            # Normalize the key (case-insensitive for strings)
            if isinstance(key, str):
                key = key.strip().lower()

            grouped[key].append(row)

        # Filter to only groups with duplicates
        duplicates = {k: v for k, v in grouped.items() if len(v) > 1}

        logger.info(f"Found {len(duplicates)} groups of duplicates")
        total_duplicates = sum(len(v) - 1 for v in duplicates.values())
        logger.info(f"Total duplicate rows to remove: {total_duplicates}")

        return duplicates

    def merge_link_fields(
        self,
        keeper: Dict[str, Any],
        duplicates: List[Dict[str, Any]],
        link_fields: Set[str]
    ) -> Dict[str, List[int]]:
        """
        Merge link field values from duplicate rows into the keeper row.

        Args:
            keeper: The row to keep and update
            duplicates: List of duplicate rows (including the keeper)
            link_fields: Set of field names that are link fields

        Returns:
            Dictionary of link field updates to apply to keeper
        """
        updates = {}

        for field in link_fields:
            # Collect all linked IDs from all duplicates
            all_linked_ids = set()

            for row in duplicates:
                linked_values = row.get(field, [])
                if linked_values:
                    # Link fields are arrays of linked row IDs
                    if isinstance(linked_values, list):
                        all_linked_ids.update(
                            item['id'] if isinstance(item, dict) else item
                            for item in linked_values
                        )

            if all_linked_ids:
                updates[field] = list(all_linked_ids)
                logger.debug(
                    f"Merging {len(all_linked_ids)} links for field '{field}' "
                    f"in row {keeper['id']}"
                )

        return updates

    def update_row(self, row_id: int, updates: Dict[str, Any]) -> bool:
        """
        Update a row with new field values.

        Args:
            row_id: ID of the row to update
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
            logger.debug(f"Updated row {row_id} with {len(updates)} fields")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update row {row_id}: {e}")
            return False

    def delete_row(self, row_id: int) -> bool:
        """
        Delete a row from the table.

        Args:
            row_id: ID of the row to delete

        Returns:
            True if successful, False otherwise
        """
        url = f"{self.api_url}/api/database/rows/table/{self.table_id}/{row_id}/"

        try:
            response = requests.delete(url, headers=self.headers)
            response.raise_for_status()
            logger.debug(f"Deleted row {row_id}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to delete row {row_id}: {e}")
            return False

    def deduplicate(
        self,
        identifying_field: str,
        dry_run: bool = True,
        keep_strategy: str = 'first'
    ) -> Dict[str, int]:
        """
        Perform deduplication on the table.

        Args:
            identifying_field: Field name to use for identifying duplicates
            dry_run: If True, only report what would be done without making changes
            keep_strategy: Which duplicate to keep ('first' or 'last' based on row ID)

        Returns:
            Dictionary with statistics about the operation
        """
        stats = {
            'rows_fetched': 0,
            'duplicate_groups': 0,
            'rows_updated': 0,
            'rows_deleted': 0,
            'errors': 0
        }

        logger.info("=" * 60)
        logger.info(f"Starting deduplication (dry_run={dry_run})")
        logger.info(f"Identifying field: {identifying_field}")
        logger.info(f"Keep strategy: {keep_strategy}")
        logger.info("=" * 60)

        # Fetch table metadata
        link_fields = self.get_link_fields()

        # Fetch all rows
        all_rows = self.fetch_all_rows()
        stats['rows_fetched'] = len(all_rows)

        # Identify duplicates
        duplicate_groups = self.identify_duplicates(all_rows, identifying_field)
        stats['duplicate_groups'] = len(duplicate_groups)

        if not duplicate_groups:
            logger.info("No duplicates found!")
            return stats

        # Process each group of duplicates
        for identifier, duplicates in duplicate_groups.items():
            logger.info(f"\nProcessing group: {identifier} ({len(duplicates)} duplicates)")

            # Sort duplicates by ID to ensure consistent behavior
            duplicates.sort(key=lambda x: x['id'])

            # Determine which row to keep
            if keep_strategy == 'first':
                keeper = duplicates[0]
                to_remove = duplicates[1:]
            else:  # 'last'
                keeper = duplicates[-1]
                to_remove = duplicates[:-1]

            logger.info(f"  Keeping row {keeper['id']}")
            logger.info(f"  Removing {len(to_remove)} duplicate(s): {[r['id'] for r in to_remove]}")

            # Merge link fields from all duplicates (including keeper)
            link_updates = self.merge_link_fields(keeper, duplicates, link_fields)

            if dry_run:
                if link_updates:
                    logger.info(f"  [DRY RUN] Would update {len(link_updates)} link fields")
                    for field, values in link_updates.items():
                        logger.info(f"    {field}: {len(values)} links")
                logger.info(f"  [DRY RUN] Would delete {len(to_remove)} row(s)")
            else:
                # Update keeper with merged link fields
                if link_updates:
                    if self.update_row(keeper['id'], link_updates):
                        stats['rows_updated'] += 1
                    else:
                        stats['errors'] += 1
                        logger.error(f"  Failed to update keeper row {keeper['id']}, skipping deletion")
                        continue

                # Delete duplicate rows
                for row in to_remove:
                    if self.delete_row(row['id']):
                        stats['rows_deleted'] += 1
                    else:
                        stats['errors'] += 1

        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("DEDUPLICATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total rows fetched: {stats['rows_fetched']}")
        logger.info(f"Duplicate groups found: {stats['duplicate_groups']}")

        if dry_run:
            logger.info(f"Would update: {sum(1 for d in duplicate_groups.values())} rows")
            logger.info(f"Would delete: {sum(len(d) - 1 for d in duplicate_groups.values())} rows")
        else:
            logger.info(f"Rows updated: {stats['rows_updated']}")
            logger.info(f"Rows deleted: {stats['rows_deleted']}")
            logger.info(f"Errors: {stats['errors']}")

        logger.info("=" * 60)

        return stats


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Deduplicate Baserow table rows while preserving link fields',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to see what would happen
  python deduplicate_table.py --identifying-field Email --dry-run

  # Actually perform deduplication
  python deduplicate_table.py --identifying-field Email

  # Keep the last occurrence instead of first
  python deduplicate_table.py --identifying-field Email --keep-strategy last

  # Use custom configuration
  python deduplicate_table.py --table-id 12345 --identifying-field Username
        """
    )

    parser.add_argument(
        '--identifying-field',
        required=True,
        help='Name of the field to use for identifying duplicates'
    )
    parser.add_argument(
        '--table-id',
        type=int,
        help='Baserow table ID (overrides .env file)'
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
        help='Actually perform the deduplication (disables dry run)'
    )
    parser.add_argument(
        '--keep-strategy',
        choices=['first', 'last'],
        default='first',
        help='Which duplicate to keep: first (lowest ID) or last (highest ID) (default: first)'
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
    table_id = args.table_id or os.getenv('TABLE_ID')

    # Validate required configuration
    if not api_url:
        logger.error("BASEROW_API_URL not provided (use --api-url or set in .env)")
        sys.exit(1)

    if not api_token:
        logger.error("BASEROW_API_TOKEN not provided (use --api-token or set in .env)")
        sys.exit(1)

    if not table_id:
        logger.error("TABLE_ID not provided (use --table-id or set in .env)")
        sys.exit(1)

    try:
        table_id = int(table_id)
    except ValueError:
        logger.error(f"Invalid table ID: {table_id}")
        sys.exit(1)

    # Determine dry run mode
    dry_run = args.dry_run and not args.no_dry_run

    if not dry_run:
        logger.warning("⚠️  DRY RUN DISABLED - Changes will be permanent!")
        response = input("Are you sure you want to proceed? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("Operation cancelled")
            sys.exit(0)

    # Create deduplicator and run
    try:
        deduplicator = BaserowDeduplicator(api_url, api_token, table_id)
        stats = deduplicator.deduplicate(
            identifying_field=args.identifying_field,
            dry_run=dry_run,
            keep_strategy=args.keep_strategy
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
